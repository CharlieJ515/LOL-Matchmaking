import asyncio
import json
from typing import List
import functools
import itertools
import os
import time
import random
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg
import psycopg_pool
from pydantic import BaseModel, RootModel
from dotenv import load_dotenv
import httpx

import limits
from limits.limits import RateLimitItem, RateLimitItemPerSecond
from limits.aio.storage import MemoryStorage, RedisStorage
from limits.aio.strategies import RateLimiter, FixedWindowRateLimiter

import structlog
import structlog.stdlib

from riot_api import Client as RiotClient
from riot_api.types import Puuid
from riot_api.types.request import (
    RoutePlatform,
    RankedTier,
    RankedQueue,
    RankedDivision,
)
from riot_api.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ServerError,
)

import logging_configuration

# level = os.environ.get("LOG_LEVEL", "INFO").upper()
# LOG_LEVEL = getattr(logging, level)
logger = structlog.get_logger("collector")
# logger.info(f"Set log level to {LOG_LEVEL}")
load_dotenv()


class PuuidListDTO(RootModel):
    root: List["PuuidDTO"]


class PuuidDTO(BaseModel):
    puuid: Puuid


API_KEY = os.getenv("RIOT_API_KEY", "")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
REDIS_DSN = os.getenv("REDIS_DSN", "")
INSERT_USER_SQL = """
    INSERT INTO users (puuid, platform_id) 
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
"""
storage = MemoryStorage()
limiter = FixedWindowRateLimiter(storage)
limit_namespace = API_KEY[-6:]
logger.info("Initialized rate limiter storage", storage=str(storage.__class__.__name__))


async def insert_user(
    logger: structlog.BoundLogger, platform: RoutePlatform, response: PuuidListDTO
):
    if pool is None:
        raise RuntimeError("Connection pool is not initialized")

    # TODO - add error handling, logging
    rows = [(puuid_dto.puuid, platform.name) for puuid_dto in response.root]
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(INSERT_USER_SQL, rows)


def add_rate_limit(
    logger: structlog.BoundLogger,
    func,
    limiter: RateLimiter,
    limits_with_keys: list[tuple[RateLimitItem, tuple[str, ...]]],
    safety_margin: float = 0.0,
    jitter: float = 0.2,
):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        while True:
            flag = True
            for limit, keys in limits_with_keys:
                if await limiter.test(limit, *keys):
                    continue

                window = await limiter.get_window_stats(limit, *keys)
                sleep_time = (
                    max(0, window.reset_time - time.time())
                    + safety_margin
                    + random.uniform(0, jitter)
                )
                logger.debug(
                    f"Local rate limit exceeded. Sleeping for {sleep_time:.2f}s",
                    limit=limit,
                    keys=keys,
                    sleep_time=sleep_time,
                )
                await asyncio.sleep(sleep_time)

                flag = False
                break  # retry whole loop after sleep

            if flag:
                break

        # now commit all
        for limit, keys in limits_with_keys:
            await limiter.hit(limit, *keys)

        logger.debug("Limits acquired. Executing query")
        res, header = await func(*args, **kwargs)
        return res, header

    return wrapper


def log_header_limits(logger: structlog.BoundLogger, headers: httpx.Headers):
    from datetime import datetime

    def parse_limit_string(s: str):
        try:
            return [tuple(map(int, part.split(":"))) for part in s.split(",") if part]
        except Exception:
            return []

    platform_limit = parse_limit_string(headers.get("X-App-Rate-Limit", ""))
    platform_count = parse_limit_string(headers.get("X-App-Rate-Limit-Count", ""))
    endpoint_limit = parse_limit_string(headers.get("X-Method-Rate-Limit", ""))
    endpoint_count = parse_limit_string(headers.get("X-Method-Rate-Limit-Count", ""))

    def build_structured_limits(limit, count, window):
        return {
            "count": count,
            "limit": limit,
            "window": window,
            "remaining": max(0, limit - count),
        }

    # time of server when response was sent
    date_str = headers["date"]
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
    response_time = dt.strftime("%Y-%m-%d %H:%M.%S")

    log_data = {}
    log_data["platform_limit1"] = build_structured_limits(
        platform_limit[0][0], platform_limit[0][1], platform_count[0][0]
    )
    log_data["platform_limit2"] = build_structured_limits(
        platform_limit[1][0], platform_limit[1][1], platform_count[1][0]
    )
    log_data["endpoint_limit"] = build_structured_limits(
        endpoint_limit[0][0], endpoint_limit[0][1], endpoint_count[0][0]
    )

    logger.debug(
        "Riot server rate limit status", response_time=response_time, **log_data
    )


async def worker(
    platform: RoutePlatform,
    queue: RankedQueue,
    tier: RankedTier,
    division: RankedDivision,
    page: int,
    worker_id: int,
    stop_all_workers: asyncio.Event,
    stop_platform_workers: asyncio.Event,
):
    logger = structlog.get_logger("collector").bind(
        worker=worker_id,
        platform=platform.value,
        queue=queue.value,
        tier=tier.value,
        division=division.value,
    )
    logger.info("Worker started")

    client = RiotClient(API_KEY)

    # add limits to region and endpoint
    limits_with_keys = [
        (
            RateLimitItemPerSecond(int(20 * 0.9), 1 + 1, limit_namespace),
            (platform.name,),
        ),
        (
            RateLimitItemPerSecond(int(50 * 0.9), 10 + 1, limit_namespace),
            (
                platform.name,
                "get_league_entries_by_tier",
            ),
        ),
        (
            RateLimitItemPerSecond(int(100 * 0.9), 120 + 1, limit_namespace),
            (platform.name,),
        ),
    ]
    client.get_league_entries_by_tier = add_rate_limit(
        logger, client.get_league_entries_by_tier, limiter, limits_with_keys
    )
    logger.debug("Added Rate Limit")

    while not stop_all_workers.is_set() and not stop_platform_workers.is_set():
        if stop_all_workers.is_set():
            logger.debug("stop_all_workers is set, stopping worker")
            break
        if stop_platform_workers.is_set():
            logger.debug("stop_platform_workers is set, stopping worker")
            break

        try:
            res, headers = await client.get_league_entries_by_tier(
                platform, queue, tier, division, page, response_model=PuuidListDTO
            )
        except httpx.HTTPError as e:
            logger.critical(
                "Encountered unexpected HTTP error, stopping worker",
                page=page,
                error=str(e),
                exc_info=True,
            )
            break
        except ServerError as e:
            # stop all platform workers as problem resides in the server
            logger.critical(
                "Encountered server error, stopping all platform workers",
                status_code=e.status_code,
                headers=e.headers,
                body=e.body,
            )
            stop_platform_workers.set()
            break
        except UnauthorizedError as e:
            # stop all workers as API key is invalid
            logger.critical(
                "Invalid API key, stopping all workers",
                API_KEY=API_KEY,
                status_code=e.status_code,
                headers=e.headers,
                body=e.body,
            )
            stop_all_workers.set()
            continue
        except RateLimitError as e:
            # wait for retry_after seconds then retry
            logger.critical(
                f"Server side rate limit exceeded. Sleeping for {e.retry_after}s",
                status_code=e.status_code,
                headers=e.headers,
                body=e.body,
                retry_after=e.retry_after,
            )
            # await asyncio.sleep(e.retry_after)
            stop_all_workers.set()
            break
        except (BadRequestError, ForbiddenError, NotFoundError) as e:
            # something wrong with query parameter, stopping current worker
            logger.critical(
                "Invalid request, stopping current user",
                status_code=e.status_code,
                headers=e.headers,
                body=e.body,
                page=page,
            )
            break

        logger.debug(
            f"Fetched page {page} for {platform.name} {tier} {division}, got {len(res.root)} results"
        )
        log_header_limits(logger, headers)

        # if response is empty list, break
        if not res.root:
            logger.info(
                f"Region: {platform.name}, Queue: {queue}, Tier: {tier}, Division: {division} - Completed at {page} page"
            )
            break

        # store Puuid to database
        await insert_user(logger, platform, res)
        logger.debug(
            f"Page {page} for {platform.name} {tier} {division} inserted to DB"
        )

        page += 1


async def main():
    global pool
    pool = psycopg_pool.AsyncConnectionPool(POSTGRES_DSN, max_size=20)
    logger.debug("Opening psycopg pool")
    await pool.open()
    logger.info(f"Created psycopg pool with max_size {pool.max_size}")

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logger.info(f"REDIS_DSN: {REDIS_DSN}")

    stop_all_workers = asyncio.Event()

    tiers = [
        RankedTier.IRON,
        RankedTier.BRONZE,
        RankedTier.SILVER,
        RankedTier.GOLD,
        RankedTier.PLATINUM,
        RankedTier.EMERALD,
        RankedTier.DIAMOND,
    ]

    logger.info("Starting all workers...")
    tasks = []
    worker_id = 0
    for platform in [RoutePlatform.KR]:
        stop_platform_workers = asyncio.Event()
        for queue, tier, division in itertools.product(
            RankedQueue, tiers, RankedDivision
        ):
            w = worker(
                platform,
                queue,
                tier,
                division,
                1,
                worker_id,
                stop_all_workers,
                stop_platform_workers,
            )
            worker_id += 1
            tasks.append(w)

    # stop_platform_workers = asyncio.Event()
    # tasks.append(
    #     worker(
    #         RoutePlatform.KR,
    #         RankedQueue.RANKED_SOLO_5x5,
    #         RankedTier.DIAMOND,
    #         RankedDivision.I,
    #         1,
    #         worker_id,
    #         stop_all_workers,
    #         stop_platform_workers,
    #     )
    # )
    logger.info(f"Created {len(tasks)} workers")

    await asyncio.gather(*tasks)

    if stop_all_workers.is_set():
        logger.info("All workers stopped.")
    else:
        logger.info("All workers completed.")

    logger.debug("Closing psycopg pool")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())

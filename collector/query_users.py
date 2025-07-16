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

import psycopg
import psycopg_pool
from pydantic import BaseModel, RootModel
from dotenv import load_dotenv
import httpx

import limits
from limits.limits import RateLimitItem, RateLimitItemPerSecond
from limits.aio.storage import MemoryStorage, RedisStorage
from limits.aio.strategies import RateLimiter, FixedWindowRateLimiter

from riot_api import Client as RiotClient
from riot_api.types import Puuid
from riot_api.types.request import (
    RoutePlatform,
    RankedTier,
    RankedQueue,
    RankedDivision,
)
from riot_api.exceptions import RateLimitError

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        RotatingFileHandler("app.log", maxBytes=10 * 1024 * 1024, backupCount=5),
        logging.StreamHandler(),  # keep printing to console
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
logger.debug(f"Using rate limiter storage: {storage.__class__.__name__}")


async def insert_user(platform: RoutePlatform, response: PuuidListDTO):
    if pool is None:
        raise RuntimeError("Connection pool is not initialized")

    rows = [(puuid_dto.puuid, platform.name) for puuid_dto in response.root]
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(INSERT_USER_SQL, rows)


def add_rate_limit(
    func,
    limiter: RateLimiter,
    limits_with_keys: list[tuple[RateLimitItem, tuple[str, ...]]],
    prefix: str,
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
                    f"{prefix} Limit {limit} for {keys} exceeded. Sleeping for {sleep_time:.2f}s"
                )
                await asyncio.sleep(sleep_time)

                flag = False
                break  # retry whole loop after sleep

            if flag:
                break

        # now commit all
        for limit, keys in limits_with_keys:
            await limiter.hit(limit, *keys)

        logger.debug(f"{prefix} Limits acquired. Executing query")
        res, header = await func(*args, **kwargs)
        return res, header

    return wrapper


def log_header_limits(headers: httpx.Headers, prefix):
    def parse_limit_string(s: str):
        return [tuple(map(int, part.split(":"))) for part in s.split(",")]

    platform_limit = parse_limit_string(headers.get("X-App-Rate-Limit", ""))
    platform_count = parse_limit_string(headers.get("X-App-Rate-Limit-Count", ""))
    endpoint_limit = parse_limit_string(headers.get("X-Method-Rate-Limit", ""))
    endpoint_count = parse_limit_string(headers.get("X-Method-Rate-Limit-Count", ""))

    def format_limits(name, limits, counts):
        lines = [f"{name}:"]
        for (limit, window), (count, _) in zip(limits, counts):
            remaining = max(0, limit - count)
            lines.append(f"  {count}/{limit} in {window}s (remaining: {remaining})")
        return "\n".join(lines)

    log_parts = []
    if platform_limit and platform_count:
        log_parts.append(
            format_limits("Platform Rate Limit", platform_limit, platform_count)
        )
    if endpoint_limit and endpoint_count:
        log_parts.append(
            format_limits("Endpoint Rate Limit", endpoint_limit, endpoint_count)
        )

    log_message = "\n".join(log_parts)
    logger.debug(f"{prefix}\n{log_message}")


global stop_workers
stop_workers = False


async def worker(
    platform: RoutePlatform,
    queue: RankedQueue,
    tier: RankedTier,
    division: RankedDivision,
    page: int,
    worker_id: int,
    stop_all_workers: asyncio.Event,
    stop_region_workers: asyncio.Event,
):
    prefix = f"[Worker {worker_id:04d}]"
    logger.info(f"{prefix} started for {platform.name}, {queue}, {tier}, {division}")

    # storage = RedisStorage(REDIS_DSN)

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
        client.get_league_entries_by_tier, limiter, limits_with_keys, prefix
    )

    while not stop_all_workers.is_set() and not stop_region_workers.is_set():
        try:
            res, headers = await client.get_league_entries_by_tier(
                platform, queue, tier, division, page, response_model=PuuidListDTO
            )
        except httpx.HTTPError as e:
            return
        except RateLimitError as e:
            continue
        logger.debug(
            f"Fetched page {page} for {platform.name} {tier} {division}, got {len(res.root)} results"
        )
        log_header_limits(headers, prefix)

        # if response is empty list, break
        if not res.root:
            logger.info(
                f"Region: {platform.name}, Queue: {queue}, Tier: {tier}, Division: {division} - Completed at {page} page"
            )
            break

        # store Puuid to database
        await insert_user(platform, res)
        logger.debug(
            f"Page {page} for {platform.name} {tier} {division} inserted to DB"
        )

        page += 1


async def main():
    global pool
    pool = psycopg_pool.AsyncConnectionPool(POSTGRES_DSN, max_size=20)

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logger.info(f"REDIS_DSN: {REDIS_DSN}")

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
    tasks = [
        worker(platform, queue, tier, division, 1, worker_id)
        for worker_id, (platform, queue, tier, division) in enumerate(
            itertools.product(RoutePlatform, RankedQueue, tiers, RankedDivision)
        )
    ]
    logger.info(f"Created {len(tasks)} workers")

    # tasks = [
    #     worker(
    #         RoutePlatform.KR,
    #         RankedQueue.RANKED_SOLO_5x5,
    #         RankedTier.DIAMOND,
    #         RankedDivision.I,
    #         1,
    #     )
    # ]

    await asyncio.gather(*tasks)
    logger.info("All workers completed.")


if __name__ == "__main__":
    asyncio.run(main())

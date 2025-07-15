import asyncio
import logging
import json
from typing import List
import functools
import itertools
import os
import time
import random

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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),  # keep printing to console
    ],
)
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
logging.debug(f"Using rate limiter storage: {storage.__class__.__name__}")


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
    limit: RateLimitItem,
    debug_identifier: str,
    *identifiers: str,
):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        while True:
            window = await limiter.get_window_stats(limit, *identifiers)
            logging.debug(
                f"{debug_identifier}: Remaining rate limit {window.remaining}"
            )

            if await limiter.hit(limit, *identifiers):
                break

            window = await limiter.get_window_stats(limit, *identifiers)
            safety_margin = 0.3 + random.uniform(0.1, 0.3)
            sleep_duration = max(0, window.reset_time - time.time() + safety_margin)
            logging.debug(
                f"{debug_identifier}: Rate limit reached, sleeping for {sleep_duration:.2f} seconds"
            )
            await asyncio.sleep(sleep_duration)

        logging.debug(f"{debug_identifier}: Rate limit check passed, running function")
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
    logging.debug(f"{prefix}\n{log_message}")


async def worker(
    platform: RoutePlatform,
    queue: RankedQueue,
    tier: RankedTier,
    division: RankedDivision,
    page: int,
    worker_id: int,
):
    prefix = f"[Worker {worker_id:04d}]"
    logging.info(f"{prefix} started for {platform.name}, {queue}, {tier}, {division}")

    # storage = RedisStorage(REDIS_DSN)

    client = RiotClient(API_KEY)

    # add limits to region and endpoint
    platform_limit2 = RateLimitItemPerSecond(int(20 * 0.9), 1 + 1, limit_namespace)
    client.send_request = add_rate_limit(
        client.send_request,
        limiter,
        platform_limit2,
        f"{prefix} PlatformLimit2",
        platform.name,
    )
    endpoint_limit = RateLimitItemPerSecond(int(50 * 0.9), 10 + 1, limit_namespace)
    client.get_league_entries_by_tier = add_rate_limit(
        client.get_league_entries_by_tier,
        limiter,
        endpoint_limit,
        f"{prefix} EndpointLimit get_league_entries_by_tier",
        platform.name,
        "get_league_entries_by_tier",
    )
    platform_limit1 = RateLimitItemPerSecond(int(100 * 0.9), 120 + 1, limit_namespace)
    client.send_request = add_rate_limit(
        client.send_request,
        limiter,
        platform_limit1,
        f"{prefix} PlatformLimit1",
        platform.name,
    )

    while True:
        res, headers = await client.get_league_entries_by_tier(
            platform, queue, tier, division, page, response_model=PuuidListDTO
        )
        logging.debug(
            f"Fetched page {page} for {platform.name} {tier} {division}, got {len(res.root)} results"
        )
        log_header_limits(headers, prefix)

        # if response is empty list, break
        if not res.root:
            logging.info(
                f"Region: {platform.name}, Queue: {queue}, Tier: {tier}, Division: {division} - Completed at {page} page"
            )
            break

        # store Puuid to database
        await insert_user(platform, res)
        logging.debug(
            f"Page {page} for {platform.name} {tier} {division} inserted to DB"
        )

        page += 1


async def main():
    global pool
    pool = psycopg_pool.AsyncConnectionPool(POSTGRES_DSN, max_size=20)

    logging.info(f"RIOT_API_KEY: {API_KEY}")
    logging.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logging.info(f"REDIS_DSN: {REDIS_DSN}")

    tiers = [
        RankedTier.IRON,
        RankedTier.BRONZE,
        RankedTier.SILVER,
        RankedTier.GOLD,
        RankedTier.PLATINUM,
        RankedTier.EMERALD,
        RankedTier.DIAMOND,
    ]

    logging.info("Starting all workers...")
    tasks = [
        worker(platform, queue, tier, division, 1, worker_id)
        for worker_id, (platform, queue, tier, division) in enumerate(
            itertools.product([RoutePlatform.KR], RankedQueue, tiers, RankedDivision)
        )
    ]
    logging.info(f"Created {len(tasks)} workers")

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
    logging.info("All workers completed.")


if __name__ == "__main__":
    asyncio.run(main())

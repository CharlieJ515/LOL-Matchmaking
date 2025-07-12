import asyncio
import logging
import json
from typing import List
import functools
import itertools

import psycopg
import psycopg_pool
from pydantic import BaseModel, RootModel

import limits
from limits.limits import RateLimitItem, RateLimitItemPerSecond
from limits.aio.storage import RedisStorage
from limits.aio.strategies import RateLimiter, FixedWindowRateLimiter

from riot_api import Client as RiotClient
from riot_api.types import Puuid
from riot_api.types.request import (
    RoutePlatform,
    RankedTier,
    RankedQueue,
    RankedDivision,
)

logging.basicConfig(level=logging.INFO)


class PuuidListDTO(RootModel):
    root: List["PuuidDTO"]


class PuuidDTO(BaseModel):
    puuid: Puuid


API_KEY = "RGAPI-9cfe84ea-c1b7-47bf-bfa8-f0df3d0aaf0c"
POSTGRES_DSN = ""
REDIS_DSN = ""
INSERT_USER_SQL = "INSERT INTO users (puuid, platform) VALUES (%s, %s)"

pool = psycopg_pool.AsyncConnectionPool(POSTGRES_DSN, max_size=20)


async def insert_user(platform: RoutePlatform, response: PuuidListDTO):
    rows = [(puuid_dto.puuid, platform.name) for puuid_dto in response.root]
    async with pool.connection() as conn:
        await conn.execute(INSERT_USER_SQL, rows)


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
            if limiter.hit(limit, *identifiers):
                break

            window = await limiter.get_window_stats(limit, *identifiers)
            logging.debug(
                f"{debug_identifier}: Rate limit reached, sleeping for {window.reset_time} seconds"
            )
            await asyncio.sleep(window.reset_time)

        logging.debug(f"{debug_identifier}: Rate limit check passed, running function")
        res, header = await func(*args, **kwargs)
        return res, header

    return wrapper


async def worker(
    platform: RoutePlatform,
    queue: RankedQueue,
    tier: RankedTier,
    division: RankedDivision,
    page: int,
):
    storage = RedisStorage(REDIS_DSN)
    limiter = FixedWindowRateLimiter(storage)
    limit_namespace = API_KEY[-6:]

    client = RiotClient(API_KEY)
    # add limits to region and endpoint
    platform_limit1 = RateLimitItemPerSecond(100, 120, limit_namespace)
    client.send_request = add_rate_limit(
        client.send_request, limiter, platform_limit1, "PlatformLimit1", platform.name
    )
    platform_limit2 = RateLimitItemPerSecond(20, 1, limit_namespace)
    client.send_request = add_rate_limit(
        client.send_request, limiter, platform_limit2, "PlatformLimit2", platform.name
    )
    endpoint_limit = RateLimitItemPerSecond(50, 10, limit_namespace)
    client.get_league_entries_by_tier = add_rate_limit(
        client.get_league_entries_by_tier,
        limiter,
        endpoint_limit,
        "EndpointLimit get_league_entries_by_tier",
        platform.name,
        "get_league_entries_by_tier",
    )

    while True:
        res, headers = await client.get_league_entries_by_tier(
            platform, queue, tier, division, page, response_model=PuuidListDTO
        )

        # if response is empty list, break
        if not res.root:
            logging.info(
                f"Region: {platform.name}, Queue: {queue}, Tier: {tier}, Division: {division} - Completed at {page} page"
            )
            break

        # store Puuid to database
        await insert_user(platform, res)

        page += 1


async def main():
    tiers = [
        RankedTier.IRON,
        RankedTier.BRONZE,
        RankedTier.SILVER,
        RankedTier.GOLD,
        RankedTier.PLATINUM,
        RankedTier.EMERALD,
        RankedTier.DIAMOND,
    ]
    tasks = [
        worker(platform, queue, tier, division, 1)
        for platform, queue, tier, division in itertools.product(
            RoutePlatform, RankedQueue, tiers, RankedDivision
        )
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

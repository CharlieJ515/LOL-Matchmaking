import asyncio
import logging
import json
from typing import List
import functools
import itertools

import psycopg
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

API_KEY = "RGAPI-9cfe84ea-c1b7-47bf-bfa8-f0df3d0aaf0c"
POSTGRES_DSN = ""
REDIS_DSN = ""


class PuuidListDTO(RootModel):
    root: List["PuuidDTO"]


class PuuidDTO(BaseModel):
    puuid: Puuid


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
    region: RoutePlatform,
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
    region_limit1 = RateLimitItemPerSecond(100, 120, limit_namespace)
    client.send_request = add_rate_limit(
        client.send_request, limiter, region_limit1, "RegionLimit1", region.name
    )
    region_limit2 = RateLimitItemPerSecond(20, 1, limit_namespace)
    client.send_request = add_rate_limit(
        client.send_request, limiter, region_limit2, "RegionLimit2", region.name
    )
    endpoint_limit = RateLimitItemPerSecond(50, 10, limit_namespace)
    client.get_league_entries_by_tier = add_rate_limit(
        client.get_league_entries_by_tier,
        limiter,
        endpoint_limit,
        "EndpointLimit get_league_entries_by_tier",
        region.name,
        "get_league_entries_by_tier",
    )

    while True:
        res, headers = await client.get_league_entries_by_tier(
            region, queue, tier, division, page, response_model=PuuidListDTO
        )

        # if response is empty list, break
        if not res.root:
            logging.info(
                f"Region: {region.name}, Queue: {queue}, Tier: {tier}, Division: {division} - Completed at {page} page"
            )
            break

        # store Puuid to database

        page += 1


async def main():
    tasks = [
        worker(region, queue, tier, division, 1)
        for region, queue, tier, division in itertools.product(
            RoutePlatform, RankedQueue, RankedTier, RankedDivision
        )
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

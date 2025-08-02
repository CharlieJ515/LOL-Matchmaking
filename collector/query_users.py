from dataclasses import replace
from typing import Optional
import asyncio
import itertools
import os

from pydantic import BaseModel, RootModel
from dotenv import load_dotenv
import httpx

import structlog
import structlog.stdlib

from riot_api.rate_limit_client import (
    RateLimitClient as RiotClient,
    RateLimitItemPerSecond,
)
from riot_api.types import Puuid
from riot_api.types.request import (
    RoutePlatform,
    RankedTier,
    RankedQueue,
    RankedDivision,
)

from logs.config import get_logger, configure_logging
from execution.query_job import QueryJob
from execution.worker import worker
from db.pool import get_pool, init_pool, close_pool
from db.users import insert_user

load_dotenv()


API_KEY = os.getenv("RIOT_API_KEY", "")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
REDIS_DSN = os.getenv("REDIS_DSN", "")
PSYCOPG_POOL_MAX_SIZE = 10
WORKER_PER_PLATFORM = 1


class PuuidListDTO(RootModel):
    root: list["PuuidDTO"]


class PuuidDTO(BaseModel):
    puuid: Puuid


def increment(
    logger: structlog.BoundLogger,
    query_job: QueryJob[PuuidListDTO],
    result: PuuidListDTO,
    headers: httpx.Headers,
) -> Optional[QueryJob[PuuidListDTO]]:
    if not result.root:
        return None

    page = query_job.params.get("page")
    assert page is not None

    new_page = page + 1
    return replace(query_job, params={**query_job.params, "page": new_page})


async def on_success(
    logger: structlog.BoundLogger,
    query_job: QueryJob[PuuidListDTO],
    result: PuuidListDTO,
    headers: httpx.Headers,
):
    pool = get_pool()
    platform: Optional[RoutePlatform] = query_job.params.get("platform")
    if not platform:
        raise ValueError

    puuids = [puuid_dto.puuid for puuid_dto in result.root]
    await insert_user(pool, platform, puuids)

    logger.info(f"Inserted {len(puuids)} Users")


async def main():
    configure_logging()
    logger = get_logger()

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logger.info(f"PSYCOPG_POOL_MAX_SIZE: {PSYCOPG_POOL_MAX_SIZE}")
    logger.info(f"REDIS_DSN: {REDIS_DSN}")
    logger.info(f"WORKER_PER_PLATFORM: {WORKER_PER_PLATFORM}")

    # Initialize psycopg pool
    await init_pool(POSTGRES_DSN, PSYCOPG_POOL_MAX_SIZE)

    # Query Parameters
    platforms: list[tuple[RoutePlatform, int]] = [
        # America
        (RoutePlatform.NA1, 797),  # 0
        (RoutePlatform.BR1, 797),  # 1
        (RoutePlatform.LA1, 797),  # 2
        (RoutePlatform.LA2, 797),  # 3
        # Europe
        (RoutePlatform.EUN1, 797),  # 4
        (RoutePlatform.EUW1, 797),  # 5
        (RoutePlatform.TR1, 797),  # 6
        (RoutePlatform.RU, 797),  # 7
        # Asia
        # (RoutePlatform.KR, 1),
        (RoutePlatform.JP1, 797),  # 8
        # SEA
        (RoutePlatform.OC1, 797),  # 9
        (RoutePlatform.SG2, 797),  # 10
        (RoutePlatform.TW2, 797),  # 11
        (RoutePlatform.VN2, 545),  # 12
    ]
    ranked_queues = [RankedQueue.RANKED_SOLO_5x5, RankedQueue.RANKED_FLEX_SR]
    tiers = [
        RankedTier.IRON,
        RankedTier.BRONZE,
        RankedTier.SILVER,
        RankedTier.GOLD,
        RankedTier.PLATINUM,
        RankedTier.EMERALD,
        RankedTier.DIAMOND,
    ]

    logger.info("Creating workers...")
    queue_list = []
    worker_id = 0
    worker_list = []
    stop_all_workers = asyncio.Event()
    for platform, start_page in platforms:
        stop_route_workers = asyncio.Event()

        # Create new queue
        job_queue = asyncio.Queue()
        queue_list.append(job_queue)

        # add margin to local limits
        key = (platform.name, "get_league_entries_by_tier")
        RiotClient.limits[key] = RateLimitItemPerSecond(45, 13, "RIOT_API")
        key = (platform.name, "route_short")
        RiotClient.limits[key] = RateLimitItemPerSecond(10, 1, "RIOT_API")
        key = (platform.name, "route_long")
        RiotClient.limits[key] = RateLimitItemPerSecond(95, 123, "RIOT_API")

        # add jobs to the queue
        for queue, tier, division in itertools.product(
            ranked_queues, tiers, RankedDivision
        ):
            await job_queue.put(
                QueryJob[PuuidListDTO](
                    method_name="get_league_entries_by_tier",
                    params={
                        "platform": platform,
                        "queue": queue,
                        "tier": tier,
                        "division": division,
                        "page": start_page,
                        "response_model": PuuidListDTO,
                    },
                    increment=increment,
                    on_success=on_success,
                )
            )

        # Create workers
        for _ in range(WORKER_PER_PLATFORM):
            w = worker(
                API_KEY,
                worker_id,
                job_queue,
                stop_all_workers,
                stop_route_workers,
            )
            worker_id += 1
            worker_list.append(w)

    logger.info(f"Created {len(worker_list)} workers")
    await asyncio.gather(*worker_list)

    if stop_all_workers.is_set():
        logger.info("All workers stopped.")
    else:
        logger.info("All workers completed.")

    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())

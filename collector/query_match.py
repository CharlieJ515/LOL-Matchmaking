from dataclasses import replace
from datetime import timedelta
from typing import Match, Optional
import asyncio
import os

from dotenv import load_dotenv
import httpx

import structlog
import structlog.stdlib

from riot_api.rate_limit_client import (
    RateLimitClient as RiotClient,
    RateLimitItemPerSecond,
    RouteRegion,
)
from riot_api.types import Puuid
from riot_api.types.dto import MatchIdListDTO
from riot_api.types.request import (
    RoutePlatform,
)

from logs.config import get_logger, configure_logging
from execution.query_job import BaseJobFactory, QueryJob, refill_queue
from execution.worker import worker
from db.pool import get_pool, init_pool, close_pool
from db.users import claim_users, update_match_id_query_date
from db.matches import insert_match_ids

load_dotenv()


API_KEY = os.getenv("RIOT_API_KEY", "")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
REDIS_DSN = os.getenv("REDIS_DSN", "")
PSYCOPG_POOL_MAX_SIZE = 10
WORKER_PER_REGION = 1

REFILL_QUEUE_THRESHOLD = 30
JOB_FACTORY_BATCH_SIZE = 20


def increment(
    logger: structlog.BoundLogger,
    query_job: QueryJob[MatchIdListDTO],
    result: MatchIdListDTO,
    headers: httpx.Headers,
) -> Optional[QueryJob[MatchIdListDTO]]:
    start = query_job.params.get("start")
    count = query_job.params.get("count")
    assert start is not None
    assert count is not None

    if len(result.root) < count:
        return None

    new_start = start + count
    return replace(query_job, params={**query_job.params, "start": new_start})


async def on_success(
    logger: structlog.BoundLogger,
    query_job: QueryJob[MatchIdListDTO],
    result: MatchIdListDTO,
    headers: httpx.Headers,
):
    pool = get_pool()

    region = query_job.params.get("region")
    assert region is not None
    match_ids = result.root
    await insert_match_ids(pool, region, match_ids)

    logger.info(f"Inserted {len(match_ids)} match ids")


async def on_completion(
    logger: structlog.BoundLogger,
    query_job: QueryJob[MatchIdListDTO],
):
    puuid = query_job.params.get("puuid")
    assert puuid

    pool = get_pool()
    await update_match_id_query_date(pool, puuid)

    logger.info("Updated user's query date", puuid=puuid)


class JobFactory(BaseJobFactory[MatchIdListDTO]):
    def __init__(
        self,
        platform: RoutePlatform,
        batch_size: int,
        last_queried: timedelta,
        lease_duration: timedelta,
    ) -> None:
        self.platform = platform
        self.batch_size = batch_size
        self.last_queried = last_queried
        self.lease_duration = lease_duration

    async def produce(self) -> list[QueryJob[MatchIdListDTO]]:
        pool = get_pool()
        puuids = await claim_users(
            pool,
            self.platform,
            self.batch_size,
            self.last_queried,
            self.lease_duration,
        )

        query_jobs = []
        region = self.platform.to_region()
        for puuid in puuids:
            query_job = QueryJob[MatchIdListDTO](
                method_name="get_match_ids_by_puuid",
                params={
                    "region": region,
                    "puuid": puuid,
                    "type": "ranked",
                    "start": 0,
                    "count": 100,
                },
                increment=increment,
                on_success=on_success,
                on_completion=on_completion,
            )
            query_jobs.append(query_job)

        return query_jobs


async def main():
    configure_logging()
    logger = get_logger()

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logger.info(f"PSYCOPG_POOL_MAX_SIZE: {PSYCOPG_POOL_MAX_SIZE}")
    logger.info(f"REDIS_DSN: {REDIS_DSN}")
    logger.info(f"WORKER_PER_REGION: {WORKER_PER_REGION}")

    # Initialize psycopg pool
    await init_pool(POSTGRES_DSN, PSYCOPG_POOL_MAX_SIZE)

    # Query Parameters
    regions: list[RouteRegion] = [
        RouteRegion.AMERICAS,
        RouteRegion.EUROPE,
        RouteRegion.ASIA,
        RouteRegion.SEA,
    ]

    logger.info("Creating workers...")
    queue_list = []
    worker_id = 0
    worker_list = []
    stop_all_workers = asyncio.Event()
    for region in regions:
        stop_route_workers = asyncio.Event()

        # Create new queue
        job_queue = asyncio.Queue()
        queue_list.append(job_queue)

        # add margin to local limits
        key = (region.name, "get_match_by_match_id")
        RiotClient.limits[key] = RateLimitItemPerSecond(45, 13, "RIOT_API")
        key = (region.name, "route_short")
        RiotClient.limits[key] = RateLimitItemPerSecond(10, 1, "RIOT_API")
        key = (region.name, "route_long")
        RiotClient.limits[key] = RateLimitItemPerSecond(95, 123, "RIOT_API")

        # add jobs to the queue
        job_factory = JobFactory(
            region,
            JOB_FACTORY_BATCH_SIZE,
            timedelta(days=100),
            timedelta(minutes=100),
        )
        refill = refill_queue(job_factory, job_queue, REFILL_QUEUE_THRESHOLD, 1)
        asyncio.create_task(refill)

        # Create workers
        for _ in range(WORKER_PER_REGION):
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

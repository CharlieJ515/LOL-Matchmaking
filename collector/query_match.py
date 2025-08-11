from datetime import timedelta
import asyncio
import os

from dotenv import load_dotenv
from rich.traceback import install
import httpx

import structlog
import structlog.stdlib

from riot_api.rate_limit_client import (
    RateLimitClient as RiotClient,
    RateLimitItemPerSecond,
    RouteRegion,
)

from logs.config import get_logger, configure_logging
from execution.query_job import BaseJobFactory, QueryJob, refill_queue
from execution.worker import worker
from db.pool import get_pool, init_pool, close_pool
from db.matches import claim_matches, insert_match, set_match_id_queried
from db.simplified_match_dto import MatchDTO

load_dotenv()
install()


API_KEY = os.getenv("RIOT_API_KEY", "")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
PSYCOPG_POOL_MAX_SIZE = 10
WORKER_PER_REGION = 1

REFILL_QUEUE_THRESHOLD = 100
JOB_FACTORY_BATCH_SIZE = 20


async def on_success(
    logger: structlog.BoundLogger,
    query_job: QueryJob[MatchDTO],
    result: MatchDTO,
    headers: httpx.Headers,
):
    pool = get_pool()
    match_id = result.metadata.matchId
    try:
        await insert_match(pool, result)
        logger.info("Inserted match", match_id=match_id)

        await set_match_id_queried(pool, match_id)
        logger.info("Marked match as queried", match_id=match_id)

    except Exception as e:
        logger.critical(
            "Failed to insert match",
            match_id=match_id,
            exc_info=True,
            exception=e,
        )


class JobFactory(BaseJobFactory[MatchDTO]):
    def __init__(
        self,
        region: RouteRegion,
        batch_size: int,
        lease_duration: timedelta,
    ) -> None:
        self.region = region
        self.batch_size = batch_size
        self.lease_duration = lease_duration

    async def produce(self) -> list[QueryJob[MatchDTO]]:
        pool = get_pool()
        match_ids = await claim_matches(
            pool,
            self.region,
            self.batch_size,
            self.lease_duration,
        )

        query_jobs = []
        for match_id in match_ids:
            query_job = QueryJob[MatchDTO](
                method_name="get_match_by_match_id",
                params={
                    "region": self.region,
                    "match_id": match_id,
                    "response_model": MatchDTO,
                },
                on_success=on_success,
            )
            query_jobs.append(query_job)

        return query_jobs


async def main():
    configure_logging()
    logger = get_logger()

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logger.info(f"PSYCOPG_POOL_MAX_SIZE: {PSYCOPG_POOL_MAX_SIZE}")
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
            timedelta(minutes=30),
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

import asyncio

import httpx
from riot_api.rate_limit_client import RateLimitClient, RateLimitExceeded
from riot_api.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ServerError,
)

from execution.query_job import QueryJob
from logs.config import get_logger
from logs.limits import log_header_limits, log_client_limits


async def worker(
    api_key: str,
    worker_id: int,
    job_queue: asyncio.Queue[QueryJob],
    stop_all_workers: asyncio.Event,
    stop_route_workers: asyncio.Event,
    queue_timeout: int = 5,
    http_error_timeout: int = 10,
):
    client = RateLimitClient(api_key)
    logger = get_logger().bind(component=f"worker_{worker_id}")
    logger.debug("Worker started")

    while True:
        # check stop event
        if stop_all_workers.is_set():
            logger.info("stop_all_workers is set, stopping worker")
            break
        if stop_route_workers.is_set():
            logger.info("stop_platform_workers is set, stopping worker")
            break

        # get next query
        try:
            query_job = await asyncio.wait_for(job_queue.get(), timeout=queue_timeout)
            logger.debug(
                "Retrieved item from queue",
                query_job=query_job,
                remaining_qsize=job_queue.qsize(),
            )
        except asyncio.TimeoutError:
            logger.info("Queue timeout, stopping worker")
            break

        # execute qeury
        skip_query = False
        res, headers = None, None  # to prevent pyright possibly unbound error
        while True:
            try:
                res, headers = await query_job.execute(client)
            except RateLimitExceeded as e:
                logger.warning(
                    f"Local rate limit exceeded. Sleeping for {e.retry_after:.2f}s",
                    retry_after=e.retry_after,
                    job=query_job,
                )
                await asyncio.sleep(e.retry_after)
                continue
            except RateLimitError as e:
                logger.critical(
                    f"Server side rate limit exceeded. Sleeping for {e.retry_after}s",
                    job=query_job,
                )
                log_header_limits(logger, e.headers)
                await log_client_limits(logger, client, query_job)
                await asyncio.sleep(e.retry_after)
                continue
            except httpx.HTTPError as e:
                logger.critical(
                    f"Encountered unexpected HTTP error, retrying after {http_error_timeout} seconds",
                    error=str(e),
                    exc_info=True,
                )
                await asyncio.sleep(http_error_timeout)
                continue
            except ServerError as e:
                # stop all platform workers as problem resides in the server
                logger.critical(
                    "Encountered server error, stopping all region workers",
                    status_code=e.status_code,
                    headers=e.headers,
                    body=e.body,
                )
                # stop_route_workers.set()
                # skip_query=True
                await asyncio.sleep(60)
                continue
            except UnauthorizedError as e:
                # stop all workers as API key is invalid
                if stop_all_workers.is_set():
                    continue

                stop_all_workers.set()
                logger.critical(
                    "Invalid API key, stopping all workers",
                    api_key=api_key,
                )
                skip_query = True
            except (BadRequestError, ForbiddenError, NotFoundError) as e:
                # something wrong with query parameter, stopping current worker
                logger.critical(
                    "Invalid request, stopping current user",
                    status_code=e.status_code,
                    headers=e.headers,
                    body=e.body,
                )
                await query_job.run_on_error(logger, e)
                skip_query = True
            except Exception as e:
                logger.critical(
                    "Encountered unexpected error",
                    query_job=query_job,
                    exception=e,
                )
                skip_query = True

            break
        if skip_query:
            continue

        # to prevent pyright possibly unbound error
        assert res is not None and headers is not None

        # log limit info
        log_header_limits(logger, headers)
        await log_client_limits(logger, client, query_job)

        # perform run_on_success
        logger.debug("Processing job result")
        await query_job.run_on_success(logger, res, headers)

        job_queue.task_done()

        # if response is full, add next job
        next_job = query_job.next(logger, res, headers)
        if next_job is None:
            logger.debug("No more pages, stopping pagination")
            await query_job.run_on_completion(logger)
        else:
            logger.debug("Queueing next window")
            await job_queue.put(next_job)

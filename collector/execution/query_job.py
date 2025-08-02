from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar, Any, Callable, Awaitable
from abc import ABC, abstractmethod
import asyncio

from riot_api import RateLimitClient
import httpx
import structlog

T = TypeVar("T")


def default_increment(
    logger: structlog.BoundLogger,
    query_job: "QueryJob[T]",
    result: T,
    headers: httpx.Headers,
) -> Optional["QueryJob[T]"]:
    return None


async def default_on_success(
    logger: structlog.BoundLogger,
    query_job: "QueryJob[T]",
    result: T,
    headers: httpx.Headers,
):
    pass


async def default_on_error(
    logger: structlog.BoundLogger,
    query_job: "QueryJob[T]",
    exc: Exception,
):
    logger.critical(
        "Query job failed with exception",
        method=query_job.method_name,
        params=query_job.params,
        error=str(exc),
        exc_info=True,
    )


async def default_on_completion(
    logger: structlog.BoundLogger,
    query_job: "QueryJob[T]",
):
    pass


@dataclass(frozen=True)
class QueryJob(Generic[T]):
    method_name: str
    params: dict[str, Any]
    increment: Callable[
        [
            structlog.BoundLogger,
            "QueryJob[T]",
            T,
            httpx.Headers,
        ],
        Optional["QueryJob[T]"],
    ] = field(default=default_increment, repr=False)
    on_success: Callable[
        [
            structlog.BoundLogger,
            "QueryJob[T]",
            T,
            httpx.Headers,
        ],
        Awaitable[None],
    ] = field(default=default_on_success, repr=False)
    on_error: Callable[
        [
            structlog.BoundLogger,
            "QueryJob[T]",
            Exception,
        ],
        Awaitable[None],
    ] = field(default=default_on_error, repr=False)
    on_completion: Callable[
        [
            structlog.BoundLogger,
            "QueryJob[T]",
        ],
        Awaitable[None],
    ] = field(default=default_on_completion, repr=False)

    def get_method(self, client: RateLimitClient) -> Callable[..., Awaitable[T]]:
        return getattr(client, self.method_name)

    async def execute(self, client: RateLimitClient) -> T:
        return await self.get_method(client)(**self.params)

    def next(
        self,
        logger: structlog.BoundLogger,
        result: T,
        headers: httpx.Headers,
    ) -> Optional["QueryJob[T]"]:
        return self.increment(logger, self, result, headers)

    async def run_on_success(
        self,
        logger: structlog.BoundLogger,
        result: T,
        headers: httpx.Headers,
    ) -> None:
        await self.on_success(logger, self, result, headers)

    async def run_on_error(
        self,
        logger: structlog.BoundLogger,
        exc: Exception,
    ) -> None:
        await self.on_error(logger, self, exc)

    async def run_on_completion(self, logger: structlog.BoundLogger) -> None:
        await self.on_completion(logger, self)


class BaseJobFactory(ABC, Generic[T]):
    @abstractmethod
    async def produce(self) -> list[QueryJob[T]]:
        pass


async def refill_queue(
    factory: BaseJobFactory[T],
    queue: asyncio.Queue[QueryJob[T]],
    threshold: int,
    sleep_time: float = 0.1,
):
    logger = structlog.get_logger("collector").bind(component="refill_queue")

    while True:
        while queue.qsize() >= threshold:
            await asyncio.sleep(sleep_time)

        job_list = await factory.produce()
        if not job_list:
            break

        for job in job_list:
            await queue.put(job)
        logger.debug(
            f"Added {len(job_list)} jobs to queue",
            new_qsize=queue.qsize(),
        )

    logger.info("No more jobs to fetch; Stopping...")

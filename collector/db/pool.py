from typing import Optional
import structlog
import psycopg_pool

logger = structlog.get_logger()

_pool: Optional[psycopg_pool.AsyncConnectionPool] = None


async def init_pool(dsn: str, max_size: int = 20) -> None:
    global _pool
    if _pool is not None:
        return

    _pool = psycopg_pool.AsyncConnectionPool(dsn, max_size=max_size)
    logger.debug("Opening psycopg pool")
    await _pool.open()
    logger.info(f"Created psycopg pool with max_size {_pool.max_size}")


def get_pool() -> psycopg_pool.AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_pool() first.")
    return _pool


async def close_pool():
    global _pool
    if _pool is None:
        return

    logger.debug("Closing psycopg pool")
    await _pool.close()
    _pool = None

import asyncio
from typing import List
import itertools
import os

import psycopg_pool
from pydantic import BaseModel
from dotenv import load_dotenv


import structlog
import structlog.stdlib

from riot_api import Client as RiotClient
from riot_api.types import Puuid
from riot_api.types.request import (
    RoutePlatform,
    RankedQueue,
)

import logging_configuration

logger = structlog.get_logger("collector")
load_dotenv()


class LeagueListDTO(BaseModel):
    entries: List["LeagueItemDTO"]


class LeagueItemDTO(BaseModel):
    puuid: Puuid


API_KEY = os.getenv("RIOT_API_KEY", "")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
REDIS_DSN = os.getenv("REDIS_DSN", "")
INSERT_USER_SQL = """
    INSERT INTO users (puuid, platform_id) 
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
"""


async def insert_user(
    logger: structlog.BoundLogger, platform: RoutePlatform, response: LeagueListDTO
):
    if pool is None:
        raise RuntimeError("Connection pool is not initialized")

    # TODO - add error handling, logging
    rows = [
        (league_item_dto.puuid, platform.name) for league_item_dto in response.entries
    ]
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(INSERT_USER_SQL, rows)


async def main():
    logger = structlog.get_logger("collector")

    global pool
    pool = psycopg_pool.AsyncConnectionPool(POSTGRES_DSN, max_size=20)
    logger.debug("Opening psycopg pool")
    await pool.open()
    logger.info(f"Created psycopg pool with max_size {pool.max_size}")

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")

    platforms = [RoutePlatform.KR]
    queues = [RankedQueue.RANKED_SOLO_5x5, RankedQueue.RANKED_FLEX_SR]

    client = RiotClient(API_KEY)
    logger.info("Starting queries")
    for platform, queue in itertools.product(platforms, queues):
        logger = logger.bind(platform=platform.name, queue=queue.value)

        # master
        res, headers = await client.get_master_league(platform, queue, LeagueListDTO)
        await insert_user(logger, platform, res)
        logger.debug("Inserted master league to DB", users=len(res.entries))

        # grandmaster
        res, headers = await client.get_grandmaster_league(
            platform, queue, LeagueListDTO
        )
        await insert_user(logger, platform, res)
        logger.debug("Inserted grandmaster league to DB", users=len(res.entries))

        # challenger
        res, headers = await client.get_challenger_league(
            platform, queue, LeagueListDTO
        )
        await insert_user(logger, platform, res)
        logger.debug("Inserted challenger league to DB", users=len(res.entries))

    logger.info("Query complete!")

    logger.debug("Closing psycopg pool")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())

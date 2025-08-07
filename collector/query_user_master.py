import asyncio
import itertools
import os

from pydantic import BaseModel
from dotenv import load_dotenv

import structlog
import structlog.stdlib

from riot_api.rate_limit_client import Client as RiotClient
from riot_api.types import Puuid
from riot_api.types.request import RoutePlatform, RankedQueue

from logs.config import get_logger, configure_logging
from db.pool import get_pool, init_pool, close_pool
from db.users import insert_user

logger = structlog.get_logger("collector")
load_dotenv()


class LeagueListDTO(BaseModel):
    entries: list["LeagueItemDTO"]


class LeagueItemDTO(BaseModel):
    puuid: Puuid


API_KEY = os.getenv("RIOT_API_KEY", "")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
REDIS_DSN = os.getenv("REDIS_DSN", "")
PSYCOPG_POOL_MAX_SIZE = 10
WORKER_PER_PLATFORM = 1


async def main():
    configure_logging()
    logger = get_logger()

    logger.info(f"RIOT_API_KEY: {API_KEY}")
    logger.info(f"POSTGRES_DSN: {POSTGRES_DSN}")
    logger.info(f"PSYCOPG_POOL_MAX_SIZE: {PSYCOPG_POOL_MAX_SIZE}")
    logger.info(f"REDIS_DSN: {REDIS_DSN}")

    await init_pool(POSTGRES_DSN, PSYCOPG_POOL_MAX_SIZE)
    pool = get_pool()

    platforms = [
        RoutePlatform.NA1,
        RoutePlatform.BR1,
        RoutePlatform.LA1,
        RoutePlatform.LA2,
        RoutePlatform.EUN1,
        RoutePlatform.EUW1,
        RoutePlatform.TR1,
        RoutePlatform.RU,
        RoutePlatform.JP1,
        RoutePlatform.KR,
        RoutePlatform.OC1,
        RoutePlatform.SG2,
        RoutePlatform.TW2,
        RoutePlatform.VN2,
    ]
    queues = [RankedQueue.RANKED_SOLO_5x5, RankedQueue.RANKED_FLEX_SR]

    client = RiotClient(API_KEY)
    logger.info("Starting queries")
    for platform, queue in itertools.product(platforms, queues):
        logger = logger.bind(platform=platform.name, queue=queue.value)

        # master
        res, headers = await client.get_master_league(platform, queue, LeagueListDTO)
        puuids = [e.puuid for e in res.entries]
        await insert_user(pool, platform, puuids)
        logger.debug(
            "Inserted master league to DB",
            users=len(puuids),
            platform=platform.name,
        )

        # grandmaster
        res, headers = await client.get_grandmaster_league(
            platform,
            queue,
            LeagueListDTO,
        )
        puuids = [e.puuid for e in res.entries]
        await insert_user(pool, platform, puuids)
        logger.debug(
            "Inserted grandmaster league to DB",
            users=len(res.entries),
            platform=platform.name,
        )

        # challenger
        res, headers = await client.get_challenger_league(
            platform, queue, LeagueListDTO
        )
        puuids = [e.puuid for e in res.entries]
        await insert_user(pool, platform, puuids)
        logger.debug(
            "Inserted challenger league to DB",
            users=len(res.entries),
            platform=platform.name,
        )

    logger.info("Query complete!")

    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())

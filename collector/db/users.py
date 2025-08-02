from datetime import timedelta
import psycopg_pool
from riot_api.types.request import RoutePlatform
from riot_api.types.base_types import Puuid


async def insert_user(
    pool: psycopg_pool.AsyncConnectionPool,
    platform: RoutePlatform,
    puuids: list[Puuid],
):
    rows = [{"puuid": puuid, "platform_name": platform.name} for puuid in puuids]
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO users (puuid, platform_name) 
                VALUES (%(puuid)s, %(platform_name)s)
                ON CONFLICT DO NOTHING
                """,
                rows,
            )


async def claim_users(
    pool: psycopg_pool.AsyncConnectionPool,
    platform: RoutePlatform,
    batch_size: int = 100,
    last_queried: timedelta = timedelta(days=100),
    lease_duration: timedelta = timedelta(minutes=30),
):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                WITH claimed AS (
                    SELECT puuid
                    FROM users
                    WHERE platform_name = %(platform_name)s
                    AND match_id_queried < NOW() - %(last_queried)s
                    AND lease_until < NOW()
                    ORDER BY puuid
                    LIMIT %(batch_size)s
                )
                UPDATE users
                SET lease_until = NOW() + %(lease_duration)s
                FROM claimed
                WHERE users.puuid = claimed.puuid
                RETURNING users.puuid;
                """,
                {
                    "platform_name": platform.name,
                    "batch_size": batch_size,
                    "last_queried": last_queried,
                    "lease_duration": lease_duration,
                },
            )
            rows = await cur.fetchall()
            return [row[0] for row in rows]


async def update_match_id_query_date(
    pool: psycopg_pool.AsyncConnectionPool,
    puuid: Puuid,
):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE users
                SET match_id_queried = CURRENT_DATE
                WHERE puuid = %(puuid)s
                """,
                {"puuid": puuid},
            )

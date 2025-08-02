from datetime import timedelta
import psycopg_pool

from riot_api.types.dto import MatchDTO
from riot_api.types.request import RouteRegion

from db.simplified_match_dto import (
    MatchDTO,
    MATCH_INSERT_SQL,
    TEAM_INSERT_SQL,
    TEAM_BAN_INSERT_SQL,
    PARTICIPANT_INSERT_SQL,
)


async def insert_match_ids(
    pool: psycopg_pool.AsyncConnectionPool,
    region: RouteRegion,
    match_ids: list[str],
):
    rows = [
        {
            "match_id": match_id,
            "region_name": region.name,
        }
        for match_id in match_ids
    ]
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO match_ids (match_id, region_name) 
                VALUES (%(match_id)s, %(region_name)s)
                ON CONFLICT DO NOTHING
                """,
                rows,
            )


async def claim_matches(
    pool: psycopg_pool.AsyncConnectionPool,
    region: RouteRegion,
    batch_size: int = 100,
    lease_duration: timedelta = timedelta(minutes=30),
):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                WITH claimed AS (
                    SELECT match_id
                    FROM match_ids
                    WHERE region_name = %(region_name)s
                    AND queried = False
                    AND lease_until < NOW()
                    ORDER BY match_id
                    LIMIT %(batch_size)s
                )
                UPDATE match_ids
                SET lease_until = NOW() + %(lease_duration)s
                FROM claimed
                WHERE match_ids.match_id = claimed.match_id
                RETURNING match_ids.match_id;
                """,
                {
                    "region_name": region.name,
                    "batch_size": batch_size,
                    "lease_duration": lease_duration,
                },
            )
            rows = await cur.fetchall()
            return [row[0] for row in rows]


async def insert_matches(
    pool: psycopg_pool.AsyncConnectionPool,
    match: MatchDTO,
):
    match_id = match.metadata.matchId

    metadata = match.metadata.model_dump()
    participant_puuid_list = metadata["participants"]

    info = match.info.model_dump(exclude={"participants", "teams"})
    team_blue = match.info.teams[0].model_dump()
    team_red = match.info.teams[1].model_dump()

    teams = []
    team_ban = []
    for team in match.info.teams:
        team_id = team.teamId
        for ban in team.bans:
            team_ban.append(
                {"matchId": match_id, "teamId": team_id, **ban.model_dump()}
            )

        team_dict = {
            "matchId": match_id,
            "teamId": team_id,
            "win": team.win,
        }

        feats = team.feats
        team_dict.update(
            {
                "EPIC_MONSTER_KILL": feats.EPIC_MONSTER_KILL.featState,
                "FIRST_BLOOD": feats.FIRST_BLOOD.featState,
                "FIRST_TURRET": feats.FIRST_TURRET.featState,
            }
        )

        objectives = team.objectives
        team_dict.update(
            {
                "atakhanFirst": objectives.atakhan.first,
                "atakhanKills": objectives.atakhan.kills,
                "baronFirst": objectives.baron.first,
                "baronKills": objectives.baron.kills,
                "championFirst": objectives.champion.first,
                "championKills": objectives.champion.kills,
                "dragonFirst": objectives.dragon.first,
                "dragonKills": objectives.dragon.kills,
                "hordeFirst": objectives.horde.first,
                "hordeKills": objectives.horde.kills,
                "inhibitorFirst": objectives.inhibitor.first,
                "inhibitorKills": objectives.inhibitor.kills,
                "riftHeraldFirst": objectives.riftHerald.first,
                "riftHeraldKills": objectives.riftHerald.kills,
                "towerFirst": objectives.tower.first,
                "towerKills": objectives.tower.kills,
            }
        )

        teams.append(team_dict)

    participants = []
    for participant in match.info.participants:
        participant_dict = participant.model_dump(exclude={"perks", "challenges"})
        challenge_dict = participant.challenges.model_dump()
        participant_dict.update(challenge_dict)
        participants.append(participant_dict)

    match_table_fields = {}
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""""")

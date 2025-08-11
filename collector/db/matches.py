from datetime import timedelta
import psycopg_pool

from riot_api.types.request import RouteRegion

from db.simplified_match_dto import (
    MatchDTO,
    INSERT_MATCH_SQL,
    INSERT_TEAM_SQL,
    INSERT_TEAM_BAN_SQL,
    INSERT_MATCH_PARTICIPANTS_SQL,
    INSERT_PARTICIPANT_STATS_SQL,
    INSERT_PARTICIPANT_CHALLENGES_SQL,
    INSERT_PARTICIPANT_PERKS_SQL,
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
                    ORDER BY lease_until, match_id
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


PERK_VAR_MAP = {
    8004: [],  # The Brazen Perfect
    8005: [1, 2],  # Press the Attack
    8006: [],  # The Eternal Champion
    8007: [],  # The Savant
    8008: [1, 2],  # Lethal Tempo
    8009: [1],  # Presence of Mind
    8010: [1],  # Conqueror
    8014: [1],  # Coup de Grace
    8016: [],  # The Merciless Elite
    8017: [1],  # Cut Down
    8021: [1],  # Fleet Footwork
    8105: [1, 2],  # Relentless Hunter
    8106: [1, 2],  # Ultimate Hunter
    8109: [],  # The Wicked Maestro
    8112: [1],  # Electrocute
    8114: [],  # The Immortal Butcher
    8115: [],  # The Aether Blade
    8120: [1, 3],  # Ghost Poro
    8124: [1],  # Predator
    8126: [1],  # Cheap Shot
    8127: [],  # The Twisted Surgeon
    8128: [1, 2],  # Dark Harvest
    8134: [1, 2],  # Ingenious Hunter
    8135: [1, 2],  # Treasure Hunter
    8136: [1, 2],  # Zombie Ward
    8137: [1],  # Sixth Sense
    8138: [1],  # Eyeball Collection
    8139: [1],  # Taste of Blood
    8140: [1],  # Grisly Mementos
    8141: [1],  # Deep Ward
    8143: [1],  # Sudden Impact
    8205: [],  # The Incontestable Spellslinger
    8207: [],  # The Cryptic
    8208: [],  # The Ancient One
    8210: [1],  # Transcendence
    8214: [1, 2],  # Summon Aery
    8220: [],  # The Calamity
    8224: [1, 2],  # Axiom Arcanist
    8226: [1, 2],  # Manaflow Band
    8229: [1],  # Arcane Comet
    8230: [1],  # Phase Rush
    8232: [1, 2],  # Waterwalking
    8233: [1, 2],  # Absolute Focus
    8234: [1],  # Celerity
    8236: [1],  # Gathering Storm
    8237: [1],  # Scorch
    8242: [1],  # Unflinching
    8275: [1],  # Nimbus Cloak
    8299: [1],  # Last Stand
    8304: [1, 2, 3],  # Magical Footwear
    8306: [1],  # Hextech Flashtraption
    8313: [1],  # Triple Tonic
    8316: [1, 2],  # Jack Of All Trades
    8318: [],  # The Ruthless Visionary
    8319: [],  # The Stargazer
    8320: [],  # The Timeless
    8321: [1],  # Cash Back
    8339: [],  # Celestial Body
    8344: [],  # The Elegant Duelist
    8345: [1, 3],  # Biscuit Delivery
    8347: [],  # Cosmic Insight
    8351: [1, 2],  # Glacial Augment
    8352: [2],  # Time Warp Tonic
    8359: [1, 2],  # Kleptomancy
    8360: [1],  # Unsealed Spellbook
    8369: [1, 2],  # First Strike
    8401: [1],  # Shield Bash
    8410: [1],  # Approach Velocity
    8414: [],  # The Behemoth
    8415: [],  # The Arcane Colossus
    8416: [],  # The Enlightened Titan
    8429: [1, 2, 3],  # Conditioning
    8430: [1],  # Iron Skin
    8435: [1],  # Mirror Shell
    8437: [1, 2],  # Grasp of the Undying
    8439: [1, 2],  # Aftershock
    8444: [1],  # Second Wind
    8446: [1],  # Demolish
    8451: [1],  # Overgrowth
    8453: [1, 2],  # Revitalize
    8454: [],  # The Leviathan
    8463: [1],  # Font of Life
    8465: [1],  # Guardian
    8472: [],  # Chrysalis
    8473: [1],  # Bone Plating
    9101: [1],  # Absorb Life
    9103: [1, 2],  # Legend: Bloodline
    9104: [1, 2],  # Legend: Alacrity
    9105: [1, 2],  # Legend: Haste
    9111: [1, 2],  # Triumph
    9923: [1, 2],  # Hail of Blades
}


async def insert_match(
    pool: psycopg_pool.AsyncConnectionPool,
    match: MatchDTO,
):
    match_id = match.metadata.matchId
    game_id = match.info.gameId
    platform_name = match.info.platformId

    # matches
    match_dict = match.info.model_dump(
        exclude={
            "participants",
            "teams",
            "platformId",
            "gameMode",
        }
    )
    match_dict["matchId"] = match_id
    match_dict["platformName"] = platform_name

    team_dicts = []
    ban_dicts = []
    for team in match.info.teams:
        team_id = team.teamId.name.lower()
        # team_bans
        for ban in team.bans:
            ban_dicts.append(
                {
                    "platformName": platform_name,
                    "gameId": game_id,
                    "teamId": team_id,
                    "pickTurn": ban.pickTurn,
                    "championId": None if ban.championId == -1 else ban.championId,
                }
            )

        # teams
        team_dict = {
            "platformName": platform_name,
            "gameId": game_id,
            "teamId": team_id,
            "win": team.win,
        }

        # feats
        feats = team.feats
        team_dict["featsEpicMonsterState"] = feats.EPIC_MONSTER_KILL.featState
        team_dict["featsFirstBloodState"] = feats.FIRST_BLOOD.featState
        team_dict["featsFirstTurretState"] = feats.FIRST_TURRET.featState

        count = 0
        if team_dict["featsEpicMonsterState"] == 3:
            count += 1
        if team_dict["featsFirstBloodState"] == 3:
            count += 1
        if team_dict["featsFirstTurretState"] == 1:
            count += 1
        if count >= 2:
            feats_claimed = True
        else:
            feats_claimed = False
        team_dict["featsClaimed"] = feats_claimed

        # objectives
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

        # game_ended_in_surrender, had_afk_teammate, perfect_dragon_souls_taken
        participants = [p for p in match.info.participants if team.teamId == p.teamId]
        game_ended_in_surrender = any([p.gameEndedInSurrender for p in participants])
        had_afk_teammate = any(
            [bool(p.challenges.hadAfkTeammate) for p in participants]
        )
        perfect_dragon_souls_taken = any(
            [bool(p.challenges.perfectDragonSoulsTaken) for p in participants]
        )

        if (
            all([p.gameEndedInSurrender for p in participants])
            != game_ended_in_surrender
        ):
            raise ValueError
        if (
            all([bool(p.challenges.perfectDragonSoulsTaken) for p in participants])
            != perfect_dragon_souls_taken
        ):
            raise ValueError

        team_dict["gameEndedInSurrender"] = game_ended_in_surrender
        team_dict["hadAfkTeammate"] = had_afk_teammate
        team_dict["perfectDragonSoulsTaken"] = perfect_dragon_souls_taken

        team_dicts.append(team_dict)

    participant_dicts = []
    stat_dicts = []
    challenge_dicts = []
    perk_dicts = []
    for participant in match.info.participants:
        participant_id = participant.participantId.value
        team_id = participant.teamId.name.lower()

        # match_participants
        participant_dict = {
            "platformName": platform_name,
            "gameId": game_id,
            "teamId": team_id,
            "teamPosition": participant.teamPosition.name.lower(),
            "participantId": participant_id,
            "championId": participant.championId,
            "summoner1Id": participant.summoner1Id.value,
            "summoner2Id": participant.summoner2Id.value,
        }
        participant_dicts.append(participant_dict)

        # participant_stats
        stat_dict = participant.model_dump(
            exclude={
                "teamId",
                "teamPosition",
                "championId",
                "summoner1Id",
                "summoner2Id",
                "challenges",
                "gameEndedInSurrender",
                "perks",
            }
        )
        stat_dict["platformName"] = platform_name
        stat_dict["gameId"] = game_id
        stat_dicts.append(stat_dict)

        # participant_challenges
        challenges = participant.challenges
        challenge_dict = challenges.model_dump(
            exclude={
                "hadAfkTeammate",
                "perfectDragonSoulsTaken",
            }
        )
        challenge_dict["soloTurretsLateGame"] = challenge_dict["soloTurretsLategame"]
        del challenge_dict["soloTurretsLategame"]
        challenge_dict["platformName"] = platform_name
        challenge_dict["participantId"] = participant_id
        challenge_dict["gameId"] = game_id

        # hadAfkTeammate field doesn't appear on player that had been afk
        # since this field default value of 0, if team_dict.hadAfkTeammate
        # doesn't match challenges.hadAfkTeammate, it means this player was afk
        team_dict = next(t for t in team_dicts if t["teamId"] == team_id)
        was_afk = team_dict["hadAfkTeammate"] != bool(challenges.hadAfkTeammate)
        challenge_dict["wasAfk"] = was_afk
        challenge_dicts.append(challenge_dict)

        # participant_perks
        perks = participant.perks
        primary_style = next(s for s in perks.styles if "primaryStyle" == s.description)
        secondary_style = next(s for s in perks.styles if "subStyle" == s.description)
        perk_dict = {
            "defensePerkId": perks.statPerks.defense,
            "flexPerkId": perks.statPerks.flex,
            "offensePerkId": perks.statPerks.offense,
            "primaryPerkStyle": None
            if primary_style.style == 0
            else primary_style.style.name.lower(),
            "secondaryPerkStyle": None
            if secondary_style.style == 0
            else secondary_style.style.name.lower(),
        }

        def add_perk_vars(prefix: str, i: int, sel):
            perk_id = sel.perk
            if perk_id == 0:
                perk_dict[f"{prefix}Perk{i}Id"] = None
                perk_dict[f"{prefix}Perk{i}Var1"] = None
                perk_dict[f"{prefix}Perk{i}Var2"] = None
                perk_dict[f"{prefix}Perk{i}Var3"] = None
                return

            vars = PERK_VAR_MAP.get(perk_id)
            if vars is None:
                raise ValueError

            perk_dict[f"{prefix}Perk{i}Id"] = perk_id
            perk_dict[f"{prefix}Perk{i}Var1"] = sel.var1 if 1 in vars else None
            perk_dict[f"{prefix}Perk{i}Var2"] = sel.var2 if 2 in vars else None
            perk_dict[f"{prefix}Perk{i}Var3"] = sel.var3 if 3 in vars else None

        # Primary style
        for i, sel in enumerate(primary_style.selections, start=1):
            add_perk_vars("primary", i, sel)

        # Secondary style
        for i, sel in enumerate(secondary_style.selections, start=1):
            add_perk_vars("secondary", i, sel)

        perk_dict["platformName"] = platform_name
        perk_dict["gameId"] = game_id
        perk_dict["participantId"] = participant_id
        perk_dicts.append(perk_dict)

    async with pool.connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.execute(INSERT_MATCH_SQL, match_dict)
                await cur.executemany(INSERT_TEAM_SQL, team_dicts)
                await cur.executemany(INSERT_TEAM_BAN_SQL, ban_dicts)
                await cur.executemany(INSERT_MATCH_PARTICIPANTS_SQL, participant_dicts)
                await cur.executemany(INSERT_PARTICIPANT_STATS_SQL, stat_dicts)
                await cur.executemany(
                    INSERT_PARTICIPANT_CHALLENGES_SQL, challenge_dicts
                )
                await cur.executemany(INSERT_PARTICIPANT_PERKS_SQL, perk_dicts)


async def set_match_id_queried(pool: psycopg_pool.AsyncConnectionPool, match_id: str):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE match_ids
                SET queried = true
                WHERE match_id = %(match_id)s
                """,
                {"match_id": match_id},
            )

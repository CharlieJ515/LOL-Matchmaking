from enum import IntEnum
from typing import List, Annotated, Literal
from datetime import datetime

from pydantic import PlainValidator, BaseModel

from riot_api.types.converters import millis_to_datetime
from riot_api.types.enums import ChampionId
from riot_api.types.enums import Participant, Team, Position, KaynTransform
from riot_api.types.base_types import (
    Count,
    AmountInt,
    AmountFloat,
    Percentage,
    TimeDelta,
)
from riot_api.types.enums.summoner_spells import SummonerSpellId


class MatchDTO(BaseModel):
    metadata: "MetadataDTO"
    info: "InfoDTO"


class MetadataDTO(BaseModel):
    # dataVersion: str
    matchId: str
    # participants: List[Puuid]


DatetimeMilli = Annotated[datetime, PlainValidator(millis_to_datetime)]


class InfoDTO(BaseModel):
    endOfGameResult: str = ""
    # gameCreation: DatetimeMilli
    gameDuration: TimeDelta
    # gameEndTimestamp: DatetimeMilli
    gameId: int
    gameMode: Literal["CLASSIC"]
    # gameName: str
    gameStartTimestamp: DatetimeMilli
    # gameType: str
    gameVersion: str
    # mapId: MapId
    participants: List["ParticipantDTO"]
    platformId: str
    # queueId: int
    teams: List["TeamDTO"]
    # tournamentCode: Optional[str] = None


class ParticipantDTO(BaseModel):
    allInPings: Count
    assistMePings: Count
    assists: Count
    baronKills: Count
    bountyLevel: Count = Count(0)
    champExperience: AmountInt
    champLevel: Count
    championId: ChampionId
    # championName: Annotated[
    #     ChampionName,
    #     PlainValidator(normalize_champion_name),
    #     PlainSerializer(lambda e: e.value, return_type=str),
    # ]
    commandPings: Count
    championTransform: KaynTransform
    consumablesPurchased: Count
    challenges: "ChallengesDTO"
    damageDealtToBuildings: AmountInt
    damageDealtToObjectives: AmountInt
    damageDealtToTurrets: AmountInt
    damageSelfMitigated: AmountInt
    deaths: Count
    detectorWardsPlaced: Count
    doubleKills: Count
    dragonKills: Count
    # eligibleForProgression: bool
    enemyMissingPings: Count
    enemyVisionPings: Count
    firstBloodAssist: bool
    firstBloodKill: bool
    firstTowerAssist: bool
    firstTowerKill: bool
    # gameEndedInEarlySurrender: bool
    gameEndedInSurrender: bool
    holdPings: Count
    getBackPings: Count
    goldEarned: AmountInt
    goldSpent: AmountInt
    # individualPosition: Position
    inhibitorKills: Count
    inhibitorTakedowns: Count
    inhibitorsLost: Count
    item0: int
    item1: int
    item2: int
    item3: int
    item4: int
    item5: int
    item6: int
    itemsPurchased: Count
    killingSprees: Count
    kills: Count
    # lane: Position
    largestCriticalStrike: AmountInt
    largestKillingSpree: Count
    largestMultiKill: Count
    longestTimeSpentLiving: TimeDelta
    magicDamageDealt: AmountInt
    magicDamageDealtToChampions: AmountInt
    magicDamageTaken: AmountInt
    # missions: "MissionsDTO"
    neutralMinionsKilled: Count
    needVisionPings: Count
    # nexusKills: Count
    # nexusTakedowns: Count
    # nexusLost: Count
    objectivesStolen: Count
    objectivesStolenAssists: Count
    onMyWayPings: Count
    participantId: Participant
    # PlayerScore0: int
    # PlayerScore1: int
    # PlayerScore2: int
    # PlayerScore3: int
    # PlayerScore4: int
    # PlayerScore5: int
    # PlayerScore6: int
    # PlayerScore7: int
    # PlayerScore8: int
    # PlayerScore9: int
    # PlayerScore10: int
    # PlayerScore11: int
    pentaKills: Count
    perks: "PerksDTO"
    physicalDamageDealt: AmountInt
    physicalDamageDealtToChampions: AmountInt
    physicalDamageTaken: AmountInt
    # placement: int
    # playerAugment1: int
    # playerAugment2: int
    # playerAugment3: int
    # playerAugment4: int
    # playerAugment5: int
    # playerAugment6: int
    # playerSubteamId: int
    pushPings: Count
    # profileIcon: int
    # puuid: Puuid
    quadraKills: Count
    # riotIdGameName: str
    # riotIdTagline: str
    # role: Role
    sightWardsBoughtInGame: Count
    spell1Casts: Count
    spell2Casts: Count
    spell3Casts: Count
    spell4Casts: Count
    # subteamPlacement: int
    summoner1Casts: Count
    summoner1Id: SummonerSpellId
    summoner2Casts: Count
    summoner2Id: SummonerSpellId
    # summonerId: str
    # summonerLevel: int
    # summonerName: str
    # teamEarlySurrendered: bool
    teamId: Team
    teamPosition: Position
    timeCCingOthers: AmountInt
    # timePlayed: TimeDelta
    totalAllyJungleMinionsKilled: Count
    totalDamageDealt: AmountInt
    totalDamageDealtToChampions: AmountInt
    totalDamageShieldedOnTeammates: AmountInt
    totalDamageTaken: AmountInt
    totalEnemyJungleMinionsKilled: Count
    totalHeal: AmountInt
    totalHealsOnTeammates: AmountInt
    totalMinionsKilled: Count
    totalTimeCCDealt: int
    totalTimeSpentDead: TimeDelta
    totalUnitsHealed: AmountInt
    tripleKills: Count
    trueDamageDealt: AmountInt
    trueDamageDealtToChampions: AmountInt
    trueDamageTaken: AmountInt
    turretKills: Count
    turretTakedowns: Count
    turretsLost: Count
    # unrealKills: Count
    visionScore: AmountInt
    visionClearedPings: Count
    visionWardsBoughtInGame: Count
    wardsKilled: Count
    wardsPlaced: Count
    # win: bool
    # basicPings: Count
    # dangerPings: Count
    # retreatPings: Count
    # championSkinId: Optional[int] = None


class ChallengesDTO(BaseModel):
    # assistStreakCount12: int = Field(alias="12AssistStreakCount")
    # baronBuffGoldAdvantageOverThreshold: Optional[int] = None
    controlWardTimeCoverageInRiverOrEnemyHalf: float = 0
    # earliestBaron: Optional[int] = None
    # earliestDragonTakedown: Optional[float] = None
    # earliestElderDragon: Optional[int] = None
    # earlyLaningPhaseGoldExpAdvantage: int
    # fasterSupportQuestCompletion: Optional[int] = None
    # fastestLegendary: Optional[float] = None
    hadAfkTeammate: int = 0
    # highestChampionDamage: Optional[int] = None
    # highestCrowdControlScore: Optional[int] = None
    # highestWardKills: Optional[int] = None
    junglerKillsEarlyJungle: int = 0
    killsOnLanersEarlyJungleAsJungler: int = 0
    # laningPhaseGoldExpAdvantage: int
    # legendaryCount: int
    maxCsAdvantageOnLaneOpponent: float = 0
    maxLevelLeadLaneOpponent: int = 0
    # mostWardsDestroyedOneSweeper: Optional[int] = None
    # mythicItemUsed: Optional[int] = None
    # playedChampSelectPosition: int
    soloTurretsLategame: int = 0
    takedownsFirst25Minutes: int = 0
    # teleportTakedowns: Optional[int] = None
    # thirdInhibitorDestroyedTime: Optional[int] = None
    # threeWardsOneSweeperCount: Optional[int] = None
    visionScoreAdvantageLaneOpponent: float = 0
    # InfernalScalePickup: int
    # fistBumpParticipation: int
    voidMonsterKill: Count = Count(0)
    # abilityUses: Count
    acesBefore15Minutes: Count
    alliedJungleMonsterKills: float
    # baronTakedowns: Count
    # blastConeOppositeOpponentCount: Count
    bountyGold: float
    buffsStolen: Count
    # completeSupportQuestInTime: int
    # controlWardsPlaced: Count
    damagePerMinute: float
    damageTakenOnTeamPercentage: Percentage
    # dancedWithRiftHerald: Count
    # deathsByEnemyChamps: Count
    dodgeSkillShotsSmallWindow: Count
    # doubleAces: Count
    # dragonTakedowns: Count
    # legendaryItemUsed: List[ItemId]
    effectiveHealAndShielding: float
    elderDragonKillsWithOpposingSoul: int
    # elderDragonMultikills: Count
    enemyChampionImmobilizations: int
    enemyJungleMonsterKills: float
    # epicMonsterKillsNearEnemyJungler: int
    # epicMonsterKillsWithin30SecondsOfSpawn: int
    epicMonsterSteals: Count
    # epicMonsterStolenWithoutSmite: int
    # firstTurretKilled: int
    # firstTurretKilledTime: Optional[float] = None
    flawlessAces: int
    # fullTeamTakedown: int
    # gameLength: TimeDelta
    # getTakedownsInAllLanesEarlyJungleAsLaner: Optional[int] = None
    goldPerMinute: float
    # hadOpenNexus: int
    immobilizeAndKillWithAlly: int
    initialBuffCount: Count
    initialCrabCount: Count
    jungleCsBefore10Minutes: float
    # junglerTakedownsNearDamagedEpicMonster: Count
    kda: AmountFloat
    killAfterHiddenWithAlly: Count
    # killedChampTookFullTeamDamageSurvived: int
    # killingSprees: int
    killParticipation: Percentage = Percentage(0)
    killsNearEnemyTurret: Count
    killsOnOtherLanesEarlyJungleAsLaner: int = 0
    # killsOnRecentlyHealedByAramPack: int
    killsUnderOwnTurret: int
    killsWithHelpFromEpicMonster: int
    knockEnemyIntoTeamAndKill: int
    kTurretsDestroyedBeforePlatesFall: int
    landSkillShotsEarlyGame: int
    laneMinionsFirst10Minutes: int
    # lostAnInhibitor: Count
    # maxKillDeficit: int
    # mejaisFullStackInTime: int
    moreEnemyJungleThanOpponent: float
    # multiKillOneSpell: Count
    # multikills: Count
    multikillsAfterAggressiveFlash: Count
    multiTurretRiftHeraldCount: Count
    # outerTurretExecutesBefore10Minutes: Count
    outnumberedKills: Count
    # outnumberedNexusKill: Count
    perfectDragonSoulsTaken: int
    # perfectGame: int
    pickKillWithAlly: int
    # poroExplosions: int
    # quickCleanse: int
    quickFirstTurret: int
    quickSoloKills: Count
    riftHeraldTakedowns: Count
    saveAllyFromDeath: Count
    # scuttleCrabKills: Count
    # shortestTimeToAceFromFirstTakedown: Optional[float] = None
    skillshotsDodged: int
    skillshotsHit: int
    # snowballsHit: int
    soloBaronKills: Count
    # SWARM_DefeatAatrox: int
    # SWARM_DefeatBriar: int
    # SWARM_DefeatMiniBosses: int
    # SWARM_EvolveWeapon: int
    # SWARM_Have3Passives: int
    # SWARM_KillEnemy: int
    # SWARM_PickupGold: float
    # SWARM_ReachLevel50: int
    # SWARM_Survive15Min: int
    # SWARM_WinWith5EvolvedWeapons: int
    soloKills: Count
    # stealthWardsPlaced: Count
    # survivedSingleDigitHpCount: Count
    # survivedThreeImmobilizesInFight: int
    takedownOnFirstTurret: int
    # takedowns: Count
    takedownsAfterGainingLevelAdvantage: int
    takedownsBeforeJungleMinionSpawn: Count
    # takedownsFirstXMinutes: Count
    # takedownsInAlcove: int
    # takedownsInEnemyFountain: Count
    # teamBaronKills: Count
    teamDamagePercentage: float = 0
    # teamElderDragonKills: Count
    # teamRiftHeraldKills: Count
    tookLargeDamageSurvived: Count
    turretPlatesTaken: Count
    turretsTakenWithRiftHerald: Count
    # turretTakedowns: Count
    # twentyMinionsIn3SecondsCount: Count
    # twoWardsOneSweeperCount: Count
    # unseenRecalls: int
    visionScorePerMinute: AmountFloat
    wardsGuarded: Count
    wardTakedowns: Count
    wardTakedownsBefore20M: Count
    # HealFromMapSources: AmountFloat


class PerksDTO(BaseModel):
    statPerks: "PerkStatsDTO"
    styles: List["PerkStyleDTO"]


class PerkStatsDTO(BaseModel):
    defense: int
    flex: int
    offense: int


class PerkStyle(IntEnum):
    NONE = 0
    PRECISION = 8000
    DOMINATION = 8100
    SORCERY = 8200
    RESOLVE = 8400
    INSPIRATION = 8300


class PerkStyleDTO(BaseModel):
    description: str
    selections: List["PerkStyleSelectionDTO"]
    style: PerkStyle


class PerkStyleSelectionDTO(BaseModel):
    perk: int
    var1: int
    var2: int
    var3: int


class FeatsDTO(BaseModel):
    EPIC_MONSTER_KILL: "FeatStateDTO"
    FIRST_BLOOD: "FeatStateDTO"
    FIRST_TURRET: "FeatStateDTO"


class FeatStateDTO(BaseModel):
    featState: int


class TeamDTO(BaseModel):
    win: bool
    feats: "FeatsDTO" = FeatsDTO(
        EPIC_MONSTER_KILL=FeatStateDTO(featState=0),
        FIRST_BLOOD=FeatStateDTO(featState=0),
        FIRST_TURRET=FeatStateDTO(featState=0),
    )
    objectives: "ObjectivesDTO"
    bans: List["BanDTO"]
    teamId: Team


class BanDTO(BaseModel):
    championId: ChampionId
    pickTurn: int


class ObjectiveDTO(BaseModel):
    first: bool
    kills: Count


class ObjectivesDTO(BaseModel):
    atakhan: "ObjectiveDTO" = ObjectiveDTO(first=False, kills=Count(0))
    baron: "ObjectiveDTO"
    champion: "ObjectiveDTO"
    dragon: "ObjectiveDTO"
    horde: "ObjectiveDTO" = ObjectiveDTO(first=False, kills=Count(0))
    inhibitor: "ObjectiveDTO"
    riftHerald: "ObjectiveDTO"
    tower: "ObjectiveDTO"


INSERT_MATCH_SQL = """
INSERT INTO matches (
    game_id,
    game_start_timestamp,
    game_duration,
    platform_name,
    game_version,
    end_of_game_result,
    match_id
) VALUES (
    %(gameId)s,
    %(gameStartTimestamp)s,
    %(gameDuration)s,
    %(platformName)s,
    %(gameVersion)s,
    %(endOfGameResult)s,
    %(matchId)s
);
"""

INSERT_TEAM_SQL = """
INSERT INTO teams (
    game_id,
    team_id,
    feats_epic_monster_state,
    feats_first_blood_state,
    feats_first_turret_state,
    atakhan_kills,
    baron_kills,
    champion_kills,
    dragon_kills,
    horde_kills,
    inhibitor_kills,
    rift_herald_kills,
    tower_kills,
    atakhan_first,
    baron_first,
    champion_first,
    dragon_first,
    horde_first,
    inhibitor_first,
    rift_herald_first,
    tower_first,
    feats_claimed,
    win,
    game_ended_in_surrender,
    had_afk_teammate,
    perfect_dragon_souls_taken,
    platform_name
) VALUES (
    %(gameId)s,
    %(teamId)s,
    %(featsEpicMonsterState)s,
    %(featsFirstBloodState)s,
    %(featsFirstTurretState)s,
    %(atakhanKills)s,
    %(baronKills)s,
    %(championKills)s,
    %(dragonKills)s,
    %(hordeKills)s,
    %(inhibitorKills)s,
    %(riftHeraldKills)s,
    %(towerKills)s,
    %(atakhanFirst)s,
    %(baronFirst)s,
    %(championFirst)s,
    %(dragonFirst)s,
    %(hordeFirst)s,
    %(inhibitorFirst)s,
    %(riftHeraldFirst)s,
    %(towerFirst)s,
    %(featsClaimed)s,
    %(win)s,
    %(gameEndedInSurrender)s,
    %(hadAfkTeammate)s,
    %(perfectDragonSoulsTaken)s,
    %(platformName)s
);
"""

INSERT_TEAM_BAN_SQL = """
INSERT INTO team_bans (
    game_id,
    team_id,
    pick_turn,
    champion_id,
    platform_name
) VALUES (
    %(gameId)s,
    %(teamId)s,
    %(pickTurn)s,
    %(championId)s,
    %(platformName)s
);
"""

INSERT_MATCH_PARTICIPANTS_SQL = """
INSERT INTO match_participants (
    game_id,
    team_id,
    team_position,
    participant_id,
    champion_id,
    summoner1_id,
    summoner2_id,
    platform_name
) VALUES (
    %(gameId)s,
    %(teamId)s,
    %(teamPosition)s,
    %(participantId)s,
    %(championId)s,
    %(summoner1Id)s,
    %(summoner2Id)s,
    %(platformName)s
);
"""

INSERT_PARTICIPANT_STATS_SQL = """
INSERT INTO participant_stats (
    game_id,
    champ_experience,
    damage_dealt_to_buildings,
    damage_dealt_to_objectives,
    damage_dealt_to_turrets,
    damage_self_mitigated,
    largest_critical_strike,
    magic_damage_dealt,
    magic_damage_dealt_to_champions,
    magic_damage_taken,
    physical_damage_dealt,
    physical_damage_dealt_to_champions,
    physical_damage_taken,
    total_damage_dealt,
    total_damage_dealt_to_champions,
    total_damage_shielded_on_teammates,
    total_damage_taken,
    true_damage_dealt,
    true_damage_dealt_to_champions,
    true_damage_taken,
    time_ccing_others,
    total_time_cc_dealt,
    total_heal,
    total_heals_on_teammates,
    total_units_healed,
    gold_earned,
    gold_spent,
    item0,
    item1,
    item2,
    item3,
    item4,
    item5,
    item6,
    participant_id,
    champion_transform,
    champ_level,
    kills,
    killing_sprees,
    largest_killing_spree,
    double_kills,
    triple_kills,
    quadra_kills,
    penta_kills,
    largest_multi_kill,
    bounty_level,
    deaths,
    longest_time_spent_living,
    total_time_spent_dead,
    assists,
    spell1_casts,
    spell2_casts,
    spell3_casts,
    spell4_casts,
    summoner1_casts,
    summoner2_casts,
    detector_wards_placed,
    wards_placed,
    wards_killed,
    vision_score,
    inhibitor_kills,
    inhibitor_takedowns,
    inhibitors_lost,
    turrets_lost,
    turret_takedowns,
    turret_kills,
    all_in_pings,
    assist_me_pings,
    command_pings,
    enemy_missing_pings,
    enemy_vision_pings,
    hold_pings,
    get_back_pings,
    need_vision_pings,
    on_my_way_pings,
    push_pings,
    vision_cleared_pings,
    dragon_kills,
    baron_kills,
    objectives_stolen,
    objectives_stolen_assists,
    total_ally_jungle_minions_killed,
    total_enemy_jungle_minions_killed,
    neutral_minions_killed,
    total_minions_killed,
    consumables_purchased,
    first_blood_kill,
    first_blood_assist,
    first_tower_kill,
    first_tower_assist,
    platform_name
) VALUES (
    %(gameId)s,
    %(champExperience)s,
    %(damageDealtToBuildings)s,
    %(damageDealtToObjectives)s,
    %(damageDealtToTurrets)s,
    %(damageSelfMitigated)s,
    %(largestCriticalStrike)s,
    %(magicDamageDealt)s,
    %(magicDamageDealtToChampions)s,
    %(magicDamageTaken)s,
    %(physicalDamageDealt)s,
    %(physicalDamageDealtToChampions)s,
    %(physicalDamageTaken)s,
    %(totalDamageDealt)s,
    %(totalDamageDealtToChampions)s,
    %(totalDamageShieldedOnTeammates)s,
    %(totalDamageTaken)s,
    %(trueDamageDealt)s,
    %(trueDamageDealtToChampions)s,
    %(trueDamageTaken)s,
    %(timeCCingOthers)s,
    %(totalTimeCCDealt)s,
    %(totalHeal)s,
    %(totalHealsOnTeammates)s,
    %(totalUnitsHealed)s,
    %(goldEarned)s,
    %(goldSpent)s,
    %(item0)s,
    %(item1)s,
    %(item2)s,
    %(item3)s,
    %(item4)s,
    %(item5)s,
    %(item6)s,
    %(participantId)s,
    %(championTransform)s,
    %(champLevel)s,
    %(kills)s,
    %(killingSprees)s,
    %(largestKillingSpree)s,
    %(doubleKills)s,
    %(tripleKills)s,
    %(quadraKills)s,
    %(pentaKills)s,
    %(largestMultiKill)s,
    %(bountyLevel)s,
    %(deaths)s,
    %(longestTimeSpentLiving)s,
    %(totalTimeSpentDead)s,
    %(assists)s,
    %(spell1Casts)s,
    %(spell2Casts)s,
    %(spell3Casts)s,
    %(spell4Casts)s,
    %(summoner1Casts)s,
    %(summoner2Casts)s,
    %(detectorWardsPlaced)s,
    %(wardsPlaced)s,
    %(wardsKilled)s,
    %(visionScore)s,
    %(inhibitorKills)s,
    %(inhibitorTakedowns)s,
    %(inhibitorsLost)s,
    %(turretsLost)s,
    %(turretTakedowns)s,
    %(turretKills)s,
    %(allInPings)s,
    %(assistMePings)s,
    %(commandPings)s,
    %(enemyMissingPings)s,
    %(enemyVisionPings)s,
    %(holdPings)s,
    %(getBackPings)s,
    %(needVisionPings)s,
    %(onMyWayPings)s,
    %(pushPings)s,
    %(visionClearedPings)s,
    %(dragonKills)s,
    %(baronKills)s,
    %(objectivesStolen)s,
    %(objectivesStolenAssists)s,
    %(totalAllyJungleMinionsKilled)s,
    %(totalEnemyJungleMinionsKilled)s,
    %(neutralMinionsKilled)s,
    %(totalMinionsKilled)s,
    %(consumablesPurchased)s,
    %(firstBloodKill)s,
    %(firstBloodAssist)s,
    %(firstTowerKill)s,
    %(firstTowerAssist)s,
    %(platformName)s
);
"""

INSERT_PARTICIPANT_CHALLENGES_SQL = """
INSERT INTO participant_challenges (
    game_id,
    bounty_gold,
    effective_heal_and_shielding,
    kda,
    kill_participation,
    damage_per_minute,
    damage_taken_on_team_pct,
    team_damage_pct,
    control_ward_time_coverage_in_river_or_enemy_half,
    vision_score_advantage_lane_opponent,
    vision_score_per_minute,
    more_enemy_jungle_than_opponent,
    gold_per_minute,
    participant_id,
    max_level_lead_lane_opponent,
    jungler_kills_early_jungle,
    kills_on_laners_early_jungle_as_jungler,
    takedowns_first_25_minutes,
    aces_before_15_minutes,
    buffs_stolen,
    dodge_skill_shots_small_window,
    flawless_aces,
    kill_after_hidden_with_ally,
    kills_near_enemy_turret,
    kills_on_other_lanes_early_jungle_as_laner,
    kills_under_own_turret,
    kills_with_help_from_epic_monster,
    multikills_after_aggressive_flash,
    took_large_damage_survived,
    takedowns_before_jungle_minion_spawn,
    takedowns_after_gaining_level_advantage,
    takedown_on_first_turret,
    solo_kills,
    skillshots_dodged,
    save_ally_from_death,
    quick_solo_kills,
    pick_kill_with_ally,
    outnumbered_kills,
    enemy_champion_immobilizations,
    immobilize_and_kill_with_ally,
    knock_enemy_into_team_and_kill,
    land_skill_shots_early_game,
    skillshots_hit,
    ward_takedowns_before_20m,
    ward_takedowns,
    wards_guarded,
    solo_turrets_late_game,
    k_turrets_destroyed_before_plates_fall,
    turrets_taken_with_rift_herald,
    turret_plates_taken,
    quick_first_turret,
    multi_turret_rift_herald_count,
    max_cs_advantage_on_lane_opponent,
    void_monster_kill,
    allied_jungle_monster_kills,
    elder_dragon_kills_with_opposing_soul,
    enemy_jungle_monster_kills,
    epic_monster_steals,
    initial_buff_count,
    initial_crab_count,
    jungle_cs_before_10_minutes,
    lane_minions_first_10_minutes,
    rift_herald_takedowns,
    solo_baron_kills,
    was_afk,
    platform_name
) VALUES (
    %(gameId)s,
    %(bountyGold)s,
    %(effectiveHealAndShielding)s,
    %(kda)s,
    %(killParticipation)s,
    %(damagePerMinute)s,
    %(damageTakenOnTeamPercentage)s,
    %(teamDamagePercentage)s,
    %(controlWardTimeCoverageInRiverOrEnemyHalf)s,
    %(visionScoreAdvantageLaneOpponent)s,
    %(visionScorePerMinute)s,
    %(moreEnemyJungleThanOpponent)s,
    %(goldPerMinute)s,
    %(participantId)s,
    %(maxLevelLeadLaneOpponent)s,
    %(junglerKillsEarlyJungle)s,
    %(killsOnLanersEarlyJungleAsJungler)s,
    %(takedownsFirst25Minutes)s,
    %(acesBefore15Minutes)s,
    %(buffsStolen)s,
    %(dodgeSkillShotsSmallWindow)s,
    %(flawlessAces)s,
    %(killAfterHiddenWithAlly)s,
    %(killsNearEnemyTurret)s,
    %(killsOnOtherLanesEarlyJungleAsLaner)s,
    %(killsUnderOwnTurret)s,
    %(killsWithHelpFromEpicMonster)s,
    %(multikillsAfterAggressiveFlash)s,
    %(tookLargeDamageSurvived)s,
    %(takedownsBeforeJungleMinionSpawn)s,
    %(takedownsAfterGainingLevelAdvantage)s,
    %(takedownOnFirstTurret)s,
    %(soloKills)s,
    %(skillshotsDodged)s,
    %(saveAllyFromDeath)s,
    %(quickSoloKills)s,
    %(pickKillWithAlly)s,
    %(outnumberedKills)s,
    %(enemyChampionImmobilizations)s,
    %(immobilizeAndKillWithAlly)s,
    %(knockEnemyIntoTeamAndKill)s,
    %(landSkillShotsEarlyGame)s,
    %(skillshotsHit)s,
    %(wardTakedownsBefore20M)s,
    %(wardTakedowns)s,
    %(wardsGuarded)s,
    %(soloTurretsLateGame)s,
    %(kTurretsDestroyedBeforePlatesFall)s,
    %(turretsTakenWithRiftHerald)s,
    %(turretPlatesTaken)s,
    %(quickFirstTurret)s,
    %(multiTurretRiftHeraldCount)s,
    %(maxCsAdvantageOnLaneOpponent)s,
    %(voidMonsterKill)s,
    %(alliedJungleMonsterKills)s,
    %(elderDragonKillsWithOpposingSoul)s,
    %(enemyJungleMonsterKills)s,
    %(epicMonsterSteals)s,
    %(initialBuffCount)s,
    %(initialCrabCount)s,
    %(jungleCsBefore10Minutes)s,
    %(laneMinionsFirst10Minutes)s,
    %(riftHeraldTakedowns)s,
    %(soloBaronKills)s,
    %(wasAfk)s,
    %(platformName)s
);
"""

INSERT_PARTICIPANT_PERKS_SQL = """
INSERT INTO participant_perks (
    game_id,
    primary_perk_style,
    secondary_perk_style,
    participant_id,
    defense_perk_id,
    flex_perk_id,
    offense_perk_id,
    primary_perk1_id,
    primary_perk1_var1,
    primary_perk1_var2,
    primary_perk1_var3,
    primary_perk2_id,
    primary_perk2_var1,
    primary_perk2_var2,
    primary_perk2_var3,
    primary_perk3_id,
    primary_perk3_var1,
    primary_perk3_var2,
    primary_perk3_var3,
    primary_perk4_id,
    primary_perk4_var1,
    primary_perk4_var2,
    primary_perk4_var3,
    secondary_perk1_id,
    secondary_perk1_var1,
    secondary_perk1_var2,
    secondary_perk1_var3,
    secondary_perk2_id,
    secondary_perk2_var1,
    secondary_perk2_var2,
    secondary_perk2_var3,
    platform_name
) VALUES (
    %(gameId)s,
    %(primaryPerkStyle)s,
    %(secondaryPerkStyle)s,
    %(participantId)s,
    %(defensePerkId)s,
    %(flexPerkId)s,
    %(offensePerkId)s,
    %(primaryPerk1Id)s,
    %(primaryPerk1Var1)s,
    %(primaryPerk1Var2)s,
    %(primaryPerk1Var3)s,
    %(primaryPerk2Id)s,
    %(primaryPerk2Var1)s,
    %(primaryPerk2Var2)s,
    %(primaryPerk2Var3)s,
    %(primaryPerk3Id)s,
    %(primaryPerk3Var1)s,
    %(primaryPerk3Var2)s,
    %(primaryPerk3Var3)s,
    %(primaryPerk4Id)s,
    %(primaryPerk4Var1)s,
    %(primaryPerk4Var2)s,
    %(primaryPerk4Var3)s,
    %(secondaryPerk1Id)s,
    %(secondaryPerk1Var1)s,
    %(secondaryPerk1Var2)s,
    %(secondaryPerk1Var3)s,
    %(secondaryPerk2Id)s,
    %(secondaryPerk2Var1)s,
    %(secondaryPerk2Var2)s,
    %(secondaryPerk2Var3)s,
    %(platformName)s
);
"""

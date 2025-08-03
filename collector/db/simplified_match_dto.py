from typing import List, Optional, Annotated

from pydantic import Field, PlainValidator, PlainSerializer, BaseModel

from riot_api.types.enums import (
    ChampionId,
    ChampionName,
    ItemId,
    MapId,
)
from riot_api.types.enums import (
    Participant,
    Team,
    Position,
    KaynTransform,
    Role,
)
from riot_api.types.converters import normalize_champion_name
from riot_api.types.base_types import (
    Puuid,
    Count,
    AmountInt,
    AmountFloat,
    Percentage,
    DatetimeMilli,
    TimeDelta,
)
from riot_api.types.enums.summoner_spells import SummonerSpellId


class MatchDTO(BaseModel):
    metadata: "MetadataDTO"
    info: "InfoDTO"


class MetadataDTO(BaseModel):
    dataVersion: str
    matchId: str
    participants: List[Puuid]


class InfoDTO(BaseModel):
    endOfGameResult: str
    gameDuration: TimeDelta
    gameId: int
    gameMode: str
    gameVersion: str
    gameStartTimestamp: DatetimeMilli
    platformId: str
    queueId: int
    participants: List["ParticipantDTO"]
    teams: List["TeamDTO"]

    # gameCreation: DatetimeMilli
    # gameEndTimestamp: DatetimeMilli
    # gameName: str
    # gameType: str
    # mapId: MapId
    # tournamentCode: Optional[str] = None


class ParticipantDTO(BaseModel):
    participantId: Participant
    puuid: Puuid
    teamId: Team

    teamPosition: Position
    timePlayed: TimeDelta
    championId: ChampionId
    championName: Annotated[
        ChampionName,
        PlainValidator(normalize_champion_name),
        PlainSerializer(lambda e: e.value, return_type=str),
    ]
    championTransform: KaynTransform
    gameEndedInSurrender: bool
    win: bool
    champExperience: AmountInt
    champLevel: Count

    kills: Count
    firstBloodKill: bool
    killingSprees: Count
    largestKillingSpree: Count
    doubleKills: Count
    tripleKills: Count
    quadraKills: Count
    pentaKills: Count
    largestMultiKill: Count
    bountyLevel: Optional[int] = None
    deaths: Count
    longestTimeSpentLiving: TimeDelta
    totalTimeSpentDead: TimeDelta
    assists: Count
    firstBloodAssist: bool

    damageDealtToBuildings: AmountInt
    damageDealtToObjectives: AmountInt
    damageDealtToTurrets: AmountInt
    damageSelfMitigated: AmountInt
    largestCriticalStrike: AmountInt
    magicDamageDealt: AmountInt
    magicDamageDealtToChampions: AmountInt
    magicDamageTaken: AmountInt
    physicalDamageDealt: AmountInt
    physicalDamageDealtToChampions: AmountInt
    physicalDamageTaken: AmountInt
    totalDamageDealt: AmountInt
    totalDamageDealtToChampions: AmountInt
    totalDamageShieldedOnTeammates: AmountInt
    totalDamageTaken: AmountInt
    trueDamageDealt: AmountInt
    trueDamageDealtToChampions: AmountInt
    trueDamageTaken: AmountInt

    spell1Casts: Count
    spell2Casts: Count
    spell3Casts: Count
    spell4Casts: Count
    summoner1Casts: Count
    summoner1Id: SummonerSpellId
    summoner2Casts: Count
    summoner2Id: SummonerSpellId
    timeCCingOthers: AmountInt
    totalTimeCCDealt: int

    totalHeal: AmountInt
    totalHealsOnTeammates: AmountInt
    totalUnitsHealed: AmountInt

    detectorWardsPlaced: Count
    wardsPlaced: Count
    wardsKilled: Count
    visionScore: AmountInt

    firstTowerKill: bool
    firstTowerAssist: bool
    inhibitorKills: Count
    inhibitorTakedowns: Count
    inhibitorsLost: Count
    turretsLost: Count
    turretTakedowns: Count
    turretKills: Count

    allInPings: Count
    assistMePings: Count
    commandPings: Count
    enemyMissingPings: Count
    enemyVisionPings: Count
    holdPings: Count
    getBackPings: Count
    needVisionPings: Count
    onMyWayPings: Count
    pushPings: Count
    visionClearedPings: Count
    basicPings: Count
    dangerPings: Count
    retreatPings: Count

    dragonKills: Count
    baronKills: Count
    objectivesStolen: Count
    objectivesStolenAssists: Count
    totalAllyJungleMinionsKilled: Count
    totalEnemyJungleMinionsKilled: Count
    neutralMinionsKilled: Count
    totalMinionsKilled: Count

    goldEarned: AmountInt
    goldSpent: AmountInt
    consumablesPurchased: Count

    item0: ItemId
    item1: ItemId
    item2: ItemId
    item3: ItemId
    item4: ItemId
    item5: ItemId
    item6: ItemId

    perks: "PerksDTO"

    challenges: "ChallengesDTO"

    # eligibleForProgression: bool
    # gameEndedInEarlySurrender: bool
    # individualPosition: Position
    # itemsPurchased: Count
    # lane: Position
    # missions: "MissionsDTO"
    # nexusKills: Count
    # nexusTakedowns: Count
    # nexusLost: Count
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
    # placement: int
    # playerAugment1: int
    # playerAugment2: int
    # playerAugment3: int
    # playerAugment4: int
    # playerAugment5: int
    # playerAugment6: int
    # playerSubteamId: int
    # profileIcon: int
    # riotIdGameName: str
    # riotIdTagline: str
    # role: Role
    # sightWardsBoughtInGame: Count
    # subteamPlacement: int
    # summonerId: str
    # summonerLevel: int
    # summonerName: str
    # teamEarlySurrendered: bool
    # unrealKills: Count
    # visionWardsBoughtInGame: Count
    # championSkinId: Optional[int] = None


class ChallengesDTO(BaseModel):
    hadAfkTeammate: Optional[int] = None
    maxLevelLeadLaneOpponent: int
    junglerKillsEarlyJungle: Optional[int] = None
    takedownsFirst25Minutes: Optional[int] = None
    acesBefore15Minutes: Count
    buffsStolen: Count
    dodgeSkillShotsSmallWindow: Count
    flawlessAces: int
    kda: AmountFloat
    killAfterHiddenWithAlly: Count
    killParticipation: Percentage
    killsNearEnemyTurret: Count
    killsOnOtherLanesEarlyJungleAsLaner: Optional[int] = None
    killsOnLanersEarlyJungleAsJungler: Optional[int] = None
    killsUnderOwnTurret: int
    killsWithHelpFromEpicMonster: int
    multikillsAfterAggressiveFlash: Count
    tookLargeDamageSurvived: Count
    takedownsBeforeJungleMinionSpawn: Count
    takedownOnFirstTurret: int
    soloKills: Count
    skillshotsDodged: int
    saveAllyFromDeath: Count
    quickSoloKills: Count
    pickKillWithAlly: int
    outnumberedKills: Count

    damagePerMinute: float
    damageTakenOnTeamPercentage: Percentage
    teamDamagePercentage: float

    enemyChampionImmobilizations: int
    immobilizeAndKillWithAlly: int
    knockEnemyIntoTeamAndKill: int
    landSkillShotsEarlyGame: int
    skillshotsHit: int

    effectiveHealAndShielding: float

    controlWardTimeCoverageInRiverOrEnemyHalf: Optional[float] = None
    visionScoreAdvantageLaneOpponent: float
    wardTakedownsBefore20M: Count
    wardTakedowns: Count
    wardsGuarded: Count
    visionScorePerMinute: AmountFloat

    soloTurretsLategame: Optional[int] = None
    kTurretsDestroyedBeforePlatesFall: int
    turretsTakenWithRiftHerald: Count
    turretPlatesTaken: Count
    quickFirstTurret: int
    multiTurretRiftHeraldCount: Count

    maxCsAdvantageOnLaneOpponent: float
    voidMonsterKill: Count
    alliedJungleMonsterKills: float
    elderDragonKillsWithOpposingSoul: int
    enemyJungleMonsterKills: float
    epicMonsterSteals: Count
    initialBuffCount: Count
    initialCrabCount: Count
    jungleCsBefore10Minutes: float
    laneMinionsFirst10Minutes: int
    moreEnemyJungleThanOpponent: float
    riftHeraldTakedowns: Count
    soloBaronKills: Count
    teamRiftHeraldKills: Count
    teamElderDragonKills: Count
    perfectDragonSoulsTaken: int
    epicMonsterKillsNearEnemyJungler: int
    epicMonsterKillsWithin30SecondsOfSpawn: int

    bountyGold: float
    goldPerMinute: float

    # assistStreakCount12: int = Field(alias="12AssistStreakCount")
    # baronBuffGoldAdvantageOverThreshold: Optional[int] = None
    # earliestBaron: Optional[int] = None
    # earliestDragonTakedown: Optional[float] = None
    # earliestElderDragon: Optional[int] = None
    # earlyLaningPhaseGoldExpAdvantage: int
    # fasterSupportQuestCompletion: Optional[int] = None
    # fastestLegendary: Optional[float] = None
    # highestChampionDamage: Optional[int] = None
    # highestCrowdControlScore: Optional[int] = None
    # highestWardKills: Optional[int] = None
    # laningPhaseGoldExpAdvantage: int
    # legendaryCount: int
    # mostWardsDestroyedOneSweeper: Optional[int] = None
    # mythicItemUsed: Optional[int] = None
    # playedChampSelectPosition: int
    # teleportTakedowns: Optional[int] = None
    # thirdInhibitorDestroyedTime: Optional[int] = None
    # threeWardsOneSweeperCount: Optional[int] = None
    # InfernalScalePickup: int
    # fistBumpParticipation: int
    # abilityUses: Count
    # baronTakedowns: Count
    # blastConeOppositeOpponentCount: Count
    # completeSupportQuestInTime: int
    # controlWardsPlaced: Count
    # dancedWithRiftHerald: Count
    # deathsByEnemyChamps: Count
    # doubleAces: Count
    # dragonTakedowns: Count
    # legendaryItemUsed: List[ItemId]
    # elderDragonMultikills: Count
    # epicMonsterStolenWithoutSmite: int
    # firstTurretKilled: int
    # firstTurretKilledTime: Optional[float] = None
    # fullTeamTakedown: int
    # gameLength: TimeDelta
    # getTakedownsInAllLanesEarlyJungleAsLaner: Optional[int] = None
    # hadOpenNexus: int
    # junglerTakedownsNearDamagedEpicMonster: Count
    # killedChampTookFullTeamDamageSurvived: int
    # killingSprees: int
    # killsOnRecentlyHealedByAramPack: int
    # lostAnInhibitor: Count
    # maxKillDeficit: int
    # mejaisFullStackInTime: int
    # multiKillOneSpell: Count
    # multikills: Count
    # outerTurretExecutesBefore10Minutes: Count
    # outnumberedNexusKill: Count
    # perfectGame: int
    # poroExplosions: int
    # quickCleanse: int
    # scuttleCrabKills: Count
    # shortestTimeToAceFromFirstTakedown: Optional[float] = None
    # snowballsHit: int
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
    # stealthWardsPlaced: Count
    # survivedSingleDigitHpCount: Count
    # survivedThreeImmobilizesInFight: int
    # takedowns: Count
    # takedownsAfterGainingLevelAdvantage: int
    # takedownsFirstXMinutes: Count
    # takedownsInAlcove: int
    # takedownsInEnemyFountain: Count
    # teamBaronKills: Count
    # turretTakedowns: Count
    # twentyMinionsIn3SecondsCount: Count
    # twoWardsOneSweeperCount: Count
    # unseenRecalls: int
    # HealFromMapSources: AmountFloat


class PerksDTO(BaseModel):
    statPerks: "PerkStatsDTO"
    styles: List["PerkStyleDTO"]


class PerkStatsDTO(BaseModel):
    defense: int
    flex: int
    offense: int


class PerkStyleDTO(BaseModel):
    description: str
    selections: List["PerkStyleSelectionDTO"]
    style: int


class PerkStyleSelectionDTO(BaseModel):
    perk: int
    var1: int
    var2: int
    var3: int


class TeamDTO(BaseModel):
    win: bool
    feats: "FeatsDTO"
    objectives: "ObjectivesDTO"
    bans: List["BanDTO"]
    teamId: Team


class BanDTO(BaseModel):
    championId: ChampionId
    pickTurn: int


class ObjectivesDTO(BaseModel):
    atakhan: "ObjectiveDTO"
    baron: "ObjectiveDTO"
    champion: "ObjectiveDTO"
    dragon: "ObjectiveDTO"
    horde: "ObjectiveDTO"
    inhibitor: "ObjectiveDTO"
    riftHerald: "ObjectiveDTO"
    tower: "ObjectiveDTO"


class ObjectiveDTO(BaseModel):
    first: bool
    kills: Count


class FeatsDTO(BaseModel):
    EPIC_MONSTER_KILL: "FeatStateDTO"
    FIRST_BLOOD: "FeatStateDTO"
    FIRST_TURRET: "FeatStateDTO"


class FeatStateDTO(BaseModel):
    featState: int


MATCH_INSERT_SQL = """
INSERT INTO matches (
    match_id,
    end_of_game_result,
    game_duration,
    game_id,
    game_mode,
    game_version,
    platform_id,
    queue_id
) VALUES (
    %(matchId)s,
    %(endOfGameResult)s,
    %(gameDuration)s,
    %(gameId)s,
    %(gameMode)s,
    %(gameVersion)s,
    %(platformId)s,
    %(queueId)s
);
"""

TEAM_INSERT_SQL = """
INSERT INTO team (
    match_id,
    team_id,
    win,

    epic_monster_state,
    first_blood_state,
    first_turret_state,

    atakhan_first,
    atakhan_kills,
    baron_first,
    baron_kills,
    champion_first,
    champion_kills,
    dragon_first,
    dragon_kills,
    horde_first,
    horde_kills,
    inhibitor_first,
    inhibitor_kills,
    rift_herald_first,
    rift_herald_kills,
    tower_first,
    tower_kills
) VALUES (
    %(matchId)s,
    %(teamId)s,
    %(win)s,

    %(epicMonsterState)s,
    %(firstBloodState)s,
    %(firstTurretState)s,

    %(atakhanFirst)s,
    %(atakhanKills)s,
    %(baronFirst)s,
    %(baronKills)s,
    %(championFirst)s,
    %(championKills)s,
    %(dragonFirst)s,
    %(dragonKills)s,
    %(hordeFirst)s,
    %(hordeKills)s,
    %(inhibitorFirst)s,
    %(inhibitorKills)s,
    %(riftHeraldFirst)s,
    %(riftHeraldKills)s,
    %(towerFirst)s,
    %(towerKills)s
);
"""

TEAM_BAN_INSERT_SQL = """
INSERT INTO team_ban (
    match_id,
    team_id,
    pick_turn,
    champion_id
) VALUES (
    %(matchId)s,
    %(teamId)s,
    %(pickTurn)s,
    %(championId)s
);
"""

PARTICIPANT_INSERT_SQL = """
INSERT INTO participant_stats (
    match_id,
    participant_id,
    puuid,
    team_id,

    team_position,
    time_played,
    champion_id,
    champion_name,
    champion_transform,
    game_ended_in_surrender,
    win,
    champ_experience,
    champ_level,

    kills,
    first_blood_kill,
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
    first_blood_assist,

    damage_dealt_to_buildings,
    damage_dealt_to_objectives,
    damage_dealt_to_turrets,
    damage_self_mitigated,
    largest_critical_strike,
    magic_damage_dealt,
    magic_damage_dealt_to_champions,
    magic_damage_taken,
    physical_damage_dealt,    match_id,
    participant_id,
    puuid,
    team_id,

    team_position,
    time_played,
    champion_id,
    champion_name,
    champion_transform,
    game_ended_in_surrender,
    win,
    champ_experience,
    champ_level,

    kills,
    first_blood_kill,
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
    first_blood_assist,

    damage_dealt_to_buildings,
    damage_dealt_to_objectives,
    damage_dealt_to_turrets,
    damage_self_mitigated,
    physical_damage_dealt_to_champions,
    physical_damage_taken,
    total_damage_dealt,
    total_damage_dealt_to_champions,
    total_damage_shielded_on_teammates,
    total_damage_taken,
    true_damage_dealt,
    true_damage_dealt_to_champions,
    true_damage_taken,

    spell1_casts,
    spell2_casts,
    spell3_casts,
    spell4_casts,
    summoner1_casts,
    summoner1_id,
    summoner2_casts,
    summoner2_id,
    time_ccing_others,
    total_time_cc_dealt,

    total_heal,
    total_heals_on_teammates,
    total_units_healed,

    detector_wards_placed,
    wards_placed,
    wards_killed,
    vision_score,

    first_tower_kill,
    first_tower_assist,
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

    gold_earned,
    gold_spent,
    consumables_purchased,

    item0,
    item1,
    item2,
    item3,
    item4,
    item5,
    item6,

    had_afk_teammate,
    max_level_lead_lane_opponent,

    jungler_kills_early_jungle,
    kills_on_laners_early_jungle_as_jungler,
    takedowns_first_25_minutes,
    aces_before_15_minutes,
    buffs_stolen,
    dodge_skill_shots_small_window,
    flawless_ace,
    kda,
    kill_after_hidden_with_ally,
    kill_participation,
    kills_near_enemy_turret,
    kills_on_other_lanes_early_jungle_as_laner,
    kills_on_laners_early_jungle_as_jungler

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
    outnumbered_kills

    damage_per_minute,
    damage_taken_on_team_pct,
    team_damage_pct,

    enemy_champion_immobilization,
    immobilize_and_kill_with_ally,
    knock_enemy_into_team_and_kill,
    land_skill_shots_early_game,
    skillshots_hit,

    effective_heal_and_shielding,

    control_ward_time_coverage_in_river_or_enemy_half,
    vision_score_advantage_lane_opponent,
    ward_takedowns_before_20m,
    ward_takedowns,
    wards_guarded,
    vision_score_per_minute,

    solo_turret_late_game,
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
    more_enemy_jungle_than_opponent,
    rift_herald_takedowns,
    solo_baron_kills,
    team_rift_herald_kills,
    team_elder_dragon_kills,
    perfect_dragon_souls_taken,
    epic_monster_kills_near_enemy_jungler,
    epic_monster_kills_within_30_seconds_of_spawn,

    bounty_gold,
    gold_per_minute,
) VALUES (
    %(matchId)s,
    %(participantId)s,
    %(puuid)s,
    %(teamId)s,
    
    %(teamPosition)s,
    %(timePlayed)s,
    %(championId)s,
    %(championName)s,
    %(championTransform)s,
    %(gameEndedInSurrender)s,
    %(win)s,
    %(champExperience)s,
    %(champLevel)s,
    
    %(kills)s,
    %(firstBloodKill)s,
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
    %(firstBloodAssist)s,
    
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
    
    %(spell1Casts)s,
    %(spell2Casts)s,
    %(spell3Casts)s,
    %(spell4Casts)s,
    %(summoner1Casts)s,
    %(summoner1Id)s,
    %(summoner2Casts)s,
    %(summoner2Id)s,
    %(timeCCingOthers)s,
    %(totalTimeCCDealt)s,
    
    %(totalHeal)s,
    %(totalHealsOnTeammates)s,
    %(totalUnitsHealed)s,
    
    %(detectorWardsPlaced)s,
    %(wardsPlaced)s,
    %(wardsKilled)s,
    %(visionScore)s,
    
    %(firstTowerKill)s,
    %(firstTowerAssist)s,
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
    
    %(goldEarned)s,
    %(goldSpent)s,
    %(consumablesPurchased)s,
    
    %(item0)s,
    %(item1)s,
    %(item2)s,
    %(item3)s,
    %(item4)s,
    %(item5)s,
    %(item6)s,
    
    %(hadAfkTeammate)s,
    %(maxLevelLeadLaneOpponent)s,
    
    %(junglerKillsEarlyJungle)s,
    %(killsOnLanersEarlyJungleAsJungler)s,
    %(takedownsFirst25Minutes)s,
    %(acesBefore15Minutes)s,
    %(buffsStolen)s,
    %(dodgeSkillShotsSmallWindow)s,
    %(flawlessAce)s,
    %(kda)s,
    %(killAfterHiddenWithAlly)s,
    %(killParticipation)s,
    %(killsNearEnemyTurret)s,
    %(killsOnOtherLanesEarlyJungleAsLaner)s,
    %(killsOnLanersEarlyJungleAsJungler)s,
    
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
    
    %(damagePerMinute)s,
    %(damageTakenOnTeamPct)s,
    %(teamDamagePct)s,
    
    %(enemyChampionImmobilization)s,
    %(immobilizeAndKillWithAlly)s,
    %(knockEnemyIntoTeamAndKill)s,
    %(landSkillShotsEarlyGame)s,
    %(skillshotsHit)s,
    
    %(effectiveHealAndShielding)s,
    
    %(controlWardTimeCoverageInRiverOrEnemyHalf)s,
    %(visionScoreAdvantageLaneOpponent)s,
    %(wardTakedownsBefore20m)s,
    %(wardTakedowns)s,
    %(wardsGuarded)s,
    %(visionScorePerMinute)s,
    
    %(soloTurretLateGame)s,
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
    %(moreEnemyJungleThanOpponent)s,
    %(riftHeraldTakedowns)s,
    %(soloBaronKills)s,
    %(teamRiftHeraldKills)s,
    %(teamElderDragonKills)s,
    %(perfectDragonSoulsTaken)s,
    %(epicMonsterKillsNearEnemyJungler)s,
    %(epicMonsterKillsWithin30SecondsOfSpawn)s,
    
    %(bountyGold)s,
    %(goldPerMinute)s,
);
"""


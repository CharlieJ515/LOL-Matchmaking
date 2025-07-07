CREATE TABLE participant_stats (
    match_id                 VARCHAR(30)  NOT NULL,
    participant_id           SMALLINT     NOT NULL,
    puuid                    VARCHAR(78)  NOT NULL,
    team_id                  SMALLINT     NOT NULL,              -- 100 / 200
    team_position            VARCHAR(10)  NOT NULL,              -- TOP/JUNGLE/...
    time_played              INT          NOT NULL,              -- sec
    champion_id              INT          NOT NULL,
    champion_name            VARCHAR(30)  NOT NULL,
    champion_transform       BOOLEAN      NOT NULL,
    game_ended_in_surrender  BOOLEAN      NOT NULL,
    win                      BOOLEAN      NOT NULL,
    champion_experience      INT          NOT NULL,
    champion_level           SMALLINT     NOT NULL,

    -- KDA
    kills                    SMALLINT     NOT NULL,
    first_blood_kill         BOOLEAN      NOT NULL,
    killing_sprees           SMALLINT     NOT NULL,
    largest_killing_spree    SMALLINT     NOT NULL,
    double_kills             SMALLINT     NOT NULL,
    triple_kills             SMALLINT     NOT NULL,
    quadra_kills             SMALLINT     NOT NULL,
    penta_kills              SMALLINT     NOT NULL,
    largest_multi_kill       SMALLINT     NOT NULL,
    bounty_level             SMALLINT     NOT NULL,
    deaths                   SMALLINT     NOT NULL,
    longest_time_spent_living INT         NOT NULL,
    total_time_spent_dead    INT          NOT NULL,
    assists                  SMALLINT     NOT NULL,
    first_blood_assist       BOOLEAN      NOT NULL,

    -- Damage
    damage_dealt_to_buildings          INT NOT NULL,
    damage_dealt_to_objectives         INT NOT NULL,
    damage_dealt_to_turrets            INT NOT NULL,
    damage_self_mitigated              INT NOT NULL,
    largest_critical_strike            INT NOT NULL,
    magic_damage_dealt                 INT NOT NULL,
    magic_damage_dealt_to_champions    INT NOT NULL,
    magic_damage_taken                 INT NOT NULL,
    physical_damage_dealt              INT NOT NULL,
    physical_damage_dealt_to_champions INT NOT NULL,
    physical_damage_taken              INT NOT NULL,
    total_damage_dealt                 INT NOT NULL,
    total_damage_dealt_to_champions    INT NOT NULL,
    total_damage_shielded_on_teammates INT NOT NULL,
    total_damage_taken                 INT NOT NULL,
    true_damage_dealt                  INT NOT NULL,
    true_damage_dealt_to_champions     INT NOT NULL,
    true_damage_taken                  INT NOT NULL,

    -- Spell & CC
    spell1_casts          INT NOT NULL,
    spell2_casts          INT NOT NULL,
    spell3_casts          INT NOT NULL,
    spell4_casts          INT NOT NULL,
    summoner1_casts       SMALLINT NOT NULL,
    summoner1_id          SMALLINT NOT NULL,
    summoner2_casts       SMALLINT NOT NULL,
    summoner2_id          SMALLINT NOT NULL,
    time_ccing_others     INT NOT NULL,
    total_time_cc_dealt   INT NOT NULL,

    -- Heal
    total_heal              INT NOT NULL,
    total_heals_on_teammates INT NOT NULL,
    total_units_healed       INT NOT NULL,

    -- Vision
    detector_wards_placed SMALLINT NOT NULL,
    wards_placed          SMALLINT NOT NULL,
    wards_killed          SMALLINT NOT NULL,
    vision_score          SMALLINT NOT NULL,

    -- Tower
    first_tower_kill      BOOLEAN  NOT NULL,
    first_tower_assist    BOOLEAN  NOT NULL,
    inhibitor_kills       SMALLINT NOT NULL,
    inhibitor_takedowns   SMALLINT NOT NULL,
    inhibitors_lost       SMALLINT NOT NULL,
    turrets_lost          SMALLINT NOT NULL,
    turret_takedowns      SMALLINT NOT NULL,
    turret_kills          SMALLINT NOT NULL,

    -- Ping
    all_in_pings         SMALLINT NOT NULL,
    assist_me_pings      SMALLINT NOT NULL,
    command_pings        SMALLINT NOT NULL,
    enemy_missing_pings  SMALLINT NOT NULL,
    enemy_vision_pings   SMALLINT NOT NULL,
    hold_pings           SMALLINT NOT NULL,
    get_back_pings       SMALLINT NOT NULL,
    need_vision_pings    SMALLINT NOT NULL,
    on_my_way_pings      SMALLINT NOT NULL,
    push_pings           SMALLINT NOT NULL,
    vision_cleared_pings SMALLINT NOT NULL,

    -- Entity
    dragon_kills                    SMALLINT NOT NULL,
    baron_kills                     SMALLINT NOT NULL,
    objectives_stolen               SMALLINT NOT NULL,
    objectives_stolen_assists       SMALLINT NOT NULL,
    total_ally_jungle_minions_killed SMALLINT NOT NULL,
    total_enemy_jungle_minions_killed SMALLINT NOT NULL,
    neutral_minions_killed          SMALLINT NOT NULL,
    total_minions_killed            SMALLINT NOT NULL,

    -- Shop
    gold_earned          INT NOT NULL,
    gold_spent           INT NOT NULL,
    consumables_purchased SMALLINT NOT NULL,

    PRIMARY KEY (match_id, participant_id)
);
CREATE INDEX idx_participants_puuid        ON participant_stats (puuid);
CREATE INDEX idx_participants_team_pos     ON participant_stats (team_position);

CREATE TABLE participant_challenges (
    match_id        VARCHAR(30) NOT NULL,
    participant_id  SMALLINT    NOT NULL,

    -- Metadata
    had_afk_teammate              BOOLEAN,
    max_level_lead_lane_opponent  SMALLINT,

    -- KDA-related challenges
    jungler_kills_early_jungle SMALLINT,
    kills_on_laners_early_jungle_as_jungler SMALLINT,
    takedowns_first_25_minutes  SMALLINT,
    aces_before_15_minutes      SMALLINT,
    buffs_stolen                SMALLINT,
    dodge_skill_shots_small_window SMALLINT,
    flawless_ace                SMALLINT,
    kda                         NUMERIC(6,2),
    kill_after_hidden_with_ally SMALLINT,
    kill_participation          NUMERIC(5,4),
    kills_near_enemy_turret     SMALLINT,
    kills_on_other_lanes_early_jungle_as_laner SMALLINT,
    kills_under_own_turret      SMALLINT,
    kills_with_help_from_epic_monster SMALLINT,
    multikills_after_aggressive_flash SMALLINT,
    took_large_damage_survived  SMALLINT,
    takedowns_before_jungle_minion_spawn SMALLINT,
    takedowns_after_gaining_level_advantage SMALLINT,
    takedown_on_first_turret    SMALLINT,
    solo_kills                  SMALLINT,
    skillshots_dodged           SMALLINT,
    save_ally_from_death        SMALLINT,
    quick_solo_kills            SMALLINT,
    pick_kill_with_ally         SMALLINT,
    outnumbered_kills           SMALLINT,

    -- Damage-ratio challenges
    damage_per_minute             NUMERIC(8,2),
    damage_taken_on_team_pct      NUMERIC(5,4),
    team_damage_pct               NUMERIC(5,4),

    -- Skill-shot & CC
    enemy_champion_immobilization SMALLINT,
    immobilize_and_kill_with_ally SMALLINT,
    knock_enemy_into_team_and_kill SMALLINT,
    land_skill_shots_early_game   SMALLINT,
    skillshots_hit                SMALLINT,

    -- Heal/Shield
    effective_heal_and_shielding  INT,

    -- Vision
    control_ward_time_coverage_in_river_or_enemy_half NUMERIC(5,4),
    vision_score_advantage_lane_opponent NUMERIC(6,2),
    ward_takedowns_before_20m     SMALLINT,
    ward_takedowns                SMALLINT,
    wards_guarded                 SMALLINT,
    vision_score_per_minute       NUMERIC(6,2),

    -- Tower
    solo_turret_late_game         SMALLINT,
    k_turrets_destroyed_before_plates_fall SMALLINT,
    turrets_taken_with_rift_herald SMALLINT,
    turret_plates_taken           SMALLINT,
    quick_first_turret            BOOLEAN,
    multi_turret_rift_herald_count SMALLINT,

    -- Entity
    max_cs_advantage_on_lane_opponent  SMALLINT,
    void_monster_kill                  SMALLINT,
    allied_jungle_monster_kills        SMALLINT,
    elder_dragon_kills_with_opposing_soul SMALLINT,
    enemy_jungle_monster_kills         SMALLINT,
    epic_monster_steals                SMALLINT,
    initial_buff_count                 SMALLINT,
    initial_crab_count                 SMALLINT,
    jungle_cs_before_10_minutes        SMALLINT,
    lane_minions_first_10_minutes      SMALLINT,
    more_enemy_jungle_than_opponent    NUMERIC(6,2),
    rift_herald_takedowns              SMALLINT,
    solo_baron_kills                   SMALLINT,
    team_rift_herald_kills             SMALLINT,
    team_elder_dragon_kills            SMALLINT,
    perfect_dragon_souls_taken         SMALLINT,

    -- Shop
    bounty_gold       INT,
    gold_per_minute   NUMERIC(8,2),

    PRIMARY KEY (match_id, participant_id),
    FOREIGN KEY (match_id, participant_id)
        REFERENCES participant_stats(match_id, participant_id)
        ON DELETE CASCADE
);
CREATE INDEX idx_challenges_kill_participation ON participant_challenges (kill_participation);
CREATE INDEX idx_challenges_kda                ON participant_challenges (kda);

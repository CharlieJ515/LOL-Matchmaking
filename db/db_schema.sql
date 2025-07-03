-- 경기 메타
CREATE TABLE matches (
    match_id           VARCHAR(30)  PRIMARY KEY,
    data_version       SMALLINT     NOT NULL CHECK (data_version > 0),
    platform_id        VARCHAR(5)   NOT NULL,
    queue_id           INT          NOT NULL,
    map_id             INT          NOT NULL,
    game_mode          VARCHAR(20)  NOT NULL,
    game_type          VARCHAR(20)  NOT NULL,
    game_version       VARCHAR(30)  NOT NULL,
    end_of_game_result VARCHAR(20)  NOT NULL,
    game_creation_ts   BIGINT       NOT NULL,
    game_start_ts      BIGINT       NOT NULL,
    game_end_ts        BIGINT       NOT NULL CHECK (game_end_ts >= game_start_ts),
    game_duration_sec  INT          NOT NULL CHECK (game_duration_sec > 0),
    tournament_code    VARCHAR(40)
);

CREATE INDEX idx_matches_platform  ON matches(platform_id);
CREATE INDEX idx_matches_queue     ON matches(queue_id);

-- 팀
CREATE TABLE match_teams (
    match_id VARCHAR(30) NOT NULL REFERENCES matches(match_id),
    team_id  SMALLINT    NOT NULL CHECK (team_id IN (100,200)),
    win      BOOLEAN     NOT NULL,
    PRIMARY KEY (match_id, team_id),
    CONSTRAINT one_winner CHECK ( (team_id = 100 AND win) + (team_id = 200 AND win) = 1 )
);

CREATE INDEX idx_teams_win ON match_teams(match_id) WHERE win; -- 승리인 경기 보려고

-- 팀 오브젝트
CREATE TABLE team_objectives (
    match_id   VARCHAR(30) NOT NULL,
    team_id    SMALLINT    NOT NULL CHECK (team_id IN (100,200)),
    objective  VARCHAR(20) NOT NULL,
    first      BOOLEAN     NOT NULL,
    kills      INT         NOT NULL CHECK (kills >= 0),
    PRIMARY KEY (match_id, team_id, objective),
    FOREIGN KEY (match_id, team_id) REFERENCES match_teams(match_id, team_id)
);

CREATE INDEX idx_obj_match_team ON team_objectives(match_id, objective); -- 특정 경기와 오브젝트

-- 참가자
CREATE TABLE match_participants (
    match_id            VARCHAR(30) NOT NULL,
    participant_id      SMALLINT    NOT NULL CHECK (participant_id BETWEEN 1 AND 10),
    team_id             SMALLINT    NOT NULL CHECK (team_id IN (100,200)),
    puuid               VARCHAR(80) NOT NULL,
    summoner_id         VARCHAR(80) NOT NULL,
    riot_game_name      VARCHAR(50) NOT NULL,
    riot_tag_line       VARCHAR(10) NOT NULL,
    champion_id         INT         NOT NULL,
    team_position       VARCHAR(10) NOT NULL CHECK (team_position IN ('TOP','JUNGLE','MID','BOT','SUP')),
    kills               SMALLINT    NOT NULL CHECK (kills >= 0),
    deaths              SMALLINT    NOT NULL CHECK (deaths >= 0),
    assists             SMALLINT    NOT NULL CHECK (assists >= 0),
    gold_earned         INT         NOT NULL CHECK (gold_earned >= 0),
    total_damage_dealt      INT     NOT NULL CHECK (total_damage_dealt >= 0),
    total_damage_to_champ   INT     NOT NULL CHECK (total_damage_to_champ >= 0),
    vision_score        SMALLINT    NOT NULL CHECK (vision_score >= 0),
    win                 BOOLEAN     NOT NULL,
    -- challenges
    PRIMARY KEY (match_id, participant_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

CREATE UNIQUE INDEX idx_participants_puuid ON match_participants(puuid, match_id); -- 플레이어 + 경기 중복 제거
CREATE INDEX idx_participants_puuid_single ON match_participants(puuid); -- 플레이어 기록 조회
CREATE INDEX idx_participants_puuid_champ ON match_participants(puuid, champion_id); -- 챔피언 기준 조회

-- 룬
CREATE TABLE participant_perks (
    match_id        VARCHAR(30) NOT NULL,
    participant_id  SMALLINT    NOT NULL CHECK (participant_id BETWEEN 1 AND 10),
    style_slot      SMALLINT    NOT NULL CHECK (style_slot IN (0,1)), -- primary = 0, sub = 1
    perk_id         INT         NOT NULL,
    var1            INT         NOT NULL CHECK (var1 >= 0), -- 룬 효과 세부 수치
    var2            INT         NOT NULL CHECK (var2 >= 0),
    var3            INT         NOT NULL CHECK (var3 >= 0),
    PRIMARY KEY (match_id, participant_id, style_slot, perk_id),
    FOREIGN KEY (match_id, participant_id) REFERENCES match_participants(match_id, participant_id)
);

CREATE INDEX idx_match_puuid_champ_perk ON participant_perks(puuid, match_id, champion_id, perk_id); -- 해당 유저가 해당 매치에서 어떤 챔피언과 룬을 썼는지 조회

-- 여기까지 

-- 타임라인
CREATE TABLE match_timelines (
    match_id        VARCHAR(30)  PRIMARY KEY REFERENCES matches(match_id),
    frame_interval  INT          NOT NULL -- ms 단위
);

-- 프레임별 상태
CREATE TABLE timeline_frames (
    match_id     VARCHAR(30)  NOT NULL,
    frame_idx    SMALLINT     NOT NULL, -- 0부터 시작
    timestamp_ms INT          NOT NULL, -- 경기 시작 기준 ms
    PRIMARY KEY (match_id, frame_idx),
    FOREIGN KEY (match_id) REFERENCES match_timelines(match_id)
);

CREATE INDEX idx_tl_frames_ts ON timeline_frames (match_id, timestamp_ms);

-- 프레임별 플레이어 정보
CREATE TABLE participant_frames (
    match_id           VARCHAR(30)  NOT NULL,
    frame_idx          SMALLINT     NOT NULL,
    participant_id     SMALLINT     NOT NULL,
    level              SMALLINT     NOT NULL,
    current_gold       INT          NOT NULL,
    total_gold         INT          NOT NULL,
    xp                 INT          NOT NULL,
    minions_killed     INT          NOT NULL,
    jungle_minions_killed INT       NOT NULL,
    position_x         INT,
    position_y         INT,
    time_enemy_cc_ms   INT          NOT NULL,
    -- champion_stats
    -- damage_stats
    PRIMARY KEY (match_id, frame_idx, participant_id),
    FOREIGN KEY (match_id, participant_id) REFERENCES match_participants(match_id, participant_id)
);

CREATE INDEX idx_pf_gold ON participant_frames (match_id, participant_id, frame_idx);

-- 게임 이벤트 (가지 수 정리 필요)
CREATE TABLE match_events (
    event_id      BIGSERIAL    PRIMARY KEY,
    match_id      VARCHAR(30)  NOT NULL REFERENCES matches(match_id),
    timestamp_ms  INT          NOT NULL,
    frame_idx     SMALLINT     NOT NULL,
    event_type    VARCHAR(30)  NOT NULL,
    -- payload
    -- GAME_STARTED
    -- ITEM_PURCHASED
    -- ITEM_DESTORYED
    -- WARD_PALCED
    -- LEVEL_UP
    -- SKILL_LEVEL_UP
    -- WARD_KILL
    -- CHAMPION_KILL
    -- TURRET_PLATE_DESTROYED
    -- GAME_END

);

CREATE INDEX idx_me_match_time ON match_events (match_id, timestamp_ms);

-- 아이템 거래
CREATE TABLE item_events (
    match_id      VARCHAR(30) NOT NULL,
    timestamp_ms  INT         NOT NULL,
    participant_id SMALLINT   NOT NULL,
    item_id       INT         NOT NULL,
    event_kind    VARCHAR(12) NOT NULL, -- PURCHASED/DESTROYED
    PRIMARY KEY (match_id, timestamp_ms, participant_id, item_id, event_kind),
    FOREIGN KEY (match_id, participant_id) REFERENCES match_participants(match_id, participant_id)
);

-- 챔피언 킬
CREATE TABLE champion_kills (
    match_id       VARCHAR(30) NOT NULL,
    timestamp_ms   INT         NOT NULL,
    killer_id      SMALLINT,
    victim_id      SMALLINT    NOT NULL,
    assisting_ids  SMALLINT[]  NULL,
    bounty         INT         NOT NULL,
    shutdown_bounty INT        NOT NULL, -- 연속킬을 기록한 플레이어를 죽였을 때 추가 골드량
    first_blood    BOOLEAN     NOT NULL,
    pos_x          INT,
    pos_y          INT,
    PRIMARY KEY (match_id, timestamp_ms, victim_id),
    FOREIGN KEY (match_id, killer_id) REFERENCES match_participants(match_id, participant_id),
    FOREIGN KEY (match_id, victim_id) REFERENCES match_participants(match_id, participant_id)
);

-- 스킬 레벨 업
CREATE TABLE skill_level_ups (
    match_id      VARCHAR(30) NOT NULL,
    timestamp_ms  INT         NOT NULL,
    participant_id SMALLINT   NOT NULL,
    skill_slot    SMALLINT    NOT NULL, -- 1/2/3/4
    level_up_type VARCHAR(10) NOT NULL, -- NORMAL/EVOLVE(특정 챔피언)
    PRIMARY KEY (match_id, timestamp_ms, participant_id, skill_slot),
    FOREIGN KEY (match_id, participant_id) REFERENCES match_participants(match_id, participant_id)
);

-- 레벨 업
CREATE TABLE level_ups (
    match_id      VARCHAR(30) NOT NULL,
    timestamp_ms  INT         NOT NULL,
    participant_id SMALLINT   NOT NULL,
    new_level     SMALLINT    NOT NULL,
    PRIMARY KEY (match_id, timestamp_ms, participant_id),
    FOREIGN KEY (match_id, participant_id) REFERENCES match_participants(match_id, participant_id)
);

-- 와드
CREATE TABLE ward_events (
    match_id      VARCHAR(30) NOT NULL,
    timestamp_ms  INT         NOT NULL,
    participant_id SMALLINT   NOT NULL,
    ward_type     VARCHAR(20) NOT NULL,
    event_kind    VARCHAR(10) NOT NULL,  -- PLACED/KILL
    pos_x         INT,
    pos_y         INT,
    PRIMARY KEY (match_id, timestamp_ms, participant_id, event_kind),
    FOREIGN KEY (match_id, participant_id) REFERENCES match_participants(match_id, participant_id)
);


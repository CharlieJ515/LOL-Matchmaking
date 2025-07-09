# LoL matchmaker


## 1 · What Is It?
This project collect and store League of Legends data to train a matchmaking AI to provide fair and competitive matchmaking for better user experience.
Based on recent match history, it will create an embedded vector of each players, which is used to generate matches with equal probability of winning.
This project is based on our hypothesis that highest user experience comes from competitive matches.

## 2 · Workflow

1. **Analyze** Riot’s public APIs (Account V1, Match V5, League V4) to understand data structures and constraints.
2. **Build** a structured relational database to store match data with optimized schemas and indexes.
3. (*Current) **Implements** a custom API client to crawl and collect large-scale match data.
4. **Extract** and engineers player- and team-level features for model training.
5. **Train** a machine learning model to predict match outcomes before a game starts.
6. **Generate** optimized team combinations with expected win ratio of 50:50

The final product will deliver fair and balanced team compositions on request.

## 2 · API Analysis

> This project includes an in-depth analysis of the Riot Games Developer APIs. The goal was to extract meaningful features for training matchmaking models.

### Key Findings

- **Participant DTO**  
  Uses fields like `teamId`, `participantId`, `championId`, `teamPosition`, `win`, `kills`, `deaths`, `assists`, `championLevel`, and `timePlayed` to derive role, performance, and match context.

- **Ping Events**  
  Includes fields like `getBackPings`, `enemyMissingPings`, `allInPings`, etc. Useful for quantifying player intention, engagement, and team communication.

- **Damage Metrics**  
  Divided into `magic`, `physical`, `true` types across dealt, taken, to champions, and to objectives.

- **Vision Control**  
  Metrics such as `visionScore`, `wardsPlaced`, `detectorWardsPlaced`, and `visionClearedPings` help quantify map awareness and support value.

- **Objectives & Team Stats**  
  Include `baronKills`, `dragonKills`, `inhibitorTakedowns`, `firstTowerKill`, and `turretKills` to assess contribution to match result.

- **Advanced Challenge Stats**  
  Features from Challenge Dto such as `soloKills`, `kda`, `killParticipation`, `jungleCsBefore10Minutes`, `effectiveHealAndShielding`, `skillshotsDodged`, and many more were used to model player tendencies and skill.

### Caveats & Considerations

- Used `teamPosition` for role inference; `individualPosition` IS server-inferred → not 100% reliable.
- `match_timeline` events are frame-based and often require aggregation or transformation.
- Static data mapping (e.g., `championId`, `spellId`, `itemId`) must be handled via DDragon JSON files.

## 3 · Database Architecture

> All DDL lives in **`/sql/schema.sql`**.

| Layer | Tables | Purpose |
|-------|--------|---------|
| **Match Metadata** | `matches` | Immutable, match-level facts |
| **Team Aggregates** | `team`, `team_ban` | One row per team per match + draft bans |
| **Participant Facts** | `participant_stats` | Per-player telemetry (≈ 130 columns) |

## 4 · API Client

> Asynchronous, static typed Riot API client in python with local rate limiter.

This project uses an **asynchronous API client** to communicate with Riot Games' API endpoints efficiently.  
The client uses `httpx`, `asyncio`, and `limits` packages, allowing high-speed parallel requests while adhering to Riot API's rate limits.
`pydantic` package is used to deserialize responses into static data structure with refined types for better semantics.

##  5 · Data Collection

> We plan to build a scalable data collector that continuously ingest match data from Riot’s API.

### Target Flow

1. **Seed with known summoner PUUIDs**
2. **Retrieve recent matchlists** using the `match-v5` endpoint
3. **Extract detailed match info** and timeline from each match ID
4. **Remove duplicates and store** in a database table
5. **Log gaps or failures** for retry queue or fallback logic

💡 All crawling respects Riot's official rate limits per region and method, ensuring our system remains compliant and non-disruptive to their infrastructure.

## 6 · Model Training – Planned Flow

> Once we have a database filled with matches, we’ll begin training models to output expected match outcomes.

### Target Flow

1. **Load data** from the database
2. **Augment and normalize** data
3. **Feed** normalized data to model
4. **Train** model to provide better prediction
5. **Plot** model metrics

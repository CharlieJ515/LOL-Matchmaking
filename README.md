# LoL matchmaker

This project collects, stores, and models Riot Games data to prevent unfair team compositions and ensure that both teams have an equal predicted win probability through fair matchmaking.

## 1 · What Is It?

> 'LoL matchmaking' is an end-to-end pipeline that

1. **Analyzes** Riot’s public APIs (Account V1, Match V5, League V4) to understand data structures and constraints.
2. **Builds** a structured relational database to store match data with optimized schemas and indexes.
3. **Implements** a custom API client to crawl and collect large-scale match data.
4. **Extracts** and engineers player- and team-level features for model training.
5. **Trains** a machine learning model to predict match outcomes before a game starts.
6. **generates** optimized team combinations whose predicted win probabilities are as close to 50:50 as possible.

The final product delivers fair and balanced team compositions whenever requested.

## 2 · API Analysis

> This project includes an in-depth reverse engineering of the Riot Games Developer APIs and raw game telemetry data. The goal was to extract meaningful, reliable features for training fair matchmaking models.

### Key Findings

- **Participant DTO**  
  Uses fields like `teamId`, `participantId`, `championId`, `teamPosition`, `win`, `kills`, `deaths`, `assists`, `championLevel`, and `timePlayed` to derive role, performance, and match context.

- **Ping Events**  
  Includes types like `getBackPings`, `enemyMissingPings`, `allInPings`, etc. Useful for quantifying player intention, engagement, and team communication.

- **Damage Metrics**  
  Divided into `magic`, `physical`, `true` types across dealt, taken, to champions, and to objectives.

- **Vision Control**  
  Metrics such as `visionScore`, `wardsPlaced`, `detectorWardsPlaced`, and `visionClearedPings` help quantify map awareness and support value.

- **Objectives & Team Stats**  
  Includes `baronKills`, `dragonKills`, `inhibitorTakedowns`, `firstTowerKill`, and `turretKills` to assess macro impact and contribution to team wins.

- **Identifiers**  
  - `puuid`: Global Riot account ID (**recommended for joins**)  
  - `riotId`: Combination of `gameName#tagline` (e.g. `summer#pado`)

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
| **Match Meta** | `matches` | Immutable, match-level facts |
| **Team Aggregates** | `team`, `team_ban` | One row per team per match + draft bans |
| **Participant Facts** | `participant_stats` | Per-player telemetry (≈ 130 columns) |

## 4 · API Client

> Fully async, typed Riot API wrapper with automatic rate limit handling and connection reuse.

This project uses an **async Python client** to interact with Riot Games' API endpoints efficiently.  
The client is built with `httpx`, `asyncio`, and `aiolimiter`, allowing for high-speed parallel requests while respecting rate limits.

1. **Create a client** with your API key and region-specific rate limit settings.
2. **Call API methods** like `get_summoner_by_name()`, `get_matchlist()`, or `get_match()`.
3. **Receive responses** already parsed as typed Python objects (using `pydantic`).
4. **Close the client** after use to release the connection pool.

##  5 · Crawling

> We plan to build a scalable, async crawler that continuously ingests match data from Riot’s API for model training and analysis.

### Target Flow

1. **Seed with known summoner PUUIDs**
2. **Retrieve recent matchlists** using the `match-v5` endpoint
3. **Extract detailed match info** and timeline from each match ID
4. **De-duplicate and store** in a database table
5. **Log gaps or failures** for retry queue or fallback logic

💡 All crawling respects Riot's official rate limits per region and method, ensuring our system remains compliant and non-disruptive to their infrastructure.

## 6 · Model Training – Planned Flow

> Once we have a steady stream of matches, we’ll begin turning raw JSON into model-ready features for training fair matchmaking predictions.

### Target Flow

1. **Load raw JSON** from the match API
2. **Flatten into structured tables** (already designed, see `participant_stats`)
3. **Extract features** such as:
   - position distribution
   - Early-game aggression
   - Vision control (vision score etc)
   - Kill participation
   - Solo carry potential
4. **Write into a versioned feature store**
5. **Train & evaluate models**
6. **Log model metrics**, confusion matrix, ROC-AUC, and fairness gap

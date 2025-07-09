# LoL matchmaker

This project collects, stores, and models Riot Games data to prevent unfair team compositions and ensure that both teams have an equal predicted win probability through fair matchmaking.

## 1 · What Is It?

'LoL matchmaking' is an end-to-end pipeline that

1. **Analyzes** Riot’s public APIs (Accout V1, Match V5, League V4) to understand data structures and constraints.
2. ""Builds** a structured relational database to store match data with optimized schemas and indexes.
3. **Implements** a custom API client to crawl and collect large-scale match data.
4. **Extracts** and engineers player- and team-level features for model training.
5. **Trains** a machine learning model to predict match outcomes before a game starts.
6. **generates** optimized team combinations whose predicted win probabilities are as close to 50:50 as possible.

The final product delivers fair and balanced team compositions whenever requested.

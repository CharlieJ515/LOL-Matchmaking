CREATE TABLE summoners (
    summoner_id SMALLINT PRIMARY KEY,
    summoner_name text NOT NULL
);

-- https://ddragon.leagueoflegends.com/cdn/15.15.1/data/en_US/summoner.json
INSERT INTO
    summoners (summoner_id, summoner_name)
VALUES
    (1, 'Cleanse'),
    (3, 'Exhaust'),
    (4, 'Flash'),
    (6, 'Ghost'),
    (7, 'Heal'),
    (11, 'Smite'),
    (12, 'Teleport'),
    (14, 'Ignite'),
    (21, 'Barrier');
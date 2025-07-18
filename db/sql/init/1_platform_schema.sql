
CREATE TABLE platform (
  platform_id VARCHAR(4) PRIMARY KEY,
  host TEXT NOT NULL
);

INSERT INTO platform (platform_id, host) VALUES
  ('BR1', 'br1.api.riotgames.com'),
  ('EUN1', 'eun1.api.riotgames.com'),
  ('EUW1', 'euw1.api.riotgames.com'),
  ('JP1', 'jp1.api.riotgames.com'),
  ('KR',  'kr.api.riotgames.com'),
  ('LA1', 'la1.api.riotgames.com'),
  ('LA2', 'la2.api.riotgames.com'),
  ('NA1', 'na1.api.riotgames.com'),
  ('OC1', 'oc1.api.riotgames.com'),
  ('TR1', 'tr1.api.riotgames.com'),
  ('RU',  'ru.api.riotgames.com'),
  ('PH2', 'ph2.api.riotgames.com'),
  ('SG2', 'sg2.api.riotgames.com'),
  ('TH2', 'th2.api.riotgames.com'),
  ('TW2', 'tw2.api.riotgames.com'),
  ('VN2', 'vn2.api.riotgames.com');

CREATE TABLE users (
	puuid TEXT PRIMARY KEY,
	match_id_queried date DEFAULT 'epoch' :: date NOT NULL,
	lease_until timestamptz DEFAULT 'epoch' :: timestamptz NOT NULL,
	platform_name TEXT NOT NULL,
	FOREIGN KEY (platform_name) REFERENCES platforms(platform_name)
);

--CREATE INDEX idx_platform_match_id_queried_lease_until_puuid ON users (
--	platform_name,
--	match_id_queried,
--	lease_until,
--	puuid
--);

--create index idx_users_platform_lease_until_queried__incl_puuid on users (
--	platform_name,
--	lease_until,
--	match_id_queried
--) include (puuid);   

CREATE INDEX IF NOT EXISTS idx_users_platform_lease
  ON users (platform_name, lease_until);

CREATE INDEX IF NOT EXISTS idx_users_platform_matchq
  ON users (platform_name, match_id_queried);

CREATE TABLE match_ids (
    lease_until timestamptz NOT NULL DEFAULT 'epoch' :: timestamptz,
    queried bool NOT NULL DEFAULT false,
    match_id TEXT PRIMARY KEY,
    region_name TEXT NOT NULL,
    FOREIGN KEY (region_name) REFERENCES regions(region_name)
);

CREATE INDEX idx_match_ids_region_queried_lease_until_match_id ON match_ids (region_name, queried, lease_until, match_id);

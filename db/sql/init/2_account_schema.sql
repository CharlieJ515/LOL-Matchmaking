CREATE TABLE users (
  puuid        VARCHAR(78) PRIMARY KEY,
  platform_id  VARCHAR(4) NOT NULL,
  FOREIGN KEY (platform_id) REFERENCES platform(platform_id)
);

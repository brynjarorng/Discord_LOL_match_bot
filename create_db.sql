DROP TABLE IF EXISTS player_matches;
CREATE TABLE player_matches (
    player_gameId bigint,
    player_role text,
    player_season int,
    player_platformId text,
    player_champion int,
    player_queue int,
    player_lane text,
    player_timestamp bigint,
	unique(player_gameId)
);

-- NEED TABLE TO LINK TO SUMMONER
DROP TABLE IF EXISTS summoner_info;
CREATE TABLE summoner_info (
    encrypted_account_id text,
    accountId text,
    puuid text,
    name text,
    summonerLevel int
)

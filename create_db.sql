DROP TABLE IF EXISTS player_matches;
CREATE TABLE player_matches (
    player_gameId  bigint,
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
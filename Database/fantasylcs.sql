-- midbot.discordinfo definition

-- Drop table

-- DROP TABLE midbot.discordinfo;

CREATE TABLE midbot.discordinfo (
	discordname text NOT NULL,
	summoner text NOT NULL,
	serverid int8 NOT NULL,
	CONSTRAINT discordinfo_pkey PRIMARY KEY (discordname, serverid)
);


-- midbot.leagues definition

-- Drop table

-- DROP TABLE midbot.leagues;

CREATE TABLE midbot.leagues (
	leagueid int8 NOT NULL,
	slug text NULL,
	"name" text NULL,
	region text NULL,
	image text NULL,
	priority int8 NULL,
	CONSTRAINT leagues_pkey PRIMARY KEY (leagueid)
);


-- midbot.teams definition

-- Drop table

-- DROP TABLE midbot.teams;

CREATE TABLE midbot.teams (
	teamid int8 NOT NULL,
	slug text NULL,
	"name" text NULL,
	code text NULL,
	image text NULL,
	"alternativeImage" text NULL,
	"backgroundImage" text NULL,
	"homeLeague.name" text NULL,
	"homeLeague.region" text NULL,
	leagueid float8 NULL,
	tournamentid int8 NOT NULL,
	CONSTRAINT teams_code_key UNIQUE (code),
	CONSTRAINT teams_name_key UNIQUE (name),
	CONSTRAINT teams_pk PRIMARY KEY (teamid, tournamentid),
	CONSTRAINT teams_slug_key UNIQUE (slug)
);


-- midbot.fantasy_matchups definition

-- Drop table

-- DROP TABLE midbot.fantasy_matchups;

CREATE TABLE midbot.fantasy_matchups (
	player_1 text NOT NULL,
	player_2 text NOT NULL,
	serverid int8 NOT NULL,
	blockname text NOT NULL,
	CONSTRAINT fantasy_matchups_pkey PRIMARY KEY (player_1, player_2, serverid, blockname),
	CONSTRAINT fantasy_matchups_fk FOREIGN KEY (player_1, serverid) REFERENCES discordinfo(discordname, serverid),
	CONSTRAINT fantasy_matchups_fk_1 FOREIGN KEY (player_2, serverid) REFERENCES discordinfo(discordname, serverid)
);


-- midbot.fantasyteam definition

-- Drop table

-- DROP TABLE midbot.fantasyteam;

CREATE TABLE midbot.fantasyteam (
	username varchar(40) NOT NULL,
	serverid int8 NOT NULL,
	tournamentid int8 NOT NULL,
	top text NULL,
	jungle text NULL,
	mid text NULL,
	bot text NULL,
	support text NULL,
	flex text NULL,
	team text NULL,
	sub1 text NULL,
	sub2 text NULL,
	sub3 text NULL,
	blockname varchar NOT NULL,
	CONSTRAINT fantasyteam_pk PRIMARY KEY (username, serverid, tournamentid, blockname),
	CONSTRAINT fantasyteam_username_fkey FOREIGN KEY (username, serverid) REFERENCES discordinfo(discordname, serverid)
);


-- midbot.tournament_schedule definition

-- Drop table

-- DROP TABLE midbot.tournament_schedule;

CREATE TABLE midbot.tournament_schedule (
	tournamentid int8 NOT NULL,
	gameid int8 NOT NULL,
	start_ts timestamp NULL,
	team1code text NULL,
	team2code text NULL,
	winner_code text NULL,
	blockname text NULL,
	state text NULL,
	matchid int8 NULL,
	CONSTRAINT tournament_schedule_pk PRIMARY KEY (gameid),
	CONSTRAINT tournament_schedule_team1code_fkey FOREIGN KEY (team1code) REFERENCES teams(code),
	CONSTRAINT tournament_schedule_team2code_fkey FOREIGN KEY (team2code) REFERENCES teams(code),
	CONSTRAINT tournament_schedule_winnerid_fkey FOREIGN KEY (winner_code) REFERENCES teams(code)
);


-- midbot.tournaments definition

-- Drop table

-- DROP TABLE midbot.tournaments;

CREATE TABLE midbot.tournaments (
	tournamentid int8 NOT NULL,
	leagueid int8 NULL,
	slug text NULL,
	startdate timestamp NULL,
	enddate timestamp NULL,
	iscurrent bool NULL,
	CONSTRAINT tournaments_pkey PRIMARY KEY (tournamentid),
	CONSTRAINT tournaments_leagueid_fkey FOREIGN KEY (leagueid) REFERENCES leagues(leagueid)
);


-- midbot.weekly_predictions definition

-- Drop table

-- DROP TABLE midbot.weekly_predictions;

CREATE TABLE midbot.weekly_predictions (
	serverid int8 NOT NULL,
	discordname text NOT NULL,
	gameid int8 NOT NULL,
	blockname text NULL,
	winner text NULL,
	correct bool NULL,
	CONSTRAINT weekly_predictions_pkey PRIMARY KEY (discordname, serverid, gameid),
	CONSTRAINT weekly_predictions_fk FOREIGN KEY (winner) REFERENCES teams(code),
	CONSTRAINT weekly_predictions_serverid_fkey FOREIGN KEY (serverid, discordname) REFERENCES discordinfo(serverid, discordname)
);


-- midbot.pickems definition

-- Drop table

-- DROP TABLE midbot.pickems;

CREATE TABLE midbot.pickems (
	username varchar(40) NOT NULL,
	serverid int8 NOT NULL,
	tournamentid int8 NOT NULL,
	one text NOT NULL,
	two text NOT NULL,
	three text NOT NULL,
	four text NOT NULL,
	five text NOT NULL,
	six text NOT NULL,
	seven text NOT NULL,
	eight text NOT NULL,
	nine text NOT NULL,
	ten text NOT NULL,
	CONSTRAINT pickems_pkey PRIMARY KEY (username, serverid, tournamentid),
	CONSTRAINT pickems_eight_fkey FOREIGN KEY (eight) REFERENCES teams(code),
	CONSTRAINT pickems_five_fkey FOREIGN KEY (five) REFERENCES teams(code),
	CONSTRAINT pickems_four_fkey FOREIGN KEY (four) REFERENCES teams(code),
	CONSTRAINT pickems_nine_fkey FOREIGN KEY (nine) REFERENCES teams(code),
	CONSTRAINT pickems_one_fkey FOREIGN KEY (one) REFERENCES teams(code),
	CONSTRAINT pickems_seven_fkey FOREIGN KEY (seven) REFERENCES teams(code),
	CONSTRAINT pickems_six_fkey FOREIGN KEY (six) REFERENCES teams(code),
	CONSTRAINT pickems_ten_fkey FOREIGN KEY (ten) REFERENCES teams(code),
	CONSTRAINT pickems_three_fkey FOREIGN KEY (three) REFERENCES teams(code),
	CONSTRAINT pickems_tournamentid_fkey FOREIGN KEY (tournamentid) REFERENCES tournaments(tournamentid),
	CONSTRAINT pickems_two_fkey FOREIGN KEY (two) REFERENCES teams(code),
	CONSTRAINT pickems_username_fkey FOREIGN KEY (username, serverid) REFERENCES discordinfo(discordname, serverid)
);


-- midbot.player_gamedata definition

-- Drop table

-- DROP TABLE midbot.player_gamedata;

CREATE TABLE midbot.player_gamedata (
	gameid int8 NOT NULL,
	summoner_name text NOT NULL,
	participantid int4 NULL,
	"timestamp" timestamp NOT NULL,
	kills int4 NULL,
	deaths int4 NULL,
	assists int4 NULL,
	creep_score int4 NULL,
	fantasy_score numeric NULL,
	"role" text NULL,
	"level" int4 NULL,
	total_gold_earned int4 NULL,
	kill_participation numeric NULL,
	champion_damage_share numeric NULL,
	wards_placed int4 NULL,
	wards_destroyed int4 NULL,
	attack_damage int4 NULL,
	ability_power int4 NULL,
	critical_chance numeric NULL,
	attack_speed numeric NULL,
	life_steal int4 NULL,
	armor int4 NULL,
	magic_resistance int4 NULL,
	tenacity numeric NULL,
	CONSTRAINT player_gamedata_pkey PRIMARY KEY (gameid, summoner_name, "timestamp"),
	CONSTRAINT player_gamedata_fk FOREIGN KEY (gameid) REFERENCES tournament_schedule(gameid)
);


-- midbot.players definition

-- Drop table

-- DROP TABLE midbot.players;

CREATE TABLE midbot.players (
	playerid int8 NOT NULL,
	summoner_name text NULL,
	firstname text NULL,
	lastname text NULL,
	image text NULL,
	"role" text NULL,
	code text NULL,
	slug text NULL,
	tournamentid int8 NOT NULL,
	CONSTRAINT players_pkey PRIMARY KEY (playerid, tournamentid),
	CONSTRAINT players_code_fkey FOREIGN KEY (code) REFERENCES teams(code),
	CONSTRAINT players_slug_fkey FOREIGN KEY (slug) REFERENCES teams(slug),
	CONSTRAINT players_tournamentid_fkey FOREIGN KEY (tournamentid) REFERENCES tournaments(tournamentid)
);


-- midbot.team_gamedata definition

-- Drop table

-- DROP TABLE midbot.team_gamedata;

CREATE TABLE midbot.team_gamedata (
	gameid int8 NOT NULL,
	teamid int8 NOT NULL,
	frame_ts timestamp NOT NULL,
	dragons int4 NULL,
	barons int4 NULL,
	towers int4 NULL,
	first_blood bool NULL,
	under_30 bool NULL,
	win bool NULL,
	fantasy_score numeric NULL,
	CONSTRAINT team_gamedata_pkey PRIMARY KEY (gameid, teamid, frame_ts),
	CONSTRAINT team_gamedata_fk FOREIGN KEY (gameid) REFERENCES tournament_schedule(gameid)
);
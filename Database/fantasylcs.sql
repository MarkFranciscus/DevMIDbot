
-- Drop table

-- DROP TABLE public.discordinfo;

CREATE TABLE public.discordinfo (
	discordname text NOT NULL,
	summoner text NOT NULL,
	serverid int8 NOT NULL,
	CONSTRAINT discordinfo_pkey PRIMARY KEY (discordname, serverid)
);

-- Drop table

-- DROP TABLE public.leagues;

CREATE TABLE public.leagues (
	leagueid int8 NOT NULL,
	slug text NULL,
	"name" text NULL,
	region text NULL,
	image text NULL,
	priority int8 NULL,
	CONSTRAINT leagues_pkey PRIMARY KEY (leagueid)
);

-- Drop table

-- DROP TABLE public.teams;

CREATE TABLE public.teams (
	teamid int8 NOT NULL,
	slug text NULL,
	"name" text NULL,
	code text NULL,
	image text NULL,
	"alternativeImage" text NULL,
	"backgroundImage" text NULL,
	"homeLeague.name" text NULL,
	"homeLeague.region" text NULL,
	"homeLeague" float8 NULL,
	CONSTRAINT teams_code_key UNIQUE (code),
	CONSTRAINT teams_name_key UNIQUE (name),
	CONSTRAINT teams_pkey PRIMARY KEY (teamid),
	CONSTRAINT teams_slug_key UNIQUE (slug)
);

-- Drop table

-- DROP TABLE public.fantasyteam;

CREATE TABLE public.fantasyteam (
	username varchar(40) NOT NULL,
	serverid int8 NOT NULL,
	leagueid int4 NOT NULL,
	top int8 NULL,
	jungle int8 NULL,
	mid int8 NULL,
	bot int8 NULL,
	support int8 NULL,
	flex text NULL,
	team text NULL,
	sub1 text NULL,
	sub2 text NULL,
	sub3 text NULL,
	CONSTRAINT fantasyteam_pkey PRIMARY KEY (username, serverid, leagueid),
	CONSTRAINT fantasyteam_username_fkey FOREIGN KEY (username, serverid) REFERENCES discordinfo(discordname, serverid)
);

-- Drop table

-- DROP TABLE public.tournaments;

CREATE TABLE public.tournaments (
	tournamentid int8 NOT NULL,
	leagueid int8 NULL,
	slug text NULL,
	startdate timestamp NULL,
	enddate timestamp NULL,
	iscurrent bool NULL,
	CONSTRAINT tournaments_pkey PRIMARY KEY (tournamentid),
	CONSTRAINT tournaments_leagueid_fkey FOREIGN KEY (leagueid) REFERENCES leagues(leagueid)
);

-- Drop table

-- DROP TABLE public.pickems;

CREATE TABLE public.pickems (
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

-- Drop table

-- DROP TABLE public.players;

CREATE TABLE public.players (
	playerid int8 NOT NULL,
	summonername text NULL,
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

CREATE TABLE team_gamedata (
	gameID BIGINT,
	teamID BIGINT REFERENCES teams,
	frame_ts TIMESTAMP,
	num_dragons INT,
	num_barons INT,
	num_towers INT,
	PRIMARY KEY (gameID, teamID),
	FOREIGN KEY()
);

CREATE TABLE player_gamedata (
	gameID BIGINT,
	playerID BIGINT REFERENCES player,
	participantID INT,
	frame_ts TIMESTAMP,
	kills INT,
	deaths INT,
	assists INT,
	creepScore INT,
	championId TEXT,
	role TEXT,
	PRIMARY KEY (gameID, playerID)
);
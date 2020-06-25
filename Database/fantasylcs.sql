-- Drop table

-- DROP TABLE public.discordinfo;

CREATE TABLE public.discordinfo (
	discordname text NOT NULL,
	summoner text NOT NULL,
	serverid int8 NOT NULL,
	CONSTRAINT discordinfo_pkey PRIMARY KEY (discordname,serverid)
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
	tournamentid int8 NOT NULL,
	CONSTRAINT teams_code_key UNIQUE (code),
	CONSTRAINT teams_name_key UNIQUE ("name"),
	CONSTRAINT teams_pk PRIMARY KEY (teamid,tournamentid),
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
	blockname varchar NOT NULL,
	CONSTRAINT fantasyteam_pk PRIMARY KEY (username,serverid,leagueid,blockname),
	CONSTRAINT fantasyteam_username_fkey FOREIGN KEY (username,serverid) REFERENCES public.discordinfo(discordname,serverid)
);

-- Drop table

-- DROP TABLE public.tournament_schedule;

CREATE TABLE public.tournament_schedule (
	tournamentid int8 NOT NULL,
	gameid int8 NOT NULL,
	start_ts timestamp NULL,
	team1code text NULL,
	team2code text NULL,
	winnerid text NULL,
	blockname text NULL,
	state text NULL,
	CONSTRAINT tournament_schedule_pk PRIMARY KEY (gameid),
	CONSTRAINT tournament_schedule_team1code_fkey FOREIGN KEY (team1code) REFERENCES public.teams(code),
	CONSTRAINT tournament_schedule_team2code_fkey FOREIGN KEY (team2code) REFERENCES public.teams(code),
	CONSTRAINT tournament_schedule_winnerid_fkey FOREIGN KEY (winnerid) REFERENCES public.teams(code)
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
	CONSTRAINT tournaments_leagueid_fkey FOREIGN KEY (leagueid) REFERENCES public.leagues(leagueid)
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
	CONSTRAINT pickems_pkey PRIMARY KEY (username,serverid,tournamentid),
	CONSTRAINT pickems_eight_fkey FOREIGN KEY (eight) REFERENCES public.teams(code),
	CONSTRAINT pickems_five_fkey FOREIGN KEY (five) REFERENCES public.teams(code),
	CONSTRAINT pickems_four_fkey FOREIGN KEY (four) REFERENCES public.teams(code),
	CONSTRAINT pickems_nine_fkey FOREIGN KEY (nine) REFERENCES public.teams(code),
	CONSTRAINT pickems_one_fkey FOREIGN KEY (one) REFERENCES public.teams(code),
	CONSTRAINT pickems_seven_fkey FOREIGN KEY (seven) REFERENCES public.teams(code),
	CONSTRAINT pickems_six_fkey FOREIGN KEY (six) REFERENCES public.teams(code),
	CONSTRAINT pickems_ten_fkey FOREIGN KEY (ten) REFERENCES public.teams(code),
	CONSTRAINT pickems_three_fkey FOREIGN KEY (three) REFERENCES public.teams(code),
	CONSTRAINT pickems_tournamentid_fkey FOREIGN KEY (tournamentid) REFERENCES public.tournaments(tournamentid),
	CONSTRAINT pickems_two_fkey FOREIGN KEY (two) REFERENCES public.teams(code),
	CONSTRAINT pickems_username_fkey FOREIGN KEY (username,serverid) REFERENCES public.discordinfo(discordname,serverid)
);

-- Drop table

-- DROP TABLE public.player_gamedata;

CREATE TABLE public.player_gamedata (
	gameid int8 NOT NULL,
	summoner_name text NOT NULL,
	participantid int4 NULL,
	frame_ts timestamp NOT NULL,
	kills int4 NULL,
	deaths int4 NULL,
	assists int4 NULL,
	creep_score int4 NULL,
	fantasy_score numeric NULL,
	"role" text NULL,
	CONSTRAINT player_gamedata_pkey PRIMARY KEY (gameid,summoner_name,frame_ts),
	CONSTRAINT player_gamedata_gameid_fkey FOREIGN KEY (gameid) REFERENCES public.tournament_schedule(gameid)
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
	CONSTRAINT players_pkey PRIMARY KEY (playerid,tournamentid),
	CONSTRAINT players_code_fkey FOREIGN KEY (code) REFERENCES public.teams(code),
	CONSTRAINT players_slug_fkey FOREIGN KEY (slug) REFERENCES public.teams(slug),
	CONSTRAINT players_tournamentid_fkey FOREIGN KEY (tournamentid) REFERENCES public.tournaments(tournamentid)
);

-- Drop table

-- DROP TABLE public.team_gamedata;

CREATE TABLE public.team_gamedata (
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
	CONSTRAINT team_gamedata_pkey PRIMARY KEY (gameid,teamid,frame_ts),
	CONSTRAINT team_gamedata_gameid_fkey FOREIGN KEY (gameid) REFERENCES public.tournament_schedule(gameid)
);

CREATE TABLE public.fantasy_matchups (
	player_1 TEXT NOT NULL REFERENCES discordinfo(discordname),
	player_2 TEXT NOT NULL REFERENCES discordinfo(discordname),
	serverid INT8 NOT NULL REFERENCES discordinfo(serverid)
	blockName TEXT NOT NULL,
	PRIMARY KEY (player_1, player_2, serverid, blockName)
)

create table public.remaining_games (
	tournamentid BIGINT REFERENCES tournaments(tournamentid),
	blockname TEXT,
	code TEXT REFERENCES teams(code),
	num_games_left INT,
	num_total_games INT,
	PRIMARY KEY (tournamentid, block_name, code)
)

CREATE TABLE public.weekly_predictions (
	serverid int8,
	discordname TEXT,
	gameid int8 REFERENCES tournament_schedule(gameid),
	blockname TEXT,
	winner TEXT REFERENCES teams(slug),
	PRIMARY KEY (discordname, serverid, gameid),
	FOREIGN KEY (serverid, discordname) REFERENCES discordinfo (serverid, discordname)	
);
drop table if exists Ranking;
drop table if exists DiscordInfo;

create table DiscordInfo (
	discordName varchar NOT NULL,
	Summoner varchar NOT NULL, 
	ServerID bigint NOT NULL,
	primary key (discordName, ServerID)
);


create table Ranking (
	username NOT NULL REFERENCES DiscordInfo(discordName),
	split integer,
	one varchar NOT NULL,
	two varchar NOT NULL,
	three varchar NOT NULL,
	four varchar NOT NULL,
	five varchar NOT NULL,
	six varchar NOT NULL,
	seven varchar NOT NULL,
	eight varchar NOT NULL,
	nine varchar NOT NULL,
	ten varchar NOT NULL,
	primary key (username, split)
);

create table LastOnline (
	username varchar NOT NULL REFERENCES DiscordInfo(discordName),
	login date NOT NULL,
	primary key (username)
);

create table Teams (
	season int NOT NULL,
	T1 varchar NOT NULL,
	T2 varchar NOT NULL,
	T3 varchar NOT NULL,
	T4 varchar NOT NULL,
	T5 varchar NOT NULL,
	T6 varchar NOT NULL,
	T7 varchar NOT NULL,
	T8 varchar NOT NULL,
	T9 varchar NOT NULL,
	T10 varchar NOT NULL,
	primary key (season)
);

create table LastCommand (
	username varchar NOT NULL REFERENCES DiscordInfo(discordName),
	command varchar NOT NULL,
	day date,
	primary key (username)
);
	

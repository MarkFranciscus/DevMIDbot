drop table if exists Ranking;
drop table if exists DiscordInfo;

create table DiscordInfo (
	discordName varchar(50) NOT NULL,
	summoner varchar(20) NOT NULL, 
	serverID bigint NOT NULL,
	primary key (discordName, ServerID)
);


create table Ranking (
	username,
	split integer,
	one varchar(3) NOT NULL,
	two varchar(3) NOT NULL,
	three varchar(3) NOT NULL,
	four varchar(3) NOT NULL,
	five varchar(3) NOT NULL,
	six varchar(3) NOT NULL,
	seven varchar(3) NOT NULL,
	eight varchar(3) NOT NULL,
	nine varchar(3) NOT NULL,
	ten varchar(3) NOT NULL,
	FOREIGN KEY fk_username(username)
    REFERENCES DiscordInfo(discordName)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
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
	

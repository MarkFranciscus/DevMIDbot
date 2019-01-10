drop table if exists ranking;
drop table if exists discordInfo;

create table discordInfo (
	discordName varchar(50) NOT NULL,
	summoner varchar(20) NOT NULL, 
	serverID bigint NOT NULL,
	primary key (discordName, ServerID)
);


create table pickem (
	username varchar(40) NOT NULL,
	serverID bigint NOT NULL,
	split int,
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
	FOREIGN KEY fk_username(username, serverID)
    REFERENCES discordInfo(discordName, serverID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
	primary key (username, split)
);

create table lastOnline (
	username varchar(40) NOT NULL REFERENCES discordInfo(discordName),
	login date NOT NULL,
	primary key (username)
);

create table teams (
	season int NOT NULL,
	T1 varchar(3) NOT NULL,
	T2 varchar(3) NOT NULL,
	T3 varchar(3) NOT NULL,
	T4 varchar(3) NOT NULL,
	T5 varchar(3) NOT NULL,
	T6 varchar(3) NOT NULL,
	T7 varchar(3) NOT NULL,
	T8 varchar(3) NOT NULL,
	T9 varchar(3) NOT NULL,
	T10 varchar(3) NOT NULL,
	primary key (season)
);

create table lastCommand (
	username varchar(40) NOT NULL REFERENCES DiscordInfo(discordName),
	command varchar(100) NOT NULL,
	day date,
	primary key (username)
);

create fantasyTeam (
	username varchar(40) NOT NULL,
	serverID bigint NOT NULL,
	split int NOT NULL,
	top int,
	jungle int,
	mid int,
	bot int,
	support int,
	flex int,
	team int,
	sub1 int,
	sub2 int,
	sub3 int,
	primary key(username, serverID, split)
);
	

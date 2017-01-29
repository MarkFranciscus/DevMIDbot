drop table if exists Ranking;
drop table if exists DiscordInfo;

create table DiscordInfo (
	discordName CHAR(100) NOT NULL UNIQUE,
	Summoner CHAR(100) NOT NULL UNIQUE, 
	primary key (discordName)
);


create table Ranking (
	username CHAR(100) NOT NULL REFERENCES DiscordInfo(discordName),
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
	primary key (username)
);

select * from ranking, DiscordInfo;
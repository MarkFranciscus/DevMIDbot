drop table if exists Ranking;
drop table if exists DiscordInfo;

create table DiscordInfo (
	discordName varchar NOT NULL,
	Summoner varchar unique, 
	primary key (discordName)
);


create table Ranking (
	username varchar NOT NULL REFERENCES DiscordInfo(Summoner),
	one varchar NOT NULL,
	two varchar NOT NULL,
	three varchar NOT NULL,
	four varchar NOT NULL,
	five varchar NOT NULL,
	six varchar NOT NULL,
	seven varchar NOT NULL,
	eight varchar NOT NULL,
	nine varchar NOT NULL,
	ten varchar NOT NULL
);

select * from ranking, DiscordInfo;
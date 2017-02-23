drop table if exists Ranking;
drop table if exists DiscordInfo;

create table DiscordInfo (
	discordName varchar NOT NULL,
	Summoner varchar NOT NULL, 
	ServerID int NOT NULL,
	primary key (discordName, ServerID)
);


create table Ranking (
	username NOT NULL REFERENCES DiscordInfo(discordName),
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
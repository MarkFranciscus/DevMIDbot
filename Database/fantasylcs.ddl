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

select * from ranking, DiscordInfo;


INSERT INTO DiscordInfo VALUES ('rhythmkiller#3594', 'goalie1752', 283697961563717634);

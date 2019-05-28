DROP TABLE IF EXISTS pickems;
DROP TABLE IF EXISTS fantasyTeam;
DROP TABLE IF EXISTS standings;
DROP TABLE IF EXISTS teams;
drop table if exists splits;
DROP TABLE IF EXISTS discordInfo;

-- Basic discord user information
CREATE TABLE discordInfo (
	discordName TEXT NOT NULL,
	summoner TEXT NOT NULL, 
	serverID BIGINT NOT NULL,
	unique (discordName, serverID),
	PRIMARY KEY (discordName, serverID)	
);

-- Split information
CREATE TABLE splits (
	splitID INT NOT null,
	splitName text not null,
	region text not null,
	title text not null,
	isCurrent BOOLEAN not null,
	alt1 text,
	alt2 text,
	alt3 text,
	alt4 text,
	alt5 text,
	unique(splitID),
	PRIMARY KEY (splitID)
);

-- Pickem ranking
CREATE TABLE pickems (
	username VARCHAR(40) NOT NULL,
	serverID BIGINT NOT NULL,
	splitID INT,
	one TEXT NOT NULL,
	two TEXT NOT NULL,
	three TEXT NOT NULL,
	four TEXT NOT NULL,
	five TEXT NOT NULL,
	six TEXT NOT NULL,
	seven TEXT NOT NULL,
	eight TEXT NOT NULL,
	nine TEXT NOT NULL,
	ten TEXT NOT NULL,
	unique(username, serverID, splitID),
	PRIMARY KEY (username, serverID, splitID),
	FOREIGN KEY (username, serverID) references discordinfo(discordName,  serverID),
	foreign key (splitID) references splits(splitID)
);

-- List of teams in a particular split
CREATE TABLE teams (
	splitID INT NOT NULL,
	team1 TEXT NOT NULL,
	team2 TEXT NOT NULL,
	team3 TEXT NOT NULL,
	team4 TEXT NOT NULL,
	team5 TEXT NOT NULL,
	team6 TEXT NOT NULL,
	team7 TEXT NOT NULL,
	team8 TEXT NOT NULL,
	team9 TEXT NOT NULL,
	team10 TEXT NOT NULL,
	unique(splitID),
	PRIMARY KEY (splitID),
	foreign key (splitID) references splits(splitID)
);

-- Fantasy team table
CREATE TABLE fantasyTeam (
	username VARCHAR(40) NOT NULL,
	serverID BIGINT NOT NULL,
	leagueID INT NOT NULL, 
	top INT,
	jungle INT,
	mid INT,
	bot INT,
	support INT,
	flex INT,
	team INT,
	sub1 INT,
	sub2 INT,
	sub3 INT,
	unique(username, serverID, leagueID),
	PRIMARY KEY(username, serverID, leagueID),
	foreign key (username, serverID) references discordinfo(discordname, serverID)
);

-- Standings
CREATE TABLE standings (
	splitID INT NOT NULL,
	updateID BIGINT NOT NULL,
	teamID VARCHAR(40) NOT NULL,
	placement INT NOT NULL,
	update_date DATE NOT NULL,
	unique(splitID, updateID, teamID),
	PRIMARY KEY(splitID, updateID, teamID),
	foreign key (splitID) references splits(splitID)
);

insert into splits values (1, 'LCS 2019 Spring Split', 'NA', 'lcs_2019_spring', true)

SELECT splitID FROM splits WHERE region = 'NA' AND isCurrent = true;
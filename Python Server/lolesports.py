import requests, json
import time


tournamentURL = "http://api.lolesports.com/api/v1/scheduleItems?leagueId={}"
teamURL = "http://api.lolesports.com/api/v1/teams?slug={1}&tournament={2}"
r = requests.get(tournamentURL.format("2"))
rawData = json.loads(r.text)

def get_team_ids():
    rosters = rawData["highlanderTournaments"][6]["rosters"].values()
    ids = []
    for x in rosters:
        ids.append(int(x["team"]))
    return ids

def get_standings():
    brackets, rosters = find_current_split()

    for bracket in brackets.values():
        if bracket["name"] == "regular_season":
            raw_standings = bracket["standings"]["result"]
    
    standings = {key:[] for key in range(1, 11, 1)}
    
    for i in range(len(raw_standings)):
        standings[i+1] = [rosters[x["roster"]]["name"] for x in raw_standings[i]]
    
    teams = rawData["teams"]
    result = {key:[] for key in range(1, 11, 1)}
    num_teams = 1
    for i in range(1, 10, 1):
        placement = []
        for x in standings[i]:
            for team in teams:
                if x == team["acronym"]:
                    placement.append(str(team["name"]))
        result[num_teams] = placement
        num_teams += len(standings[i])

def find_current_split():
    """Find current split and roster"""
    for split in rawData["highlanderTournaments"]:
        if split["title"] == "lcs_2019_spring":
            brackets = split["brackets"]
            rosters = split["rosters"]
    return brackets, rosters

def get_slug(ids):
    teams = rawData["teams"]
    slugs = []
    for x in ids:
        for y in teams:
            if x == y["id"]:
                slugs.append(y["slug"])
                break
    print(slugs)

print(get_standings())

# Each row is: Rank/Team/Wins/Losses
format_string = "%-4s %-20s %-s %-s"

# print "Current NA LCS STANDINGS"
# print "-----------------------------"
# print format_string % ("RANK", "TEAM", "W", "L")
# for row in stats_table.find_all("tr"):
# 	cells = row.find_all("td")
# 	if len(cells) > 0:
# 		print (format_string % (cells[0].text.strip(), cells[2].text.strip(), cells[3].text.strip(), cells[4].text.strip()))
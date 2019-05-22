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
    # Find current split and
    for split in rawData["highlanderTournaments"]:
        if split["title"] == "lcs_2019_spring":
            brackets = split["brackets"]
            rosters = split["rosters"]

    for bracket in brackets.values():
        if bracket["name"] == "regular_season":
            raw_standings = bracket["standings"]["result"]
    
    standings = {key:[] for key in range(1, 11, 1)}
    
    for i in range(len(raw_standings)):
        standings[i+1] = [rosters[x["roster"]]["name"] for x in raw_standings[i]]
    
    teams = rawData["teams"]
    result = []
    num_teams = 0
    for i in range(1, 11, 1):
        placement = []
        for x in standings[i]:
            num_teams += 1
            for team in teams:
                if x == team["acronym"]:
                    placement.append(str(team["name"]))
        standings[num_teams] = placement
    print(standings)

def get_slug(ids):
    teams = rawData["teams"]
    # print(teams)
    slugs = []
    for x in ids:
        for y in teams:
            # print (x, y["id"])
            if x == y["id"]:
                # print (x, y["id"])
                slugs.append(y["slug"])
                break
    print(slugs)
# parse the text of the URL
# q = get_team_ids()
# print(q)
print(get_standings())
# get_slug(q)
# Each row is: Rank/Team/Wins/Losses
format_string = "%-4s %-20s %-s %-s"

# print "Current NA LCS STANDINGS"
# print "-----------------------------"
# print format_string % ("RANK", "TEAM", "W", "L")
# for row in stats_table.find_all("tr"):
# 	cells = row.find_all("td")
# 	if len(cells) > 0:
# 		print (format_string % (cells[0].text.strip(), cells[2].text.strip(), cells[3].text.strip(), cells[4].text.strip()))
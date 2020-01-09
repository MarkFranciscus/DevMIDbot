import requests, json
import time
# import psycopg2
# from utility import connect_database

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

def get_standings(region):
    brackets, rosters = find_current_split(region)

    for bracket in brackets.values():
        if bracket["name"] == "regular_season":
            raw_standings = bracket["standings"]["result"]
    
    standings = {key:[] for key in range(1, 11, 1)}
    
    for i in range(len(raw_standings)):
        standings[i+1] = [rosters[x["roster"]]["name"] for x in raw_standings[i]]
    
    teams = rawData["teams"]
    result = {}
    num_teams = 1
    for i in range(1, 10, 1):
        for x in standings[i]:
            result[x] = num_teams
        num_teams += len(standings[i])
    return result

def find_current_split(region):
    """Find current split and roster"""

    for split in rawData["highlanderTournaments"]:
        if split["title"] == region:
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

def score(players_standings, real_standings):
    score = 0
    for i in range(1, 10, 1):
        score += (i - real_standings[players_standings[i]])**2
        print(score)
    return score

def format_standing_list(standings):
    temp = dict((v,k) for k,v in standings.items())
    print(temp)
    return [standings[i] for i in range(1, 10)]

import requests
import json
import datetime

header = {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"}

def getLeagues(hl="en-US"):
    d = {}    
    param = {"hl": hl}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getLeagues",
        headers=header, params=param)

    rawData = json.loads(r.text)
    leagues = rawData["data"]["leagues"]

    for league in leagues:
        d[league["name"]] = league["id"]
    
    print(d)
    
    return d

def getSchedule(leagueId, hl="en-US"):
    d = {}    
    param = {"hl": hl, "leagueId": leagueId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getSchedule",
        headers=header, params=param)
    rawData = json.loads(r.text)
    leagues = rawData["data"]

def getLive(hl="en-US"):
    pass

def getTournamentsForLeague(leagueId, hl="en-US"):
    d = {}    
    param = {"hl": hl, "leagueId": leagueId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTournamentsForLeague",
        headers=header, params=param)
    rawData = json.loads(r.text)
    tournaments = rawData["data"]["leagues"][0]["tournaments"]

    for tournament in tournaments:
        endDate = datetime.datetime.strptime(tournament["endDate"], "%Y-%m-%d")
        if endDate > datetime.datetime.now():
            print(tournament["id"])
            return tournament["id"]


def getStandings(tournamentId, hl="en-US"):
    standings = {}    
    param = {"hl": hl, "tournamentId": tournamentId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getStandings",
        headers=header, params=param)
    rawData = json.loads(r.text)

    stages = rawData["data"]["standings"][0]["stages"]

    for stage in stages:
        if stage["name"] == "Regular Season":
            for ordinal  in stage["sections"][0]["rankings"]:
                standings[ordinal["ordinal"]] = [] 
                for team in ordinal["teams"]:
                    standings[ordinal["ordinal"]].append(team["code"])
    print(standings)
    return standings

def getSlugs(tournamentId, hl="en-US"):
    slugs = []

    param = {"hl": hl, "tournamentId": tournamentId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getStandings",
        headers=header, params=param)
    rawData = json.loads(r.text)

    stages = rawData["data"]["standings"][0]["stages"]

    for stage in stages:
        if stage["name"] == "Regular Season":
            for ordinal  in stage["sections"][0]["rankings"]:
                for team in ordinal["teams"]:
                    slugs += [team["slug"]]
    print(slugs)
    return slugs

def getCompletedEvents():
    pass


def getEventDetails():
    pass


def getTeams(id, hl="en-US"):

    param = {"hl": hl, "id": id}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTeams",
        headers=header, params=param)
    rawData = json.loads(r.text)

def getPlayers(id, hl="en-US"):
    players = []
    param = {"hl": hl, "id": id}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTeams",
        headers=header, params=param)
    rawData = json.loads(r.text)
    players = rawData["data"]["teams"][0]["players"]
    return players
   

def getGames():
    pass


def getWindow():
    pass


def getDetails():
    pass


def navItems():
    pass


def videos():
    pass


def score(players_standings, real_standings):
    score = 0
    for i in range(1, 10, 1):
        score += (i - real_standings[players_standings[i]])**2
        # print(score)
    return score


def format_standing_list(standings):
    temp = dict((v,k) for k,v in standings.items())
    # print("temp", temp)
    return [temp[i] for i in range(1, 11)]


if __name__ == "__main__":
    # getLive()
    # getStandings(tournamentId=103462439438682788)
    # getSlugs(tournamentId=103462439438682788)
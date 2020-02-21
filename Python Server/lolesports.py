import datetime
import json
import time

import pandas as pd
import requests
from pandas import json_normalize

import utility

header = {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"}


def getLeagues(hl="en-US"):
    
    param = {"hl": hl}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getLeagues",
                     headers=header, params=param)

    rawData = json.loads(r.text)
    leagues = rawData["data"]["leagues"]
    
    leagues = pd.DataFrame().from_dict(json_normalize(
        leagues), orient='columns')
    
    return leagues


def getSchedule(leagueId, include_pagetoken=False, hl="en-US", pageToken=""):
    d = {}
    param = {"hl": hl, "leagueId": leagueId, "pageToken": pageToken}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getSchedule",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    events = rawData["data"]["schedule"]["events"]
    
    if include_pagetoken:
        pageTokens = rawData["data"]["schedule"]["pages"]
        return events, pageTokens
    else:
        return events


def getLive(hl="en-US"):
    param = {"hl": hl}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getLive",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    events = rawData["data"]["schedule"]["events"]
    return events


def getTournamentsForLeague(leagueId, hl="en-US"):
    d = {}
    param = {"hl": hl, "leagueId": leagueId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTournamentsForLeague",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    data = rawData["data"]["leagues"][0]["tournaments"]

    tournaments = pd.DataFrame().from_dict(json_normalize(data))
    tournaments['startDate'] = pd.to_datetime(tournaments['startDate'], utc=True)
    tournaments['endDate'] = pd.to_datetime(tournaments['endDate'], utc=True)
    tournaments.columns = map(str.lower, tournaments.columns)
    return tournaments


def getStandings(tournamentId, hl="en-US"):
    standings = {}
    param = {"hl": hl, "tournamentId": tournamentId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getStandings",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    print(f"{r.elapsed.total_seconds()}")
    stages = rawData["data"]["standings"][0]["stages"]

    for stage in stages:
        if stage["name"] == "Regular Season":
            for ordinal in stage["sections"][0]["rankings"]:
                standings[ordinal["ordinal"]] = []
                for team in ordinal["teams"]:
                    standings[ordinal["ordinal"]].append(team["code"])
    for i in range(1, 11):
        if i not in standings.keys():
            standings[i] = ['']
    return standings


def getSlugs(tournamentId, hl="en-US"):
    slugs = []

    param = {"hl": hl, "tournamentId": tournamentId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getStandings",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    # print(f"{r.elapsed.total_seconds()}")
    if  "errors" in rawData.keys():
        return []
    stages = rawData["data"]["standings"][0]["stages"]

    for stage in stages:
        if stage["name"] == "Regular Season":
            for ordinal in stage["sections"][0]["rankings"]:
                for team in ordinal["teams"]:
                    slugs += [team["slug"]]
    # print(slugs)
    return slugs


def getCodes(tournamentId, hl="en-US"):
    codes = []

    param = {"hl": hl, "tournamentId": tournamentId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getStandings",
                     headers=header, params=param)
    rawData = json.loads(r.text)

    stages = rawData["data"]["standings"][0]["stages"]

    for stage in stages:
        if stage["name"] == "Regular Season":
            for ordinal in stage["sections"][0]["rankings"]:
                for team in ordinal["teams"]:
                    codes += [team["code"]]
    # print(codes)
    return codes


def getCompletedEvents():
    pass


def getEventDetails(matchId, hl="en-US"):
    param = {"hl": hl, "id": matchId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getEventDetails",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    # print(rawData["data"].keys())
    return rawData["data"]["event"]


def get_teams(id = None, hl="en-US"):

    param = {"hl": hl, "id": id}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTeams",
                     headers=header, params=param)
    rawData = json.loads(r.text)

    team = pd.DataFrame.from_dict(json_normalize(
        rawData["data"]["teams"]), orient='columns')
    # print(rawData)
    del team['players']
    # print(team)
    return team


def getPlayers(id, hl="en-US"):

    players = pd.DataFrame()
    param = {"hl": hl, "id": id}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTeams",
                     headers=header, params=param)

    rawData = json.loads(r.text)
    player_data = rawData["data"]["teams"][0]["players"]
    team = rawData["data"]["teams"][0]['code']
    slug = rawData["data"]["teams"][0]['slug']

    players = pd.DataFrame().from_dict(json_normalize(player_data), orient='columns')
    players['code'] = [team] * players.shape[0]
    players['slug'] = [slug] * players.shape[0]
    return players


def getGames():
    pass


def getWindow(gameId, starting_time=""):
    params = {'startingTime': starting_time}
    r = requests.get(
        "https://feed.lolesports.com/livestats/v1/window/{}".format(gameId), params=params)
    # r.encoding = 'utf-8'
    if r.status_code == 200: 
        rawData = json.loads(r.text)
        
        blueTeam = rawData['gameMetadata']['blueTeamMetadata']['esportsTeamId']
        blueMetadata_dict = rawData['gameMetadata']['blueTeamMetadata']['participantMetadata']
        
        redTeam = rawData['gameMetadata']['redTeamMetadata']['esportsTeamId']
        redMetadata_dict = rawData['gameMetadata']['redTeamMetadata']['participantMetadata']

        blueMetadata = pd.DataFrame().from_dict(json_normalize(blueMetadata_dict), orient='columns')
        redMetadata = pd.DataFrame().from_dict(json_normalize(redMetadata_dict), orient='columns')

        frames = rawData['frames']

        matchid = rawData['esportsMatchId']
        return blueTeam, blueMetadata, redTeam, redMetadata, frames, matchid
    else:
        # raise Exception(f"getWindow giving status code {r.status_code}")
        pass
    
def navItems():
    pass


def videos():
    pass


def score(players_standings, real_standings):
    score = []
    for i in range(0, 10, 1):
        score += [(i - real_standings[players_standings[i]])**2]
        # print(f"{players_standings[i]} - {score}")
    return score


def format_standing_list(standings):
    temp = dict((v, k) for k, v in standings.items())
    # print("temp", temp)
    return [temp[i] for i in range(1, 11)]


def getDetails(gameId, starting_time="", participantIds=""):
    params = {'startingTime': starting_time,
              'participantIds': participantIds}
    r = requests.get("https://feed.lolesports.com/livestats/v1/details/{}".format(gameId), params=params)
    rawData = json.loads(r.text)
    frames = rawData["frames"]
    participants = pd.DataFrame()
    for frame in frames:
        participant_data = frame["participants"]
        for participant in participant_data:
            participant['timestamp'] = frame['rfc460Timestamp']
        participants = pd.concat([participants, pd.DataFrame().from_dict(json_normalize(participant_data), orient='columns')])
        # participants['timestamp'] = frame['rfc460Timestamp']
        # print(participants)
        # print(frame['rfc460Timestamp'])
    return participants

# if __name__ == "__main__":
    # slugs = getSlugs(tournamentId=103540419468532110)
    # date_time_str = '2020-02-01 19:00:00.0'
    
    
    # data.to_csv('game2.csv')

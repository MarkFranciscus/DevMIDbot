import datetime
import json
import time
import asyncio

import pandas as pd
import requests
from aiohttp import ClientSession
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
    param = {"hl": hl, "leagueId": leagueId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTournamentsForLeague",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    data = rawData["data"]["leagues"][0]["tournaments"]

    tournaments = pd.DataFrame().from_dict(json_normalize(data))
    tournaments['startDate'] = pd.to_datetime(
        tournaments['startDate'], utc=True)
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
    if "errors" in rawData.keys():
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


def get_teams(id=None, hl="en-US"):

    param = {"hl": hl, "id": id}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTeams",
                     headers=header, params=param)
    rawData = json.loads(r.text)

    team = pd.from_dict(rawData["data"]["teams"])  # , orient='columns')
    team.drop('players', axis=1, inplace=True)
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


async def getWindow(session, gameID, starting_time=""):
    params = {'startingTime': starting_time}
    # r = requests.get(
    #     "https://feed.lolesports.com/livestats/v1/window/{}".format(gameID), params=params)
    async with session.get(f"https://feed.lolesports.com/livestats/v1/window/{gameID}", params=params, raise_for_status=True) as response:
        raw_data = await response.json()

        blue_teamID = raw_data['gameMetadata']['blueTeamMetadata']['esportsTeamId']
        blue_metadata = json_normalize(
            raw_data['gameMetadata']['blueTeamMetadata']['participantMetadata'])

        red_teamID = raw_data['gameMetadata']['redTeamMetadata']['esportsTeamId']
        red_metadata = json_normalize(
            raw_data['gameMetadata']['redTeamMetadata']['participantMetadata'])

        metadata = pd.concat([blue_metadata, red_metadata], ignore_index=True)
        metadata[['code', 'summoner_name']] = metadata['summonerName'].str.split(expand=True)
        
        red_team = json_normalize(raw_data['frames'], meta=[
                                  'redTeam', 'rfc460Timestamp', 'gameState'])
        blue_team = json_normalize(raw_data['frames'], meta=[
                                   'blueTeam', 'rfc460Timestamp', 'gameState'])

        red_team.drop(list(red_team.filter(
            regex='participants|blueTeam')), axis=1, inplace=True)
        blue_team.drop(list(blue_team.filter(
            regex='participants|redTeam')), axis=1, inplace=True)
        
        red_team.columns = red_team.columns.str.replace(r'redTeam.', '')
        blue_team.columns = blue_team.columns.str.replace(r'blueTeam.', '')
        
        red_team['teamID'] = red_teamID
        red_team['side'] = 'red'
        red_team['code'] = metadata.code.unique()[0]
        
        blue_team['teamID'] = blue_teamID
        blue_team['side'] = 'blue'
        blue_team['code'] = metadata.code.unique()[1] 

        teams = pd.concat([red_team, blue_team], ignore_index=True)
        teams['timestamp'] = pd.to_datetime(teams['rfc460Timestamp'], format='%Y-%m-%dT%H:%M:%S.%fZ', exact=False)

        blue_participants = json_normalize(
            raw_data['frames'], ['blueTeam', 'participants'], ['rfc460Timestamp'])
        red_participants = json_normalize(
            raw_data['frames'], ['redTeam', 'participants'], ['rfc460Timestamp'])

        participants = pd.concat(
            [blue_participants, red_participants], ignore_index=True)
        participants = pd.merge(participants, metadata, on='participantId')
        participants['timestamp'] = pd.to_datetime(participants['rfc460Timestamp'], format='%Y-%m-%dT%H:%M:%S.%fZ', exact=False)
        participants["gameid"] = gameID
        teams['gameid'] = gameID
        participants.drop('summonerName', axis=1, inplace=True)
        
        matchID = raw_data['esportsMatchId']
        return metadata, participants, teams, matchID

def navItems():
    pass


def videos():
    pass


def score(players_standings, real_standings):
    score = []
    for i in range(0, 10, 1):
        score += [(i+1 - real_standings[players_standings[i]])**2]
        # print(f"{players_standings[i]} - {score}")
    return score


def format_standing_list(standings):
    temp = dict((v, k) for k, v in standings.items())
    # print("temp", temp)
    return [temp[i] for i in range(1, 11)]


async def getDetails(session, gameID, timestamp="", participantIds=""):
    params = {'startingTime': timestamp,
              'participantIds': participantIds}
    async with session.get(f"https://feed.lolesports.com/livestats/v1/details/{gameID}", params=params, raise_for_status=True) as response:
        raw_data = await response.json()

        frames = raw_data["frames"]
        
        participant_data = json_normalize(frames, 'participants', 'rfc460Timestamp')
        participant_data['timestamp'] = pd.to_datetime(participant_data['rfc460Timestamp'], format='%Y-%m-%dT%H:%M:%S.%fZ')
        return participant_data
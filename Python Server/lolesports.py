import requests
import json
import datetime
import pandas as pd
from pandas.io.json import json_normalize

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


def getSchedule(leagueId, hl="en-US", pageToken=""):
    d = {}
    param = {"hl": hl, "leagueId": leagueId, "pageToken": pageToken}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getSchedule",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    events = rawData["data"]["schedule"]["events"]
    return events


def getLive(hl="en-US"):
    pass


def getTournamentsForLeague(leagueId, hl="en-US"):
    d = {}
    param = {"hl": hl, "leagueId": leagueId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getTournamentsForLeague",
                     headers=header, params=param)
    rawData = json.loads(r.text)
    data = rawData["data"]["leagues"][0]["tournaments"]

    tournaments = pd.DataFrame().from_dict(json_normalize(data))
    tournaments['startDate'] = pd.to_datetime(tournaments['startDate'])
    tournaments['endDate'] = pd.to_datetime(tournaments['endDate'])
    tournaments.columns = map(str.lower, tournaments.columns)
    return tournaments
    # for tournament in tournaments:
    #     endDate = datetime.datetime.strptime(tournament["endDate"], "%Y-%m-%d")
    #     if endDate > datetime.datetime.now():
    #         print(tournament["id"])
    #         return tournament["id"]


def getStandings(tournamentId, hl="en-US"):
    standings = {}
    param = {"hl": hl, "tournamentId": tournamentId}
    r = requests.get("https://esports-api.lolesports.com/persisted/gw/getStandings",
                     headers=header, params=param)
    rawData = json.loads(r.text)

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


def getEventDetails():
    pass


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
    rawData = json.loads(r.text)

    blueTeam = rawData['gameMetadata']['blueTeamMetadata']['esportsTeamId']
    blueMetadata_dict = rawData['gameMetadata']['blueTeamMetadata']['participantMetadata']
    
    redTeam = rawData['gameMetadata']['redTeamMetadata']['esportsTeamId']
    redMetadata_dict = rawData['gameMetadata']['redTeamMetadata']['participantMetadata']

    blueMetadata = pd.DataFrame().from_dict(json_normalize(blueMetadata_dict), orient='columns')
    redMetadata =pd.DataFrame().from_dict(json_normalize(redMetadata_dict), orient='columns')

    return blueTeam, blueMetadata, redTeam, redMetadata


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
    temp = dict((v, k) for k, v in standings.items())
    # print("temp", temp)
    return [temp[i] for i in range(1, 11)]


def roundTime(dt=None, roundTo=10):
   """Round a datetime object to any time lapse in seconds"""
   if dt == None: 
       dt = datetime.datetime.now()
   seconds = (dt.replace(tzinfo=None) - dt.min).seconds
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)


def getDetails(gameId, starting_time="", participantIds=""):
    params = {'startingTime': starting_time,
              'participantIds': participantIds}
    # print(starting_time)
    r = requests.get("https://feed.lolesports.com/livestats/v1/details/{}".format(gameId), params=params)
    rawData = json.loads(r.text)
    # print(rawData)
    participant_data = rawData["frames"][0]["participants"]
    # print(participant_data)
    participants = pd.DataFrame().from_dict(json_normalize(participant_data), orient='columns')
    # print(participants)
    return participants

if __name__ == "__main__":
    slugs = getSlugs(tournamentId=103462439438682788)
    # blueTeam, blueMetadata, redTeam, redMetadata = getWindow("103462440145619680", starting_time=ts)
    # gameMetadata = pd.concat([blueMetadata, redMetadata]) 
    # participants = participants[['participantId', 'kills', 'deaths', 'assists', 'creepScore']].copy()
    # print(pd.merge(participants, gameMetadata, on="participantId"))
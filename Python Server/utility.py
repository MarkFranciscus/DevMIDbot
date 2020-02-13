from configparser import ConfigParser
import os
from difflib import SequenceMatcher
# from tabulate import tabulate
import itertools
import random
import time

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine.url import URL
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import sqlalchemy
from sqlalchemy.sql import and_, text

import lolesports
import datetime
import numpy as np
import pandas as pd
from pandas import json_normalize
import dateutil.parser

# print(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))
# meta = MetaData()
conn = None
Base = None


def config(filename='config.ini', section='database'):

    # create a parser
    parser = ConfigParser()

    # read config file
    filepath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '.')) + '/'
    parser.read(filepath + filename)
    db = {}

    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            'Section {0} not found in the {1} file'.format(section, filename))

    return db


def connect_database():
    """ Connect to the PostgreSQL database server """
    global conn
    global Base

    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    # print(params)
    url = URL(**params)
    engine = create_engine(url, client_encoding='utf8', use_batch_mode=True)
    conn = engine.connect()
    conn.execute("SET search_path TO public")

    Base = automap_base()
    Base.prepare(engine, reflect=True)

    return Base, engine


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def fantasy_player_scoring(playerStats):
    score = 0
    multipliers = {"kills": 2, "deaths": -0.5,
                   "assists": 1.5, "creepScore": 0.01}
    isOver10 = False
    for stat in multipliers.keys():
        score += playerStats[stat] * multipliers[stat]
        if stat in ["kills", "assists"] and playerStats[stat] >= 10 and not isOver10:
            score += 2
    return score


def fantasy_team_scoring(teamStats):
    multipliers = {"dragons": 1, "barons": 2, "towers": 1,
                   "first_blood": 2, "win": 2, "under_30": 2}
    score = 0
    for stat in multipliers.keys():
        if stat in ["first_blood", "under_30", "win"] and teamStats[stat]:
            score += multipliers[stat]
        else:
            score += teamStats[stat] * multipliers[stat]
    return score


def format_standings(standings):
    scoreStandings = {}
    for key, value in standings.items():
        for string in value:
            if string == '':
                continue
            scoreStandings[string] = key
    return scoreStandings


def format_table(rows, standings, region):
    headers = ["Username", "1st", "2nd", "3rd", "4th",
               "5th", "6th",  "7th", "8th", "9th", "10th", "Score"]

    last_row = [region.upper()]
    for i in range(1, 11):
        if i in standings.keys():
            last_row.append("\n".join(standings[i]))
        else:
            last_row.append("")
    last_row += [0]
    pickems = rows + [last_row]

    return tabulate(pickems, headers, tablefmt="fancy_grid")


def init_data(engine):

    # league
    leagues = database_insert_leagues(engine)

    # tournaments
    tournaments = database_insert_tournaments(leagues, engine)

    # teams
    current_tournaments = tournaments[tournaments['iscurrent'] == True]
    teams = database_insert_teams(current_tournaments)

    # tournamentschedule
    tournament_schedule = database_insert_schedule(engine)

    # players
    players = database_insert_players(engine)


def database_insert_players(current_tournaments):
    players_dataframe = pd.DataFrame()
    for tournament in current_tournaments['tournamentid']:
        for slug in lolesports.getSlugs(tournament):
            temp_players = lolesports.getPlayers(slug)
            temp_players['tournamentid'] = tournament
            players_dataframe = pd.concat(
                [players_dataframe, temp_players], ignore_index=True)
    players_dataframe.rename(columns={'id': 'playerid'}, inplace=True)
    players_dataframe.columns = map(str.lower, players_dataframe.columns)
    players_dataframe.to_sql(
        "players", engine, if_exists='append', index=False)


def database_insert_teams(current_tournaments):
    teams = pd.DataFrame(columns=['slug', 'name', 'code', 'image', 'alternativeImage',
                                  'backgroundImage', 'homeLeague.name', 'homeLeague.region'])
    for tournament in current_tournaments['tournamentid']:
        for slug in lolesports.getSlugs(tournament):
            if len(teams.loc[teams['slug'] == slug].index) != 0:
                continue
            teams = pd.concat(
                [teams, lolesports.get_teams(slug)], ignore_index=True)
            teams['tournamentid'] = tournament
    teams.rename(columns={'id': 'teamid'}, inplace=True)
    # print(teams)
    # teams.to_sql("teams", engine, if_exists='append', index=False)
    return teams


def database_insert_tournaments(league, engine=None):
    all_tournaments = pd.DataFrame()
    for leagueid in league['leagueid']:
        tournaments = lolesports.getTournamentsForLeague(leagueid)
        tournaments['leagueid'] = leagueid
        tournaments['iscurrent'] = False
        tournaments.rename(columns={'id': 'tournamentid'}, inplace=True)
        dt = datetime.datetime.utcnow()
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        p = (tournaments['startdate'] <= dt) & (dt <= tournaments['enddate'])
        tournaments['iscurrent'] = np.where(p, True, False)
        all_tournaments = pd.concat(
            [all_tournaments, tournaments], ignore_index=True)
    # all_tournaments.to_sql("tournaments", engine, if_exists='append', index=False)
    return all_tournaments


def database_insert_leagues(engine):
    league = lolesports.getLeagues()
    league.rename(columns={'id': 'leagueid'}, inplace=True)
    # league.to_sql("leagues", engine, index=False, if_exists='append')
    return league


def database_insert_players(engine):
    players_dataframe = pd.DataFrame()
    slugs = lolesports.getSlugs(tournamentId=103462439438682788)
    for slug in slugs:
        players_dataframe = pd.concat(
            [players_dataframe, lolesports.getPlayers(slug)])
    players_dataframe.columns = map(str.lower, players_dataframe.columns)
    players_dataframe.rename(columns={'id': 'playerid'}, inplace=True)
    players_dataframe.to_sql(
        "players", engine, if_exists='append', index=False)
    return players_dataframe


def database_insert_schedule(engine):
    leagues = lolesports.getLeagues()
    schedule = pd.DataFrame()

    for leagueID in leagues['id']:
        events = lolesports.getSchedule(leagueId=leagueID)
        tournaments = lolesports.getTournamentsForLeague(leagueID)
        dt = datetime.datetime.utcnow()
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        p = (tournaments['startdate'] <= dt) & (dt <= tournaments['enddate'])
        tournaments['iscurrent'] = np.where(p, True, False)
        tournaments = tournaments[tournaments['iscurrent'] == True]

        for event in events:
            if event['type'] != "match":
                continue
            d = {}
            gameid = lolesports.getEventDetails(event['match']['id'])[
                'match']['games'][0]["id"]
            d['gameID'] = [gameid]
            startTime = dateutil.parser.isoparse(event['startTime'])
            d['start_ts'] = [startTime]
            d['team1code'] = [event['match']['teams'][0]['code']]
            d['team2code'] = [event['match']['teams'][1]['code']]
            d['state'] = [event['state']]
            d['blockName'] = [event['blockName']]
            p = (tournaments['startdate'] <= startTime) & (
                startTime < tournaments['enddate'])

            if len(tournaments.loc[p, 'id'].index) == 0:
                continue

            d['tournamentid'] = [tournaments.loc[p, 'id'].iloc[0]]
            if d['tournamentid'] in [102147203732523011, 103540419468532110]:
                continue

            temp = pd.DataFrame().from_dict(d)
            schedule = pd.concat([schedule, temp], ignore_index=True)

    schedule.columns = map(str.lower, schedule.columns)
    schedule.to_sql("tournament_schedule", engine,
                    if_exists='append', index=False)
    return schedule


def round_robin(teams):
    """ Generates a schedule of "fair" pairings from a list of units """
    set_size = 2
    schedule = set()

    # teams = range(5)
    for comb in itertools.product(teams, repeat=set_size):
        comb = sorted(list(comb))
        if len(set(comb)) == set_size:
            schedule.add(tuple(comb))
    schedule = list(schedule)
    random.shuffle(schedule)
    return(schedule)

# def weekly_schedule(teams, schedule):
#     for week in range(8):


def roundTime(dt=None, roundTo=10):
    """Round a datetime object to any time lapse in seconds"""
    if dt == None:
        dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+roundTo/2) // roundTo * roundTo
    return dt + datetime.timedelta(0, rounding-seconds, -dt.microsecond)


def database_update_teams(engine):
    leagues = database_insert_leagues(engine)
    tournaments = database_insert_tournaments(leagues, engine)
    current_tournaments = tournaments[tournaments['iscurrent'] == True]
    teams = database_insert_teams(current_tournaments)

    oldTeams = pd.read_sql_table("teams", engine)
    oldTeams = oldTeams.drop(["homeLeague"], axis=1)
    newTeams = teams[~teams["slug"].isin(oldTeams["slug"])]

    newTeams.to_sql("teams", engine, if_exists='append',  index=False)


def fantasy_league_table():
    get_fantasy_player_score = """
        select
            pg.summoner_name,
            sum(pg.fantasy_score),
            blockName
        from
            player_gamedata as pg,
            (
            select
                gameid,
                max(frame_ts)
            from
                player_gamedata
            group by
                gameid) as most_recent_ts,
            tournament_schedule as ts
        where
            pg.gameid = most_recent_ts.gameid
            and pg.frame_ts = most_recent_ts.max
            and pg.gameid = ts.gameid
        group by
            summoner_name,
            blockName
    """


def database_insert_gamedata(engine):
    session = Session(engine)
    Tournament_Schedule = Base.classes.tournament_schedule
    Tournaments = Base.classes.tournaments
    Player_Gamedata = Base.classes.player_gamedata
    # SQL to get split id for given region

    player_columns = ['gameid', 'participantId', 'frame_ts', 'kills', 'deaths',
                      'assists', 'creepScore', 'fantasy_score', 'summoner_name', 'role']
    map_columns = {'gameid': 'gameid', 'participantId': 'participantid',
                   'frame_ts': 'frame_ts', 'kills': 'kills', 'deaths': 'deaths',
                   'assists': 'assists', 'creepScore': 'creep_score', 'fantasy_score': 'fantasy_score',
                   'summoner_name': 'summoner_name', 'role': 'role'}

    team_columns = ['gameid', 'teamid', 'frame_ts', 'dragons', 'barons',
                    'towers', 'first_blood', 'under_30', 'win', 'fantasy_score']

    already_inserted = session.query(Player_Gamedata.gameid).distinct().all()
    already_inserted = list(set([x[0] for x in already_inserted]))

    gameid_result = session.query(Tournaments.leagueid, Tournament_Schedule.tournamentid, Tournament_Schedule.gameid,
                                  Tournament_Schedule.start_ts, Tournament_Schedule.state).join(Tournaments, Tournament_Schedule.tournamentid == Tournaments.tournamentid).filter(Tournament_Schedule.state == "completed", Tournament_Schedule.tournamentid == 103462439438682788, ~Tournament_Schedule.gameid.in_(already_inserted)).all()
    for row in gameid_result:
        leagueid = row.leagueid
        tournamentid = row.tournamentid
        gameid = row.gameid
        start_ts = row.start_ts
        # start_ts_datetime = datetime.datetime.strptime(
        #     start_ts, '%Y-%m-%dT%H:%M:%S.%fZ')
        start_ts += datetime.timedelta(hours=5)
        date_time_obj = roundTime(start_ts)
        timestamps = []
        gameStartFlag = False
        blueFirstBlood = False
        redFirstBlood = False
        state = "unstarted"

        while state != "finished":
            start_time = time.time()
            player_data = pd.DataFrame()
            team_data = pd.DataFrame()

            timestamp = date_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
            date_time_obj += datetime.timedelta(seconds=10)
            # Catches
            try:
                blueTeamID, blueMetadata, redTeamID, redMetadata, frames, matchid = lolesports.getWindow(
                    gameid, starting_time=timestamp)
            except Exception as error:
                print(f"{error} - {timestamp} - {gameid}")
                continue

            # If there's only two frames then they will be redundant frames ¯\_(ツ)_/¯
            if (len(frames) < 2):
                continue

            # Team's codes
            blueCode = blueMetadata["summonerName"].iloc[0].split(' ', 1)[1]
            redCode = redMetadata["summonerName"].iloc[0].split(' ', 1)[1]

            gameMetadata = pd.concat(
                [blueMetadata, redMetadata], ignore_index=True)

            # Start processing frame data
            for frame in frames:

                state = frame['gameState']  # Checks if game is over

                if state == 'paused':
                    continue

                # Checks if frame is redundant
                if frame['rfc460Timestamp'] in timestamps:
                    continue
                else:
                    timestamps.append(frame['rfc460Timestamp'])
                participants = pd.DataFrame()
                teams = pd.DataFrame()

                # Saves time stamp of game start
                if not gameStartFlag:
                    gameStartFlag = True
                    startTS = datetime.datetime.strptime(
                        frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

                blueTeam = frame['blueTeam']
                redTeam = frame['redTeam']

                bluePlayers = blueTeam.pop('participants')
                redPlayers = redTeam.pop('participants')

                for player in bluePlayers:
                    player['fantasy_score'] = fantasy_player_scoring(player)
                    player['gameid'] = gameid
                    player['frame_ts'] = frame['rfc460Timestamp']

                for player in redPlayers:
                    player['fantasy_score'] = fantasy_player_scoring(player)
                    player['gameid'] = gameid
                    player['frame_ts'] = frame['rfc460Timestamp']

                participants = pd.concat([participants, pd.DataFrame().from_dict(
                    json_normalize(bluePlayers)), pd.DataFrame().from_dict(
                    json_normalize(redPlayers))], ignore_index=True)

                temp_participants = pd.merge(
                    participants, gameMetadata, on="participantId")
                player_data = pd.concat(
                    [player_data, temp_participants], ignore_index=True)

                blueTeam['dragons'] = len(blueTeam['dragons'])
                blueTeam['gameid'] = gameid
                blueTeam['teamid'] = blueTeamID
                blueTeam['frame_ts'] = frame['rfc460Timestamp']
                blueTeam['first_blood'] = blueTeam['totalKills'] == 1 and redTeam['totalKills'] == 0 or blueFirstBlood
                blueTeam['win'] = False
                blueTeam['under_30'] = False

                redTeam['dragons'] = len(redTeam['dragons'])
                redTeam['gameid'] = gameid
                redTeam['teamid'] = redTeamID
                redTeam['frame_ts'] = frame['rfc460Timestamp']
                redTeam['first_blood'] = redTeam['totalKills'] == 1 and blueTeam['totalKills'] == 0 or redFirstBlood
                redTeam['win'] = False
                redTeam['under_30'] = False

                if blueTeam['first_blood']:
                    blueFirstBlood = True
                if redTeam['first_blood']:
                    redFirstBlood = True

                # Checks which team won
                if state == "finished":
                    events = lolesports.getSchedule(leagueid)
                    # matchid = gameid - 1
                    for event in events:
                        match = event["match"]
                        # print(f"{match['id']} - {matchid} - {int(match['id']) == matchid}")
                        if match["id"] == matchid:
                            if match["teams"][0]["result"]["outcome"] == "win":
                                if blueCode == match["teams"][0]["code"]:
                                    blueWin = True
                                else:
                                    blueWin = False
                            else:
                                if blueCode == match["teams"][1]["code"]:
                                    blueWin = True
                                else:
                                    blueWin = False
                            break
                        else:
                            continue

                    if blueWin:
                        blueTeam['win'] = True
                        endTS = datetime.datetime.strptime(
                            frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        blueTeam['under_30'] = endTS - \
                            startTS < datetime.timedelta(minutes=30)
                    else:
                        redTeam['win'] = True
                        endTS = datetime.datetime.strptime(
                            frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        redTeam['under_30'] = endTS - \
                            startTS < datetime.timedelta(minutes=30)

                blueTeam['fantasy_score'] = fantasy_team_scoring(blueTeam)
                redTeam['fantasy_score'] = fantasy_team_scoring(redTeam)

                teams = pd.concat([teams, pd.DataFrame().from_dict(
                    json_normalize(blueTeam)), pd.DataFrame().from_dict(
                    json_normalize(redTeam))], ignore_index=True)
                teams = teams[team_columns]

                team_data = pd.concat([team_data, teams], ignore_index=True)
            # print(player_data)
            if state == 'paused':
                continue
            player_data[['code', 'summoner_name']] = player_data['summonerName'].str.split(
                ' ', 1, expand=True)
            player_data = player_data[player_columns]
            player_data.rename(columns=map_columns, inplace=True)
            player_data.to_sql("player_gamedata", engine,
                               if_exists='append', index=False)
            team_data.to_sql("team_gamedata", engine,
                             if_exists='append', index=False)
            print(
                f"state: {state}, Time: {timestamp}, Loop Time: {time.time() - start_time}")


if __name__ == "__main__":
    Base, engine = connect_database()

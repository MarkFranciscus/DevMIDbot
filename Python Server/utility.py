import asyncio
import datetime
import itertools
import os
import random
import time
from configparser import ConfigParser
from difflib import SequenceMatcher
from time import sleep

import dateutil.parser
import numpy as np
import pandas as pd
import sqlalchemy
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pandas.io.json import json_normalize
from sqlalchemy import MetaData, Table, create_engine, inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import and_, text
from tabulate import tabulate

import lolesports

conn = None
Base = None


def config(filename='config.ini', section='database'):

    # create a parser
    parser = ConfigParser()

    # read config file
    filepath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..')) + '/'
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


def database_insert_gamedata(engine, Base):
    session = Session(engine)
    Tournament_Schedule = Base.classes.tournament_schedule
    Tournaments = Base.classes.tournaments
    Player_Gamedata = Base.classes.player_gamedata
    # SQL to get split id for given region

    already_inserted = session.query(Player_Gamedata.gameid).distinct().all()
    already_inserted = list(set([x[0] for x in already_inserted]))
    today = datetime.datetime.now()
    gameid_result = session.query(Tournaments.leagueid, Tournament_Schedule.tournamentid, Tournament_Schedule.gameid,
                                  Tournament_Schedule.start_ts, Tournament_Schedule.state).join(Tournaments, Tournament_Schedule.tournamentid == Tournaments.tournamentid).filter(Tournament_Schedule.state != "finished", Tournament_Schedule.tournamentid == 103462439438682788, ~Tournament_Schedule.gameid.in_(already_inserted), Tournament_Schedule.start_ts <= today)
    # print(str(gameid_result))
    for row in gameid_result:
        # if row.gameid in [103462440145685324]:
        parse_gamedate(engine, Base, row.leagueid, row.tournamentid, row.gameid, row.start_ts)


def parse_gamedate(engine, Base, leagueid, tournamentid, gameid, start_ts, live_data=False):
    # if live_data == False:
    start_ts += datetime.timedelta(hours=5)
    date_time_obj = roundTime(start_ts)
    timestamps = []
    gameStartFlag = False
    blueFirstBlood = False
    redFirstBlood = False
    state = "unstarted"
    session = Session(engine)
    player_columns = ['gameid', 'participantId', 'frame_ts', 'kills', 'deaths',
                      'assists', 'creepScore', 'fantasy_score', 'summoner_name', 'role']
    map_columns = {'gameid': 'gameid', 'participantId': 'participantid',
                   'frame_ts': 'frame_ts', 'kills': 'kills', 'deaths': 'deaths',
                   'assists': 'assists', 'creepScore': 'creep_score', 'fantasy_score': 'fantasy_score',
                   'summoner_name': 'summoner_name', 'role': 'role'}

    team_columns = ['gameid', 'teamid', 'frame_ts', 'dragons', 'barons',
                    'towers', 'first_blood', 'under_30', 'win', 'fantasy_score']
    print(f"Starting game {gameid}")
    while state != "finished":

        start_time = time.time()
        player_data = pd.DataFrame()
        team_data = pd.DataFrame()

        timestamp = date_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        date_time_obj += datetime.timedelta(seconds=10)

        # Catches errors
        try:
            blueTeamID, blueMetadata, redTeamID, redMetadata, frames, matchid = lolesports.getWindow(
                gameid, starting_time=timestamp)
        except Exception as error:
            print(f"{error} - {timestamp} - {gameid}")
            if live_data:
                loopTime = time.time() - start_time
                print("Game hasn't started yet")
                sleep(10 - loopTime)
            continue

        # If there's only two frames then they will be redundant frames ¯\_(ツ)_/¯
        if (len(frames) < 2):
            if live_data:
                loopTime = time.time() - start_time
                print("Skipping over redudant frames")
                sleep(10 - loopTime)
            continue

        # Team's codes
        blueCode = blueMetadata["summonerName"].iloc[0].split(' ', 1)[0]
        redCode = redMetadata["summonerName"].iloc[0].split(' ', 1)[0]

        gameMetadata = pd.concat(
            [blueMetadata, redMetadata], ignore_index=True)

        # Start processing frame data
        for frame in frames:

            state = frame['gameState']  # Checks if game is over
            # print(state)
            if state == 'paused':
                if live_data:
                    loopTime = time.time() - start_time
                    print("Skipping over redudant frames")
                    sleep(10 - loopTime)
                continue

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
                # print("test")
                events = lolesports.getSchedule(leagueid)
                # matchid = gameid - 1
                # print(f'finished - {matchid}')
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
                session = Session(engine)
                Tournament_Schedule = Base.classes.tournament_schedule
                game = session.query(Tournament_Schedule).filter(Tournament_Schedule.gameid == gameid).first()
                game.state = 'finished'
                
                if blueWin:
                    blueTeam['win'] = True
                    endTS = datetime.datetime.strptime(
                        frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    blueTeam['under_30'] = endTS - \
                        startTS < datetime.timedelta(minutes=30)
                    game.winner_code = blueCode
                else:
                    redTeam['win'] = True
                    endTS = datetime.datetime.strptime(
                        frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    redTeam['under_30'] = endTS - \
                        startTS < datetime.timedelta(minutes=30)
                    game.winner_code = redCode
                print(f"game id: {gameid} - block:{game.blockname} - winner: {game.winner_code}")
                session.commit()
            
            # Checks if frame is redundant
            if frame['rfc460Timestamp'] in timestamps:
                continue
            else:
                timestamps.append(frame['rfc460Timestamp'])
            
            participants = pd.concat([participants, pd.DataFrame().from_dict(
                json_normalize(bluePlayers)), pd.DataFrame().from_dict(
                json_normalize(redPlayers))], ignore_index=True)

            temp_participants = pd.merge(
                participants, gameMetadata, on="participantId")
            player_data = pd.concat(
                [player_data, temp_participants], ignore_index=True)

            blueTeam['fantasy_score'] = fantasy_team_scoring(blueTeam)
            redTeam['fantasy_score'] = fantasy_team_scoring(redTeam)

            teams = pd.concat([teams, pd.DataFrame().from_dict(
                json_normalize(blueTeam)), pd.DataFrame().from_dict(
                json_normalize(redTeam))], ignore_index=True)
            teams = teams[team_columns]

            team_data = pd.concat([team_data, teams], ignore_index=True)
        if state == 'paused':
            if live_data:
                loopTime = time.time() - start_time
                print("Game is paused")
                sleep(10 - loopTime)
            continue
        player_data[['code', 'summoner_name']] = player_data['summonerName'].str.split(
            ' ', 1, expand=True)
        player_data = player_data[player_columns]
        player_data.rename(columns=map_columns, inplace=True)
        player_data.to_sql("player_gamedata", engine,
                           if_exists='append', index=False)
        team_data.to_sql("team_gamedata", engine,
                         if_exists='append', index=False)
        # print(
        #     f"state: {state}, Time: {timestamp}, Loop Time: {time.time() - start_time}")
        if live_data:
            loopTime = time.time() - start_time
            print("Data parsed")
            sleep(10 - loopTime)

    


def get_fantasy_league_table(engine, Base, serverid=158269352980774912, tournamentid= 103462439438682788):
    FantasyTeam = Base.classes.fantasyteam
    blockName = get_block_name(engine, Base, tournamentid)
    selectFantasyPlayerScore = f"""
    select
        summoner_name,
        "role" ,
        sum(fantasy_score) as fantasy_score
    from
        player_gamedata as pg
    inner join (
        select
            gameid
        from
            tournament_schedule
        where
            blockname = '{blockName}'
            and tournamentid =  {tournamentid}) as games on
        pg.gameid = games.gameid
    inner join (
        select
            gameid,
            max(frame_ts)
        from
            player_gamedata
        group by
            gameid) as most_recent_ts on
        most_recent_ts.gameid = games.gameid
        and pg.frame_ts = most_recent_ts.max
    group by
        summoner_name,
        "role"
    """
    selectFantasyTeamScore = f"""select
        code as "summoner_name",
        'team' as "role",
        sum(fantasy_score) as fantasy_score
    from
        team_gamedata as tg
    inner join (
        select
            gameid
        from
            tournament_schedule
        where
            blockname = '{blockName}'
            and tournamentid = {tournamentid} ) as games on
        tg.gameid = games.gameid
    inner join (
        select
            gameid,
            max(frame_ts)
        from
            team_gamedata
        group by
            gameid) as most_recent_ts on
        most_recent_ts.gameid = games.gameid
        and tg.frame_ts = most_recent_ts.max inner join
        teams t on t.teamid = tg.teamid 
    group by
        code,
        "role"
        """

    roles = ['Top', 'Jungle', 'Mid', 'Bottom', 'Support', 'Flex', 'Team']
    session = Session(engine)
    selectFantasyTeams = session.query(FantasyTeam.username, FantasyTeam.top, FantasyTeam.jungle, FantasyTeam.mid,
                                       FantasyTeam.bot, FantasyTeam.support, FantasyTeam.flex, FantasyTeam.team).filter(FantasyTeam.serverid == serverid, FantasyTeam.blockname == blockName)

    playerFantasyScores = pd.read_sql(selectFantasyPlayerScore, engine)
    teamFantasyScores = pd.read_sql(selectFantasyTeamScore, engine)
    columns = ['role', 'summoner_name', 'fantasy_score']
    playerFantasyScores = playerFantasyScores[columns]
    fantasyScores = pd.concat(
        [playerFantasyScores, teamFantasyScores], ignore_index=True)
    scoreTables = {}
    for row in selectFantasyTeams:
        df = pd.DataFrame({"summoner_name": list(row[1:])})
        scoreTables[row[0]] = pd.merge(
            df, fantasyScores, how='left', on="summoner_name")
        for i in range(7):
            scoreTables[row[0]].loc[i, 'role'] = roles[i]
        scoreTables[row[0]] = scoreTables[row[0]][columns]
        scoreTables[row[0]].fillna(0, inplace=True)

        
        # scoreTables[row[0]] = pd.concat(
        #     [scoreTables[row[0]], sumFrame], ignore_index=True)
        # print(list(scoreTables[row[0]].columns.values)[::-1])
    return scoreTables


def get_block_name(engine, Base, tournamentid):
    Tournament_Schedule = Base.classes.tournament_schedule
    session = Session(engine)
    blockResult = session.query(Tournament_Schedule.blockname).filter(Tournament_Schedule.state != 'finished',
                                                                      Tournament_Schedule.tournamentid == tournamentid).order_by(Tournament_Schedule.start_ts).first()
    return blockResult[0]


def live_data():
    Base, engine = connect_database()
    print(f"Live data at {datetime.datetime.now()}")
    events = lolesports.getLive()
    for event in events:
        if event['type'] == "match" and int(event['league']['id']) == 98767991299243165:
            leagueid = event['league']['id']
            matchid = event['id']
            session = Session(engine)
            Tournaments = Base.classes.tournaments
            tournamentid = session.query(Tournaments.tournamentid).filter(
                Tournaments.leagueid == leagueid, Tournaments.iscurrent == True).first()[0]
            event_details = lolesports.getEventDetails(matchid)
            gameid = event_details['match']['games'][0]['id']
            start_ts = event["startTime"]
            start_ts_datetime = datetime.datetime.now() - datetime.timedelta(seconds=30)
            parse_gamedate(engine, Base, leagueid, tournamentid, gameid, start_ts_datetime, live_data=True)


if __name__ == "__main__":
    Base, engine = connect_database()
    # live_data()
    database_insert_gamedata(engine, Base)
    

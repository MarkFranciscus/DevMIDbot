import asyncio
import datetime
import itertools
import json
import os
import random
import time
from configparser import ConfigParser
from difflib import SequenceMatcher
from time import sleep
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import dateutil.parser
import numpy as np
import pandas as pd
import sqlalchemy
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pandas import json_normalize
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import and_, text
from tabulate import tabulate

import lolesports

conn = None
Base = None

logging.basicConfig(level=logging.INFO, filename='midbot.log', filemode='w', format='%(name)s - %(process)d - %(levelname)s - %(message)s')

def config(filename='config.ini', section='database'):
    """Reads config file, returns the given section

    Args:
        filename (str, optional): name of config file. Defaults to 'config.ini'.
        section (str, optional): Section of config file. Defaults to 'database'.

    Raises:
        Exception: Section not found in config file

    Returns:
        (dictionary): values found in config file 
    """
    # create a parser
    logging.info("Reading config file")
    parser = ConfigParser()

    # read config file
    filepath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..')) + '/'
    parser.read(filepath + filename)
    result = {}

    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            result[param[0]] = param[1]
    else:
        logging.error(f"No section {section} in {filename}")
        raise Exception(
            f"Section {section} not found in the {filename} file")
    logging.info(f"Loaded {section} from {filename}")
    return result


def connect_database():
    """Connect to the PostgreSQL database server

    Returns:
        (Engine): The database engine instance used to connect to DBAPI
        (Base): Holds the database relations
    """
    global conn
    global Base

    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    logging.info(f"Connecting to the PostgreSQL database")
    
    # Create URL to connect to database, connect, and set default scheme to public
    url = URL(**params)
    engine = create_engine(url, client_encoding='utf8', use_batch_mode=True)
    conn = engine.connect()
    conn.execute("SET search_path TO public")

    # Map database relations
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    logging.info("Connected")
    return Base, engine


def similar(string_1, string_2):
    """ Compares how similar 2 strings are

    Args:
        string_1 (str): The first string to compare
        string_2 (str): The second string to compare

    Returns:
        (float): A measure of the strings similarities
    """
    return SequenceMatcher(None, string_1, string_2).ratio()


def fantasy_player_scoring(player_stats):
    """ Calculates the fantasy score for a given player's stats

    Args:
        player_stats (dictionary): Players stats for a given frame

    Returns:
        float: final calculation of fantasy score
    """
    score = 0
    multipliers = {"kills": 2.0, "deaths": -0.5, "assists": 1.5, "creepScore": 0.01,  "triple": 2, "quadra": 5, "penta": 10}
    is_over_10 = False
    for stat in multipliers.keys():
        score += player_stats[stat] * multipliers[stat]
        if stat in ["kills", "assists"] and player_stats[stat] >= 10 and not is_over_10:
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
    """Initializes database with League of Legends eSports API data

    Args:
        Engine: The database engine instance used to connect to DBAPI
    """
    # league
    leagues = database_insert_leagues(engine)

    # tournaments
    tournaments = database_insert_tournaments(leagues, engine)

    # teams
    current_tournaments = tournaments[tournaments['iscurrent'] == True]
    database_insert_teams(current_tournaments, engine)

    # tournamentschedule
    database_insert_schedule(engine)

    # players
    database_insert_players(current_tournaments, engine)


def database_insert_players(current_tournaments, engine):
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
        "players", engine, if_exists='append', index=False, method='multi')
    return players_dataframe


def database_insert_teams(current_tournaments, engine):
    teams = pd.DataFrame(columns=['slug', 'name', 'code', 'image', 'alternativeImage',
                                  'backgroundImage', 'homeLeague.name', 'homeLeague.region'])
    for tournament in current_tournaments['tournamentid']:
        leagueID = current_tournaments[current_tournaments['tournamentid']
                                       == tournament].iloc[0]['leagueid']
        for slug in lolesports.getSlugs(tournament):
            if len(teams.loc[teams['slug'] == slug].index) != 0:
                continue
            teams = pd.concat(
                [teams, lolesports.get_teams(slug)], ignore_index=True)
            teams['tournamentid'] = tournament
            teams['homeLeague'] = leagueID
    teams.rename(
        columns={'id': 'teamid', 'homeLeague': 'leagueid'}, inplace=True)
    teams = teams[teams['slug'] != 'tbd']
    teams.to_sql("teams", engine, if_exists='append',
                 index=False, method='multi')
    return teams


def database_insert_tournaments(leagues, engine=None):
    all_tournaments = pd.DataFrame()
    for leagueid in leagues['leagueid']:
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
    # all_tournaments.to_sql("tournaments", engine, if_exists='append', index=False, method='multi')
    return all_tournaments


def database_insert_leagues(engine):
    leagues = lolesports.getLeagues()
    leagues.rename(columns={'id': 'leagueid'}, inplace=True)
    # leagues.to_sql("leagues", engine, index=False, if_exists='append', method='multi')
    return leagues


def database_insert_schedule(engine):
    leagues = lolesports.getLeagues()
    schedule = pd.DataFrame()
    for leagueID in leagues['id']:
        page_token = ""
        while page_token is not None:
            events, pages = lolesports.getSchedule(
                leagueId=leagueID, include_pagetoken=True, pageToken=page_token)
            page_token = pages['older']
            tournaments = lolesports.getTournamentsForLeague(leagueID)
            dt = datetime.datetime.utcnow()
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            p = (tournaments['startdate'] <= dt) & (
                dt <= tournaments['enddate'])
            tournaments['iscurrent'] = np.where(p, True, False)

            for event in events:
                startTime = dateutil.parser.isoparse(event['startTime'])
                p = (tournaments['startdate'] <= startTime) & (
                    startTime < tournaments['enddate'])
                if event['type'] != "match":
                    continue
                d = {}
                gameid = lolesports.getEventDetails(event['match']['id'])[
                    'match']['games'][0]["id"]
                d['gameID'] = [int(gameid)]
                # logging.info(type(gameid))
                startTime = dateutil.parser.isoparse(event['startTime'])
                d['start_ts'] = [startTime]
                d['team1code'] = [str(event['match']['teams'][0]['code'])]
                d['team2code'] = [str(event['match']['teams'][1]['code'])]
                d['state'] = [str(event['state'])]
                d['blockName'] = [str(event['blockName'])]
                d['matchid'] = [int(event['match']['id'])]

                if event['state'] != 'unstarted':
                    if event['match']["teams"][0]["result"]["outcome"] == "win":
                        d['winner_code'] = [event['match']["teams"][0]["code"]]
                    elif event['match']["teams"][1]["result"]["outcome"] == "win":
                        d['winner_code'] = [event['match']["teams"][1]["code"]]
                else:
                    d['winner_code'] = None

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
    logging.info(schedule)
    # logging.info(schedule)

    # schedule.to_csv("schedule.csv", index=False)
    schedule.to_sql("tournament_schedule", engine,
                    if_exists='append', index=False, method='multi')
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


def round_time(dt=None, roundTo=10):
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
    teams = database_insert_teams(current_tournaments, engine)

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
                                  Tournament_Schedule.start_ts, Tournament_Schedule.state).join(
                                      Tournaments, Tournament_Schedule.tournamentid == Tournaments.tournamentid).filter(
                                          Tournament_Schedule.tournamentid == 104174992692075107, Tournament_Schedule.state != "finished", ~Tournament_Schedule.gameid.in_(already_inserted), Tournament_Schedule.start_ts <= today)

    threads= []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for row in gameid_result:
            threads.append(executor.submit(parse_gamedata, engine, Base, row.leagueid,
                        row.tournamentid, row.gameid, row.start_ts))
    
    for task in as_completed(threads):
        logging.info(task.result())


def parse_gamedata(engine, Base, leagueID, tournamentID, gameID, start_ts, live_data=False):
    start_ts += datetime.timedelta(hours=4, minutes=20)
    date_time_obj = round_time(start_ts)
    kill_tracker = {}
    timestamps = []
    game_start_flag = True
    blue_first_blood = False
    red_first_blood = False
    state = "unstarted"
    session = Session(engine)
    team_columns = ['gameid', 'teamid', 'frame_ts', 'dragons', 'barons',
                    'towers', 'first_blood', 'under_30', 'win', 'fantasy_score']

    logging.info(f"Starting game {gameID}")
    while state != "finished":

        start_time = time.time()
        player_data = pd.DataFrame()
        team_data = pd.DataFrame()

        timestamp = date_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        date_time_obj += datetime.timedelta(seconds=10)

        # Catch if api throws error
        try:
            blue_team_ID, blue_metadata, red_team_ID, red_metadata, frames, matchID = lolesports.getWindow(
                gameID, starting_time=timestamp)
        except Exception as error:
            # logging.info(f"{error} - {timestamp} - {gameID}")
            live_data_check(start_time, live_data)
            continue
        try:
            participants_details = lolesports.getDetails(gameID, timestamp)
        except Exception as error:
            logging.info(error)
            continue

        # If there's only two frames then they will be redundant frames ¯\_(ツ)_/¯
        if (len(frames) < 2):
            live_data_check(start_time, live_data)
            continue

        # Team's codes
        blue_code = blue_metadata["summonerName"].iloc[0].split(' ', 1)[0]
        red_code = red_metadata["summonerName"].iloc[0].split(' ', 1)[0]

        game_metadata = pd.concat(
            [blue_metadata, red_metadata], ignore_index=True)

        # Start processing frame data
        for frame in frames:
            state = frame['gameState']

            if '.' not in frame['rfc460Timestamp']:
                frameTS = datetime.datetime.strptime(
                    frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            else:
                frameTS = datetime.datetime.strptime(
                    frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

            # Checks if game is paused
            if state == 'paused' or frameTS in timestamps:
                live_data_check(start_time, live_data)
                continue
            timestamps.append(frameTS)
            
            participants = pd.DataFrame()
            teams = pd.DataFrame()

            blue_team = frame['blueTeam']
            red_team = frame['redTeam']

            blue_players = blue_team.pop('participants')
            red_players = red_team.pop('participants')

            # Initializes some variables at the start of the game
            #   Timestamp of game start
            #   kill tracker for multikills
            if game_start_flag:
                game_start_flag = False
                startTS = frameTS

                blue_prev_kills = 0
                red_prev_kills = 0

                for player in blue_players:
                    kill_tracker[player['participantId']] = {
                        'killCount': 0, 'currentHealth': player['currentHealth'], 'killTS': startTS, 'kills': 0, 'double': 0, 'triple': 0, 'quadra': 0, 'penta': 0, 'prevKills': 0}

                for player in red_players:
                    kill_tracker[player['participantId']] = {
                        'killCount': 0, 'currentHealth': player['currentHealth'], 'killTS': startTS, 'kills': 0, 'double': 0, 'triple': 0, 'quadra': 0, 'penta': 0, 'prevKills': 0}

            blue_players, kill_tracker = player_update(
                blue_players, red_players, kill_tracker, blue_team['totalKills'], blue_prev_kills, frameTS, gameID)
            red_players, kill_tracker = player_update(
                red_players, blue_players, kill_tracker, red_team['totalKills'], red_prev_kills, frameTS, gameID)

            blue_team = team_update(
                blue_team, red_team, gameID, blue_team_ID, frameTS, blue_first_blood)
            red_team = team_update(
                red_team, blue_team, gameID, red_team_ID, frameTS, red_first_blood)

            if blue_team['first_blood']:
                blue_first_blood = True
            
            if red_team['first_blood']:
                red_first_blood = True

            # Checks which team won
            if state == "finished":

                winner_code = get_winner(leagueID, matchID)

                session = Session(engine)
                Tournament_Schedule = Base.classes.tournament_schedule
                game = session.query(Tournament_Schedule).filter(
                    Tournament_Schedule.gameid == gameID).first()
                game.state = state

                blue_team['win'] = blue_code == winner_code
                red_team['win'] = red_code == winner_code

                endTS = datetime.datetime.strptime(
                    frame['rfc460Timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if blue_team['win']:
                    blue_team['under_30'] = endTS - \
                        startTS < datetime.timedelta(minutes=30)
                else:
                    red_team['under_30'] = endTS - \
                        startTS < datetime.timedelta(minutes=30)
                game.winner_code = winner_code
                logging.info(
                    f"game id: {gameID} - block:{game.blockname} - winner: {game.winner_code}")
                session.commit()

            blue_players = pd.DataFrame().from_dict(json_normalize(blue_players))
            red_players = pd.DataFrame().from_dict(json_normalize(red_players))

            participants = pd.concat(
                [participants, blue_players, red_players], ignore_index=True)

            temp_participants = pd.merge(
                participants, game_metadata, on="participantId")
            player_data = pd.concat(
                [player_data, temp_participants], ignore_index=True)

            blue_team['fantasy_score'] = fantasy_team_scoring(blue_team)
            red_team['fantasy_score'] = fantasy_team_scoring(red_team)

            teams = pd.concat([teams, pd.DataFrame().from_dict(
                json_normalize(blue_team)), pd.DataFrame().from_dict(
                json_normalize(red_team))], ignore_index=True)
            teams = teams[team_columns]

            team_data = pd.concat([team_data, teams], ignore_index=True)

            blue_prev_kills = blue_team["totalKills"]
            red_prev_kills = red_team["totalKills"]

        if state == 'paused':
            live_data_check(start_time, live_data)
            continue

        if player_data.empty:
            live_data_check(start_time, live_data)
            continue

        player_data = player_data_processing(player_data, participants_details)

        team_data.drop_duplicates(
            subset=["gameid", "teamid", "frame_ts"], inplace=True)
        
        # player_data.to_sql("player_gamedata", engine,
        #                    if_exists='append', index=False, method='multi')
        # team_data.to_sql("team_gamedata", engine,
        #                  if_exists='append', index=False, method='multi')

        live_data_check(start_time, live_data)


def get_fantasy_league_table(engine, Base, serverid, tournamentid=103462439438682788):
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
        # logging.info(list(scoreTables[row[0]].columns.values)[::-1])
    return scoreTables


def get_block_name(engine, Base, tournamentid):
    Tournament_Schedule = Base.classes.tournament_schedule
    session = Session(engine)
    blockResult = session.query(Tournament_Schedule.blockname).filter(Tournament_Schedule.start_ts >= datetime.datetime.now() - datetime.timedelta(days=3),
                                                                      Tournament_Schedule.tournamentid == tournamentid).order_by(Tournament_Schedule.start_ts).first()
    return blockResult[0]

# Timeout check not working


def multikill(participantID, player, enemy_players, team_kills, prev_team_kills, currentTS):
    all_enemies_dead = True
    doubleTripleQuadraKill = currentTS - player["killTS"] <= datetime.timedelta(
                                seconds=10) and player["killCount"] < 4
    pentaKill = currentTS - player["killTS"] <= datetime.timedelta(
                seconds=30) and player["killCount"] >= 4 and all_enemies_dead
    
    # If kill occured in the last frame
    if player["kills"] > player["prevKills"] or player["killCount"] > 0:

        # allEnemiesDead = True
        # Check if a player is still dead
        for enemy_player in enemy_players:
            if enemy_player["currentHealth"] > 0:
                all_enemies_dead = False

        # if player["kills"] > player["prevKills"]:
        if doubleTripleQuadraKill:
            player["killCount"] += 1
            player["killTS"] = currentTS 
        elif pentaKill:
            player["killCount"] = 0 
            player["pentaKill"] += 1
            player["killTS"] = currentTS

        doubleTripleQuadraKillTimeout = currentTS - \
            player["killTS"] > datetime.timedelta(seconds=10) and player["killCount"] < 4
        pentaKillTimeout = currentTS - player["killTS"] > datetime.timedelta(
            seconds=30) and player["killCount"] == 4 or not all_enemies_dead
        
        if doubleTripleQuadraKillTimeout:
            if player["killCount"] == 2:
                logging.info("double")
                player["double"] += 1
            elif player["killCount"] == 3:
                logging.info("triple")
                player["triple"] += 1
            player["killCount"] = 0

        if player["killCount"] == 4:            
            if currentTS - player["killTS"] > datetime.timedelta(seconds=30) or not all_enemies_dead:
                logging.info("quadra")
                player["killCount"] = 0
                player["quadra"] += 1
            player["killCount"] = 0
    return player


def check_role_constraint(players, role, serverid, summoner_name, Base):
    """[summary]

    Args:
        players ([type]): [description]
        role ([type]): [description]
        serverid ([type]): [description]
        summoner_name ([type]): [description]
        Base ([type]): [description]

    TODO
    """
    constraint = 2
    role_count = {"top": 0, "jungle": 0, "mid": 0,
                  "bot": 0, "support": 0, "team": 0}
    Players = Base.classes.players
    FantasyTeam = Base.classes.fantasyteam


def team_update(team, otherTeam, gameID, teamID, frameTS, teamFirstBlood):
    team['dragons'] = len(team['dragons'])
    team['gameid'] = gameID
    team['teamid'] = teamID
    team['frame_ts'] = frameTS
    team['first_blood'] = team['totalKills'] == 1 and otherTeam['totalKills'] == 0 or teamFirstBlood
    team['win'] = False
    team['under_30'] = False
    return team


def player_update(players, enemyPlayers, killTracker, teamKills, prevTeamKills, frameTS, gameID):
    for player in players:
        participantID = player['participantId']
        
        logging.info(participantID)
        
        killTracker[participantID]['currentHealth'] = player['currentHealth']
        killTracker[participantID]['kills'] = player['kills']

        killTracker[participantID] = multikill(participantID,
            killTracker[participantID], enemyPlayers, teamKills, prevTeamKills, frameTS)
        player.update(killTracker[participantID])

        player['fantasy_score'] = fantasy_player_scoring(player)
        player['gameid'] = gameID
        player['timestamp'] = frameTS
        killTracker[participantID]['prevKills'] = player['kills']
    return players, killTracker


def insert_predictions(engine, Base, teams, blockName, tournamentID, serverID, discordName, gameIDs):
    Weekly_Predictions = Base.classes.weekly_predictions
    predictionRows = [{'serverid': serverID, 'discordname': discordName, 'blockname': blockName,
                       'gameid': gameID, 'winner': team} for team, gameID in zip(teams, gameIDs)]
    # logging.info(predictionRows)

    engine.execute(Weekly_Predictions.__table__.insert(), predictionRows)


def update_predictions(engine):
    update_weekly_predictions = text(
        f"""update weekly_predictions wp set correct=(winner_code = winner) from tournament_schedule ts where wp.gameid=ts.gameid""")
    engine.execute(update_weekly_predictions)


def update_winners(Base, engine):
    Tournaments = Base.classes.tournaments
    Tournament_Schedule = Base.classes.tournament_schedule

    session = Session(engine)
    current_tournaments = session.query(Tournaments.leagueid, Tournaments.tournamentid, Tournaments.startdate, Tournaments.enddate).filter(
        Tournaments.iscurrent).filter(Tournaments.leagueid == 98767991299243165)

    for tournament in current_tournaments:
        games = session.query(Tournament_Schedule).filter(Tournament_Schedule.tournamentid==tournament.tournamentid)
        for game in games:
           game.winner_code = get_winner(tournament.leagueid, game.matchid)


def get_winner(leagueID, matchID):
    page_token = ""
    while page_token is not None:
        events, pages = lolesports.getSchedule(
            leagueId=leagueID, include_pagetoken=True, pageToken=page_token)
        page_token = pages["older"]
        for event in events:

            if event['type'] != "match" or event["match"]["id"] != matchID:
                continue

            if event['match']["teams"][0]["result"]["outcome"] == "win":
                return event['match']["teams"][0]["code"]
            elif event['match']["teams"][1]["result"]["outcome"] == "win":
                return event['match']["teams"][1]["code"]


def live_data_check(start_time, live_data=False):
    if live_data:
        loopTime = time.time() - start_time
        logging.info("Game is paused")
        sleep(10 - loopTime)


def player_data_processing(player_data, participants_details):
    player_columns = ['gameid', 'participantId', 'timestamp', 'kills', 'deaths',
                      'assists', 'creepScore', 'fantasy_score', 'summoner_name', 'role', 'level',
                      'totalGoldEarned', 'killParticipation', 'championDamageShare',
                      'wardsPlaced', 'wardsDestroyed', 'attackDamage', 'abilityPower',
                      'criticalChance', 'attackSpeed', 'lifeSteal', 'armor', 'magicResistance',
                      'tenacity']
    map_columns = {'gameid': 'gameid', 'participantId': 'participantid',
                   'timestamp': 'timestamp', 'kills': 'kills', 'deaths': 'deaths',
                   'assists': 'assists', 'creepScore': 'creep_score', 'fantasy_score': 'fantasy_score',
                   'summoner_name': 'summoner_name', 'role': 'role', 'totalGoldEarned': 'total_gold_earned',
                   'killParticipation': 'kill_participation', 'championDamageShare': 'champion_damage_share',
                   'wardsPlaced': 'wards_placed', 'wardsDestroyed': 'wards_destroyed',
                   'attackDamage': 'attack_damage', 'abilityPower': 'ability_power',
                   'criticalChance': 'critical_chance', 'attackSpeed': 'attack_speed', 'lifeSteal': 'life_steal',
                   'armor': 'armor', 'magicResistance': 'magic_resistance', 'tenacity': 'tenacity'}

    player_data = player_data.merge(participants_details, on=[
        'timestamp', 'participantId', 'kills', 'deaths', 'assists', 'creepScore', 'level'])
    player_data[['code', 'summoner_name']] = player_data['summonerName'].str.split(
        ' ', 1, expand=True)
    player_data = player_data[player_columns]
    player_data.drop_duplicates(
        subset=["summoner_name", "gameid", "timestamp"], inplace=True)
    player_data.rename(columns=map_columns, inplace=True)
    return player_data

if __name__ == "__main__":
    Base, engine = connect_database()
    database_insert_gamedata(engine, Base)

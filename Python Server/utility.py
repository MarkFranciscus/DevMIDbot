import asyncio
import itertools
import json
import logging
import os
import pickle
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from time import sleep
from timeit import default_timer

from aiohttp import ClientSession
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

logging.basicConfig(level=logging.DEBUG, filename='midbot.log', filemode='w',
                    format='%(name)s - %(process)d - %(levelname)s - %(message)s')


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
    conn.execute("SET search_path TO midbot")

    metadata = MetaData()
    metadata.reflect(engine, schema='midbot')
    # Map database relations
    Base = automap_base(metadata=metadata)
    # Base.prepare(engine, reflect=True)
    Base.prepare()
    logging.debug(f"{list(Base.classes)}")
    logging.info("Connected")
    return engine, Base


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
    multipliers = {"kills": 2.0, "deaths": -0.5, "assists": 1.5,
                   "creepScore": 0.01,  "triple": 2, "quadra": 5, "penta": 10}
    is_over_10 = False
    for stat in multipliers.keys():
        score += player_stats[stat] * multipliers[stat]
        if stat in ["kills", "assists"] and player_stats[stat] >= 10 and not is_over_10:
            score += 2
    return score


def fantasy_team_scoring(team_stats):
    """ Calculates fantasy score for a teams stats

    Args:
        team_stats (dict): A dictionary of team stats

    Returns:
        int: The calculation of team score
    """
    multipliers = {"dragons": 1, "barons": 2, "towers": 1,
                   "first_blood": 2, "win": 2, "under_30": 2}
    score = 0
    for stat in multipliers.keys():
        if stat in ["first_blood", "under_30", "win"] and team_stats[stat]:
            score += multipliers[stat]
        else:
            score += team_stats[stat] * multipliers[stat]
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
    current_tournaments = tournaments[tournaments['iscurrent']]
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
        "players", engine, if_exists='append', index=False, method='multi', schema='midbot')
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
                 index=False, method='multi', schema='midbot')
    return teams


def database_insert_tournaments(leagues, engine=None):
    all_tournaments = pd.DataFrame()
    for leagueid in leagues['leagueid']:
        tournaments = lolesports.getTournamentsForLeague(leagueid)
        tournaments['leagueid'] = leagueid
        tournaments['iscurrent'] = False
        tournaments.rename(columns={'id': 'tournamentid'}, inplace=True)
        dt = datetime.utcnow()
        dt = dt.replace(tzinfo=timezone.utc)
        p = (tournaments['startdate'] <= dt) & (dt <= tournaments['enddate'])
        tournaments['iscurrent'] = np.where(p, True, False)
        all_tournaments = pd.concat(
            [all_tournaments, tournaments], ignore_index=True)
    # all_tournaments.to_sql("tournaments", engine, if_exists='append', index=False, method='multi', schema='midbot')
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
            dt = datetime.utcnow()
            dt = dt.replace(tzinfo=timezone.utc)
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
                    if_exists='append', index=False, method='multi', schema='midbot')
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


def round_time(dt=None, date_delta=timedelta(seconds=10), to='down'):
    """Round a datetime object to a multiple of a timedelta

    Args:
        dt (datetime): datetime.datetime object, default now.
        date_delta (timedelta) : timedelta object, we round to a multiple of this, default 1 minute.
        to (str) : Round up, down or to nearest
    """
    round_to = date_delta.total_seconds()

    if dt is None:
        dt = datetime.now()
    seconds = (dt - dt.min).seconds

    if to == 'up':
        # // is a floor division, not a comment on following line (like in javascript):
        rounding = (seconds + round_to) // round_to * round_to
    elif to == 'down':
        rounding = seconds // round_to * round_to
    else:
        rounding = (seconds + round_to / 2) // round_to * round_to

    return dt + timedelta(0, rounding - seconds, -dt.microsecond)


def database_update_teams(engine):
    leagues = database_insert_leagues(engine)
    tournaments = database_insert_tournaments(leagues, engine)
    current_tournaments = tournaments[tournaments['iscurrent']]
    teams = database_insert_teams(current_tournaments, engine)

    oldTeams = pd.read_sql_table("teams", engine)
    oldTeams = oldTeams.drop(["homeLeague"], axis=1)
    newTeams = teams[~teams["slug"].isin(oldTeams["slug"])]

    newTeams.to_sql("teams", engine, if_exists='append',  index=False)


async def database_insert_gamedata(engine, Base, tournamentID):
    session = Session(engine)
    Tournament_Schedule = Base.classes.tournament_schedule
    Tournaments = Base.classes.tournaments
    Player_Gamedata = Base.classes.player_gamedata

    # SQL to get split id for given region
    already_inserted = session.query(Player_Gamedata.gameid).distinct().all()
    already_inserted = list(set([x[0] for x in already_inserted]))
    today = datetime.now()
    gameid_result = session.query(Tournament_Schedule.gameid, Tournaments.leagueid).join(
        Tournaments, Tournament_Schedule.tournamentid == Tournaments.tournamentid).filter(
        Tournament_Schedule.tournamentid == tournamentID, Tournament_Schedule.state != "finished", ~Tournament_Schedule.gameid.in_(already_inserted),  ~Tournament_Schedule.gameid.in_([104174992718816262]), Tournament_Schedule.start_ts <= today)

    for row in gameid_result:
        await parse_gamedata(row.gameid, row.leagueid, engine)

    # with ThreadPoolExecutor(max_workers=10) as executor:
    #         loop = asyncio.get_event_loop()
    #         START_TIME = default_timer()
    #         tasks = [
    #             loop.run_in_executor(
    #                 executor,
    #                 await parse_gamedata,
    #                 *(row.gameid, row.leagueid, engine)
    #             )
    #             for row in gameid_result
    #         ]
    #         for response in await asyncio.gather(*tasks):
    #             pass


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
    blockResult = session.query(Tournament_Schedule.blockname).filter(Tournament_Schedule.start_ts >= datetime.now() - timedelta(days=3),
                                                                      Tournament_Schedule.tournamentid == tournamentid).order_by(Tournament_Schedule.start_ts).first()
    return blockResult[0]


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


def insert_predictions(engine, Base, teams, blockName, tournamentID, serverID, discordName, gameIDs):
    Weekly_Predictions = Base.classes.weekly_predictions
    predictionRows = [{'serverid': serverID, 'discordname': discordName, 'blockname': blockName,
                       'gameid': gameID, 'winner': team} for team, gameID in zip(teams, gameIDs)]
    # logging.info(predictionRows)

    engine.execute(Weekly_Predictions.__table__.insert(), predictionRows)


def update_predictions(engine):
    update_weekly_predictions = text(
        f"""update midbot.weekly_predictions wp set correct=(winner_code = winner) from midbot.tournament_schedule ts where wp.gameid=ts.gameid""")
    engine.execute(update_weekly_predictions)


def update_winners(engine, Base):
    Tournaments = Base.classes.tournaments
    Tournament_Schedule = Base.classes.tournament_schedule

    session = Session(engine)
    current_tournaments = session.query(Tournaments.leagueid, Tournaments.tournamentid, Tournaments.startdate, Tournaments.enddate).filter(
        Tournaments.iscurrent).filter(Tournaments.leagueid == 98767991299243165)

    for tournament in current_tournaments:
        games = session.query(Tournament_Schedule).filter(
            Tournament_Schedule.tournamentid == tournament.tournamentid)
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


async def parse_gamedata(gameID, leagueID, engine):
    """ Parses gamedata, makes asyncronous API calls, vectorized processing

    Args:
        gameID (int): unique ID for League of Legends eSports game
        leagueID (int): unique ID for League of Legends eSports league
    """
    start_time = time.time()
    print(f"parsing {gameID}")
    rename_player_columns = {'gameid': 'gameid', 'participantId': 'participantid',
                             'timestamp': 'timestamp', 'kills': 'kills', 'deaths': 'deaths',
                             'assists': 'assists', 'creepScore': 'creep_score', 'fantasy_score': 'fantasy_score',
                             'summoner_name': 'summoner_name', 'role': 'role', 'totalGoldEarned': 'total_gold_earned',
                             'killParticipation': 'kill_participation', 'championDamageShare': 'champion_damage_share',
                             'wardsPlaced': 'wards_placed', 'wardsDestroyed': 'wards_destroyed', 'level': 'level',
                             'attackDamage': 'attack_damage', 'abilityPower': 'ability_power', 'items': 'items',
                             'criticalChance': 'critical_chance', 'attackSpeed': 'attack_speed', 'lifeSteal': 'life_steal',
                             'armor': 'armor', 'magicResistance': 'magic_resistance', 'tenacity': 'tenacity', "kill_1.0": "single",
                             "kill_2.0": "double", "kill_3.0": "triple", "kill_4.0": "quadra", "kill_5.0": "penta",
                             "perkMetadata.perks": "runes", "abilities": "abilities", "rfc460Timestamp": "rfc460timestamp"}
    team_rename_columns = {'rfc460Timestamp': 'rfc460timestamp', 'gameState': 'game_state', 'totalGold': 'total_gold', 
                           'inhibitors': 'inhibitors', 'towers': 'towers', 'barons': 'barons', 'totalKills': 'total_kills',
                           'dragons': 'dragons', 'teamID': 'teamid', 'side': 'side', 'code': 'code', 'timestamp': 'timestamp',
                           'gameid': 'gameid', 'num_dragons': 'num_dragons', 'win': 'win', 'under_30': 'under_30', 
                           'first_blood': 'first_blood', 'fantasy_score': 'fantasy_score'}

    logging.info(f"Starting game {gameID}")

    participants, teams, participants_details = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Calculates the number of 10s periods for the duration of the game
    async with ClientSession() as session:
        _, _, x, _ = await lolesports.getWindow(session, gameID)
    timestamp = x["timestamp"].min().to_pydatetime()
    timestamp = round_time(timestamp)

    temp_max_ts = timestamp + timedelta(days=1)
    temp_max_ts = temp_max_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    async with ClientSession() as session:
        _, _, x, _ = await lolesports.getWindow(session, gameID, temp_max_ts)
    
    if not teams["gameState"].str.contains('finished').any():
        return

    max_ts = x["timestamp"].max().to_pydatetime()
    max_ts = round_time(max_ts)

    num_periods = round((max_ts - timestamp).total_seconds() / 10)

    logging.info(f"Making getWindow calls")
    # Completes getWindow API calls asynchronously
    # with ThreadPoolExecutor(max_workers=10) as executor:
    async with ClientSession() as session:
        tasks = [
            asyncio.ensure_future(lolesports.getWindow(
                session, gameID, (timestamp + timedelta(seconds=i*10)).strftime("%Y-%m-%dT%H:%M:%SZ")))
            for i in range(num_periods)
        ]
        for response in await asyncio.gather(*tasks):
            participants = pd.concat(
                [participants, response[1]], ignore_index=True)
            teams = pd.concat([teams, response[2]], ignore_index=True)
            matchID = response[3]

    logging.info(f"Making getDetails calls")
    # Compeletes getDetails API calls asynchronously
    async with ClientSession() as session:
        tasks = [
            asyncio.ensure_future(lolesports.getDetails(
                session, gameID, (timestamp + timedelta(seconds=i*10)).strftime("%Y-%m-%dT%H:%M:%SZ")))
            for i in range(num_periods)
        ]
        for response in await asyncio.gather(*tasks):
            participants_details = pd.concat(
                [participants_details, response], ignore_index=True)

    # Sort dataframes by timestamp
    participants.sort_values(
        ['timestamp', 'participantId'], ignore_index=True, inplace=True)
    teams.sort_values(
        ['timestamp'], ignore_index=True, inplace=True)
    participants_details.sort_values(
        ['timestamp', 'participantId'], ignore_index=True, inplace=True)

    participants['multikill'] = 1

    # The next bunch of code is a bunch of messy vectorization, to determine when double, triples, quadras, pentas happen

    # Determine which frame a kill happens at
    participants['kill_event'] = participants.groupby(
        'participantId')['kills'].diff().fillna(0).astype(bool)

    participants.loc[(participants['kill_event']), 'kill_count'] = 1

    # Calculates the time inbetween kills
    participants.loc[participants['kill_event'], 'kill_timeout'] = participants[participants['kill_event']].groupby(
        'participantId')['timestamp'].diff().fillna(pd.Timedelta(0, unit='S'))
    print(participants[]['kill_event'])
    
    # First pass detection for when kills need reset
    # Since single, double, triple, quadra have the same requirements and penta's are different
    participants.loc[(participants['kill_event']) & (
        participants['kill_timeout'] > timedelta(seconds=30)), 'kill_reset'] = 1

    participants['kill_reset'].fillna(0, inplace=True)

    participants['cumsum'] = participants[participants['kill_event']].groupby(
        'participantId')['kill_reset'].cumsum()

    participants['multikill'] = participants[participants['kill_event']].groupby(
        ['participantId', 'cumsum'])['kill_count'].cumsum()

    # Checks to see if any player on the othe

    # Gets the max current health at each timestamp for each team
    participants['max_health'] = participants.groupby(
        ['timestamp', 'code'])['currentHealth'].transform(max)
    # print(participants.columns.values)
    df = participants[['timestamp', 'code', 'max_health']].copy()
    participants.drop('max_health', axis=1, inplace=True)

    # Swaps the codes
    code_1 = df['code'].unique()[0]
    code_2 = df['code'].unique()[1]
    df['code'] = df['code'].map({code_1: code_2, code_2: code_1})

    # Add to participant dataframe
    participants = pd.merge(participants, df, on=['timestamp', 'code'])
    participants.drop_duplicates(inplace=True)

    # Second pass resets
    # Single, double, triple, quadra resets
    # If the time inbetween kills has been more than 10s
    participants.loc[(participants['kill_event']) & (participants['multikill'] <= 4) & (
        participants['kill_timeout'] > timedelta(seconds=10)), 'kill_reset'] = 1

    # Penta reset
    # If time inbetween kills has been more than 30s or someone on the enemy team has respawned
    participants.loc[(participants['kill_event']) & (participants['multikill'] == 5) & (
        (participants['kill_timeout'] > timedelta(seconds=30)) | (participants['max_health'] > 0)), 'kill_reset'] = 1

    # I forget how this works again hahaha
    participants['cumsum'] = participants[participants['kill_event']].groupby(
        'participantId')['kill_reset'].cumsum()

    participants['multikill'] = participants[participants['kill_event']].groupby(
        ['participantId', 'cumsum'])['kill_count'].cumsum()

    participants['multikill'].fillna(0, inplace=True)

    # Onehot encode the multikills, 1 -> single, 2 -> double, 3 -> triple, 4 -> quadra, 5 -> penta
    participants = pd.get_dummies(participants, "kill", columns=['multikill'])

    # Merge participant_details
    participants = participants.merge(participants_details, on=[
        'timestamp', 'participantId', 'kills', 'deaths', 'assists', 'creepScore', 'level', 'rfc460Timestamp'])

    # Clean up participant dataframe, rename columns, sort, drop extra columns
    participants.rename(columns=rename_player_columns, inplace=True)
    participants_details.sort_values(
        ['timestamp', 'participantId'], inplace=True)
    player_drop_columns = set(participants.columns.values) - \
        set(rename_player_columns.values())
    participants.drop(player_drop_columns, axis=1, inplace=True)

    # cumulative sum for onehot encoded multikills
    multikill_columns = ['single', 'double', 'triple', 'quadra', 'penta']

    for column in multikill_columns:
        if column not in participants:
            participants[column] = 0
        participants[column].cumsum()

    # Calculate fantasy score
    player_weight_columns = ['kills', 'deaths', 'assists',
                             'creep_score', 'triple', 'quadra', 'penta']
    player_weights = pd.DataFrame(
        {"weights": [2.0, -0.5, 1.5, 0.01, 2, 5, 10]}, index=player_weight_columns)

    participants['fantasy_score'] = participants[player_weight_columns].dot(
        player_weights)

    # Teams
    # Basic info
    teams['num_dragons'] = teams['dragons'].str.len()
    teams['win'] = 0
    teams['under_30'] = 0

    # Some messy vectorization
    # Determine when first blood happens
    teams['first_blood'] = np.nan

    # Determine when kills happen
    teams['kill_event'] = teams.groupby(
        'code')['totalKills'].diff().fillna(0).astype(bool)

    # Determine when first blood happens
    teams.loc[(teams['kill_event']) & (teams[teams['kill_event']]['timestamp']
                                       == teams[teams['kill_event']]['timestamp'].min()), 'first_blood'] = 1

    # Set first blood for team in future timestamps
    teams.loc[(teams['code'] == teams[teams['first_blood'] == 1]['code'].iloc[0]) & (
        teams['timestamp'] > teams[teams['first_blood'] == 1]['timestamp'].min()), 'first_blood'] = 1
    teams['first_blood'].fillna(0, inplace=True)

    winner_code = get_winner(leagueID, matchID)

    # Determine if game won in under 30
    teams.loc[(teams['code'] == winner_code) & (
        teams['gameState'] == 'finished'), 'win'] = 1
    teams.loc[(teams['win'] == 1) & (teams.timestamp.max() -
                                     teams.timestamp.min() < timedelta(minutes=30)), 'under_30'] = 1

    # Calculate fantasy score
    team_weight_columns = ['num_dragons', 'barons',
                           'towers', 'first_blood', 'win', 'under_30']
    team_weights = pd.DataFrame(
        {"weights": [1.0, 2.0, 1.0, 2.0, 2.0, 2.0]}, index=team_weight_columns)
    teams['fantasy_score'] = teams[team_weight_columns].dot(team_weights)

    # Final dataframe clean up, rename columns, drop extra
    teams.rename(columns=team_rename_columns, inplace=True)
    teams.drop('kill_event', axis=1, inplace=True)
    teams = teams.astype({'win': 'bool', 'first_blood': 'bool', 'under_30': 'bool'})


    participants.drop_duplicates(
        ['gameid', 'summoner_name', 'timestamp'], inplace=True)
    teams.drop_duplicates(['timestamp', 'teamid', 'gameid'], inplace=True)

    participants.to_sql("player_gamedata", engine, "midbot", 'append', False)
    teams.to_sql("team_gamedata", engine, "midbot", 'append', False)

    print(f"Game: {gameID} - Clock {time.time()- start_time}")

if __name__ == "__main__":
    engine, Base = connect_database()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        parse_gamedata(104174992718816262, 98767991299243165, engine))
    #     database_insert_gamedata(engine, Base, 104174992692075107))
    loop.run_until_complete(future)
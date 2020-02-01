from configparser import ConfigParser
import os
from difflib import SequenceMatcher
from tabulate import tabulate

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

# print(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))
meta = MetaData()
conn = None
Base = None

def config(filename='config.ini', section='database'):

    # create a parser
    parser = ConfigParser()

    # read config file
    filepath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) + '/'
    parser.read(filepath + filename)
    db = {}

    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

def connect_database():
    """ Connect to the PostgreSQL database server """
    global conn
    global Base

    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')

    url = URL(**params)
    engine = create_engine(url, client_encoding='utf8')
    conn = engine.connect()
    conn.execute("SET search_path TO public")

    Base = automap_base()
    Base.prepare(engine, reflect=True)

    return Base, engine


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def fantasy_scoring(player_stats):
    score = 0
    multipliers = {"kills": 2, "deaths": -1, "assist": 1.5, "creepScore":0.01, "towers":1, "dragon": 1}
    for stat in player_stats.keys():
        score += player_stats[stat] * multipliers[stat]
    return stat

def format_standings(standings):
    scoreStandings = {}
    for key, value in standings.items():
        for string in value:
            if string == '':
                continue
            scoreStandings[string] = key
    return scoreStandings

def format_table(rows, standings, region):
    headers = ["Username", "1st", "2nd", "3rd", "4th", "5th", "6th",  "7th", "8th", "9th", "10th", "Score"]

    last_row = [region.upper()]
    for i in range(1, 11):
        if i in standings.keys():
            last_row.append("\n".join(standings[i]))
        else:
            last_row.append("")
    last_row += [0]
    pickems = rows + [last_row]
    return tabulate(pickems, headers, tablefmt="fancy_grid")

def schedule_data(leagueID):
    events = lolesports.getSchedule(leagueId=leagueID)
    schedule = pd.DataFrame()

    for event in events:
        d = {}
        d['start_ts'] = event['startTime']
        d['state'] = event['state']
        d['blockName'] = event['blockName']
        d['gameID'] = event['match']['id']
        # temp = 

def init_data(engine):
    # players
    players_dataframe = pd.DataFrame()
    # slugs = lolesports.getSlugs(tournamentId=103462439438682788)
    # for slug in slugs:
    #    players_dataframe = pd.concat([players_dataframe, lolesports.getPlayers(slug)])
    # players_dataframe.columns = map(str.lower, players_dataframe.columns)
    # players_dataframe.rename(columns={'id':'playerid'}, inplace=True)
    # players_dataframe.to_sql("players", engine, if_exists='append', index=False)
    # print(players_dataframe)
    # league
    league = lolesports.getLeagues()
    league.rename(columns={'id':'leagueid'}, inplace=True)
    # league.to_sql("leagues", engine, index=False, if_exists='append')
    # print(league)

    # tournaments
    all_tournaments = pd.DataFrame()
    for leagueid in league['leagueid']:
        tournaments = lolesports.getTournamentsForLeague(leagueid)
        tournaments['leagueid'] = leagueid
        tournaments['iscurrent'] = False
        tournaments.rename(columns={'id':'tournamentid'}, inplace=True)
        p = (tournaments['startdate'] <= datetime.datetime.now()) & (datetime.datetime.now() <= tournaments['enddate'])
        tournaments['iscurrent'] = np.where(p, True, False) 
        all_tournaments = pd.concat([all_tournaments, tournaments], ignore_index=True)

    # all_tournaments.to_sql("tournaments", engine, if_exists='append', index=False,)
    
    current_tournaments = all_tournaments[all_tournaments['iscurrent'] == True]
    # teams
    teams = pd.DataFrame()
    for tournament in current_tournaments['tournamentid']:
        print(tournament)
        for slug in lolesports.getSlugs(tournament):
            temp_players = lolesports.getPlayers(slug)
            temp_players['tournamentid'] = tournament
            players_dataframe = pd.concat([players_dataframe, temp_players], ignore_index=True)
            # teams = pd.concat([teams, lolesports.get_teams(slug)], ignore_index=True)
    
    players_dataframe.rename(columns={'id':'playerid'}, inplace=True)
    players_dataframe.columns = map(str.lower, players_dataframe.columns)
    # print(players_dataframe[players_dataframe['playerid'] == '98926509759999764'])
    players_dataframe.to_sql("players", engine, if_exists='append', index=False)
            
    # teams.rename(columns={'id':'teamid'}, inplace=True)
    # print(teams)
    # teams.to_sql("teams", engine, if_exists='append', index=False)



# if __name__ == "__main__":
#     base, engine = connect_database()
#     # engine = None   
#     init_data(engine)
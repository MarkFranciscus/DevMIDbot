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
import dateutil.parser

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
            players_dataframe = pd.concat([players_dataframe, temp_players], ignore_index=True)
    players_dataframe.rename(columns={'id':'playerid'}, inplace=True)
    players_dataframe.columns = map(str.lower, players_dataframe.columns)
    players_dataframe.to_sql("players", engine, if_exists='append', index=False)

def database_insert_teams(current_tournaments):
    teams = pd.DataFrame(columns=['teamid', 'slug', 'name', 'code', 'image', 'alternativeImage',
       'backgroundImage', 'homeLeague.name', 'homeLeague.region'])
    for tournament in current_tournaments['tournamentid']:
        for slug in lolesports.getSlugs(tournament):
            if len(teams.loc[teams['slug'] == slug, 'teamid'].index) == 0:
                continue
            teams = pd.concat([teams, lolesports.get_teams(slug)], ignore_index=True)
            teams['tournamentid'] = tournament
    teams.rename(columns={'id':'teamid'}, inplace=True)
    teams.to_sql("teams", engine, if_exists='append', index=False)
    return teams

def database_insert_tournaments(league, engine):
    all_tournaments = pd.DataFrame()
    for leagueid in league['leagueid']:
        tournaments = lolesports.getTournamentsForLeague(leagueid)
        tournaments['leagueid'] = leagueid
        tournaments['iscurrent'] = False
        tournaments.rename(columns={'id':'tournamentid'}, inplace=True)
        dt = datetime.datetime.utcnow()
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        p = (tournaments['startdate'] <= dt) & (dt <= tournaments['enddate'])
        tournaments['iscurrent'] = np.where(p, True, False) 
        all_tournaments = pd.concat([all_tournaments, tournaments], ignore_index=True)
    # all_tournaments.to_sql("tournaments", engine, if_exists='append', index=False)    
    return all_tournaments

def database_insert_leagues(engine):
    league = lolesports.getLeagues()
    league.rename(columns={'id':'leagueid'}, inplace=True)
    # league.to_sql("leagues", engine, index=False, if_exists='append')
    return league

def database_insert_players(engine):
    players_dataframe = pd.DataFrame()
    slugs = lolesports.getSlugs(tournamentId=103462439438682788)
    for slug in slugs:
       players_dataframe = pd.concat([players_dataframe, lolesports.getPlayers(slug)])
    players_dataframe.columns = map(str.lower, players_dataframe.columns)
    players_dataframe.rename(columns={'id':'playerid'}, inplace=True)
    players_dataframe.to_sql("players", engine, if_exists='append', index=False)
    return  players_dataframe

def database_insert_schedule(engine, tournaments):
    leagues = lolesports.getLeagues()
    schedule = pd.DataFrame()
    
    for leagueID in leagues['id']:
        events = lolesports.getSchedule(leagueId=leagueID)
        tournaments = lolesports.getTournamentsForLeague(leagueID)
        
        tournaments = tournaments[tournaments['iscurrent'] == True]
        
        for event in events:
            if event['type'] != "match":
                continue
    
            d = {}
            d['gameID'] = [event['match']['id']]
            startTime = dateutil.parser.isoparse(event['startTime'])
            d['start_ts'] = [startTime]
            d['team1code']  = [event['match']['teams'][0]['code']]
            d['team2code']  = [event['match']['teams'][1]['code']]
            d['state'] = [event['state']]
            d['blockName'] = [event['blockName']]
            p = (tournaments['startdate'] <= startTime) & (startTime < tournaments['enddate'])

            if len(tournaments.loc[p, 'id'].index) == 0:
                continue            
            
            d['tournamentid'] = [tournaments.loc[p, 'id'].iloc[0]]#, 'tournamentid'].iloc[0]
            if d['tournamentid'] in [102147203732523011, 103540419468532110]:
                continue
            
            temp = pd.DataFrame().from_dict(d)
            schedule = pd.concat([schedule, temp], ignore_index=True)
    
    schedule.columns = map(str.lower, schedule.columns)
    schedule.to_sql("tournament_schedule", engine, if_exists='append', index=False)
    return schedule

# if __name__ == "__main__":
#     base, engine = connect_database()
#     # engine = None   
#     init_data(engine)
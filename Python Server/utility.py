from configparser import ConfigParser
# import psycopg2
import os

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine.url import URL
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

# from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import sqlalchemy
from sqlalchemy.sql import and_, text

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
    # print(params)
    url = URL(**params)

    engine = create_engine(url)
    conn = engine.connect()
    conn.execute("SET search_path TO public")

    # execute a statement
    # print('PostgreSQL database version:')
    # result = conn.execute('SELECT version()')
    
    # display the PostgreSQL database server version
    # for row in result:
    #     print(row)

    Base = automap_base()
    Base.prepare(engine, reflect=True)
    return Base, engine

def get_table(name):
    global meta
    global conn

    # return Table(name, meta, autoload=True, autoload_with=)

# print(connect_database())
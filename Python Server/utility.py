from configparser import ConfigParser
import psycopg2
import os

# print(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))

def config(filename='config.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    filepath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) + '\\'
    parser.read(filepath+ filename)
 

    # get section, default to postgresql
    db = {}
    print(parser)
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db

def connect_database():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        # create a cursor
        cur = conn.cursor()
        
        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
        return cur
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    # finally:
    #     if conn is not None:
    #         conn.close()
    #         print('Database connection closed.')

print(connect_database())
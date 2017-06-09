import asyncio

import LeagueStats
import psycopg2
from discord.ext.commands import Bot
import botinfo
# import mysql.connector
# import MySQLdb
import pymysql.cursors

mid_bot = Bot(command_prefix="!")

try:
    # cnx = MySQLdb.connect(host='127.0.0.1', user=botinfo.user, password=botinfo.password, database=botinfo.dbname)


    # Connect to the database
    cnx = pymysql.connect(host='127.0.0.1',
                                 user=botinfo.user,
                                 password=botinfo.password,
                                 database=botinfo.dbname,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
except:
    print("didn't connect")

cur = cnx.cursor
# curB = cnx.cursor(buffered=True)

# try:
#     conn = psycopg2.connect(
#         "dbname=" + botinfo.dbname + " user=" + botinfo.user + " host=" + botinfo.host + " password=" + botinfo.password)
#     conn.autocommit = True
# except:
#     print("didn't connect")
#
# cur = conn.cursor()

@mid_bot.event
@asyncio.coroutine
def on_read():
    print("Client logged in")

#Command for the sake of testing, prints serverid ten times
@mid_bot.command(pass_context=True)
@asyncio.coroutine
def test(ctx, *args):
    strtest = "```"
    # for i in range(10):
    strtest += str(ctx.message.server.id)
    print(strtest)
    strtest += '```'
    yield from mid_bot.say(strtest)




#Displays win-loss of the past 10 games
@mid_bot.command(pass_context=True)
@asyncio.coroutine
def last10(ctx, *args):
    if len(args) == 1: # a username has been given, look up that name
        yield from mid_bot.say((LeagueStats.last10Games(args[0])))
    elif len(args) == 0: #no username has been given
        sql = "select summoner from discordinfo where discordName='" + str(
            ctx.message.author) + "' and serverID=" + str(ctx.message.server.id) + ";" # construct sql query
        print(sql) # log it
        try:
            cur.execute(sql) #execute sql query
        except:
            print("failed to find username")
        try:
            username = cur.fetchall() #use what the database returns to look up stats
            print(str(username[0][0]).rstrip())
            yield from mid_bot.say(LeagueStats.last10Games(str(username[0][0]).rstrip()))
        except:
            print("failed to fetch username")
    else: #error
        yield from mid_bot.say("Too many parameters")

#In progress
@mid_bot.command()
@asyncio.coroutine
def ranking(*args):
    print(args)

#Insert user into database
@mid_bot.command(pass_context=True)
@asyncio.coroutine
def setup(ctx, *args):
    member = ctx.message.author
    print(member) #log messages
    print(ctx.message)
    print(args)
    try: #insert user into database
        sql = "INSERT INTO DiscordInfo VALUES ('" + str(member) + "', '" + args[0] + "', " + str(
            ctx.message.server.id) + ");"
        print(sql)
        print(cur.execute(sql))
        try:
            sql = "select * from discordinfo;"
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                print(row) #log user in database
        except: #error
            print("didnt select")
        yield from mid_bot.say("Tied @" + str(member) + " to " + args[0]) #success
        # print(cur.fetchall)
    except: #error
        print("didn't insert")


@mid_bot.command(pass_context=True)
@asyncio.coroutine
def predict(ctx, *args):
    print(args)
    print(len(args))
    username = ctx.message.author
    print(username)
    if len(args) == 10:
        sql = "INSERT INTO ranking VALUES ('" + str(username) + "', '" + args[0] + "', '" + args[1] + "', '" + args[
            2] + "', '" + args[3] + "', '" + args[4] + "', '" + args[5] + "', '" + args[6] + "', '" + args[7] + "', '" + \
              args[8] + "', '" + args[9] + "');"
        print(sql)
        try:
            print(cur.execute(sql))
            try:
                sql = "select * from ranking;"
                cur.execute(sql)
                rows = cur.fetchall()
                for row in rows:
                    print("                                            ", row)
                yield from mid_bot.say("Stored @" + str(username) + "'s prediction")
            except:
                print("didnt select")
        except:
            print("failed to insert")
    else:
        yield from mid_bot.say("Please list 10 teams")

#Displays a table into server of players fantasy score
@mid_bot.command()
@asyncio.coroutine
def fantasy():
    # Starts formatting
    result = "Fantasy Predictions \n\n ```Username                |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  | 10  | Score  \n" \
             "------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----|\n"

    sql = "select * from ranking;"
    try: #recieve table
        cur.execute(sql)
    except: #error
        print("didn't select")
    try:
        #format by going row by row
        rows = cur.fetchall()
        for i in range(len(rows)):
            for item in rows[i]:
                if len(item) > 3:
                    result += item.ljust(23) + " | " #pad username
                elif len(item) == 3:
                    result += item + " | "#delimiter
                else:
                    result += item + "  | " #delimiter
            if i < len(rows) - 1:
                result += "\n------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----|\n"
            else: #last row
                result += "\n-------------------------------------------------------------------------------------\n"


    except: #error
        print("didn't fetch")
    result += "```" #finish formatting
    yield from mid_bot.say(result) #output

#displays stats about players last game
@mid_bot.command(pass_context=True)
@asyncio.coroutine
def lastgame(ctx, *args):
    if len(args) == 1: # username been given
        yield from mid_bot.say((LeagueStats.lastGame(args[0])))
    elif len(args) == 0: #no username been given, user default
        sql = "select summoner from discordinfo where discordName='" + str(
            ctx.message.author) + "' and serverID=" + str(ctx.message.server.id) + ";" #construct sql query
        print(sql)
        try:
            cur.execute(sql) # execute sql query
        except:
            print("failed to find username") #error
        try:
            username = cur.fetchall() #fetch
            print(str(username[0][0]).rstrip())
        except: #error
            print("failed to fetch username")
        try: #output
            yield from mid_bot.say(LeagueStats.lastGame(str(username[0][0]).rstrip()))
        except: #error
            print ("stats problem")
    else: #error
        yield from mid_bot.say("Too many parameters")

#lists all commands
@mid_bot.command()
@asyncio.coroutine
def commands():
    commands = """List of commands : \n
                  !setup <League of Legends Summoner Name>
                  \t - Ties your discord account to your League of Legends account \n
                  !shitter
                  \t - Outs the shitter of the sever \n
                  !last10 <Summoner Name>
                  \t - Win - Loss of the most recent 10 games of a League of Legends account \n
                  !predict <team> <team> <team> <team> <team> <team> <team> <team> <team> <team>
                  \t - Stores LCS prediction \n
                  !lastgame <Summoner Name>
                  \t - Displays details of last ranked game \n
                  !fantasy
                  \t - Displays all LCS predictions \n
                  !commands
                  \t - Lists all possible commands
               """

    yield from mid_bot.say(commands)

#inprogress
@mid_bot.command()
@asyncio.coroutine
def lcs():
    yield from mid_bot.say("123")

mid_bot.run(botinfo.BOT_TOKEN)

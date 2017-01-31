import discord
from discord.ext.commands import Bot

import botinfo
import LeagueStats

import os
import psycopg2
import subprocess
import urllib

mid_bot = Bot(command_prefix="!")
# url = urllib.parse(os.environ["postgres://vppudcomfsevnd:bfbfe939ccd4505078be77bbc439bfce1b38d9e925ecd9d47fa18884c740b3e9@ec2-54-163-246-165.compute-1.amazonaws.com:5432/d4nsuj4jjqjaui"])

# proc = subprocess.Popen('heroku config:get postgres://vppudcomfsevnd:bfbfe939ccd4505078be77bbc439bfce1b38d9e925ecd9d47fa18884c740b3e9@ec2-54-163-246-165.compute-1.amazonaws.com:5432/d4nsuj4jjqjaui -a fantasylcs', stdout=subprocess.PIPE, shell=True)
# db_url = proc.stdout.read().decode('utf-8').strip()

try:
    conn = psycopg2.connect("dbname='d4nsuj4jjqjaui' user='vppudcomfsevnd' host='ec2-54-163-246-165.compute-1.amazonaws.com' password='bfbfe939ccd4505078be77bbc439bfce1b38d9e925ecd9d47fa18884c740b3e9'")
    conn.autocommit = True
except:
    print ("didn't connect")
# conn = psycopg2.connect('postgres://vppudcomfsevnd:bfbfe939ccd4505078be77bbc439bfce1b38d9e925ecd9d47fa18884c740b3e9@ec2-54-163-246-165.compute-1.amazonaws.com:5432/d4nsuj4jjqjaui')
# conn = psycopg2.connect(
#     database="d4nsuj4jjqjaui",
#     user="vppudcomfsevnd",
#     password="bfbfe939ccd4505078be77bbc439bfce1b38d9e925ecd9d47fa18884c740b3e9",
#     host="ec2-54-163-246-165.compute-1.amazonaws.com",
#     port="5432"
# )

cur = conn.cursor()

@mid_bot.event
async def on_read():
    print("Client logged in")

@mid_bot.command()
async def hello(*args):
        return await mid_bot.say("Hello world!")

@mid_bot.command()
async def shitter(*args):
    return await mid_bot.say(LeagueStats.shitter())

@mid_bot.command(pass_context=True)
async def last10(ctx, *args):
    if len(args) == 1:
        return await mid_bot.say((LeagueStats.last10Games(args[0])))
    elif len(args) == 0:
        sql = "select * from discordinfo where discordName = " +  str(ctx.message.author) + ";"
        try:
            cur.execute(sql)
        except:
            print("failed to find username")
        try:
            username = cur.fetchall()
            print(username[0])
            return await mid_bot.say(LeagueStats.last10Games(str(username[0])))
        except:
            print("failed to fetch username")
    else:
        return await mid_bot.say("Too many parameters")

@mid_bot.command()
async def ranking(*args):
        print(args)

@mid_bot.command(pass_context=True)
async def setup(ctx, *args):
    member = ctx.message.author
    print(member)
    print(ctx.message)
    print(args)
    try:
        sql = "INSERT INTO DiscordInfo VALUES ('" + str(member) + "', '" + args[0] + "');"
        print(sql)
        print(cur.execute(sql))
        try:
            sql = "select * from discordinfo;"
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                print(row)
        except:
            print("didnt select")
        return await mid_bot.say("Tied @" + str(member) + " to " + args[0])
        # print(cur.fetchall)
    except:
        print("didn't insert")


@mid_bot.command(pass_context=True)
async def predict(ctx, *args):
    print(args)
    print(len(args))
    username = ctx.message.author
    print(username)
    if len(args) == 10:
        sql = "INSERT INTO ranking VALUES ('" + str(username) + "', '" + args[0] + "', '" + args[1] + "', '" + args[2] + "', '" + args[3] + "', '" + args[4] + "', '" + args[5] + "', '" + args[6] + "', '" + args[7] + "', '" + args[8] + "', '" + args[9] + "');"
        print(sql)
        try:
            print (cur.execute(sql))
            try:
                sql = "select * from ranking;"
                cur.execute(sql)
                rows = cur.fetchall()
                for row in rows:
                    print("                                            ", row)
                return await mid_bot.say("Stored @" + str(username) + "'s prediction")
            except:
                print("didnt select")
        except:
            print("failed to insert")
    else:
        return await mid_bot.say("Please list 10 teams")

@mid_bot.command()
async def fantasy():

        result = "Fantasy Predictions \n\n\t\t\t\t\t|  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  |  10  \n"
        sql = "select * from ranking;"
        try:
            cur.execute(sql)
        except:
            print("didnt select")
        try:

            rows = cur.fetchall()
            for row in rows:
                for item in row:
                    if len(item) > 3:
                        result += item[:20] + " |"

                result += "\n"

        except:
            print("didn't fetch")

        return await mid_bot.say(result)

@mid_bot.command()
async def commands():
    commands = """List of commands : \n
                  !setup <League of Legends Summoner Name>
                  \t - Ties your discord account to your League of Legends account \n
                  !shitter
                  \t - Outs the shitter of the sever \n
                  !last10 <League of Legends Summoner Name>
                  \t - Win - Loss of the most recent 10 games of a League of Legends account \n
                  !predict <team> <team> <team> <team> <team> <team> <team> <team> <team> <team>
                  \t - Stores LCS prediction \n
                  !fantasy
                  \t - Displays all LCS predictions \n
                  !commands
                  \t - Lists all possible commands
               """


    return await mid_bot.say(commands)

@mid_bot.command()
async def fuckyou():
    return await mid_bot.say("Fuck you ivan")


mid_bot.run(botinfo.BOT_TOKEN)

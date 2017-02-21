import discord
from discord.ext.commands import Bot

import botinfo
import LeagueStats

import os
import psycopg2
import subprocess
import urllib

mid_bot = Bot(command_prefix="!")

try:
    conn = psycopg2.connect("dbname=" + botinfo.dbname + " user=" + botinfo.user + " host=" + botinfo.host + " password=" + botinfo.password)
    conn.autocommit = True
except:
    print ("didn't connect")


cur = conn.cursor()

@mid_bot.event
async def on_read():
    print("Client logged in")

@mid_bot.command(pass_context=True)
async def test(ctx, *args):
    strtest = "```"
    for i in range(10):
        strtest = ctx.server
    print(strtest)
    strtest += '```'
    return await mid_bot.say(strtest)

@mid_bot.command()
async def shitter(*args):
    sql = "select summoner from discordinfo"
    try:
        cur.execute(sql)
    except:
        print("failed to find username")
    try:
        usernames = cur.fetchall()
    except:
        print("failed to fetch usernames")
    return await mid_bot.say(LeagueStats.shitter(usernames))

@mid_bot.command(pass_context=True)
async def last10(ctx, *args):
    if len(args) == 1:
        return await mid_bot.say((LeagueStats.last10Games(args[0])))
    elif len(args) == 0:
        sql = "select summoner from discordinfo where discordName='" + str(ctx.message.author) + "';"
        print(sql)
        try:
            cur.execute(sql)
        except:
            print("failed to find username")
        try:
            username = cur.fetchall()
            print(str(username[0][0]).rstrip())
            return await mid_bot.say(LeagueStats.last10Games(str(username[0][0]).rstrip()))
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

        result = "Fantasy Predictions \n\n ```Username                |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  | 10  |  \n" \
                 "------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----|\n"

        sql = "select * from ranking;"
        try:
            cur.execute(sql)
        except:
            print("didn't select")
        try:

            rows = cur.fetchall()
            for i in range(len(rows)):
                for item in rows[i]:
                    if len(item) > 3:
                        result += item[:23] + " | "
                    elif len(item) == 3:
                        result += item + " | "
                    else :
                        result += item + "  | "
                if i < len(rows) - 1:
                    result += "\n------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----|\n"
                else:
                    result += "\n------------------------------------------------------------------------------------|\n"


        except:
            print("didn't fetch")
        result += "```"
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


mid_bot.run(botinfo.BOT_TOKEN)

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

@mid_bot.command()
async def last10(*args):
    return await mid_bot.say((LeagueStats.last10Games(args[0])))
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
        print((sql))
        cur.execute(sql)
    except:
        print("didn't insert")
    try:
        sql = "select * from discordinfo;"
        cur.execute(sql)
        rows = cur.fetchall()
        for row in rows:
            print("   ", row[1][1])
    except:
        print("didnt select")

mid_bot.run(botinfo.BOT_TOKEN)

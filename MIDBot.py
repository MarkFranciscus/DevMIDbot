import discord
from discord.ext.commands import Bot

import botinfo
import LeagueStats

import os
import psycopg2

import urllib

mid_bot = Bot(command_prefix="!")
urllib.uses_netloc.append("postgres")
url = urllib.parse(os.environ["postgres://vppudcomfsevnd:bfbfe939ccd4505078be77bbc439bfce1b38d9e925ecd9d47fa18884c740b3e9@ec2-54-163-246-165.compute-1.amazonaws.com:5432/d4nsuj4jjqjaui"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

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
async def setup(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.message.author



mid_bot.run(botinfo.BOT_TOKEN)

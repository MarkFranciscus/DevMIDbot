import discord
from discord.ext.commands import Bot

import botinfo
import LeagueStats

mid_bot = Bot(command_prefix="!")
# conn = psycopg2.connect("dbname='FantasyLCS' user='postgres' host='localhost' password='password'")

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

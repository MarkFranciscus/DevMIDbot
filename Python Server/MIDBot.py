import asyncio
from asyncio import sleep
import time

from discord.ext.commands import Bot

import utility
import lolesports

import sqlalchemy
from sqlalchemy.sql import and_, text
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

import pandas as pd

Base, engine = None, None

MIDBot = Bot(command_prefix="!", case_insensitive=True)

regions = {"european masters": "EUROPE", "lla": "LATIN AMERICA", "worlds": "INTERNATIONAL", "all-star event": "INTERNATIONAL", "lcs": "NORTH AMERICA", "lec": "EUROPE", "lck": "KOREA",
           "lpl": "CHINA", "msi": "INTERNATIONAL", "opl": "OCEANIA", "cblol": "BRAZIL", "tcl": "TURKEY", "college championship": "NORTH AMERICA", "ljl": "JAPAN", "lcs academy": "NORTH AMERICA"}
codesLCS = ['EG', 'TSM', 'C9', 'IMT', 'DIG', 'CLG', 'TL', 'FLY', 'GG', '100']


@MIDBot.event
async def on_ready():
    global Base, engine
    Base, engine = utility.connect_database()
    print("Connected")


@MIDBot.event
async def on_read():
    print("Client logged in")


# Command for the sake of testing, prints serverid ten times
@MIDBot.command(pass_context=True)
async def test(ctx, *args):
    strtest = "```"
    strtest += str(ctx.message.guild.id)
    strtest += '```'
    await ctx.send(strtest)


# In progress
@MIDBot.command()
async def ranking(*args):
    print(args)


# Insert user into database
@MIDBot.command(pass_context=True)
async def setup(ctx, *args):
    member = ctx.message.author
    print(member)  # log messages
    print(ctx.message)
    print(args)
    setupSQL = "INSERT INTO DiscordInfo VALUES ('" + str(member) + "', '" + args[0] + "', " + str(
        ctx.message.guild.id) + ");"
    print(setupSQL)
    try:  # insert user into database
        print(conn.execute(setupSQL))
        await ctx.send("Tied @" + str(member) + " to " + args[0])  # success
        # print(conn.fetchall)
    except:  # error
        print("didn't insert")


@MIDBot.command(pass_context=True)
async def pickem(ctx, *args):
    global Base, engine
    username = str(ctx.message.author)
    # region = args[0]
    region_result = None
    session = Session(engine)

    # Format pickem table
    if len(args) == 1:
        region = args[0].lower()
        Tournaments = Base.classes.tournaments
        Pickems = Base.classes.pickems
        Leagues = Base.classes.leagues

        # SQL to get split id for given region
        region_result = session.query(Tournaments.tournamentid).join(Leagues).filter(
            and_(Tournaments.iscurrent, Leagues.slug.like(region))).all()

        for row in region_result:
            print(row.tournamentid)
            tournamentID = row.tournamentid

        standings = lolesports.getStandings(tournamentID)
        score_standings = utility.format_standings(standings)
        pickem_result = session.query(Pickems).filter(
            and_(Pickems.tournamentid == tournamentID, Pickems.serverid == ctx.message.guild.id)).all()
        player_pickems = []
        # format by going row by row
        for row in pickem_result:
            i = 0
            player = [row.one, row.two, row.three, row.four,
                              row.five, row.six, row.seven, row.eight, row.nine, row.ten]
            score = sum(lolesports.score(player, score_standings))
            player_pickems.append([row.username, row.one, row.two, row.three, row.four,
                         row.five, row.six, row.seven, row.eight, row.nine, row.ten, score])
        msg = "```" + utility.format_table(player_pickems, standings, args[0]) + "```"

    elif len(args) == 2:
        

    elif len(args) == 11:

        if args[0].lower() not in regions:
            msg = "Please choose a valid region"

        region = regions[args[0].lower()]
        Tournaments = Base.classes.splits
        Pickems = Base.classes.pickems

        region_result = session.query(Tournaments.splitid).filter(
            and_(Tournaments.iscurrent, Tournaments.region.like(region))).all()

        for row in region_result:
            tournamentID = row.splitid

        teams = lolesports.getCodes(tournamentID)
        picks = args[1:]
        team2code = {}
        similarity = {}
        for pick in picks:
            similarity[pick] = []
            for team in teams:
                similarity[pick] += [team,
                                     utility.similar(pick.lower(), team.lower())]
                if utility.similar(pick.lower(), team.lower()) > 0.6:
                    team2code[pick] = team
                    break

        for pick in picks:
            if pick not in team2code.keys():
                msg = "Pick {} isn't a valid team".format(pick)
                break

        row = [username, ctx.message.guild.id, tournamentID, team2code[args[1]], team2code[args[2]], team2code[args[3]], team2code[args[4]],
               team2code[args[5]], team2code[args[6]], team2code[args[7]], team2code[args[8]], team2code[args[9]], team2code[args[10]]]
        print("Inserting")
        session.execute(Pickems.__table__.insert().values(row))
        session.commit()
        print("Inserted")
        msg = "Stored your picks"

    # if len(args) == 2:

    else:
        msg = "Please list 10 teams"

    await ctx.send(msg)


# Displays a table into server of players fantasy score
@MIDBot.command(pass_context=True)
async def fantasy(ctx, *args):
    if len(args) is 0:
        ctx.send("Fuck you", ctx.message.author)
    if args[0].lower() == "start":

        await ctx.send("Starting draft")

        # Usually averages out to 40s
        await count(30, ctx)
    elif args[0].lower() == "create":
        pass
    elif args[0].lower() == "join":
        pass
    else:
        ctx.send("Fuck you", ctx.message.author)


async def count(num, ctx):
    """Countdown; print messages to the channel while command isn't stopped/halted"""
    for i in range(num, -1, -1):
        await ctx.channel.send(str(i))
        await sleep(1 - MIDBot.latency)
        end_time = time.time()


# lists all commands
@MIDBot.command()
async def commands(ctx):
    commands = """List of commands : \n
                  !setup <League of Legends Summoner Name>
                  \t - Ties your discord account to your League of Legends account \n
                  !pickem <region[NA, EU, KR, CN]> <team> <team> <team> <team> <team> <team> <team> <team> <team> <team>
                  \t - Stores LCS prediction \n
                  !pickem <region[NA, EU, KR, CN]>
                  \t - Shows LCS predictions on server for given region
                  !fantasy
                  \t - Displays all LCS predictions \n
                  !commands
                  \t - Lists all possible commands
               """

    await ctx.send(commands)


# inprogress
@MIDBot.command()
async def lcs(ctx):
    await ctx.send("123")


if __name__ == '__main__':
    discordTokens = utility.config(section='discord')
    MIDBot.run(discordTokens['bot_token'])

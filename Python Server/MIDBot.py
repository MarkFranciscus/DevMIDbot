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
        if args[0] not in regions.keys():
            msg = "Please give a valid region"
        region = regions[args[0]]
        Splits = Base.classes.splits
        Pickems = Base.classes.pickems

        # SQL to get split id for given region
        region_result = session.query(Splits.splitid).filter(
            and_(Splits.iscurrent, Splits.region.like(region))).all()

        # print("splitID", region_result)
        for row in region_result:
            print(row.splitid)
            splitID = row.splitid

        standings = lolesports.getStandings(splitID)
        score_standings = utility.format_standings(standings)
        pickem_result = session.query(Pickems).filter(
            and_(Pickems.splitid == splitID, Pickems.serverid == ctx.message.guild.id)).all()
        player_pickems = []
        # format by going row by row
        for row in pickem_result:
            i = 0
            player = [row.one, row.two, row.three, row.four,
                              row.five, row.six, row.seven, row.eight, row.nine, row.ten]
            score = lolesports.score(player, score_standings)
            player_pickems.append([row.username, row.one, row.two, row.three, row.four,
                         row.five, row.six, row.seven, row.eight, row.nine, row.ten, score])
        msg = "```" + utility.format_table(player_pickems, standings, args[0]) + "```"

    elif len(args) == 11:

        if args[0].lower() not in regions:
            msg = "Please choose a valid region"

        region = regions[args[0].lower()]
        Splits = Base.classes.splits
        Pickems = Base.classes.pickems

        region_result = session.query(Splits.splitid).filter(
            and_(Splits.iscurrent, Splits.region.like(region))).all()

        for row in region_result:
            splitID = row.splitid

        teams = lolesports.getCodes(splitID)
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

        row = [username, ctx.message.guild.id, splitID, team2code[args[1]], team2code[args[2]], team2code[args[3]], team2code[args[4]],
               team2code[args[5]], team2code[args[6]], team2code[args[7]], team2code[args[8]], team2code[args[9]], team2code[args[10]]]
        print("Inserting")
        session.execute(Pickems.__table__.insert().values(row))
        session.commit()
        print("Inserted")
        msg = "Stored your picks"

    if len(args) == 2:

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


# Displays win-loss of the past 10 games
# TODO doesn't work
# @MIDBot.command(pass_context=True)
# async def last10(ctx, *args):
    # if len(args) == 1: # a username has been given, look up that name
    #     await ctx.send(LeagueStats.last10Games(args[0]))
    # elif len(args) == 0: #no username has been given
    #     sql = "select summoner from discordinfo where discordName='" + str(
    #         ctx.message.author) + "' and serverID=" + str(ctx.message.guild.id) + ";" # construct sql query
    #     print(sql) # log it
    #     try:
    #         conn.execute(sql) #execute sql query
    #     except:
    #         print("failed to find username")
    #     try:
    #         username = conn.fetchall() #use what the database returns to look up stats
    #         print(str(username[0][0]).rstrip())
    #         await ctx.send(LeagueStats.last10Games(str(username[0][0]).rstrip()))
    #     except:
    #         print("failed to fetch username")
    # else: #error
    #     await ctx.send("Too many parameters")

# async def draft_timer(channel):
    # numSeconds = 10
    # print(channel)
    # message = "Timer: {}".format(str(numSeconds))
    # timer = await channel.send(message)
    # await asyncio.sleep(1)
    # while numSeconds > 0:
    #     numSeconds -= 1
    #     newMessage = "Timer: {}".format(str(numSeconds))
    #     await timer.edit(content=newMessage)
    #     await asyncio.sleep(1)

# displays stats about players last game
# TODO doesn't work
# @MIDBot.command(pass_context=True)
# async def lastgame(ctx, *args):
    # if len(args) == 1: # username been given
    #     await ctx.send((LeagueStats.lastGame(args[0])))
    # elif len(args) == 0: #no username been given, user default
    #     sql = "select summoner from discordinfo where discordName='" + str(
    #         ctx.message.author) + "' and serverID=" + str(ctx.message.guild.id) + ";" #construct sql query
    #     print(sql)
    #     try:
    #         conn.execute(sql) # execute sql query
    #     except:
    #         print("failed to find username") #error
    #     try:
    #         username = conn.fetchall() #fetch
    #         print(str(username[0][0]).rstrip())
    #     except: #error
    #         print("failed to fetch username")
    #     try: #output
    #         await ctx.send(LeagueStats.lastGame(str(username[0][0]).rstrip()))
    #     except: #error
    #         print ("stats problem")
    # else: #error
    #     await ctx.send("Too many parameters")

if __name__ == '__main__':
    discordTokens = utility.config(section='discord')
    MIDBot.run(discordTokens['bot_token'])

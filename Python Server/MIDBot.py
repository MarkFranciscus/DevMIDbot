import asyncio
from discord.ext.commands import Bot

import utility
import lolesports

import sqlalchemy
from sqlalchemy.sql import and_, text
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

# import LeagueStats
# import psycopg2

Base, engine = None, None

MIDBot = Bot(command_prefix="!", case_insensitive=True)

regions = ["NA", "KR", "EU", "CN"]


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
    # for i in range(10):
    # strtest += str('%d\n' % (i))
    # print(strtest)
    strtest += str(ctx.message.guild.id)
    strtest += '```'
    await ctx.send(strtest)


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
    region = args[0]
    region_result = None
    session = Session(engine)

    # Format pickem table
    if len(args) == 1:
        Splits = Base.classes.splits
        Pickems = Base.classes.pickems

        # SQL to get split id for given region
        region_result = session.query(Splits.splitid).filter(
            and_(Splits.iscurrent, Splits.region.match(region))).all()

        # print("splitID", region_result)
        for row in region_result:
            splitID = row.splitid

        # Starts formatting
        result = "Fantasy Predictions \n\n ```Username                |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  |  10 |  Score  |\n" \
            "------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+---------|\n"

        pickemSQL = "select * from pickems where splitID = {} and serverID = {};".format(
            splitID, ctx.message.guild.id)

        pickem_result = session.query(Pickems).filter(
            and_(Pickems.splitid == splitID, Pickems.serverid == ctx.message.guild.id)).all()

        # format by going row by row
        for row in pickem_result:
            i = 0
            standings = [row.one, row.two, row.three, row.four,
                         row.five, row.six, row.seven, row.eight, row.nine, row.ten]
            score = lolesports.score(standings, lolesports.get_standings(
                "lcs_2019_summer"))  # TODO score function
            standings = [row.username] + standings
            # Format pickem row
            for j in range(len(standings)):

                column = str(standings[j])
                if j == 0:
                    result += column.ljust(23) + " |"  # pad username
                else:
                    result += "{:^5}".format(column)
                    result += "|"  # delimiter

            # End row with score
            result += "{:^9}".format(str(score)) + "|"

            # row seperator
            if i < len(standings) - 1:
                result += "\n------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+---------|\n"

            i += 1
        
        result += "Standings".ljust(23) + " |"  # pad username
        standings = lolesports.format_standing_list(
            lolesports.get_standings("lcs_2019_summer"))
        for team in standings:
            result += "{:^5}".format(team)
            result += "|"  # delimiter
        result += "{:^9}".format('0') + "|"        

        result += "\n{:-^94}|\n".format("")
        result += "```"  # finish formatting
        await ctx.send(result)  # output

    elif len(args) == 11:
        if args[0].upper() in regions:
            regionSQL = "SELECT splitID FROM splits WHERE region LIKE '{}' AND isconnrent = true;".format(
                region)
            print(regionSQL)
            try:
                conn.execute(regionSQL)
            except(Exception, psycopg2.Error) as error:
                await ctx.send("Oopsies I messed up, I already let me know, but please create a git issue describing the issue! https://github.com/MarkFranciscus/DevMIDbot/issues")
                print("failed execute", error)

            try:
                splitID = conn.fetchall()[0][0]
            except:
                print("failed to find region")
                await ctx.send("Oopsies I messed up, I already let me know, but please create a git issue describing the issue! https://github.com/MarkFranciscus/DevMIDbot/issues")

            pickemSQL = "INSERT INTO pickems VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');".format(
                username, ctx.message.guild.id, splitID, args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[9], args[10])
            print(pickemSQL)
            try:
                print(conn.execute(pickemSQL))
                # try:
                #     sql = "select * from ranking;"
                #     conn.execute(sql)
                #     rows = conn.fetchall()
                #     for row in rows:
                #         print("                                            ", row)
                await ctx.send("Stored {}'s prediction".format(ctx.message.author.mention))
                # except:
                #     print("didnt select")
            except(Exception, psycopg2.Error) as error:
                print("failed execute", error)
                await ctx.send("""Oopsies I messed up, I already let the dumb dev know, but please create a git issue describing the issue! 
                            https://github.com/MarkFranciscus/DevMIDbot/issues""")
        else:
            await ctx.send("{} give a valid region".format(ctx.message.author.mention()))
    else:
        await ctx.send("Please list 10 teams")


# Displays a table into server of players fantasy score
# TODO change to !pickem command with <region> parameter
@MIDBot.command(pass_context=True)
async def fantasy(ctx, *args):
    if args[0].lower() == "start":
        await ctx.send("Starting draft")
        channel = ctx.channel
        # MIDBot.loop.create_task(draft_timer(channel))
    elif args[0].lower() == "create":
        pass
    elif args[0].lower() == "join":
        pass


# async def draft_timer(channel):
#     numSeconds = 10
#     print(channel)
#     message = "Timer: {}".format(str(numSeconds))
#     timer = await channel.send(message)
#     await asyncio.sleep(1)
#     while numSeconds > 0:
#         numSeconds -= 1
#         newMessage = "Timer: {}".format(str(numSeconds))
#         await timer.edit(content=newMessage)
#         await asyncio.sleep(1)

# displays stats about players last game
# TODO doesn't work
# @MIDBot.command(pass_context=True)
# async def lastgame(ctx, *args):
#     if len(args) == 1: # username been given
#         await ctx.send((LeagueStats.lastGame(args[0])))
#     elif len(args) == 0: #no username been given, user default
#         sql = "select summoner from discordinfo where discordName='" + str(
#             ctx.message.author) + "' and serverID=" + str(ctx.message.guild.id) + ";" #construct sql query
#         print(sql)
#         try:
#             conn.execute(sql) # execute sql query
#         except:
#             print("failed to find username") #error
#         try:
#             username = conn.fetchall() #fetch
#             print(str(username[0][0]).rstrip())
#         except: #error
#             print("failed to fetch username")
#         try: #output
#             await ctx.send(LeagueStats.lastGame(str(username[0][0]).rstrip()))
#         except: #error
#             print ("stats problem")
#     else: #error
#         await ctx.send("Too many parameters")


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

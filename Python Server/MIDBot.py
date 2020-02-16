import asyncio
import time
from asyncio import sleep

import pandas as pd
import sqlalchemy
from discord.ext.commands import Bot
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, text
from tabulate import tabulate

import lolesports
import utility

Base, engine = None, None

MIDBot = Bot(command_prefix="!", case_insensitive=True)

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
    serverid = ctx.message.guild.id
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
            and_(Tournaments.iscurrent, Leagues.slug.like(region))).first()

        tournamentID = region_result[0]

        standings = lolesports.getStandings(tournamentID)
        score_standings = utility.format_standings(standings)
        pickem_result = session.query(Pickems).filter(
            and_(Pickems.tournamentid == tournamentID, Pickems.serverid == serverid)).all()
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
        if args[1].lower() == "breakdown":
            region = args[0].lower()
            Tournaments = Base.classes.tournaments
            Pickems = Base.classes.pickems
            Leagues = Base.classes.leagues

            # SQL to get split id for given region
            tournamentID = session.query(Tournaments.tournamentid).join(Leagues).filter(
                and_(Tournaments.iscurrent, Leagues.slug.like(region))).first()[0]
            
            standings = lolesports.getStandings(tournamentID)
            score_standings = utility.format_standings(standings)
            pickem_result = session.query(Pickems).filter(
                Pickems.tournamentid == tournamentID, Pickems.serverid == serverid, Pickems.username == username).first()

            player = [pickem_result.one, pickem_result.two, pickem_result.three, pickem_result.four,
                    pickem_result.five, pickem_result.six, pickem_result.seven, pickem_result.eight, pickem_result.nine, pickem_result.ten]
            scores = lolesports.score(player, score_standings)
            scores += [sum(scores)]
        
            
            standingsTable = []
            for i in range(1, 11):
                if i in standings.keys():
                    standingsTable.append("\n".join(standings[i]))
                else:
                    standingsTable.append("")
            standingsTable += [0]
            # print(standingsTable)
            labels = ["1st", "2nd", "3rd", "4th",
                    "5th", "6th",  "7th", "8th", "9th", "10th", "Score"]
            # print (f"{len(labels)} - {len(standingsTable)} - {len(scores)}")
            player += ['']
            breakdownDict = {'': labels, 'Standings': standingsTable, 'Pickem': player, 'Scores': scores}
            breakdownFrame = pd.DataFrame(breakdownDict)
            msg = f"```{tabulate(breakdownFrame, 'keys', tablefmt='fancy_grid', showindex=False)}```"
    elif len(args) == 11:

        # if args[0].lower() not in regions:
        #     msg = "Please choose a valid region"

        region_result = session.query(Tournaments.tournamentid).join(Leagues).filter(
            and_(Tournaments.iscurrent, Leagues.slug.like(region))).all()

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
    global Base, engine
    # if len(args) is 0:
    #     ctx.send("Fuck you", ctx.message.author)
    if args[0].lower() == "start":

        await ctx.send("Starting draft")

        # Usually averages out to 40s
        await count(30, ctx)
    elif args[0].lower() == "create":
        pass
    elif args[0].lower() == "join":
        pass    
    elif args[0].lower() == "lcs":
        result = "'''Matchups\n"
        Fantasy_Matchups = Base.classes.fantasy_matchups
        session = Session(engine)
        
        scoreFrame = utility.get_fantasy_league_table(engine, Base)
        
        serverid = ctx.message.guild.id
        # print(serverid)
        FantasyTeam = Base.classes.fantasyteam
        tournamentidResult = session.query(FantasyTeam.tournamentid).filter(FantasyTeam.serverid == serverid).first()
        tournamentid = tournamentidResult[0]

        blockName = utility.get_block_name(engine, Base, tournamentid)
        matchups = session.query(Fantasy_Matchups.player_1, Fantasy_Matchups.player_2).filter(Fantasy_Matchups.blockname == blockName)

        for matchup in matchups:
            player1 = matchup[0]
            player2 = matchup[1]
            player1Frame = scoreFrame[player1]
            player2Frame = scoreFrame[player2]
            player1Columns = list(scoreFrame[player2].columns.values)
            player2Columns = list(scoreFrame[player2].columns.values)[::-1]
            player1Map = {x:x + " 1" for x in player1Columns}
            player2Map = {x:x + " 2" for x in player2Columns}
            player1Frame = player1Frame[player1Columns]
            player2Frame = player2Frame[player2Columns]
            player1Frame.rename(player1Map, inplace=True)
            player2Frame.rename(player2Map, inplace=True)
            print(player1Frame)
            print(player2Frame)
            matchupFrame = pd.merge(player1Frame, player2Frame, on='role', suffixes=[' 1', ' 2'],)
            msg = f"```{tabulate(matchupFrame, headers='keys', tablefmt='fancy_grid', showindex=False)}```"
            
            await ctx.send(msg)
    
    # else:
    #     ctx.send("Fuck you", ctx.message.author)


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

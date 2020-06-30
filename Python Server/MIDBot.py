import asyncio
import time
from asyncio import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import pandas as pd
import sqlalchemy
from discord.ext.commands import Bot
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, text, func
import tabulate
from datetime import datetime
import lolesports
import utility

tabulate.PRESERVE_WHITESPACE = True
Base, engine = None, None

MIDBot = Bot(command_prefix="!", case_insensitive=True)


@MIDBot.event
async def on_ready():
    global Base, engine
    Base, engine = utility.connect_database()
    session = Session(engine)
    scheduler = AsyncIOScheduler()

    Tournament_Schedule = Base.classes.tournament_schedule
    today = datetime.now()
    game_ts_result = session.query(Tournament_Schedule.start_ts).filter(
        Tournament_Schedule.start_ts > today).all()
    for start_ts in game_ts_result:
        scheduler.add_job(utility.live_data, 'date', run_date=start_ts[0])
    scheduler.start()
    # scheduler.print_jobs()


@MIDBot.event
async def on_read():
    print("Client logged in")


# # Command for the sake of testing, prints serverid ten times
# @MIDBot.command(pass_context=True)
# async def test(ctx, *args):
#     strtest = "```"
#     strtest += str(ctx.message.guild.id)
#     strtest += '```'
#     await ctx.send(strtest)


# In progress
@MIDBot.command()
async def ranking(*args):
    print(args)


# Insert user into database
@MIDBot.command(pass_context=True)
async def setup(ctx, *args):
    session = Session(engine)
    discordinfo = Base.classes.discordinfo

    member = ctx.message.author
    summoner = args[0]
    serverid = ctx.message.guild.id

    discordinfo.discordname, discordinfo.summoner, discordinfo.serverid = member, summoner, serverid
    session.commit()
    await ctx.send("Tied @" + str(member) + " to " + args[0])  # success


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
        msg = "```" + \
            utility.format_table(player_pickems, standings, args[0]) + "```"

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
            breakdownDict = {
                '': labels, 'Standings': standingsTable, 'Pickem': player, 'Scores': scores}
            breakdownFrame = pd.DataFrame(breakdownDict)
            msg = f"```{tabulate.tabulate(breakdownFrame, 'keys', tablefmt='fancy_grid', showindex=False)}```"
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
    if args[0].lower() == "start":
        await ctx.send("Starting draft")
        # Usually averages out to 40s
        await count(30, ctx)
    elif args[0].lower() == "create":
        pass
    elif args[0].lower() == "join":
        pass
    elif args[0].lower() == "lcs":

        Fantasy_Matchups = Base.classes.fantasy_matchups
        FantasyTeam = Base.classes.fantasyteam

        session = Session(engine)

        columns = ['role', 'summoner_name', 'fantasy_score']

        scoreFrame = utility.get_fantasy_league_table(engine, Base)

        serverid = ctx.message.guild.id

        tournamentidResult = session.query(FantasyTeam.tournamentid).filter(
            FantasyTeam.serverid == serverid).first()
        tournamentid = tournamentidResult[0]

        blockName = utility.get_block_name(engine, Base, tournamentid)

        matchups = session.query(Fantasy_Matchups.player_1, Fantasy_Matchups.player_2).filter(
            Fantasy_Matchups.blockname == blockName)
        playerWeekProgressStatement = f"select code, summoner_name, num_games_left, num_total_games from week_progress where blockname = '{blockName}' and tournamentid = {tournamentid}"
        teamWeekProgressStatement = f"select distinct code as summoner_name , num_games_left, num_total_games from week_progress where blockname = '{blockName}' and tournamentid = {tournamentid}"
        playerWeekProgress = pd.read_sql(playerWeekProgressStatement, engine)
        # playerWeekProgress['summoner_name'] = playerWeekProgress['code'] + ' ' + playerWeekProgress['summoner_name']
        # playerWeekProgress.drop(['code'], axis=1)
        teamWeekProgress = pd.read_sql(teamWeekProgressStatement, engine)
        weekProgress = pd.concat(
            [playerWeekProgress, teamWeekProgress], ignore_index=True)
        await ctx.send(blockName)
        
        for matchup in matchups:
            player1 = matchup[0]
            player2 = matchup[1]

            player1Frame = scoreFrame[player1]
            player2Frame = scoreFrame[player2]

            player1Columns = list(scoreFrame[player1].columns.values)
            player2Columns = list(scoreFrame[player2].columns.values)[::-1]

            player1Frame = pd.merge(
                player1Frame, weekProgress, on='summoner_name')
            player1Frame.fillna('', inplace=True)
            player2Frame = pd.merge(
                player2Frame, weekProgress, on='summoner_name')
            player2Frame.fillna('', inplace=True)

            p1_total_games_left = sum(player1Frame.num_games_left)
            p1_total_games = sum(player1Frame.num_total_games)
            p2_total_games_left = sum(player2Frame.num_games_left)
            p2_total_games = sum(player2Frame.num_total_games)

            player1Frame['summoner_name'] = (player1Frame['code'].str.ljust(4, ' ') + ' ' + player1Frame['summoner_name']).str.ljust(
                17, ' ') + ' (' + player1Frame.num_games_left.map(str) + '/' + player1Frame.num_total_games.map(str) + ')'
            player1Frame = player1Frame[player1Columns]
            sumRow = {'role': 'Total', 'summoner_name': '(' + str(p1_total_games_left) + '/' + str(p1_total_games) + ')', 'fantasy_score': sum(
                player1Frame['fantasy_score'])}
            
            player1Frame = pd.concat(
                [player1Frame, pd.DataFrame(sumRow, index=[0])], ignore_index=True)

            player2Frame['summoner_name'] = '(' + player2Frame.num_games_left.map(str) + '/' + player2Frame.num_total_games.map(
                str) + ') ' + (player2Frame['summoner_name'] + ' ' + player2Frame['code']).str.rjust(12, ' ')
            player2Frame = player2Frame[player2Columns]

            sumRow = {'role': 'Total', 'summoner_name': '(' + str(p2_total_games_left) + '/' + str(p2_total_games) + ')', 'fantasy_score': sum(
                player2Frame['fantasy_score'])}

            player2Frame = pd.concat(
                [player2Frame, pd.DataFrame(sumRow, index=[0])], ignore_index=True)
            player2Frame = player2Frame[player2Columns]

            matchupFrame = pd.merge(
                player1Frame, player2Frame, on='role', suffixes=[' 1', ' 2'])
            matchupFrame.columns = ['role', player1,
                                    'Fantasy Score', 'Fantasy Score', player2]
            msg = f"```{tabulate.tabulate(matchupFrame, headers='keys', tablefmt='fancy_grid', showindex=False)}```"
            await ctx.send(msg)


@MIDBot.command(pass_context=True)
async def schedule(ctx, *args):
    """ !schedule <region> <week(optional)>"""
    global Base, engine
    session = Session(engine)
    region = args[0].lower()
    Tournaments = Base.classes.tournaments
    Tournament_Schedule = Base.classes.tournament_schedule
    # Teams = Base.classes.Teams
    #  = Base.classes.pickems
    Leagues = Base.classes.leagues

    # SQL to get split id for given region
    tournamentID = session.query(Tournaments.tournamentid).join(Leagues).filter(
                and_(Tournaments.iscurrent, Leagues.slug.like(region))).first()[0]

    blockName = utility.get_block_name(engine, Base, tournamentID)

    games = session.query(Tournament_Schedule).filter(and_(Tournament_Schedule.blockname == blockName, Tournament_Schedule.tournamentid == tournamentID))
    result = f"```{region} - {blockName}\n"
    for row in games:
        result += row.team1code + " vs. " + row.team2code + "\n"
    result += "```" 
    await ctx.channel.send(result)


@MIDBot.command(pass_context=True)
async def predict(ctx, *args):
    global Base, engine
    """ !predict <region> <slug> ... <slug> """
    session = Session(engine)
    region = args[0].lower()
    Tournaments = Base.classes.tournaments
    Pickems = Base.classes.pickems
    Leagues = Base.classes.leagues
    Weekly_Predictions = Base.classes.weekly_predictions
    Tournament_Schedule = Base.classes.tournament_schedule

    username = str(ctx.message.author)
    serverID = ctx.message.guild.id
    
    # SQL to get split id for given region
    tournamentID = session.query(Tournaments.tournamentid).join(Leagues).filter(
        and_(Tournaments.iscurrent, Leagues.slug.like(region))).first()[0]

    blockName = utility.get_block_name(engine, Base, tournamentID)
    
    if len(args) > 4:
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

        predictions = []
        for i in range(1, 11, 1):
            predictions.append(team2code[args[i]])
        
        games = session.query(Tournament_Schedule.gameid, Tournament_Schedule.team1code, Tournament_Schedule.team2code).filter(and_(Tournament_Schedule.blockname == blockName, Tournament_Schedule.tournamentid == tournamentID)).order_by(Tournament_Schedule.start_ts)
        teams = [(game[1], game[2]) for game in games]
        
        flag = False
        for i in range(len(predictions)):
            if predictions[i] not in teams[i]:
                # print(predictions[i], teams[i])
                flag = True
        if flag:
            msg = "Teams out of order"
        else:            
            gameIDs = [game[0] for game in games]
            utility.insert_predictions(engine, Base, predictions, blockName, tournamentID, serverID, username, gameIDs)
            msg = "Stored"
    elif len(args) == 1:
        # utility.update_predictions(engine, username, serverID)
        prediction_result = session.query(Weekly_Predictions, Tournament_Schedule).filter(
            and_(Weekly_Predictions.gameid == Tournament_Schedule.gameid, Weekly_Predictions.serverid == serverID, Weekly_Predictions.discordname == username, Weekly_Predictions.blockname == blockName)).order_by(Tournament_Schedule.start_ts)

        prediction_result = pd.read_sql(prediction_result.statement, engine)
        prediction_result["correct"] = prediction_result["winner"] == prediction_result["winner_code"]
        # prediction_result[prediction_result["winner"] != prediction_result["winner_code"]] = False
        last_row = {"team1code": "Total", "team2code": "", "winner": "", "winner_code": f"""{prediction_result[prediction_result["correct"] == True].shape[0]}/{prediction_result.shape[0]}""", "correct": f"""{prediction_result[prediction_result["correct"] == True].shape[0]/prediction_result.shape[0]*100}%"""}
        prediction_result = prediction_result[["team1code", "team2code", "winner", "winner_code", "correct"]]
        prediction_result = pd.concat([prediction_result, pd.DataFrame(last_row, index=[0])], ignore_index=True)
        print(prediction_result)
        prediction_result.columns = ["Team", "Team", "Prediction", "Winner", "Correct"]
        msg = f"```{tabulate.tabulate(prediction_result, headers='keys', tablefmt='fancy_grid', showindex=False)}```"
    
    await ctx.channel.send(msg)


async def count(num, ctx):
    """Countdown; print messages to the channel while command isn't stopped/halted"""
    for i in range(num, -1, -1):
        await ctx.channel.send(str(i))
        await sleep(1 - MIDBot.latency)
        end_time = time.time()


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


if __name__ == '__main__':
    discordTokens = utility.config(section='discord')
    MIDBot.run(discordTokens['bot_token'])

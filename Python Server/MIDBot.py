import asyncio
import LeagueStats
import psycopg2
from discord.ext.commands import Bot
import utility

MIDBot = Bot(command_prefix="!")
cur = None
regions = ["NA", "KR", "EU", "CN"]


@MIDBot.event
async def on_ready():
    cur = utility.connect_database()

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
@MIDBot.command(pass_context=True)
async def last10(ctx, *args):
    if len(args) == 1: # a username has been given, look up that name
        await ctx.send(LeagueStats.last10Games(args[0]))
    elif len(args) == 0: #no username has been given
        sql = "select summoner from discordinfo where discordName='" + str(
            ctx.message.author) + "' and serverID=" + str(ctx.message.guild.id) + ";" # construct sql query
        print(sql) # log it
        try:
            cur.execute(sql) #execute sql query
        except:
            print("failed to find username")
        try:
            username = cur.fetchall() #use what the database returns to look up stats
            print(str(username[0][0]).rstrip())
            await ctx.send(LeagueStats.last10Games(str(username[0][0]).rstrip()))
        except:
            print("failed to fetch username")
    else: #error
        await ctx.send("Too many parameters")

#In progress
@MIDBot.command()
async def ranking(*args):
    print(args)

#Insert user into database
@MIDBot.command(pass_context=True)
async def setup(ctx, *args):
    member = ctx.message.author
    print(member) #log messages
    print(ctx.message)
    print(args)
    try: #insert user into database
        sql = "INSERT INTO DiscordInfo VALUES ('" + str(member) + "', '" + args[0] + "', " + str(
            ctx.message.guild.id) + ");"
        print(sql)
        print(cur.execute(sql))
        try:
            sql = "select * from discordinfo;"
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                print(row) #log user in database
        except: #error
            print("didnt select")
        await ctx.send("Tied @" + str(member) + " to " + args[0]) #success
        # print(cur.fetchall)
    except: #error
        print("didn't insert")


@MIDBot.command(pass_context=True)
async def pickem(ctx, *args):
    # print(args[0])
    # print(len(args))
    username = str(ctx.message.author)
    region = args[0]
    # print(username)
    if len(args) == 11:
        if args[0].upper() in regions:
            regionSQL = "SELECT splitID FROM splits WHERE region = '{}' AND isCurrent = true;".format(region)
            print(regionSQL)
            try:
                cur.execute(regionSQL)
            except:
                print("failed execute")

            try:
                splitID = cur.fetchall()
                print(splitID)
            except:
                print("failed to find region")
            # sql = "INSERT INTO pickems VALUES ('" + str(username) + "', '" + ctx.message.guild.id + "', '" + splitID + "', '" + args[0] + "', '" + args[1] + "', '" + args[
            #     2] + "', '" + args[3] + "', '" + args[4] + "', '" + args[5] + "', '" + args[6] + "', '" + args[7] + "', '" + \
            #     args[8] + "', '" + args[9] + "', '" + args[10] + "');"
            pickemSQL = "INSERT INTO pickems VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');".format(username, ctx.message.guild.id, args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[9],)
            print(pickemSQL)
            try:
                print(cur.execute(pickemSQL))
                # try:
                #     sql = "select * from ranking;"
                #     cur.execute(sql)
                #     rows = cur.fetchall()
                #     for row in rows:
                #         print("                                            ", row)
                #     await ctx.send("Stored {}".format(ctx.message.author.mention()) + "'s prediction")
                # except:
                #     print("didnt select")
            except:
                print("failed to insert")
        else:
            await ctx.send("{} give a valid region".format(ctx.message.author.mention()))
    else:
        await ctx.send("Please list 10 teams")

#Displays a table into server of players fantasy score
@MIDBot.command(pass_context=True)
async def fantasy(ctx, *args):
    # Starts formatting
    result = "Fantasy Predictions \n\n ```Username                |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  | 10  | Score  \n" \
             "------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----|\n"

    sql = "select * from ranking;"
    try: #recieve table
        cur.execute(sql)
    except: #error
        print("didn't select")
    try:
        #format by going row by row
        rows = cur.fetchall()
        for i in range(len(rows)):
            for item in rows[i]:
                if len(item) > 3:
                    result += item.ljust(23) + " | " #pad username
                elif len(item) == 3:
                    result += item + " | "#delimiter
                else:
                    result += item + "  | " #delimiter
            if i < len(rows) - 1:
                result += "\n------------------------+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----|\n"
            else: #last row
                result += "\n-------------------------------------------------------------------------------------\n"


    except: #error
        print("didn't fetch")
    result += "```" #finish formatting
    await ctx.send(result) #output

# displays stats about players last game
# TODO doesn't work
@MIDBot.command(pass_context=True)
async def lastgame(ctx, *args):
    if len(args) == 1: # username been given
        await ctx.send((LeagueStats.lastGame(args[0])))
    elif len(args) == 0: #no username been given, user default
        sql = "select summoner from discordinfo where discordName='" + str(
            ctx.message.author) + "' and serverID=" + str(ctx.message.guild.id) + ";" #construct sql query
        print(sql)
        try:
            cur.execute(sql) # execute sql query
        except:
            print("failed to find username") #error
        try:
            username = cur.fetchall() #fetch
            print(str(username[0][0]).rstrip())
        except: #error
            print("failed to fetch username")
        try: #output
            await ctx.send(LeagueStats.lastGame(str(username[0][0]).rstrip()))
        except: #error
            print ("stats problem")
    else: #error
        await ctx.send("Too many parameters")

#lists all commands
@MIDBot.command()
async def commands():
    commands = """List of commands : \n
                  !setup <League of Legends Summoner Name>
                  \t - Ties your discord account to your League of Legends account \n
                  !shitter
                  \t - Outs the shitter of the sever \n
                  !last10 <Summoner Name>
                  \t - Win - Loss of the most recent 10 games of a League of Legends account \n
                  !predict <team> <team> <team> <team> <team> <team> <team> <team> <team> <team>
                  \t - Stores LCS prediction \n
                  !lastgame <Summoner Name>
                  \t - Displays details of last ranked game \n
                  !fantasy
                  \t - Displays all LCS predictions \n
                  !commands
                  \t - Lists all possible commands
               """

    await ctx.send(commands)

#inprogress
@MIDBot.command()
async def lcs():
    await ctx.send("123")

if __name__ == '__main__':
    discordTokens = utility.config(section='discord')
    MIDBot.run(discordTokens['bot_token'])

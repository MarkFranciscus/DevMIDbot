from cassiopeia import riotapi
from operator import itemgetter

riotapi.set_region("NA")
riotapi.set_api_key("e0675e35-f858-48d1-ad1b-cfac6fb6955c")

tierToNumber = {'bronze': 0, 'silver': 1, 'gold': 2, 'platinum': 3, 'diamond': 4, 'master': 5, 'challenger': 6}
numberToTier = {0: 'bronze', 1: 'silver', 2: 'gold', 3: 'platinum', 4: 'diamond', 5: 'master', 6: 'challenger'}
divisionToNumber = {'five': 0, 'four': 1, 'three': 2, 'two': 3, 'one':4}
numberToDivision = {0:'five', 1:'four',2:'three',3:'two',4:'one'}

def shitter(usernames):
    # summoner1 = riotapi.get_summoner_by_name("rythemkiller")
    # summoner2 = riotapi.get_summoner_by_name("courageousfalcon")
    # summoner3 = riotapi.get_summoner_by_name("flailure")

    # print("{name} is a level {level} summoner on the NA server.".format(name=summoner.name, level=summoner.level))
    print(usernames)
    eloList = []
    for user in usernames:
        print(user.trim())
        newSummoner = riotapi.get_summoner_by_name(user.trim())
        currentUser = riotapi.get_league_entries_by_summoner(summoners=newSummoner)
        if len(eloList) == 0:
            eloList.append([tierToNumber[str(currentUser[1].tier)[5:]], divisionToNumber[str(currentUser[1].entries[0].division)[9:]], currentUser[1].entries[0].league_points, currentUser[1].entries[0].summoner])
        else:
            eloList.append([tierToNumber[str(currentUser[1].tier)[5:]], divisionToNumber[str(currentUser[1].entries[0].division)[9:]], currentUser[1].entries[0].league_points, currentUser[1].entries[0].summoner])
            eloList = (sorted(eloList, key=itemgetter(0, 1, 2)))
            eloList.pop()

    # mark = riotapi.get_league_entries_by_summoner(summoners=summoner1)
    # ivan = riotapi.get_league_entries_by_summoner(summoners=summoner2)
    # daniel = riotapi.get_league_entries_by_summoner(summoners=summoner3)

    # eloList = [[tierToNumber[str(mark[1].tier)[5:]], divisionToNumber[str(mark[1].entries[0].division)[9:]], mark[1].entries[0].league_points, mark[1].entries[0].summoner], [tierToNumber[str(ivan[1].tier)[5:]], divisionToNumber[str(ivan[1].entries[0].division)[9:]], ivan[1].entries[0].league_points, ivan[1].entries[0].summoner], [tierToNumber[str(daniel[1].tier)[5:]], divisionToNumber[str(daniel[1].entries[0].division)[9:]], daniel[1].entries[0].league_points, daniel[1].entries[0].summoner]]


    return str(eloList[0][3].name) + " is the shitter - " + str( numberToTier[eloList[0][0]]) + " " + str(numberToDivision[eloList[0][1]]) + " " + str(eloList[0][2]) + " LP"



def last10Games(username):
    summoner = riotapi.get_summoner_by_name(username)
    win = 0
    loss = 0
    for match_reference in summoner.match_list():
        if (win + loss) >= 10:
            return (username + " is " + (str(win) + " - " + str(loss)))
        match = riotapi.get_match(match_reference)
        print(match.data.queueType)
        if match.data.queueType == 'RANKED_FLEX_SR' or match.data.queueType == 'TEAM_BUILDER_RANKED_SOLO':
            summonerFound = False
            for participant in match.blue_team.participants:
               if participant.summoner == summoner:
                   summonerFound = True
                   break
                   # if match.blue_team.win:
                   #     win +=1
                   #     print("win " + str(win))
                   #
                   #     break;
                   # else:
                   #      loss +=1
            if not summonerFound and match.blue_team.win:
                loss += 1
            elif summonerFound and not match.blue_team.win:
                loss += 1
            else:
                win += 1
            print("win " + str(win) + ", lose " + str(loss))
            # if not summonerFound and match.red_team.win:
            #     win +=1
        # if match.queue == 'flex':
# def elo(username);
#
# last10Games("rythemkiller")
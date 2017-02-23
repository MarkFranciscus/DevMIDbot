from operator import itemgetter
from cassiopeia import riotapi
import BotInfo

riotapi.set_region(BotInfo.region)
riotapi.set_api_key(BotInfo.riotkey)

tierToNumber = {'bronze': 0, 'silver': 1, 'gold': 2, 'platinum': 3, 'diamond': 4, 'master': 5, 'challenger': 6}
numberToTier = {0: 'bronze', 1: 'Silver', 2: 'Gold', 3: 'Platinum', 4: 'Diamond', 5: 'Master', 6: 'Challenger'}
divisionToNumber = {'five': 0, 'four': 1, 'three': 2, 'two': 3, 'one':4}
numberToDivision = {0:'V', 1:'IV',2:'III',3:'II',4:'I'}

def shitter(usernames):

    eloList = []
    for user in usernames:
        newSummoner = riotapi.get_summoner_by_name(user[0].strip())
        currentUser = riotapi.get_league_entries_by_summoner(summoners=newSummoner)
        if len(eloList) == 0:
            eloList.append([tierToNumber[str(currentUser[1].tier)[5:]], divisionToNumber[str(currentUser[1].entries[0].division)[9:]], currentUser[1].entries[0].league_points, currentUser[1].entries[0].summoner])
        else:
            eloList.append([tierToNumber[str(currentUser[1].tier)[5:]], divisionToNumber[str(currentUser[1].entries[0].division)[9:]], currentUser[1].entries[0].league_points, currentUser[1].entries[0].summoner])
            eloList = (sorted(eloList, key=itemgetter(0, 1, 2)))
            eloList.pop()


    return str(eloList[0][3].name) + " is the shitter - " + str( numberToTier[eloList[0][0]]) + " " + str(numberToDivision[eloList[0][1]]) + " " + str(eloList[0][2]) + " LP"



def last10Games(username):
    summoner = riotapi.get_summoner_by_name(username)
    win = 0
    loss = 0
    for match_reference in summoner.match_list():
        if (win + loss) >= 10:
            return (username + " is " + (str(win) + " - " + str(loss)))
        match = riotapi.get_match(match_reference)
        if match.data.queueType == 'RANKED_FLEX_SR' or match.data.queueType == 'TEAM_BUILDER_RANKED_SOLO':
            summonerFound = False
            for participant in match.blue_team.participants:
               if participant.summoner == summoner:
                   summonerFound = True
                   break
            if not summonerFound and match.blue_team.win:
                loss += 1
            elif summonerFound and not match.blue_team.win:
                loss += 1
            else:
                win += 1
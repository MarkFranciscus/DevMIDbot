from operator import itemgetter
import cassiopeia as riotapi
from utility import config

riotAPIKeys = config(section='riot')
riotapi.set_default_region(riotAPIKeys['region'])
riotapi.set_riot_api_key(riotAPIKeys['riotkey'])

tierToNumber = {'bronze': 0, 'silver': 1, 'gold': 2, 'platinum': 3, 'diamond': 4, 'master': 5, 'challenger': 6}
numberToTier = {0: 'bronze', 1: 'Silver', 2: 'Gold', 3: 'Platinum', 4: 'Diamond', 5: 'Master', 6: 'Challenger'}
divisionToNumber = {'five': 0, 'four': 1, 'three': 2, 'two': 3, 'one':4}
numberToDivision = {0:'V', 1:'IV',2:'III',3:'II',4:'I'}

def shitter(usernames):

    eloList = []
    for user in usernames:
        newSummoner = riotapi.get_summoner(name=user[0].strip())
        currentUser = riotapi.get_league_entries_by_summoner(summoners=newSummoner)
        if len(eloList) == 0:
            eloList.append([tierToNumber[str(currentUser[1].tier)[5:]], divisionToNumber[str(currentUser[1].entries[0].division)[9:]], currentUser[1].entries[0].league_points, currentUser[1].entries[0].summoner])
        else:
            eloList.append([tierToNumber[str(currentUser[1].tier)[5:]], divisionToNumber[str(currentUser[1].entries[0].division)[9:]], currentUser[1].entries[0].league_points, currentUser[1].entries[0].summoner])
            eloList = (sorted(eloList, key=itemgetter(0, 1, 2)))
            eloList.pop()


    return str(eloList[0][3].name) + " is the shitter - " + str( numberToTier[eloList[0][0]]) + " " + str(numberToDivision[eloList[0][1]]) + " " + str(eloList[0][2]) + " LP"

def last10Games(username):
    summoner = riotapi.get_summoner(name=username)
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

def lastGame(username):
    summoner = riotapi.get_summoner(name=username)
    matchList = summoner.match_list()
    k = 0
    d = 0
    a = 0
    cs = 0
    outcome = "LOSS"
    champion = ""
    summonerFound = False
    for i, match_reference in enumerate(matchList[0:1]):
        match = match_reference.match()
        duration = match.duration
        for participant in match.participants:
           if participant.summoner_id == summoner.id:
                k += participant.stats.kills
                d += participant.stats.deaths
                a += participant.stats.assists
                champion = participant.champion.name
                cs = participant.stats.cs
        for participant in match.blue_team.participants:
            if participant.summoner == summoner:
                summonerFound = True
                if match.blue_team.win:
                    outcome = "WIN"
        if not summonerFound and match.red_team.win:
            outcome = "WIN"
    return "{0} - {1}/{2}/{3} - {4}cs - {5} ({6})".format(champion, k, d, a, cs, outcome, duration)
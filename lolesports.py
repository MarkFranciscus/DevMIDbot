import requests, json
# from bs4 import BeautifulSoup
import time

# url_to_scrape = 'https://www.lolesports.com/en_US/na-lcs/na_2018_summer/standings/regular_season'
# r = requests.get(url_to_scrape)

tournamentURL = "http://api.lolesports.com/api/v1/scheduleItems?leagueId={}"
teamURL = "http://api.lolesports.com/api/v1/teams?slug={1}&tournament={2}"
# print(tournamentURL.format("2"))
r = requests.get(tournamentURL.format("2"))
rawData = json.loads(r.text)

# print(rawData.keys())
# print("")
# print(len(rawData["highlanderTournaments"]))
# print("")
# print(rawData["highlanderTournaments"][6].keys())
# print("")
# print(rawData["highlanderTournaments"][6]["rosters"].values())
def get_team_ids():
    rosters = rawData["highlanderTournaments"][6]["rosters"].values()
    ids = []
    for x in rosters:
        ids.append(int(x["team"]))
    return ids

def get_standings():
    standings = rawData["highlanderTournaments"][6]["standings"]
    teams = rawData["teams"]
    result = []
    for i in standings:
        for team in teams:
            if i == team["guid"]:
                result.append(team["name"])
    print(result)

def get_slug(ids):
    teams = rawData["teams"]
    # print(teams)
    slugs = []
    for x in ids:
        for y in teams:
            # print (x, y["id"])
            if x == y["id"]:
                # print (x, y["id"])
                slugs.append(y["slug"])
                break
    print(slugs)
# parse the text of the URL
# q = get_team_ids()
# print(q)
print(get_standings())
# get_slug(q)
# Each row is: Rank/Team/Wins/Losses
format_string = "%-4s %-20s %-s %-s"

# print "Current NA LCS STANDINGS"
# print "-----------------------------"
# print format_string % ("RANK", "TEAM", "W", "L")
# for row in stats_table.find_all("tr"):
# 	cells = row.find_all("td")
# 	if len(cells) > 0:
# 		print (format_string % (cells[0].text.strip(), cells[2].text.strip(), cells[3].text.strip(), cells[4].text.strip()))
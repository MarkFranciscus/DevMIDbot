import time
import MIDBot
from utility import config

if __name__ == '__main__':
    discordTokens = config(section='discord')
    MIDBot.MIDBot.run(discordTokens['BOT_TOKEN'])
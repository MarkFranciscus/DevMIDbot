import time
import daemon
import MIDBot
import BotInfo

with daemon.DaemonContext():
    MIDBot.midbot.run(BotInfo.BOT_TOKEN)
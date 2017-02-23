import time
import daemon
import MIDBot

with daemon.DaemonContext():
    MIDBot.MIDBot()
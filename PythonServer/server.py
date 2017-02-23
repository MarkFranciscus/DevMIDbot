import time
from daemon import runner
import MIDBot

with daemon.DaemonContext():
    MIDBot.MIDBot()
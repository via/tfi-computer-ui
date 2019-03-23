import serial
import copy
import re
import time
from PySide2.QtCore import QObject, Signal, QThread, QMutex, QMutexLocker

class Tfi(QObject):

    feed_re = r"\* rpm=(?P<rpm>\d+) sync=(?P<sync>\d+) t0_count=(?P<t0_count>\d+)" +\
              r" map=(?P<map>[\d\.]+) adv=(?P<adv>[\d\.]+) dwell_us=(?P<dwell_us>\d+).*"
    feed_update = Signal()
    sendCommand = Signal(str)

    def __init__(self):
        super(Tfi, self).__init__()
        self.lock = QMutex()
        self.command_queue = []
        self.fields = []
        self.status = {
            "rpm": 0,
            "sync": False,
            "t0_count": 0,
            "map": 0,
            "advance": 0,
            "dwell": 0,
            "parse_error": False }

    def _read_feed_vars(self, line):
        self.fields = line.split()[1].split(',')
        print(self.fields)

    def fetch_feed_vars(self):
        self.command_queue.append({
            "callback": self._read_feed_vars,
            "command": "get config.feed",
        }) 
        self._send_command()

    def _send_command(self):
        if "sent" not in  self.command_queue[0]:
            self.command_queue[0]["sent"] = True
            self.sendCommand.emit(self.command_queue[0]["command"])

    def _finish_command_response(self, line):
        self.command_queue[0]["callback"](line)
        del self.command_queue[0]
        if len(self.command_queue) > 0:
            self._send_command()
    

    def process_packet(self, feedline):
        feedline = str(feedline)
        packet = {}

        if feedline.startswith("* "):
           self._finish_command_response(feedline)
           return

        if len(self.fields) == 0:
            return
        parts = feedline[2:].rstrip().split(',')

        locker = QMutexLocker(self.lock)
        try:
            self.status = dict(zip(self.fields,parts))
            self.status['parse_error'] = False
        except:
            self.status['parse_error'] = True
            return
        finally:
            locker.unlock()
        self.feed_update.emit()

    def get_status(self):
        locker = QMutexLocker(self.lock)
        return copy.copy(self.status)


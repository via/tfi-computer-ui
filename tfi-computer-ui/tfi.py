import serial
import copy
import re
import time
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker, QString

class Tfi(QObject):

    feed_re = r"\* rpm=(?P<rpm>\d+) sync=(?P<sync>\d+) t0_count=(?P<t0_count>\d+)" +\
              r" map=(?P<map>[\d\.]+) adv=(?P<adv>[\d\.]+) dwell_us=(?P<dwell_us>\d+).*"
    feed_update = pyqtSignal()
    sendCommand = pyqtSignal(QString)

    def __init__(self):
        super(Tfi, self).__init__()
        self.lock = QMutex()
        self.command_queue = []
        self.fields = []
        self.status = {}
            "rpm": 0,
            "sync": False,
            "t0_count": 0,
            "map": 0,
            "advance": 0,
            "dwell": 0,
            "parse_error": False }

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
        self.status['parse_error'] = True
        packet = {}

        if feedline.startswith("* "):
           self._finish_command_response(feedline)

        parts = feedline[2:].rstrip().split(' ')
        for part in parts:
            pair = part.split('=')
            if len(pair) != 2:
                return
            packet[str(pair[0])] = str(pair[1])

        locker = QMutexLocker(self.lock)
        try:
            self.status.update({
                "rpm": int(packet['rpm']),
                "sync": True if packet['sync'] == "1" else False,
                "t0_count": int(packet['t0_count']),
                "map": float(packet['map']),
                "advance": float(packet['adv']),
                "dwell": int(packet['dwell_us'])
                })
        except:
            return
        finally:
            locker.unlock()
        self.status['parse_error'] = False
        self.feed_update.emit()

    def get_status(self):
        locker = QMutexLocker(self.lock)
        return copy.copy(self.status)


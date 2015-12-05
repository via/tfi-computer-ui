import serial
import copy
import re
import time
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker

class Tfi(QObject):

  feed_re = r"\* rpm=(?P<rpm>\d+) sync=(?P<sync>\d+) t0_count=(?P<t0_count>\d+)" +\
      r" map=(?P<map>[\d\.]+) adv=(?P<adv>[\d\.]+) dwell_us=(?P<dwell_us>\d+).*"
  feed_update = pyqtSignal()

  def __init__(self):
    super(Tfi, self).__init__()
    self.lock = QMutex()
    self.status = {
            "rpm": 0,
            "sync": False,
            "t0_count": 0,
            "map": 0,
            "advance": 0,
            "dwell": 0,
            "parse_error": False
            }

  def process_packet(self, feedline):
    m = re.match(Tfi.feed_re, feedline)
    if m is None:
      self.status['parse_error'] = True
      return
    self.status['parse_error'] = True

    locker = QMutexLocker(self.lock)
    self.status.update({
        "rpm": m.group('rpm'),
        "sync": True if m.group('sync') else False,
        "t0_count": m.group('t0_count'),
        "map": m.group('map'),
        "advance": m.group('adv'),
        "dwell": m.group('dwell_us')
        })
    locker.unlock()
    self.feed_update.emit()
    print "emit"

  def get_status(self):
    locker = QMutexLocker(self.lock)
    return copy.copy(self.status)


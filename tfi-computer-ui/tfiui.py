import sys
import time

from PySide2.QtWidgets import QApplication
from viaems.model import Model
from serialsource import TCPTarget
from logfilesource import LogFileTarget
from autocalibrate import AutoCalibrate
from windows import MainWindow, GaugesDialog, LogViewDialog

app = QApplication(sys.argv)


class TfiUI():
    def connUpdate(self):
        pass

    def update_cb(self, nodes):
        time_since = time.time() - self.last_update
        if time_since > (1/30):
            self.last_update = time.time()
            self.gauge_dialog.updateStats(self.model.nodes)
            self.gauge_dialog.update()
            self.main_window.status_updates(nodes)

        if self.autocal:
            self.autocal.update(nodes)
        curtime = self.model.get_node('status.current_time')
        map = self.model.get_node('status.sensors.map')
        rpm = self.model.get_node('status.decoder.rpm')
        ego = self.model.get_node('status.sensors.ego')

        if curtime and map:
            self.logview.add_data(int(curtime.val), {"rpm": int(rpm.val), "map":
                float(map.val), "ego": float(ego.val)})

    def enumerate_cb(self):
        self.main_window.enumeration_completed()

    def interrogate_cb(self):
        self.main_window.interrogation_completed()
        vetable = self.model.get_node('config.tables.ve')
        #self.autocal = AutoCalibrate(vetable, tickrate=4000000)

    def __init__(self):
        target = TCPTarget()
#        target = LogFileTarget("testlog")
        target.start()
        self.last_update = time.time()

        self.logview = LogViewDialog()
        self.logview.show()
        self.logview.adjustSize()

        self.gauge_dialog = GaugesDialog()
        self.gauge_dialog.show()
        self.gauge_dialog.adjustSize()

        self.model = Model(target, update_cb=self.update_cb,
                           enumerate_cb=self.enumerate_cb,
                           interrogate_cb=self.interrogate_cb)
        self.main_window = MainWindow(self.model)
        self.main_window.closed.connect(app.quit)
        self.main_window.show()
        self.main_window.adjustSize()

        self.model.start_interrogation()

        self.autocal = None


tfi = TfiUI()
print(app.topLevelWidgets())
sys.exit(app.exec_())

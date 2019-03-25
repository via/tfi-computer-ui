import sys
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt
from viaems.parser import Parser
from viaems.model import Model
from widgets import DialGauge, BarGauge, Bulb
from serialsource import TCPTarget

class GaugesDialog(QDialog):
    def __init__(self):
        super(GaugesDialog, self).__init__()
        self.layout = QGridLayout(self)

        self.rpm = DialGauge()
        self.rpm.setMinimum(0)
        self.rpm.setMaximum(9000)
        self.rpm.addCriticalRange(6000, 9000)
        self.rpm.setLabel("RPM")
        for trpm in range(0, 9):
            self.rpm.addGraduation(trpm * 1000, str(trpm), 5, 0.09)

        for trpm in range(0, 9000, 125):
            self.rpm.addGraduation(trpm, None, 2, 0.03)

        for trpm in range(0, 9000, 500):
            self.rpm.addGraduation(trpm, None, 2, 0.05)

        self.manpres = BarGauge()
        self.manpres.setMinimum(0)
        self.manpres.setMaximum(100)
        self.manpres.setLabel("MAP")
        self.manpres.addCriticalRange(85, 100)
        for kpa in range(0, 101, 25):
            self.manpres.addGraduation(kpa, str(kpa), 2, 0.1)

        self.adv = BarGauge()
        self.adv.setMinimum(0)
        self.adv.setMaximum(45)
        self.adv.setLabel("ADVANCE")
        self.adv.addCriticalRange(40, 45)
        for deg in range(0, 46, 10):
            self.adv.addGraduation(deg, str(deg), 2, 0.1)
        self.adv.addGraduation(45, str(45), 2, 0.1)

        self.iat = BarGauge()
        self.iat.setMinimum(0.5)
        self.iat.setMaximum(1.5)
        self.iat.setLabel("EGO")
        self.iat.addCriticalRange(1.1, 1.5)
        for deg in [.6, .8,  1.0 , 1.2, 1.4]:
            self.iat.addGraduation(deg, str(deg), 2, 0.1)

        self.connstatus = Bulb()
        self.connstatus.setLabel("LINK")
        self.syncstatus = Bulb()
        self.syncstatus.setLabel("SYNC")

        self.layout.addWidget(self.rpm, 0, 0, 1, 2)
        self.layout.setColumnStretch(0, 1)
        self.layout.addWidget(self.manpres, 1, 0, 1, 2)
        self.layout.setRowMinimumHeight(2, 10)
        self.layout.addWidget(self.adv, 3, 0, 1, 2)
        self.layout.setRowMinimumHeight(4, 10)
        self.layout.addWidget(self.iat, 5, 0, 1, 2)
        self.layout.addWidget(self.connstatus, 6, 0)
        self.layout.addWidget(self.syncstatus, 6, 1)

        pal = QPalette()
        pal.setColor(QPalette.Background, Qt.black)
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def updateLinkStatus(self, up):
        self.connstatus.setStatus(up)
        self.connstatus.update()

    def updateStats(self, stats):

        if 'status.rpm' in stats:
            self.rpm.setValue(int(float(stats['status.rpm'].value())))
        if 'status.sensors.map' in stats:
            self.manpres.setValue(int(float(stats['status.sensors.map'].value())))
        if 'status.timing_advance' in stats:
            self.adv.setValue(int(float(stats['status.timing_advance'].value())))
        if 'status.sensors.ego' in stats:
            self.iat.setValue(float(stats['status.sensors.ego'].value()))
        if 'status.decoder_state' in stats:
            self.syncstatus.setStatus(stats['status.decoder_state'].value() == "full")
            

#class VarsDialog(QDialog):
#    def __init__(self):
#        super(VarsDialog, self).__init__()
#        table = QTableWidget(self)
#        table.setRowCount(1)
#        table.setRowCount(1)
#        table.setItem(1, 1, QTableWidgetItem("asdf"))



app = QApplication(sys.argv)
gauge_dialog = GaugesDialog()

gauge_dialog.show()
gauge_dialog.adjustSize()


def connUpdate():
    print("Connection updated: ", connection.connected)
    gauge_dialog.updateLinkStatus(connection.connected)

def update_cb(model):
    gauge_dialog.updateStats(model.nodes)
    gauge_dialog.update()


target = TCPTarget()
target.start()

model = Model(target, update_cb=update_cb)
model.start_interrogation()


sys.exit(app.exec_())

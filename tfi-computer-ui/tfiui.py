import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
from tfi import Tfi
from widgets import DialGauge, BarGauge, Bulb
from serialsource import SerialTFISource, FileTFISource

class GaugesDialog(QDialog):
    def __init__(self):
        super(GaugesDialog, self).__init__()
        self.layout = QGridLayout(self)

        self.rpm = DialGauge()
        self.rpm.setMinimum(0)
        self.rpm.setMaximum(6000)
        self.rpm.addCriticalRange(4500, 6000)
        self.rpm.setLabel("RPM")
        for trpm in range(0, 6):
            self.rpm.addGraduation(trpm * 1000, str(trpm), 5, 0.09)

        for trpm in range(0, 6000, 125):
            self.rpm.addGraduation(trpm, None, 2, 0.03)

        for trpm in range(0, 6000, 250):
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
        self.iat.setMinimum(-20)
        self.iat.setMaximum(60)
        self.iat.setLabel("AIR TEMP")
        self.iat.addCriticalRange(30, 60)
        for deg in range(-20, 61, 20):
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
        self.rpm.setValue(stats['rpm'])
        self.manpres.setValue(int(float(stats['map'])))
        self.adv.setValue(int(float(stats['advance'])))
        self.syncstatus.setStatus(stats['sync'])



app = QApplication(sys.argv)
gauge_dialog = GaugesDialog()

gauge_dialog.show()
gauge_dialog.adjustSize()

connection = SerialTFISource('/dev/cuaU0')
#connection = FileTFISource('/home/via/minicom2.cap', 0.001)
tfiparser = Tfi()

def tfi_update():
    stat = tfiparser.get_status()
    gauge_dialog.updateStats(stat)
    gauge_dialog.update()

def connUpdate():
    print "Connection updated: ", connection.connected
    gauge_dialog.updateLinkStatus(connection.connected)

connection.connectionStatusUpdate.connect(connUpdate, Qt.QueuedConnection)
connection.packetArrived.connect(tfiparser.process_packet, Qt.QueuedConnection)
tfiparser.feed_update.connect(tfi_update)
connection.start()

sys.exit(app.exec_())

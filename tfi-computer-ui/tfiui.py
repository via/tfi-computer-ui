import sys
from PySide2.QtWidgets import QApplication
from viaems.parser import Parser
from viaems.model import Model
from serialsource import TCPTarget
from windows import MainWindow, GaugesDialog


app = QApplication(sys.argv)

class TfiUI():
    def connUpdate(self):
        print("Connection updated: ", connection.connected)
        self.gauge_dialog.updateLinkStatus(connection.connected)
    
    def update_cb(self, nodes):
        self.gauge_dialog.updateStats(self.model.nodes)
        self.gauge_dialog.update()

        self.main_window.status_updates(nodes)

    def interrogate_cb(self):
        self.main_window.interrogation_completed()


    def __init__(self):
        target = TCPTarget()
        target.start()
        
        self.model = Model(target, update_cb=self.update_cb, interrogate_cb=self.interrogate_cb)
        
        self.main_window = MainWindow(self.model)
        self.main_window.show()
        self.main_window.adjustSize()

        self.gauge_dialog = GaugesDialog()
        self.gauge_dialog.show()
        self.gauge_dialog.adjustSize()
        
        self.model.start_interrogation()

tfi = TfiUI()
sys.exit(app.exec_())

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt, Signal
from PySide2.QtCharts import QtCharts

from models import StatusModel, TableModel, TableEditorModel, TableEditorDelegate
from widgets import DialGauge, BarGauge, Bulb

from datetime import datetime
import time


class MainWindow(QtWidgets.QMainWindow):
    closed = Signal()

    def __init__(self, model=None):
        super(MainWindow, self).__init__()
        self.last_updated = time.time()
        self.model = model
        self.interrogate_status = "in progress"

        tables_groupbox = QtWidgets.QGroupBox("Tables")
        tables_layout = QtWidgets.QHBoxLayout()
        tables_groupbox.setLayout(tables_layout)
        self.table_view = QtWidgets.QTableView()
        self.table_model = TableModel()
        self.table_view.setModel(self.table_model)
        self.table_view.doubleClicked.connect(self.select_table)

        tables_layout.addWidget(self.table_view)

        self.table_editor_model = TableEditorModel()
        self.table_editor = QtWidgets.QTableView()
        self.table_editor.setModel(self.table_editor_model)
        self.table_editor.setItemDelegate(TableEditorDelegate())
        tables_layout.addWidget(self.table_editor)

        tables_layout.setStretch(1, 10)
        tables_layout.setStretch(2, 60)

        statuses_groupbox = QtWidgets.QGroupBox("Status")
        statuses_layout = QtWidgets.QVBoxLayout()
        statuses_groupbox.setLayout(statuses_layout)
        self.status_view = QtWidgets.QTableView()
        self.status_model = StatusModel()
        self.status_view.setModel(self.status_model)
        statuses_layout.addWidget(self.status_view)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tables_groupbox)
        layout.addWidget(statuses_groupbox)

        mainwidget = QtWidgets.QWidget()
        mainwidget.setLayout(layout)

        self.setCentralWidget(mainwidget)

        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

        filemenu = self.menuBar().addMenu("File")

        filemenu.addAction("Save Config...")

        loadaction = filemenu.addAction("Load Config...")
        loadaction.triggered.connect(self._load_config_action)

        flashaction = filemenu.addAction("Flash")
        flashaction.triggered.connect(self._flash_action)

        dfuaction = filemenu.addAction("Reboot to DFU")
        dfuaction.triggered.connect(self._dfu_action)

    def _dfu_action(self):
        self.model.parser.dfu()

    def _flash_action(self):
        self.model.parser.flash()

    def _load_config_action(self):
       filename = QtWidgets.QFileDialog.getOpenFileName(self, "Load Config",
               filter="ViaEMS Configs (*.json *.config)")
       self.model.load_from_file(filename[0]) 


    def closeEvent(self, event):
        self.closed.emit()

    def status_updates(self, status):
        status_display_changed = False
        if len(status.keys()) != len(self.status_model.nodes):
            status_display_changed = True
        self.status_model.new_data(status)
        if status_display_changed:
            self.status_view.resizeRowsToContents()
            self.status_view.resizeColumnsToContents()
            self.status_view.setColumnWidth(1, 100)
        hz = 1 / (time.time() - self.last_updated)
        self.last_updated = time.time()

        table = self.table_editor_model
        if table.node:
            if table.node.colname == "RPM" and table.node.rowname == "MAP":
                table.highlight_point = (
                    self.model.status['sensor.map'],
                    self.model.status['rpm'])
                table.dataChanged.emit(table.createIndex(0, 0),
                    table.createIndex(15, 15),
                    [Qt.BackgroundRole])

        self.statusbar.showMessage("Interrogation: {}  (Hz: {:d})".format(self.interrogate_status, int(hz)))

    def select_table(self, index):
        if index is None:
            return

        node = self.table_model.nodes[index.row()]
        self.table_editor_model.setNode(node)

        self.table_editor.resizeColumnsToContents()
        self.table_editor.resizeRowsToContents()

    def interrogation_completed(self):
        self.interrogate_status = "completed"

        self.model.dump_to_file("./logs/{}.config".format(datetime.isoformat(datetime.now())))
        print (self.model.nodes)

    def enumeration_completed(self):
        print (self.model.nodes)
        self.status_model._model_changed(self.model)
        self.table_model._model_changed(self.model)

        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()


class LogViewDialog(QtWidgets.QDialog):
    def __init__(self):
        super(LogViewDialog, self).__init__()

        layout = QtWidgets.QVBoxLayout(self)
        chartview = QtCharts.QChartView()

        self.chart = QtCharts.QChart()
        self.rpm_series = QtCharts.QLineSeries()
        self.chart.addSeries(self.rpm_series)
        self.chart.createDefaultAxes()
        self.chart.axisY().setRange(0, 10000)

        chartview.setChart(self.chart)

        layout.addWidget(chartview)

    def add_data(self, time, value):
        self.rpm_series.append(time, value)
        self.chart.axisX().setRange(time - 200000, time)


class GaugesDialog(QtWidgets.QDialog):
    def __init__(self):
        super(GaugesDialog, self).__init__()
        self.layout = QtWidgets.QGridLayout(self)

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
        self.adv.addCriticalRange(40, 50)
        for deg in range(0, 50, 10):
            self.adv.addGraduation(deg, str(deg), 2, 0.1)

        self.ego = BarGauge()
        self.ego.setMinimum(0.5)
        self.ego.setMaximum(1.5)
        self.ego.setLabel("EGO")
        self.ego.addCriticalRange(1.1, 1.5)
        for deg in [.6, .8, 1.0, 1.2, 1.4]:
            self.ego.addGraduation(deg, str(deg), 2, 0.1)

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
        self.layout.addWidget(self.ego, 5, 0, 1, 2)
        self.layout.addWidget(self.connstatus, 6, 0)
        self.layout.addWidget(self.syncstatus, 6, 1)

        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, Qt.black)
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def updateLinkStatus(self, up):
        self.connstatus.setStatus(up)
        self.connstatus.update()

    def updateStats(self, updates):
        if 'rpm' in updates:
            self.rpm.setValue(updates['rpm'])
        if 'sensor.map' in updates:
            self.manpres.setValue(updates['sensor.map'])
        if 'sensor.ego' in updates:
            self.ego.setValue(updates['sensor.ego'])
        if 'advance' in updates:
            self.adv.setValue(updates['advance'])


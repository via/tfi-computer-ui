from PySide2 import QtWidgets
from PySide2 import QtCore
from viaems.model import *

class StatusModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super(StatusModel, self).__init__()
        self.nodes = []

    def _model_changed(self, model):
        self.nodes = []
        for n in sorted(model.nodes):
            node = model.nodes[n]
            if isinstance(node, StatusNode):
                self.nodes.append(node)
        self.modelReset.emit()

    def new_data(self, nodes=[]):
        for newdata_node in nodes:
            for row in range(len(self.nodes)):
                if newdata_node == self.nodes[row].name:
                    self.dataChanged.emit(self.createIndex(0, row),
                            self.createIndex(2, row))
                    break

    def rowCount(self, parent):
        if parent is None:
            return 0

        return len(self.nodes)

    def columnCount(self, parent):
        return 0 if parent is None else 3

    def flags(self, index):
        flags = super(StatusModel, self).flags(index)
        if index.column() == 2:
            flags = flags | (QtCore.Qt.ItemIsUserCheckable |
                    QtCore.Qt.ItemIsEnabled)
        return flags

    def setData(self, index, value, role):
        if index and index.column() == 2 and role == QtCore.Qt.CheckStateRole:
            if value == QtCore.Qt.Checked:
                self.nodes[index.row()].set_auto_refresh(True)
            else:
                self.nodes[index.row()].set_auto_refresh(False)
            return True

        return False

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return self.nodes[index.row()].name
            elif index.column() == 1:
                return self.nodes[index.row()].value()
        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 2:
                if self.nodes[index.row()].auto_refresh:
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

    def headerData(self, column, orientation, role):
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return
        if column == 0:
            return "Node"
        elif column == 1:
            return "Value"
        elif column == 2:
            return "Logged"

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super(TableModel, self).__init__()
        self.nodes = []

    def _model_changed(self, model):
        self.nodes = []
        for n in sorted(model.nodes):
            node = model.nodes[n]
            if isinstance(node, TableNode):
                self.nodes.append(node)
        self.modelReset.emit()

    def rowCount(self, parent):
        if parent is None:
            return 0

        return len(self.nodes)

    def columnCount(self, parent):
        return 0 if parent is None else 1

    def headerData(self, column, orientation, role):
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return
        if column == 0:
            return "Node"

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.nodes[index.row()].name

class TableEditorModel(QtCore.QAbstractTableModel):
    def __init__(self, table_node=None):
        super(TableEditorModel, self).__init__()
        self.node = table_node

    def setNode(self, node):
        self.node = node
        self.modelReset.emit()

    def rowCount(self, parent):
        if parent is None or self.node is None:
            return 0

        return self.node.val["rows"]

    def columnCount(self, parent):
        if parent is None or self.node is None:
            return 0

        return self.node.val["cols"]

    def data(self, index, role):
        if self.node is None:
            return
        if role == QtCore.Qt.DisplayRole:
            return self.node.val["values"][index.row()][index.column()]

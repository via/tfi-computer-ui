from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
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

    def new_data(self, nodes={}):
        for i, statusnode in enumerate(self.nodes):
            if statusnode.name in nodes.keys():
                self.dataChanged.emit(self.createIndex(0, i),
                        self.createIndex(2, i))

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

class TableEditorDelegate(QtWidgets.QStyledItemDelegate):

#    def createEditor(self, parent, option, index):
#        super().createEditor(parent, option, index)
#        self.set = False

    def setEditorData(self, editor, index):
        if not hasattr(self, 'set') or not self.set:
            self.set = True
            text = index.model().data(index, QtCore.Qt.DisplayRole)
            editor.setText(index.model().data(index, QtCore.Qt.DisplayRole))

class TableEditorModel(QtCore.QAbstractTableModel):
    def __init__(self, table_node=None):
        super(TableEditorModel, self).__init__()
        self.node = table_node
        self.highlight_point = None

    def setNode(self, node):
        self.node = node
        self.modelReset.emit()

    def rowCount(self, parent):
        if parent is None or self.node is None:
            return 0

        if self.node.naxis == 1:
            return 1

        return self.node.rows

    def columnCount(self, parent):
        if parent is None or self.node is None:
            return 0

        return self.node.cols

    def data(self, index, role):
        if self.node is None:
            return
        if role == QtCore.Qt.DisplayRole:
            if self.node.naxis == 2:
                return self.node.table[index.row()][index.column()]
            else:
                return self.node.table[index.column()]
        if role == QtCore.Qt.ForegroundRole:
            if self.node.naxis == 2 and self.node.table_written[index.row()][index.column()]:
                return QtGui.QColor(QtCore.Qt.red)
            if self.node.naxis == 1 and self.node.table_written[index.column()]:
                return QtGui.QColor(QtCore.Qt.red)
        if role == QtCore.Qt.BackgroundRole and self.highlight_point:
            dist = self.node.get_position_dist(index.row(), index.column(),
                    self.highlight_point[0], self.highlight_point[1])
            if dist <= 2:
                color = QtGui.QColor(QtCore.Qt.green)
                color = color.lighter((dist + 1.0) * 100)
                return color
    
    def headerData(self, i, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if self.node.naxis == 2:
            if orientation == QtCore.Qt.Horizontal:
                return self.node.col_labels[i]
            else:
                return self.node.row_labels[i]
        else:
            if orientation == QtCore.Qt.Horizontal:
                return self.node.col_labels[i]

    def flags(self, index):
        flags = super(TableEditorModel, self).flags(index)
        flags = flags | QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role):
        self.node.set_point(index.row(), index.column(), value)
        return True

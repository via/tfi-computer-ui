from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets

class Series():
    def __init__(self, name):
        self.name = name
        self.data = []
        self.series_range = (0, 0)
        self.color = QtCore.Qt.red

    def insert(self, time, point):
        self.data.append((time, point))
        if point < self.series_range[0]:
            self.series_range = (point, self.series_range[1])
        elif point > self.series_range[1]:
            self.series_range = (self.series_range[0], point)

    def set_color(self, color):
        self.color = color

    def get_time_range(self):
        if not len(self.data):
            return (0, 0)
        return (self.data[0][0], self.data[-1][0])

    def set_series_range(self, range):
        self.series_range = range

    def get_points(self, start_time=None, stop_time=None):
        if not start_time:
            start_time = self.get_time_range()[0]
        if not stop_time:
            stop_time = self.get_time_range()[1]
        for point in self.data:
            if point[0] >= start_time and point[0] <= stop_time:
                yield(point)


class Plot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Plot, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                QtWidgets.QSizePolicy.MinimumExpanding)
        self.series = {}
        self.time_range = (None, None)

        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def add_series(self, s):
        self.series.update({
            s.name: s
        })

    def set_time_range(self, start=None, stop=None):
        self.time_range = (start, stop)

    def get_time_range(self):
        start, stop = self.time_range
        if not start:
            start = 0
            for s in self.series.values():
                r = s.get_time_range()
                if r[0] < start:
                    start = r[0]
        if not stop:
            stop = 0
            for s in self.series.values():
                r = s.get_time_range()
                if r[1] > stop:
                    stop = r[1]
        return (start, stop)


    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def _point_series_to_widget(self, series, point):
        widget_range = self.get_time_range()
        x = ((point[0] - widget_range[0]) / (widget_range[1] - widget_range[0])) * self.rect().width()
        y = (point[1] / series.series_range[1]) * self.rect().height()

        y = self.rect().height() - y
        return QtCore.QPointF(x, y)

    def drawWidget(self, qp):
        for name, series in self.series.items():
            qp.setPen(QtGui.QPen(series.color, 1))
            prev_point = None
            for point in series.get_points(*self.get_time_range()):
                cur_point = self._point_series_to_widget(series, point)
                if prev_point:
                    qp.drawLine(prev_point, cur_point)
                prev_point = cur_point


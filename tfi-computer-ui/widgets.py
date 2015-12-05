from PyQt4 import QtGui
from PyQt4 import QtCore
import math

class Bulb(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Bulb, self).__init__(parent)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                QtGui.QSizePolicy.MinimumExpanding)
        self.lit = False
        self.label = None

    def setStatus(self, lit):
        self.lit = lit

    def setLabel(self, l):
        self.label = l

    def sizeHint(self):
        return QtCore.QSize(80, 80)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        qp.setPen(QtGui.QPen(QtCore.Qt.red, 4))
        qp.setBrush(QtGui.QBrush(QtCore.Qt.red))

        bulbcenter = QtCore.QPoint(self.rect().center().x(),
                self.rect().center().y() * 0.8)
        bulbbox = QtCore.QRect(-20, -20, 40, 40)
        bulbbox.moveCenter(bulbcenter)
        qp.drawEllipse(bulbbox)

        qp.setPen(QtGui.QPen(QtCore.Qt.black, 4))
        if self.lit:
            qp.setBrush(QtGui.QBrush(QtCore.Qt.red))
        else:
            qp.setBrush(QtGui.QBrush(QtCore.Qt.black))
        innerbox = QtCore.QRect(-19, -19, 38, 38)
        innerbox.moveCenter(bulbcenter)
        qp.drawEllipse(innerbox)

        if self.label:
            qp.setPen(QtGui.QPen(QtCore.Qt.white, 4))
            font = QtGui.QFont('Gauge', 12, QtGui.QFont.Normal)
            qp.setFont(font)
            fmetrics = QtGui.QFontMetrics(font)
            textpos = QtCore.QPoint(self.rect().center().x(),
                    self.rect().bottom() * 0.9)
            textpos -=fmetrics.boundingRect(self.label).center()
            qp.drawText(textpos, self.label)

class Gauge(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Gauge, self).__init__(parent)
        self.value = 0
        self.minimum = 0
        self.maximum = 1
        self.label = None
        self.crit = []
        self.ticks = []
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding)

    def setValue(self, value):
        self.value = value

    def setMinimum(self, val):
        self.minimum = val

    def setMaximum(self, val):
        self.maximum = val

    def setLabel(self, val):
        self.label = val

    def addCriticalRange(self, range_start, range_stop):
        self.crit.append({"start": range_start, "stop": range_stop})

    def addGraduation(self, value, label, thickness, length):
        self.ticks.append({
            "value": value,
            "label": label,
            "thickness": thickness,
            "length": length
            })

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

class BarGauge(Gauge):
    def __init__(self, parent=None):
        super(BarGauge, self).__init__(parent)
        self.start = 0.09
        self.stop = 0.91
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                QtGui.QSizePolicy.MinimumExpanding)

    def sizeHint(self):
        return QtCore.QSize(150, 100)

    def _barPosition(self, value):
        pos = self.start + (self.stop - self.start) * \
                ((float(value) - self.minimum) / (self.maximum - self.minimum))
        return QtCore.QPoint(pos * self.rect().width(), self.rect().height() * 0.4)

    def _drawTick(self, qp, value, length):
        pos = self._barPosition(value)
        toppos = pos - QtCore.QPoint(0, self.rect().height() * length)
        qp.drawLine(pos, toppos)



    def drawWidget(self, qp):
        pen = QtGui.QPen(QtCore.Qt.white, 3)
        qp.setPen(pen)
        font = QtGui.QFont('Gauge', 14, QtGui.QFont.Normal)
        qp.setFont(font)


        # Critical regions
        for reg in self.crit:
            thickness = self.rect().height() * 0.1
            start = self._barPosition(reg['start'])
            stop = self._barPosition(reg['stop'])

            start += QtCore.QPoint(thickness / 2, -thickness / 2)
            stop -= QtCore.QPoint(thickness / 2, thickness / 2)
            qp.setPen(QtGui.QPen(QtCore.Qt.red, thickness))
            qp.drawLine(start, stop)     

        pen = QtGui.QPen(QtCore.Qt.white, 3)
        qp.setPen(pen)
        qp.drawLine(self._barPosition(self.minimum),
                self._barPosition(self.maximum))

        # Start/Stop ticks
        self._drawTick(qp, self.minimum, 0.15)
        self._drawTick(qp, self.maximum, 0.15)

        # Graduations
        for tick in self.ticks:
            pos = self._barPosition(tick['value'])
            qp.setPen(QtGui.QPen(QtCore.Qt.white, tick['thickness']))
            self._drawTick(qp, tick['value'], tick['length'])
            if tick['label']:
                fmetrics = QtGui.QFontMetrics(font)
                textpos = pos + QtCore.QPoint(0, self.rect().height() * 0.15)
                textpos -= fmetrics.boundingRect(tick['label']).center()
                qp.drawText(textpos, tick['label'])

        # Pointer
        t_height = self.rect().height() * 0.15
        t_width = self.rect().width() * 0.10
        qp.setPen(QtGui.QPen(QtCore.Qt.white, 1))
        qp.setBrush(QtGui.QBrush(QtCore.Qt.white))
        pos = self._barPosition(self.value)
        qp.drawConvexPolygon(pos, pos + QtCore.QPoint(t_width / 2, -t_height),
                                  pos + QtCore.QPoint(-t_width / 2, -t_height))

        # Label
        if self.label:
            qp.setPen(QtGui.QPen(QtCore.Qt.white, 4))
            font = QtGui.QFont('Gauge', 12, QtGui.QFont.Normal)
            qp.setFont(font)
            fmetrics = QtGui.QFontMetrics(font)
            bbox = fmetrics.boundingRect(self.label)
            pos = self.rect().center() - bbox.center()
            pos.setY(self.rect().height() * 0.20)
            qp.drawText(pos, self.label)

        # Value text
        qp.setPen(QtGui.QPen(QtCore.Qt.white, 4))
        font = QtGui.QFont('Gauge', 20, QtGui.QFont.Normal)
        qp.setFont(font)
        fmetrics = QtGui.QFontMetrics(font)
        bbox = fmetrics.boundingRect(str(self.value))
        pos = self.rect().center() - bbox.center()
#        pos.setY(pos.y() + bbox.height() + self.rect().height() * 0.05)
        pos.setY(self.rect().height() * 0.85)
        qp.drawText(pos, str(self.value))
        

class DialGauge(Gauge):
    def __init__(self, parent=None):
        super(DialGauge, self).__init__(parent)
        self.start_angle = 210
        self.stop_angle = -30
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                QtGui.QSizePolicy.MinimumExpanding)

    def sizeHint(self):
        return QtCore.QSize(150, 200)

    def _angleFromValue(self, val):
        angle = self.start_angle + (self.stop_angle - self.start_angle) * \
                ((float(val) - self.minimum) / (self.maximum - self.minimum))
        return angle

    def _arcPosition(self, angle, r):
        deg = math.radians(angle)
        p = QtCore.QPoint(math.cos(deg) * self.rect().width() / 2 * r,
                   -math.sin(deg) * self.rect().height() / 2 * r)
        p += self.rect().center()
        return p


    def _drawTick(self, qp, angle, length):
        start = self._arcPosition(angle, 1)
        stop = self._arcPosition(angle, 1 - length)
        qp.drawLine(start, stop)

    def drawWidget(self, qp):

        pen = QtGui.QPen(QtCore.Qt.white, 4)
        qp.setPen(pen)
        font = QtGui.QFont('Gauge', 14, QtGui.QFont.Normal)
        qp.setFont(font)

        qp.drawArc(self.rect(), self.start_angle * 16, 
                (self.stop_angle - self.start_angle) * 16)

        # Start/Stop ticks
        self._drawTick(qp, self.start_angle, 0.05)
        self._drawTick(qp, self.stop_angle, 0.05)
        
        # Graduations
        for tick in self.ticks:
            angle = self._angleFromValue(tick['value'])
            qp.setPen(QtGui.QPen(QtCore.Qt.white, tick['thickness']))
            self._drawTick(qp, angle, tick['length'])
            if tick['label']:
                fmetrics = QtGui.QFontMetrics(font)
                textpos = self._arcPosition(angle, (1 - tick['length'] - 0.2))
                textpos -= fmetrics.boundingRect(tick['label']).center()
                qp.drawText(textpos, tick['label'])

        # Critical regions
        for reg in self.crit:
            start_angle = self._angleFromValue(reg['start'])
            stop_angle = self._angleFromValue(reg['stop'])
            qp.setPen(QtGui.QPen(QtCore.Qt.red, 4))
            qp.drawArc(self.rect(), start_angle * 16, 
                    (stop_angle - start_angle) * 16)

        # Needle
        pointer_angle = self._angleFromValue(self.value)
        qp.setPen(QtGui.QPen(QtCore.Qt.white, 4))
        self._drawTick(qp, pointer_angle, 1)
        qp.setPen(QtGui.QPen(QtCore.Qt.red, 6))
        self._drawTick(qp, pointer_angle, 0.3)

        # Label
        if self.label:
            qp.setPen(QtGui.QPen(QtCore.Qt.white, 4))
            font = QtGui.QFont('Gauge', 12, QtGui.QFont.Normal)
            qp.setFont(font)
            fmetrics = QtGui.QFontMetrics(font)
            bbox = fmetrics.boundingRect(self.label)
            pos = self.rect().center() - bbox.center()
            pos.setY(pos.y() + bbox.height() + self.rect().height() * 0.05)
            qp.drawText(pos, self.label)

        # Value text
        qp.setPen(QtGui.QPen(QtCore.Qt.white, 4))
        font = QtGui.QFont('Gauge', 20, QtGui.QFont.Normal)
        qp.setFont(font)
        fmetrics = QtGui.QFontMetrics(font)
        bbox = fmetrics.boundingRect(str(self.value))
        pos = self.rect().center() - bbox.center()
        pos.setY(pos.y() + bbox.height() + self.rect().height() * 0.10)
        qp.drawText(pos, str(self.value))

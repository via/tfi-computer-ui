from PyQt4.QtCore import *
import serial
import socket
import time

class SerialTFISource(QThread):
    connectionStatusUpdate = pyqtSignal()
    packetArrived = pyqtSignal(QString)

    def __init__(self, device):
        super(SerialTFISource, self).__init__()
        self.serial = serial.Serial(device,  115200, timeout=1)
        self.connected = False

    def run(self):
        while self.isRunning():
            line = self.serial.readline()
            if not line and self.connected:
                self.connected = False
                self.connectionStatusUpdate.emit()
            if line:
                if not self.connected:
                    self.connected = True
                    self.connectionStatusUpdate.emit()
                self.packetArrived.emit(line)

class FileTFISource(QThread):
    connectionStatusUpdate = pyqtSignal()
    packetArrived = pyqtSignal(QString)

    def __init__(self, fname, delay=None):
        super(FileTFISource, self).__init__()
        self.connected = False
        self.delay = delay
        self.fname = fname

    def run(self):
        with open(self.fname) as f: 
            self.connected = True
            self.connectionStatusUpdate.emit()
            for line in f:
                self.packetArrived.emit(line)
                if self.delay:
                    time.sleep(self.delay)
        self.connected = False
        self.connectionStatusUpdate.emit()

class TCPTFISource(QThread):
    connectionStatusUpdate = pyqtSignal()
    packetArrived = pyqtSignal(QString)

    def __init__(self, host='localhost', port=1235):
        super(TCPTFISource, self).__init__()
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.file = self.socket.makefile()

    def sendCommand(self, line):
        line = str(line) + "\n"
        self.socket.send(line)

    def run(self):
        self.connected = True
        self.connectionStatusUpdate.emit()
        for line in self.file:
            self.packetArrived.emit(line)
        self.connected = False
        self.connectionStatusUpdate.emit()

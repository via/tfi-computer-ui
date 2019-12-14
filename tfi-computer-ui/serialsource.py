from PySide2.QtCore import QThread, Signal
import socket

class TCPTarget(QThread):
    packet_update = Signal(str)
    status_update = Signal(bool)

    def __init__(self, host='localhost', port=1236,
            packet_callback=None, status_callback=None):
        super(TCPTarget, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.connected = True
        self.file = self.socket.makefile(encoding='latin1',
                buffering=1)
        self.set_packet_callback(packet_callback)
        self.set_status_callback(status_callback)

    def set_packet_callback(self, cb):
        self.packet_update.connect(cb)

    def set_status_callback(self, cb):
        if cb:
            self.status_update.connect(cb)
        self.status_update.emit(self.connected)

    def send_command(self, line):
        line = str(line) + "\n"
        self.socket.send(bytes(line, encoding='latin1'))

    def run(self):
        self.status_update.emit(self.connected)

        for line in self.file:
            self.packet_update.emit(line)

        self.connected = False
        self.status_update.emit(self.connected)

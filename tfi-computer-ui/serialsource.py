from PySide2.QtCore import QThread
import socket

class TCPTarget(QThread):
    def __init__(self, host='localhost', port=1235,
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
        self.packet_callback = cb

    def set_status_callback(self, cb):
        self.status_callback = cb
        if cb:
            self.status_callback(self.connected)

    def send_command(self, line):
        line = str(line) + "\n"
        self.socket.send(bytes(line, encoding='latin1'))

    def run(self):
        if self.status_callback:
            self.status_callback(self.connected)

        for line in self.file:
            if self.packet_callback:
                self.packet_callback(line)

        self.connected = False
        if self.status_callback:
            self.status_callback(self.connected)

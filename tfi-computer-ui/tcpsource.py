from PySide2.QtCore import QThread, Signal
import socket
import cbor

class TCPTarget(QThread):
    packet_update = Signal(dict)
    status_update = Signal(bool)

    def __init__(self, host='localhost', port=1234,
            packet_callback=None, status_callback=None):
        super(TCPTarget, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.connected = True
        self.file = self.socket.makefile('rwb')
        self.set_packet_callback(packet_callback)
        self.set_status_callback(status_callback)

    def set_packet_callback(self, cb):
        self.packet_update.connect(cb)

    def set_status_callback(self, cb):
        if cb:
            self.status_update.connect(cb)
        self.status_update.emit(self.connected)

    def send_command(self, message):
        cbor.dump(message, self.file)
        self.file.flush()

    def run(self):
        self.status_update.emit(self.connected)

        while True:
            packet = cbor.load(self.file)
            self.packet_update.emit(packet)

        self.connected = False
        self.status_update.emit(self.connected)

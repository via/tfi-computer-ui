from datetime import datetime
import json
import gzip

class Parser():

    def __init__(self, target, data_update_cb):
        self.command_queue = []
        self.feed_fields = []
        self.data_update_cb = data_update_cb
        self.target = target
        target.set_status_callback(self._status_callback)
        target.set_packet_callback(self._packet_callback)
        self.logfile = gzip.open('./logs/{}.gz'.format(datetime.isoformat(datetime.now())), 'wt')

    def structure(self, cb):
        cmd = {"id": 1, "type": "request", "method": "structure"}
        self._send_request(cmd, cb)

    def get(self, cb, path):
        cmd = {"id": 2, "type": "request", "method": "get", "path": path}
        self._send_request(cmd, cb)

    def set(self, cb, path, value):
        cmd = {"id": 3, "type": "request", "method": "set", "path": path,
                "value": value}
        self._send_request(cmd, cb)

    def dfu(self):
        cmd = {"id": 8, "type": "request", "method": "bootloader"}
        self._send_request(cmd, None)

    def ping(self, cb):
        cmd = {"id": 8, "type": "request", "method": "ping"}
        self._send_request(cmd, cb)

    def flash(self, cb=None):
        cmd = {"id": 10, "type": "request", "method": "flash"}
        self._send_request(cmd, cb)

    def _send_request(self, request, callback):
        self.command_queue.append({
            "command": request,
            "callback": callback,
            })
        # If queue was empty
        if len(self.command_queue) == 1:
            self.target.send_command(self.command_queue[0]["command"])

    def _finish_command_response(self, msg):
        if self.command_queue[0]["callback"]:
            self.command_queue[0]["callback"](msg)
        del self.command_queue[0]
        if len(self.command_queue) > 0:
            self.target.send_command(self.command_queue[0]["command"])

    def _status_callback(self, state):
        pass

    def _packet_callback(self, msg):
        if msg['type'] == 'response':
            self._finish_command_response(msg)
        elif msg['type'] == 'description':
            self.feed_fields = msg['keys']
        elif msg['type'] == 'feed':
            if len(self.feed_fields) == 0:
                return
            values = msg['values']
            self.status = dict(zip(self.feed_fields, values))
            self.status['parse_error'] = False
            json.dump(self.status, self.logfile)
            self.logfile.write('\n')
            if self.data_update_cb:
                self.data_update_cb(self.status)


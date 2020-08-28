from datetime import datetime

class Parser():

    def __init__(self, target, data_update_cb):
        self.command_queue = []
        self.feed_fields = []
        self.data_update_cb = data_update_cb
        self.target = target
        target.set_status_callback(self._status_callback)
        target.set_packet_callback(self._packet_callback)
        self.logfile = open('./logs/{}'.format(datetime.isoformat(datetime.now())), 'w')

    def structure(self, cb):
        cmd = {"id": 1, "type": "request", "method": "structure"}
        self._send_request(cmd, cb)

    def get(self, cb, path):
        cmd = {"id": 2, "type": "request", "method": "get", "path": path}
        self._send_request(cmd, cb)

    def set(self, cb, node, args=[]):
        cmd = {"id": 3, "type": "request", "method": "set", "path": path}
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
            values = msg['values']
            self.status = dict(zip(self.feed_fields, values))
            self.status['parse_error'] = False
            if self.data_update_cb:
                self.data_update_cb(self.status)


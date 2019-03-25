class Parser():

    def __init__(self, target, data_update_cb):
        self.command_queue = []
        self.feed_fields = []
        self.data_update_cb = data_update_cb
        self.target = target
        target.set_status_callback(self._status_callback)
        target.set_packet_callback(self._packet_callback)
        self.get(self._read_feed_vars, "config.feed")
        self.logfile = open('/home/via/tmp/log', 'w')

    def list(self, cb, prefix):
        cmd = "list {}".format(prefix)
        self._send_request(cmd, cb)

    def get(self, cb, node, args=[]):
        cmd = "get {}".format(node)
        for arg in args:
            cmd += " {}".format(arg)
        self._send_request(cmd, cb)

    def set(self, cb, node, args=[]):
        cmd = "set {}".format(node)
        for arg in args:
            if isinstance(args, dict):
                cmd += " {}={}".format(arg, args[arg])
            else:
                cmd += " {}".format(arg)
        self._send_request(cmd, cb)

        # Special case, we want to know if we're changing the config feed
        if node == "config.feed":
            self.get(self._read_feed_vars, "config.feed")

    def _read_feed_vars(self, line):
        if line is None:
            return
        self.logfile.write(line)
        self.feed_fields = line.strip().split(',')

    def _send_request(self, request, callback):
        self.command_queue.append({
            "command": request,
            "callback": callback,
            })
        # If queue was empty
        if len(self.command_queue) == 1:
            self.target.send_command(self.command_queue[0]["command"])

    def _finish_command_response(self, line, success=True):
        line = self._parse_response(line)

        if self.command_queue[0]["callback"]:
            self.command_queue[0]["callback"](line if success else None)
        del self.command_queue[0]
        if len(self.command_queue) > 0:
            self.target.send_command(self.command_queue[0]["command"])

    def _status_callback(self, state):
        pass

    def _parse_response(self, response):
        parts = response.split()
        # Handle K/V pairs
        if "=" in parts[0]:
            resp = {}
            for part in parts:
                k, v = part.split('=')
                resp[k] = v
            return resp
        
        if len(parts) > 1:
            return parts

        return response

    def _packet_callback(self, line):
        line = str(line)
        packet = {}

        if line.startswith("* "):
            self._finish_command_response(line[2:], success=True)
            return

        if line.startswith("- "):
            self._finish_command_response(line[2:], success=False)
            return

        if len(self.feed_fields) == 0:
            return

        self.logfile.write(line)
        parts = line[2:].rstrip().split(',')

        try:
            self.status = dict(zip(self.feed_fields, parts))
            self.status['parse_error'] = False
        except:
            self.status['parse_error'] = True
            return

        if self.data_update_cb:
            self.data_update_cb(self.status)


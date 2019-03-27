import time

from viaems.parser import Parser

class Node():
    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.val = None
        self.auto_refresh = False
        self.last_refresh = None

    def _refresh_cb(self, val):
        self.val = val

    def refresh(self):
        self.model.parser.get(self._refresh_cb, self.name)

    def set_auto_refresh(self, val):
        self.model.set_auto_refresh(self.name, val)
        self.auto_refresh = val

    def value(self):
        return self.val

    def set(self, newvalue):
        pass

class StatusNode(Node):
    pass

class TableNode(Node):

    def _refresh_row(self, row):
        def refresh_point(val):
            if not self.table["values"][row]:
                self.table["values"][row] = []
            self.table["values"][row] = [float(x) for x in val]
            if row == self.table["rows"] - 1:
               # We've finished syncing
               self.last_refresh = time.time()
        cols = ["[{}][{}]".format(row, col) 
                for col in range(self.table["cols"])]
        self.model.parser.get(refresh_point, self.name, cols)

    def _refresh_single_axis(self):
        def refresh_point(val):
            self.table["values"] = [float(x) for x in val]
            self.last_refresh = time.time()
        points = ["[{}]".format(row) 
                for row in range(self.table["rows"])]
        self.model.parser.get(refresh_point, self.name, points)

    def _refresh_info(self, val):
        if not isinstance(val, dict):
            return
        val.update({
            "rowlabels": val["rowlabels"][1:-1].split(","),
            "collabels": val["rowlabels"][1:-1].split(","),
            "rows": int(val["rows"]),
            "cols": int(val["cols"]),
            "naxis": int(val["naxis"]),
            })
        self.table = val
        self.table["values"] = [None] * self.table["rows"]
        for r in range(self.table["rows"]):
            self.table["values"][r] = [0.0] * self.table["cols"]

        if self.table["naxis"] == 2:
            for row in range(self.table["rows"]):
                self._refresh_row(row)
        else:
            self._refresh_single_axis()
                    
    def refresh(self):
        self.model.parser.get(self._refresh_info, self.name)

class Model():
    
    def __init__(self, target, update_cb=None, interrogate_cb=None):
        self.target = target
        self.parser = Parser(target, self._new_data)
        self.update_cb = update_cb
        self.interrogate_cb = interrogate_cb

        self.nodes = {}

    def start_interrogation(self):
        self.parser.list(self._handle_listing, "")

    def _handle_listing(self, resp):
        for node in resp:
            if node.startswith("status."):
                n = StatusNode(node, model=self)
                self.nodes[node] = n
                if node in self.parser.feed_fields:
                    n.auto_refresh = True
                n.refresh()
            elif node.startswith("config.tables."):
                n = TableNode(node, model=self)
                self.nodes[node] = n
                n.refresh()
        self.interrogate_cb()

    def set_auto_refresh(self, node, enabled):
        current = self.parser.feed_fields
        if node in current and not enabled:
            current.remove(node)
        elif node not in current and enabled:
            current.append(node)
        self.parser.set(None, "config.feed", ",".join(current))

    def _new_data(self, data):
        for field in data:
            if field in self.nodes:
                self.nodes[field].val = data[field]
        if self.update_cb:
            self.update_cb(self)


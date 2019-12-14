import json
import math
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
        self.last_refresh = time.time()

    def refresh(self):
        self.model.parser.get(self._refresh_cb, self.name)

    def set_auto_refresh(self, val):
        self.model.set_auto_refresh(self.name, val)
        self.auto_refresh = val

    def value(self):
        return self.val

    def set(self, newvalue):
        self.model.parser.set(None, self.name, newvalue)


class StatusNode(Node):
    
    def set(self, value):
        pass


class TableNode(Node):

    def _refresh_row(self, row):
        def refresh_point(val):
            if not self.table[row]:
                self.table[row] = []
            self.table[row] = [float(x) for x in val]
            if row == self.rows - 1:
                # We've finished syncing
                self.last_refresh = time.time()
        cols = ["[{}][{}]".format(row, col)
                for col in range(self.cols)]
        self.model.parser.get(refresh_point, self.name, cols)

    def _refresh_single_axis(self):
        def refresh_point(val):
            self.table = [float(x) for x in val]
            self.last_refresh = time.time()
        points = ["[{}]".format(col)
                  for col in range(self.cols)]
        self.model.parser.get(refresh_point, self.name, points)

    def set_point(self, row, col, val):
        pos = None
        if self.naxis == 2:
            pos = "[{}][{}]".format(row, col)
            self.table[row][col] = val
            self.table_written[row][col] = True
        else:
            pos = "[{}]".format(col)
            self.table[col] = val
            self.table_written[col] = True
        self.model.parser.set(None, self.name, {pos: val})

    def set(self, value):
        if value == {}:
            return

        self.row_labels = value["rowlabels"]
        self.col_labels = value["collabels"]
        self.rows = value["rows"]
        self.cols = value["cols"]
        self.rowname = value["rowname"]
        self.colname = value["colname"]
        self.naxis = value["naxis"]
        self.table = value["table"]

        self.model.parser.set(None, self.name, {
            "collabels": ",".join(self.col_labels),
            "rows": self.rows,
            "cols": self.cols,
            "colname": self.colname,
            "naxis": self.naxis})
        if self.naxis == 1:
            points = ["[{}]={}".format(col, val) for col, val in enumerate(self.table)]
            self.model.parser.set(None, self.name, points)
        else:
            self.model.parser.set(None, self.name, {
                "rowname": self.rowname,
                "rowlabels": ",".join(self.row_labels)
                })
            for row, data in enumerate(self.table):
                points = ["[{}][{}]={}".format(row, col, val) for col, val in
                        enumerate(data)]
                self.model.parser.set(None, self.name, points)

        

    def get_position_dist(self, row, col, row_v, col_v):
        if self.naxis == 1:
            return 1000
        r_radius = (float(self.row_labels[-1]) - float(self.row_labels[0])) / self.rows
        c_radius = (float(self.col_labels[-1]) - float(self.col_labels[0])) / self.cols

        r_ind_val = float(self.row_labels[row])
        c_ind_val = float(self.col_labels[col])

        r_dist = abs(row_v - r_ind_val) / r_radius
        c_dist = abs(col_v - c_ind_val) / c_radius

        return math.sqrt(math.pow(r_dist, 2) + math.pow(c_dist, 2))


    def _refresh_info(self, val):
        if not isinstance(val, dict):
            self.last_refresh = time.time()
            return
        self.row_labels = val["rowlabels"][1:-1].split(",")
        self.col_labels = val["collabels"][1:-1].split(",")
        self.rows = int(val["rows"])
        self.cols = int(val["cols"])
        self.rowname = val["rowname"]
        self.colname = val["colname"]
        self.naxis = int(val["naxis"])

        if self.naxis == 2:
            self.table = [None] * self.rows
            self.table_written = [None] * self.rows
            for r in range(self.rows):
                self.table[r] = [0.0] * self.cols
                self.table_written[r] = [False] * self.cols
                self._refresh_row(r)
        else:
            self.table = [0.0] * self.cols
            self.table_written = [False] * self.cols
            self._refresh_single_axis()

    def refresh(self):
        self.model.parser.get(self._refresh_info, self.name)

    def value(self):
        """Return a dict representing the full table metadata and data."""
        if not hasattr(self, "table"):
            return {}
        return {
            "rowlabels": self.row_labels,
            "collabels": self.col_labels,
            "rows": self.rows,
            "cols": self.cols,
            "rowname": self.rowname,
            "colname": self.colname,
            "naxis": self.naxis,
            "table": self.table
            }

class Model():

    def __init__(self, target, update_cb=None, enumerate_cb=None, interrogate_cb=None):
        self.target = target
        self.parser = Parser(target, self._new_data)
        self.update_cb = update_cb
        self.interrogate_cb = interrogate_cb
        self.enumerate_cb = enumerate_cb
        self.full_interrogation_completed = False
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
        self.enumerate_cb()

    def set_auto_refresh(self, node, enabled):
        current = self.parser.feed_fields.copy()
        if node in current and not enabled:
            current.remove(node)
        elif node not in current and enabled:
            current.append(node)
        self.parser.set(None, "config.feed", ",".join(current))

    def get_node(self, nodename):
        for name, node in self.nodes.items():
            if nodename == name:
                return node

    def _new_data(self, data):
        for field in data:
            if field in self.nodes:
                self.nodes[field].val = data[field]
        if self.update_cb:
            self.update_cb(data)
        if not self.full_interrogation_completed and len(self.nodes) > 0:
            # Iterate through all nodes, are we done?
            if None not in [x.last_refresh for x in self.nodes.values()]:
                self.full_interrogation_completed = True
                self.interrogate_cb()

    def load_from_file(self, path):
        config = json.load(open(path, "r"))
        for nodename, node in self.nodes.items():
            if isinstance(node, StatusNode):
                continue
            if nodename not in config:
                continue
            if config[nodename] is None:
                continue
            node.set(config[nodename])

    def dump_to_file(self, path):
        results = {}
        for nodename, node in self.nodes.items():
            if isinstance(node, StatusNode):
                continue
            results[nodename] = node.value()

        with open(path, "w") as f:
            json.dump(results, f)


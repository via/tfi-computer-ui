import json
import math
import time

from viaems.parser import Parser


class Node():
    def __init__(self, name, path, model):
        self.model = model
        self.name = name
        self.path = path
        self.val = None
        self.auto_refresh = False
        self.last_refresh = None

    def _refresh_cb(self, msg):
        self.val = msg['response']
        self.last_refresh = time.time()

    def refresh(self):
        self.model.parser.get(self._refresh_cb, self.path)

    def value(self):
        return self.val

    def set(self, newvalue):
        self.model.parser.set(None, self.name, newvalue)


class StatusNode(Node):
    
    def set(self, value):
        pass

class ConfigNode(Node):
    pass
    
class TableNode(Node):

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
            "naxis": self.naxis,
            "rows": self.rows,
            "cols": self.cols,
            })
        self.model.parser.set(None, self.name, {
            "collabels": "[" + ",".join(self.col_labels) + "]",
            "colname": self.colname,
            })
        if self.naxis == 1:
            points = ["[{}]={}".format(col, val) for col, val in enumerate(self.table)]
            self.model.parser.set(None, self.name, points)
        else:
            self.model.parser.set(None, self.name, {
                "rowname": self.rowname,
                "rowlabels": "[" + ",".join(self.row_labels) + "]"
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
        self.col_labels = val["response"]["horizontal-axis"]['values']
        self.row_labels = val["response"]["vertical-axis"]['values']
        self.rows = len(self.row_labels)
        self.cols = len(self.col_labels)
        self.colname = val["response"]["horizontal-axis"]["name"]
        self.rowname = val["response"]["vertical-axis"]["name"]
        self.naxis = val["response"]["num-axis"]
        self.table = val["response"]["data"]

    def refresh(self):
        self.model.parser.get(self._refresh_info, self.path)

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
        self.parser.structure(self._handle_structure)

    def _handle_structure(self, resp):
        for name in resp['response']['tables']:
            n = TableNode(name=name, path=["tables", name], model=self)
            self.nodes[name] = n
            n.refresh()
        self.enumerate_cb()

    def get_node(self, nodename):
        for name, node in self.nodes.items():
            if nodename == name:
                return node

    def _new_data(self, data):
        pass

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


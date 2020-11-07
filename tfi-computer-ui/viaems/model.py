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
        def set_cb(req):
            print(f"Setting {self.path} -> {req}")
        self.model.parser.set(set_cb, self.path, newvalue)

class TableNode(Node):

    def set_point(self, row, col, val):
        path = self.path + ["data"]
        if self.naxis == 2:
            self.table[row][col] = val
#            self.table_written[row][col] = True
            path.append(row)
            path.append(col)
        else:
            self.table[col] = val
#            self.table_written[col] = True
            path.append(row)
        def set_cb(req):
            print(f"Setting {path} -> {req}")
        self.model.parser.set(set_cb, path, float(val))


    def set(self, value):
        if value == {}:
            return

        self._from_dict(value)

        def set_cb(req):
            print(f"Setting {self.path} -> {req}")
        self.model.parser.set(set_cb, self.path, value)

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


    def _from_dict(self, val):
        self.col_labels = val["horizontal-axis"]['values']
        self.row_labels = val["vertical-axis"]['values']
        self.rows = len(self.row_labels)
        self.cols = len(self.col_labels)
        self.colname = val["horizontal-axis"]["name"]
        self.rowname = val["vertical-axis"]["name"]
        self.naxis = val["num-axis"]
        self.table = val["data"]

    def _refresh_info(self, val):
        if not isinstance(val, dict):
            self.last_refresh = time.time()
            return
        self._from_dict(val["response"])

    def refresh(self):
        self.model.parser.get(self._refresh_info, self.path)

    def value(self):
        """Return a dict representing the full table metadata and data."""
        if not hasattr(self, "table"):
            return {}
        return {
            "horizontal-axis": {
                "name": self.colname,
                "values": self.col_labels,
                },
            "vertical-axis": {
                "name": self.rowname,
                "values": self.row_labels,
                },
            "num-axis": self.naxis,
            "data": self.table,
            }

class Model():

    def __init__(self, target, update_cb=None, enumerate_cb=None, interrogate_cb=None):
        self.target = target
        self.parser = Parser(target, self._feed_message)
        self.update_cb = update_cb
        self.interrogate_cb = interrogate_cb
        self.enumerate_cb = enumerate_cb
        self.full_interrogation_completed = False
        self.nodes = {}
        self.status = {}

    def start_interrogation(self):
        self.parser.structure(self._handle_structure)

    def _recurse_structure(self, path, resp):
        if isinstance(resp, list):
            res = []
            for i, k in enumerate(resp):
                res += [self._recurse_structure(path + [i], k)]
            return res
        if isinstance(resp, dict):
            if "_type" in resp.keys():
                if resp["_type"] == "table":
                    name = ".".join([str(x) for x in path])
                    n = TableNode(name=name, path=path, model=self)
                    n.refresh()
                    return n
                else:
#                if resp["_type"] == "uint32" or resp["_type"] == "string" or resp["_type"] == "float":
                    print(resp)
                    name = ".".join([str(x) for x in path])
                    n = Node(name=name, path=path, model=self)
                    n.refresh()
                    return n
            else:
                res = {}
                for k, v in resp.items():
                    res[k] = self._recurse_structure(path + [k], v)
                return res


    def _handle_structure(self, resp):
        self.nodes = self._recurse_structure([], resp['response'])
        self.enumerate_cb()
        self.parser.ping(self._finish_interrogate)

    def _finish_interrogate(self, bleh):
        self.interrogate_cb()

    def get_node(self, nodename):
        for name, node in self.nodes.items():
            if nodename == name:
                return node

    def _feed_message(self, data):
        self.status = data
        self.update_cb(data)

    def _recurse_config_load(self, fileconf, targetconf):
        if isinstance(targetconf, Node):
            targetconf.set(fileconf)
        elif isinstance(targetconf, dict):
            for k, v in targetconf.items():
                if k in fileconf:
                    self._recurse_config_load(fileconf[k], targetconf[k])
        elif isinstance(targetconf, list):
            for i, v in enumerate(targetconf):
                if i <= len(fileconf):
                    self._recurse_config_load(fileconf[i], targetconf[i])

    def load_from_file(self, path):
        config = json.load(open(path, "r"))
        self._recurse_config_load(config, self.nodes)

    def dump_to_file(self, path):

        with open(path, "w") as f:
            json.dump(self.nodes, f, default=lambda x: x.value())


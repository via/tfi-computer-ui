from PySide2.QtWidgets import QApplication
from serialsource import TCPTarget
from viaems.model import Model
import sys

class AutoCalibrate():
    def __init__(self, vetable, tickrate=4000000, interval=0.5):
        self.data_points = []
        self.tickrate = tickrate
        self.interval = interval
        self.last_correction = 0
        self.vetable = vetable
        self.required_nodes = ["status.fueling.ve", 
                               "status.fueling.lambda", 
                               "status.fueling.tipin", 
                               "status.fueling.ete", 
                               "status.sensors.ego",
                               "status.sensors.map",
                               "status.sensors.tps",
                               "status.sensors.brv",
                               "status.current_time",
                               "status.decoder.rpm"]
        self.ranges = {
                "status.sensors.ego": 0.03,
                "status.sensors.map": 5,
                "status.sensors.tps": 3,
                "status.sensors.brv": 0.4,
                "status.fueling.lambda": 0.05,
                "status.fueling.ve": 3,
                }
        self._reset_points(self.required_nodes)

    def _ticks_to_seconds(self, ticks):
        return ticks / self.tickrate

    def _inputs_are_stable(self, nodes=[]):
        for k in nodes:
            if self.maxs[k] - self.mins[k] > self.ranges[k]:
                print("Unstable input {}: {}-{} greater than {}".format(k,
                    self.mins[k], self.maxs[k], self.ranges[k]))
                return False
        return True

    def _average(self, nodes=[]):
        return {
                k: self.sums[k] / self.count
                for k in nodes
                }

    def _reset_points(self, nodes):
        self.mins = {k: 1e100 for k in nodes}
        self.maxs = {k: -1e100 for k in nodes}
        self.sums = {k: 0 for k in nodes}
        self.count = 0

    def _add_point(self, nodes):
        for k, v in nodes.items():
            if v < self.mins[k]:
                self.mins[k] = v
            if v > self.maxs[k]:
                self.maxs[k] = v
            self.sums[k] += v
        self.count += 1

    def write_change(self, rpm, pres, old_ve, new_ve):
        # Are we near a rpm point?
        rpm_point = None
        map_point = None

        for i, r in enumerate(self.vetable.col_labels):
            if abs(float(r) - rpm) < 200:
                rpm_point = i
                break
        for i, m in enumerate(self.vetable.row_labels):
            if abs(float(m) - pres) < 3:
                map_point = i
                break

        if rpm_point and map_point:
            actual = round(old_ve + (new_ve - old_ve) * 0.25, 1)
            print ("rpm = {} map = {}   {} -> {} ({})".format(
                rpm, pres, old_ve, new_ve, actual))
            if actual < 3 or actual > 100:
                print("ABORT")
                sys.exit(1)
            self.vetable.set_point(map_point, rpm_point, actual)
        else:
            print("{} / {} not close enough to load point".format(rpm, pres))

    def update(self, nodes):
        points = {
            k: float(v) for k, v in nodes.items() if k in self.required_nodes
            }

        curtime = self._ticks_to_seconds(points["status.current_time"])
        self._add_point(points)

        if curtime - self.last_correction > self.interval:
            if self._inputs_are_stable(["status.sensors.ego",
                                   "status.sensors.map",
                                   "status.sensors.tps",
                                   "status.sensors.brv",
                                   "status.fueling.lambda",
                                   "status.fueling.ve"]):
                averages = self._average([
                            "status.sensors.ego",
                            "status.sensors.map",
                            "status.decoder.rpm",
                            "status.fueling.lambda",
                            "status.fueling.ve"])

                try:
                    new_ve = self.ve_correction(averages['status.fueling.ve'],
                        averages['status.fueling.lambda'], averages['status.sensors.ego'])
                    self.write_change(averages['status.decoder.rpm'],
                            averages['status.sensors.map'],
                            averages['status.fueling.ve'], 
                            new_ve)
                except:
                    pass

            self.last_correction = curtime
            self._reset_points(self.required_nodes)
            
    def ve_correction(self, old_ve, lmbda, ego):
        return old_ve * (ego / lmbda)


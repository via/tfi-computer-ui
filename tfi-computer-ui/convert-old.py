#!/usr/bin/env python
import sys
import json

def convert_table_name(name):
    if name == "boost_control":
        return "boost-control"
    if name == "commanded_lambda":
        return "lambda"
    if name == "dwell":
        return "dwell"
    if name == "engine_temp_enrich":
        return "temp-enrich"
    if name == "injector_dead_time":
        return "injector_dead_time"
    if name == "timing":
        return "timing"
    if name == "tipin_enrich_amount":
        return "tipin-amount"
    if name == "tipin_enrich_duration":
        return "tipin-time"
    if name == "ve":
        return "ve"
    return None

def convert_table(value):
    table = {
            "horizontal-axis": {
                "name": value["colname"],
                "values": [float(x) for x in value["collabels"] if x != ""],
                },
            "vertical-axis": {
                "name": value["rowname"],
                "values": [float(x) for x in value["rowlabels"] if x != ""],
                },
            "num-axis": value["naxis"],
            "data": value["table"],
            }
    return table



source = json.load(open(sys.argv[1]))

result = {
    "decoder": {
        "offset": float(source["config.decoder.offset"]),
        "type": source["config.decoder.trigger"],
        "max-variance": float(source["config.decoder.max_variance"]),
        "min-rpm": float(source["config.decoder.min_rpm"]),
        },
    "fueling": {
        "injector-cc": float(source["config.fueling.injector_cc"]),
        "cylinder-cc": float(source["config.fueling.cyclinder_cc"]),
        "fuel-stoich-ratio": float(source["config.fueling.fuel_stoich_ratio"]),
        "injections-per-cycle": int(source["config.fueling.injections_per_cycle"]),
        "fuel-pump-pin": int(source["config.fueling.fuel_pump_pin"]),
        "crank-enrich": {
            "crank-rpm": float(source["config.fueling.crank_enrich_rpm"]),
            "crank-temp": float(source["config.fueling.crank_enrich_temp"]),
            "enrich-amt": float(source["config.fueling.crank_enrich_amt"]),
            },
        },
    "ignition": {
        "min-fire-time": int(source["config.ignition.min_fire_time_us"]),
        },
    "tables": {}
    }

for item, value in source.items():
    if item.startswith("config.tables."):
        if value == {}:
            continue
        name = item[14:]
        newname = convert_table_name(name)
        if newname:
            result["tables"][newname] = convert_table(value)


print(json.dumps(result))

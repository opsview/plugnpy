# check_cpu.py - An example Opsview plugin written with plugnpy
from __future__ import print_function

import plugnpy
import psutil


def get_cpu_usage():
    """Returns CPU Usage %"""
    return psutil.cpu_percent(interval=2.0)


def get_args():
    """Gets passed arguments using plugnpy.Parser.
    This will exit 3 (UNKNOWN) if an input is missing"""
    parser = plugnpy.Parser(description="Monitors CPU Usage", copyright="Example Copyright 2017-2018")
    parser.add_argument('-w', '--warning', help="Warning percentage")
    parser.add_argument('-c', '--critical', help="Critical percentage")
    parser.add_argument('-d', '--debug', action="store_true", help="Debug mode")

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    check = plugnpy.Check()  # Instantiate Check object
    # Add Metric
    check.add_metric('cpu_usage', get_cpu_usage(), '%', args.warning, args.critical, display_name="CPU Usage",
                     msg_fmt="{name} at {value}{unit}")
    # Run Check (handles printing and exit codes)
    check.final()

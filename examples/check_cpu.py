#!/usr/bin/env python3
# Copyright (C) 2003-2021 Opsview Limited. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    parser = plugnpy.Parser(description="Monitors CPU Usage", copystr="Example Copyright 2017-2019")
    parser.add_argument('-w', '--warning', help="Warning percentage")
    parser.add_argument('-c', '--critical', help="Critical percentage")
    parser.add_argument('-d', '--debug', action="store_true", help="Debug mode")

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    check = plugnpy.Check()  # Instantiate Check object
    # Add Metric
    check.add_metric('cpu_usage', get_cpu_usage(), '%', args.warning, args.critical, display_name="CPU Usage",
                     display_format="{name} at {value}{unit}")
    # Run Check (handles printing and exit codes)
    check.final()

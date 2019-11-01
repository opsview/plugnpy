#!/opt/opsview/python/bin/python
# Copyright (C) 2003-2019 Opsview Limited. All rights reserved
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

import plugnpy
import psutil


def get_mem_usage():
    return psutil.virtual_memory()


def get_swap_usage():
    return psutil.swap_memory()


def get_args():
    """Gets passed arguments using plugnpy.Parser.
    This will exit 3 (UNKNOWN) if an input is missing"""
    parser = plugnpy.Parser(description="Monitors Memory Utilisation")
    parser.set_copyright("Example Copyright 2017-2019")
    parser.add_argument('-m', '--mode', help="Mode for the plugin to run (the service check)", required=True,
                        choices=['virtual_memory', 'swap_usage'])
    parser.add_argument('-w', '--warning', help="The warning threshold")
    parser.add_argument('-c', '--critical', help="The critical threshold")
    parser.add_argument('-d', '--debug', action="store_true", help="Debug mode", default=False)

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    check = plugnpy.Check()  # Instantiate Check object

    if args.mode == "virtual_memory":
        memory_usage = get_mem_usage()
        # Add Metrics to Check Object
        check.add_metric('mem_utilisation', memory_usage.percent, '%', None, None,
                         display_name="Memory Utilisation", display_format="{name} at {value}{unit}")
        check.add_metric('mem_buffer', memory_usage.buffers, 'B', args.warning, args.critical,
                         display_name="Memory Buffer", convert_metric=True)
        check.add_metric('mem_cache', memory_usage.cached, 'B', '', '',
                         display_name="Memory Cache", convert_metric=True)
        check.add_metric('mem_free', memory_usage.free, 'B', '', '',
                         convert_metric=True, display_in_summary=False)
        check.add_metric('test', None, '', '', '',
                         display_format="An example of adding a dummy metric to add another line",
                         display_in_perf=False)
    elif args.mode == "swap_usage":
        swap_usage = get_swap_usage()
        check.add_metric('swap_utilisation', swap_usage.percent, '%', args.warning, args.critical)
        check.add_metric('swap_in', swap_usage.sin, 'B', '', '', convert_metric=True)
        check.add_metric('swap_out', swap_usage.sout, 'B', '', '', convert_metric=True)

    check.final()

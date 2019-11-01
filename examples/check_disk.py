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


def get_disk_usage():
    return psutil.disk_usage('/')


def get_args():
    """Gets passed arguments using plugnpy.Parser.
    This will exit 3 (UNKNOWN) if an input is missing"""
    parser = plugnpy.Parser(description="Monitors Disk Utilisation")
    parser.set_copyright("Example Copyright 2017-2019")
    parser.add_argument('-m', '--mode', help="Mode for the plugin to run (the service check)", required=True,
                        choices=['disk_usage'])
    parser.add_argument('-w', '--warning', help="The warning threshold")
    parser.add_argument('-c', '--critical', help="The critical threshold")
    parser.add_argument('-d', '--debug', action="store_true", help="Debug mode", default=False)
    parser.add_argument('--no-cachemanager', action="store_true", help="Debug mode", default=False)

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    check = plugnpy.Check()

    if args.mode == "disk_usage":
        # get data via the cache manager, caches the data if it does not exist in the cache manager
        disk_usage = plugnpy.CacheManagerUtils.get_via_cachemanager(args.no_cachemanager, args.mode, get_disk_usage)
        check.add_metric('disk_usage', disk_usage.percent, '%', args.warning, args.critical)

    check.final()

#!/usr/bin/python
#
# Copyright 2012 Sonya Huang
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
#

# This is a script that converts world continent and country boundary
# shapefiles into a format that can be plotted with GNUPlot.
#
# This has used specifically with the Continents and Country boundaries
# (generalized) shapefiles from the ESRI Data and Maps (2010) collection,
# which should be available to users with an ESRI license.
#

# TODO: reorganize files so meanings of top level directories are
# consistent, perhaps by country:
#
# usa
# tw
# cn
# uk
# jp
# ca (if feasible)
# wiod
#


import sys
# usa
from usa.parsers import iobench, ioannual, iobench_codes, pcebridge, eia_annual
from usa.postparsers import iobench_transactions, eiasupp, distribute_btus
# curated countries
import ca.parser, cn.parser, jp.parser, tw.parser, uk.parser
# wiod
import wiod.parser, wiod.parsers.un, wiod.parsers.world_supplement, wiod.parsers.eia

parse_options = {
    "usa": {
        "iobench": {"parser": iobench},
        "ioannual": {"parser": ioannual},
        "iobench_codes": {"parser": iobench_codes},
        "eia_annual": {"parser": eia_annual},
        "pcebridge": {"parser": pcebridge},
        },
    "countries": {
        "ca": {"parser": ca.parser},
        "cn": {"parser": cn.parser},
        "tw": {"parser": tw.parser},
        "uk": {"parser": uk.parser},
        "jp": {"parser": jp.parser},
        },
    "wiod": {
        "wiod": {"parser": wiod.parser},
        "un": {"parser": wiod.parsers.un},
        "world_supplement": {"parser": wiod.parsers.world_supplement},
        "eia_world": {"parser": wiod.parsers.eia},
        },
    }

if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg == "all":
        for (key, options) in parse_options.items():
            for (subkey, suboptions) in options.items():
                suboptions["parse"] = "y"
    elif arg in parse_options:
        for (subkey, suboptions) in parse_options[arg].items():
            suboptions["parse"] = "y"
    else:
        for (key, options) in parse_options.items():
            if arg in options:
                options[arg]["parse"] = "y"
else:
    # read input
    for (key, options) in parse_options.items():
        descend = input("parse items from %s? " % key)
        if descend == "y":
            for (subkey, suboptions) in options.items():
                suboptions["parse"] = input("parse %s? " % subkey)

# follow directions from input
for (key, options) in parse_options.items():
    for (subkey, suboptions) in options.items():
        if "parse" in suboptions and suboptions["parse"] == "y":
            suboptions["parser"].doparse()

            # manually take care of dependencies for now
            # (scripts that depend on the parser, not vice versa)
            if subkey == "iobench":
                iobench_transactions.dopostparse()
    
            if subkey in ("iobench", "iobench_codes", "eia_annual"):
                eiasupp.dopostparse()
                distribute_btus.dopostparse()


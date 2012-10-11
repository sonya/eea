#!/usr/bin/python3
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

import csv, re

from common import fileutils
from common.dbhelper import SQLTable
from wiod import config

def doparse():
    table = SQLTable("%s.mdg_emissions" % config.UN_SCHEMA,
                     ["country", "year", "value"],
                     ["char(3)", "int", "float"]).create()
    table.truncate()

    country_dict = dict((v, k) for k, v in config.countries.items())
    country_dict["Slovakia"] = "SVK"
    country_dict["Russian Federation"] = "RUS"

    year_pat = re.compile("[12]\d{3}")

    path = fileutils.getdatapath("mdg_emissions.csv", "un")
    with open(path, "r") as fh:
        csvf = csv.reader(fh)
        header = next(csvf)
        header_index = {}

        years = []
        for i in range(len(header)):
            header_index[header[i]] = i
            if year_pat.match(header[i]):
                years.append(header[i])

        for row in csvf:
            if len(row) <= header_index["SeriesCode"] or \
                    row[header_index["SeriesCode"]] != "749":
                continue
            country_name = row[header_index["Country"]]
            if country_name not in country_dict:
                continue
            country = country_dict[country_name]
            for year in years:
                value = row[header_index[year]].strip()
                if len(value):
                    table.insert([country, int(year), float(value)])
                
                


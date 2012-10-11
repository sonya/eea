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

import xlrd
from common import fileutils
from common.dbhelper import SQLTable
from wiod import config

def doparse():
    country_dict = dict((v, k) for k, v in config.countries.items())
    country_dict["Slovakia"] = "SVK"

    sources = ["total", "nuclear", "thermal", "renewable",
               "geothermal", "solar", "wind", "biomass"]
    measurements = ["capacity", "consumption"]

    tablename = "%s.world_power" % ("eia")
    table = SQLTable(
        tablename,
        ["year", "country", "source", "units", "value"],
        ["int", "char(3)", "varchar(15)", "varchar(4)", "float"])
    table.create()
    table.truncate()

    for source in sources:
        for measure in measurements:
            if measure == "consumption":
                if source in ("geothermal", "solar", "wind", "biomass"):
                    continue

                units = "bkWh"
            elif measure == "capacity":
                units = "MkW"

            filename = source + "_" + measure + ".xls"
            path = fileutils.getcache(filename, "eia")
            wb = xlrd.open_workbook(path)
            sheet = wb.sheet_by_index(0)
            header = None
            for i in range(sheet.nrows):
                row = sheet.row_values(i)
                if header is None:
                    if len(row) > 2 and type(row[2]) is float:
                        header = []
                        for cell in row:
                            if type(cell) is float:
                                header.append(int(cell))
                            else:
                                header.append(None)
                        header_len = len(header)
                elif len(row) > 2:
                    country_name = row[0]
                    if country_name in country_dict:
                        country = country_dict[country_name]
                        for i in range(2, header_len):
                            value = row[i]
                            year = header[i]
                            if type(value) is float and value > 0:
                                table.insert(
                                    [year, country, source, units, value])
                            


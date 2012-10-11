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
from usa import dbsetup

from usa import config
from common import fileutils
from common.dbhelper import SQLTable

def doparse():
    for year in (1972, 1977):
        table = SQLTable("%s.codes_%d" % (config.IO_SCHEMA, year),
                         ["code", "description"],
                         ["char(6)", "text"]).create()
        table.truncate()
        filepath = fileutils.getdatapath("io_sectors_%d.csv" % year, "usa")
        with open(filepath, "r") as fh:
            csvf = csv.reader(fh)
            for row in csvf:
                if len(row) and len(row[0]):
                    table.insert([row[0], row[1]])

        if year == 1972:
            # this is stated in the rtf file for both 1972 and 1977
            # but this code never appears in 1977, the documentation
            # was probably not properly updated
            table.insert(["870000", "total value added"])

    writer = dbsetup.IOCodeTableWriter()
    
    writer.set_year(1982, "Io-code.doc")
    with open(writer.get_filename()) as f:
        for line in f:
            if len(line) > 8:
                code = line[:6]
                desc = line[8:]
                writer.writerow(code, desc)
    
    writer.set_year(1987, "SIC-IO.DOC")
    with open(writer.get_filename()) as f:
        pattern = re.compile('\s*(\d{1,2})\.(\d{4})\s+([^0-9\*]+)')
        for line in f:
            match = pattern.match(line)
            if match:
                code = match.group(1).rjust(2, '0') + match.group(2)
                desc = match.group(3).strip('(. \r\n')
                writer.writerow(code, desc)
    
    writer.set_year(1992, "io-code.txt")
    with open(writer.get_filename()) as f:
        for line in f:
            if len(line) > 7:
                code = line[:6]
                desc = line[7:]
                writer.writerow(code, desc)
    
    writer.set_year(1997, "IO-CodeDetail.txt")
    with open(writer.get_filename()) as f:
        csvf = csv.reader(f)
        for row in csvf:
            if len(row) == 2:
                writer.writerow(row[0], row[1])
    
    writer.set_year(2002, "REV_NAICSUseDetail 4-24-08.txt")
    with open(writer.get_filename()) as f:
        valid_line = re.compile("[A-Z0-9]{6}\s")
        line = f.readline().strip().replace("GasPipeVal", "GasPipe   ")
        fields = dbsetup.get_header_locations(dbsetup.replace_tabs(line))
        codemap = {}
        for line in f:
            if valid_line.match(line):
                row = dbsetup.get_values_for_fields(
                    dbsetup.replace_tabs(line), fields)
                codemap[row["Commodity"]] = row["CommodityDescription"]
                codemap[row["Industry"]] = row["IndustryDescription"]
    
        for (code, desc) in codemap.items():
            writer.writerow(code, desc)
    
    writer.flush()

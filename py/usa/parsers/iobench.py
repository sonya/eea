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
from usa import dbsetup
from usa.dbsetup import IOTableStateTracker

## utilities for 2002 tables

def doparse():
    tracker = IOTableStateTracker()
    
    #tracker.create_simple_transaction_table(
    #    "1947", "1947/1947 Transactions 85-level Data.txt")
    #tracker.create_simple_transaction_table(
    #    "1958", "1958/1958 Transactions 85-level Data.txt")
    #tracker.create_simple_transaction_table(
    #    "1963", "1963/1963 Transactions 367-level Data.txt")
    #tracker.create_simple_transaction_table(
    #    "1967", "1967/1967 Transactions 484-level Data.txt", 1000)
    
    tracker.create_simple_make_use(
        "1972", "1972/1972 Transactions 496-level Data.txt", 1000)
    tracker.create_simple_make_use(
        "1977", "1977/1977 Transactions 537-level Data.txt", 1000)

    tracker.create_make_table("1982")
    tracker.create_use_table("1982", True)
    with open(fileutils.getcache("82-6DT.DAT", "1982"), "r") as f:
        for line in f:
            if len(line) >= 112: # right-aligned
                input_ind = line[0:6]
                output_ind = line[6:12]
                use_dollars = line[12:22]
                make_dollars = line[22:32]
                tracker.insert_make(input_ind, output_ind, make_dollars, 100)
                tracker.insert_use(input_ind, output_ind, use_dollars,
                                   {"margins": line[32:42],
                                    "rail_margin": line[42:52],
                                    "truck_margin": line[52:62],
                                    "water_margin": line[62:72],
                                    "air_margin": line[72:82],
                                    "pipe_margin": line[82:92],
                                    "wholesale_margin": line[92:102],
                                    "retail_margin": line[102:112]},
                                    100) # this year dollars are in 100,000s
    
    tracker.create_make_table("1987")
    with open(fileutils.getcache("TBL1-87.DAT", "1987"), "r") as f:
        for line in f:
            if len(line) >= 24: # right-aligned
                tracker.insert_make(
                    line[0:6], line[7:13], line[15:24], 1000)
    
    tracker.create_use_table("1987", True)
    with open(fileutils.getcache("TBL2-87.DAT", "1987"), "r") as f:
        for line in f:
            if len(line) >= 96: # right-aligned
                input_ind = line[0:6]
                output_ind = line[7:13]
                use_dollars = line[15:24].strip()
                tracker.insert_use(
                    input_ind, output_ind, use_dollars,
                    {"margins": line[24:33],
                     "rail_margin": line[33:42],
                     "truck_margin": line[42:51],
                     "water_margin": line[51:60],
                     "air_margin": line[60:69],
                     "pipe_margin": line[69:78],
                     "wholesale_margin": line[78:87],
                     "retail_margin": line[87:96]},
                    1000)
    
    # the documentation for 1992 appears very incorrect unless there
    # is some way for tabs to be 7 characters for two fields and 9 
    # characters for the rest of the fields. we will just assume the
    # file is an ordinary tab-delimited file.
    
    tracker.create_make_table("1992")
    with open(fileutils.getcache("IOMAKE.TXT", "1992"), "r") as f:
        for line in f:
            row = line.split("\t")
            if len(row) == 4:
                tracker.insert_make(row[0], row[1], row[3], 1000)
    
    tracker.create_use_table("1992", True)
    with open(fileutils.getcache("IOUSE.TXT", "1992"), "r") as f:
        for line in f:
            row = line.split("\t")
            if len(row) == 13:
                tracker.insert_use(
                    row[0], row[1], row[3],
                    {"margins": row[4],
                     "rail_margin": row[5],
                     "truck_margin": row[6],
                     "water_margin": row[7],
                     "air_margin": row[8],
                     "pipe_margin": row[9],
                     "gaspipe_margin": row[10],
                     "wholesale_margin": row[11],
                     "retail_margin": line[12]},
                    1000)
    
    tracker.create_make_table("1997")
    with open(fileutils.getcache("NAICSMakeDetail.txt", "1997")) as f:
        csvf = csv.reader(f)
        for row in csvf:
            if len(row) == 4:
                tracker.insert_make(row[0], row[1], row[3], 1000)    
    
    tracker.create_use_table("1997", True)
    with open(fileutils.getcache("NAICSUseDetail.txt", "1997")) as f:
        csvf = csv.reader(f)
        for row in csvf:
            if len(row) == 15:
                tracker.insert_use(
                    row[0], row[1], row[4],
                    {"margins": row[5],
                     "rail_margin": row[6],
                     "truck_margin": row[7],
                     "water_margin": row[8],
                     "air_margin": row[9],
                     "pipe_margin": row[10],
                     "gaspipe_margin": row[11],
                     "wholesale_margin": row[12],
                     "retail_margin": row[13]},
                    1000)
    
    # contrary to the format documentation, revised 2002 tables are
    # delimited with mixed tabs and spaces. they appear fixed width with
    # 8-char tabs. field names fortunately do not contain whitespace.
    valid_line = re.compile("[A-Z0-9]{6}\s")
    
    tracker.create_make_table("2002")
    with open(fileutils.getcache("REV_NAICSMakeDetail 4-24-08.txt", "2002")) as f:
        fields = dbsetup.get_header_locations(
                     dbsetup.replace_tabs(f.readline().strip()))
        for line in f:
            if valid_line.match(line):
                row = dbsetup.get_values_for_fields(dbsetup.replace_tabs(line), fields)
                tracker.insert_make(
                    row["Industry"], row["Commodity"], row["ProVal"], 1000)
    
    tracker.create_use_table("2002", True)
    with open(fileutils.getcache("REV_NAICSUseDetail 4-24-08.txt", "2002")) as f:
        # cheat here because it's not worth the trouble to deal with
        # lack of whitespace between two fields (GasPipeVal and WhsVal)
        line = f.readline().strip().replace("GasPipeVal", "GasPipe   ")
        fields = dbsetup.get_header_locations(dbsetup.replace_tabs(line))
        for line in f:
            if valid_line.match(line):
                row = dbsetup.get_values_for_fields(
                    dbsetup.replace_tabs(line), fields)
                tracker.insert_use(
                    row["Commodity"], row["Industry"], row["ProVal"],
                    {"margins": row["StripMar"],
                     "rail_margin": row["RailVal"],
                     "truck_margin": row["TruckVal"],
                     "water_margin": row["WaterVal"],
                     "air_margin": row["AirVal"],
                     "pipe_margin": row["PipeVal"],
                     "gaspipe_margin": row["GasPipe"],
                     "wholesale_margin": row["WhsVal"],
                     "retail_margin": row["RetVal"]},
                    1000)
    
    tracker.flush()

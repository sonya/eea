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

import os
from usa import bea, config
from common.dbhelper import SQLTable
import common.config
from common import fileutils
from common.dbconnect import db

# all these functions are only here to deal with bea 2002 data

def replace_tabs(line):
    found = line.find("\t")
    while found != -1:
        tabsize = -(found % -8)
        if tabsize == 0:
            tabsize = 8
        line = line[0:found] + " "*tabsize + line[found+1:]
        found = line.find("\t")
    return line

def get_header_locations(line):
    fields = {}
    lastindex = 0
    lastfield = None
    for field in line.split():
        thisindex = line.find(field)
        if lastfield is not None:
            fields[lastfield] = (lastindex, thisindex)
        lastfield = field
        lastindex = thisindex
    fields[lastfield] = (lastindex, len(line))
    return fields

def get_values_for_fields(line, fields):
    result = {}
    for field, (start, end) in fields.items():
        result[field] = line[start:end]
    return result

class TableStateTracker:

    def __init__(self):
        self.xact = None
        self.table = None

    def drop_table(self, tablename, cascade=False):
        self.table = SQLTable(tablename)
        self.table.drop(cascade)

    def create_table(self, tablename, cols, coltypes, cascade=False):
        self.flush()
        self.table = SQLTable(tablename, cols, coltypes)
        self.table.drop(cascade)
        self.table.create()
        self.warmup()

    def insert_row(self, values):
        self.table.insert(values)
        #self.current_stmt(*values)

    def warmup(self):
        self.xact = db.xact(mode="READ WRITE")
        self.xact.begin()

    def flush(self):
        if self.xact is not None:
            self.xact.commit()

# call warmup and flush manually after registering all tables
class MultiTableStateTracker(TableStateTracker):
    def __init__(self):
        TableStateTracker.__init__(self)
        self.tables = {}

    def create_table(self, tablename, cols, coltypes, cascade=False):
        table = SQLTable(tablename, cols, coltypes)
        table.drop(cascade)
        table.create()
        self.tables[tablename] = table

    def insert_row(self, tablename, values):
        self.tables[tablename].insert(values)

    def flush(self):
        TableStateTracker.flush(self)
        self.tables = {}

class IOTableStateTracker(TableStateTracker):

    def __init__(self):
        TableStateTracker.__init__(self)
        
        self.make_table = None
        self.use_table = None

        self.make_insert_count = 0
        self.use_insert_count = 0

    def flush(self):
        TableStateTracker.flush(self)

        if self.make_insert_count:
            print("%d rows inserted to make table"
                  % self.make_insert_count)
            self.make_insert_count = 0
        if self.use_insert_count:
            print("%d rows inserted to use table"
                  % self.use_insert_count)
            self.use_insert_count = 0

    def create_make_table(self, year):
        print("creating make table for %s..." % year)

        tablename = "%s.make_%s" % (config.IO_SCHEMA, year)
        self.make_table = SQLTable(tablename,
                          ["industry", "commodity", "thousands"],
                          ["varchar(6)", "varchar(6)", "bigint"])
        self.make_table.create()
        self.make_table.truncate()

    def create_use_table(self, year, has_margins=False):
        print("creating use table for %s..." % year)

        cols = ["commodity", "industry", "thousands"]
        coltypes = ["varchar(6)", "varchar(6)", "bigint"]
        if has_margins:
            for field in bea.use_table_margins:
                cols.append(field)
                coltypes.append("int")

        tablename = "%s.use_%s" % (config.IO_SCHEMA, year)
        self.use_table = SQLTable(tablename, cols, coltypes)
        self.use_table.create()
        self.use_table.truncate()

    def insert_make(self, indus, commod, makeval, factor=1):
        value = float(makeval) * factor
        if (value != 0):
            self.make_table.insert([indus.strip(),commod.strip(), int(value)])
            self.make_insert_count += 1

    def insert_use(self, commod, indus, useval,
                   margins={}, factor=1):

        useval = float(useval) * factor
        nonzero = useval

        values = [commod.strip(), indus.strip(), int(useval)]
        if len(margins) > 0:
            for margin_field in bea.use_table_margins:
                value = 0
                if margin_field in margins:
                    value = float(margins[margin_field]) * factor
                    if value:
                        nonzero += value
                values.append(value)

        if nonzero != 0:
            self.use_table.insert(values)
            self.use_insert_count += 1

    # this is for years with no distinction between
    # make and use tables
    def create_simple_transaction_table(self, year, filename, factor=1):
        print("creating transations table for %s..." % year)

        tablename = "%s.transactions_%s" % (config.IO_SCHEMA, year)
        xtable = SQLTable(tablename,
                          ["producer", "consumer", "thousands"],
                          ["varchar(6)", "varchar(6)", "int"])
        xtable.create()
        xtable.truncate()

        insert_count = 0
        with open(fileutils.getcache(filename), "r") as f:
            for line in f:
                cols = line.split()
                if len(cols) >= 3:
                    value = float(cols[2]) * factor
                    if (value != 0):
                        xtable.insert([cols[0], cols[1], int(value)])
                        insert_count += 1

        print ("%d rows inserted" % insert_count)

    # this is for years that have make and use but no margins
    def create_simple_make_use(self, year, filename, factor=1):
        self.create_make_table(year)
        self.create_use_table(year, has_margins=False)
        with open(fileutils.getcache(filename), "r") as f:
            for line in f:
                cols = line.split()
                if len(cols) == 4:
                    input_ind = cols[0]    # comm consumed (producing ind)
                    output_ind = cols[1]   # consuming ind (comm produced) 
                    use_dollars = cols[2]  # use in producers' prices
                    make_dollars = cols[3] # make in producers' prices

                self.insert_make(input_ind, output_ind, make_dollars, factor)
                self.insert_use(commod=input_ind, indus=output_ind,
                                useval=use_dollars, factor=factor)

class IOCodeTableWriter(TableStateTracker):

    def __init__(self):
        TableStateTracker.__init__(self)
        self.filename = None
        self.table = None
        self.codes = {}

    def set_year(self, year, filename):
        self.flush()
        self.year = year
        self.filename = filename
        tablename = config.IO_SCHEMA + ".codes_" + str(year)
        self.create_table(tablename,
                          ["code", "description"],
                          ["char(6)", "text"])

    def get_filename(self):
        filepath = os.path.join(str(self.year), self.filename)
        return fileutils.getcache(filepath)

    def flush(self):
        insert_count = len(self.codes)
        for (code, desc) in self.codes.items():
            self.table.insert([code, desc])
        TableStateTracker.flush(self)
        self.codes = {}
        if insert_count:
            print("%d rows inserted for year %s"
                  % (insert_count, str(self.year)))

    def writerow(self, code, desc):
        self.codes[code.strip()] = desc.strip()



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

import codecs, csv
import common.config
from common.dbconnect import db

class SQLTable:

    def __init__(self, name, colnames=[], coltypes=[]):
        self.name = name
        self.colnames = colnames
        self.coltypes = coltypes

    def runsql(self, sql):
        if common.config.DEBUG_MODE:
            print(sql)
        db.execute(sql)

    def drop(self, cascade=False):
        if cascade:
            sql = "DROP TABLE IF EXISTS %s CASCADE" % self.name
        else:
            sql = "DROP TABLE IF EXISTS %s" % self.name
        self.runsql(sql)

    def truncate(self):
        sql = "TRUNCATE TABLE %s" % self.name
        self.runsql(sql)

    def create(self):
        # convert field types to lowercase for checking in insert()
        colspec = ["%s %s" % (fname, ftype.lower()) for (fname, ftype) \
                       in zip(self.colnames, self.coltypes)]
        sql = "CREATE TABLE IF NOT EXISTS %s (\n    %s\n)" \
            % (self.name, ",\n    ".join(colspec))
        self.runsql(sql)
        self.prepare()
        return self

    def prepare(self):
        placeholders = ["$%d" % (i+1) for i in range(len(self.colnames))]
        self.stmt = db.prepare(
            "INSERT INTO %s VALUES ( %s )"
            % (self.name, ", ".join(placeholders)))

    def insert(self, values):
        clean_values = []
        for (value, vtype) in zip(values, self.coltypes):
            if vtype.startswith("int"):
                if type(value) is str and len(value.strip()) == 0:
                    clean_values.append(None)
                else:
                    clean_values.append(int(value))
            elif vtype.startswith("float"):
                if value is None or \
                        (type(value) is str and len(value.strip()) == 0):
                    clean_values.append(None)
                else:
                    clean_values.append(float(value))
            else:
                clean_values.append(value)

        self.stmt(*clean_values)

    def getall(self, conditions=[], args=[]):
        if len(conditions):
            whereclause = " AND ".join(conditions)
            sql = "SELECT * FROM %s WHERE %s" % (self.name, whereclause)
        else:
            sql = "SELECT * FROM %s" % self.name

        stmt = db.prepare(sql)

        if len(args):
            return stmt(*args)

        return stmt()

class CSVTable:

    def __init__(self, filename, has_header=False, encoding=None):
        self.filename = filename
        self.has_header = has_header
        self.colnames = None
        self.reverse_colnames = None
        self.sqltable = None
        self.encoding = encoding

    def create_sql_table(self, tablename, colnames, coltypes):
        self.sqltable = SQLTable(tablename, colnames, coltypes)

    # colnames: array of field names from file header
    def set_colnames(self, colnames):
        self.colnames = colnames
        self.reverse_colnames = {}
        for i in range(len(colnames)):
            self.reverse_colnames[colnames[i]] = i

    # col_map: mapping between sql columns and csv columns/indices
    # col_funcs: function to perform on certain column
    # skip_callback: function called on row to determine if present row
    #     should be skipped
    def parse_to_sql(self, col_map=None, col_funcs={},
                     skip_callback=None, cascade=False, append=False):

        if not append:
            self.sqltable.drop(cascade)
            self.sqltable.create()
        else:
            self.sqltable.prepare()

        # for non-utf8 encodings, create file handle using
        # codecs.open(filename, mode, encoding)
        # http://stackoverflow.com/a/5429346
        if self.encoding is None:
            openfunc = open
            openargs = (self.filename, "r")
        else:
            openfunc = codecs.open
            openargs = (self.filename, "r", self.encoding)

        with openfunc(*openargs) as fh:
            with db.xact(mode="READ WRITE") as xact:
                xact.begin()

                csvfile = csv.reader(fh)
                if self.has_header:
                    header = next(csvfile)
                    self.set_colnames(header)
    
                column_order = []
                rev_col_map = {}
                for sql_col in self.sqltable.colnames:
                    if col_map is None:
                        col_id = len(column_order)
                        column_order.append(col_id)
                        rev_col_map[col_id] = sql_col
                    elif sql_col in col_map:
                        column_order.append(col_map[sql_col])
                        rev_col_map[col_map[sql_col]] = sql_col
                    else:
                        column_order.append(None)

                for row in csvfile:
                    if skip_callback is not None and skip_callback(row):
                        continue
                    insert_values = []
                    for col_id in column_order:
                        if col_id is None:
                            insert_values.append(None)
                        else:
                            if self.colnames is not None:
                                value = row[self.reverse_colnames[col_id]]
                            else:
                                value = row[col_id]
    
                            if col_id in col_funcs:
                                func = col_funcs[col_id]
                                value = func(value)
                            elif col_id in rev_col_map and \
                                    rev_col_map[col_id] in col_funcs:
                                func = col_funcs[rev_col_map[col_id]]
                                value = func(value)
    
                            insert_values.append(value)
    
                    self.sqltable.insert(insert_values)

                xact.commit()


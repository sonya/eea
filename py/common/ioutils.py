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

from scipy import sparse

from common import regexes, sqlhelper
from common.dbconnect import db
from common.dbhelper import SQLTable
from common.matrixutils import NamedMatrix, TotalOutputMatrix, FinalDemandMatrix

class IOMatrixGenerator:

    def __init__(self, transaction_table,
                 from_sector_name="from_sector",
                 to_sector_name="to_sector",
                 value_column_name="value",
                 final_demand_sectors=[],
                 universal_conditions=[]):

        self.strings = {
            "from_sector": from_sector_name,
            "to_sector": to_sector_name,
            "value_column": value_column_name,
            }

        self.set_table(transaction_table)
        self.set_fd_sectors(final_demand_sectors)

        self.pce_col = None
        self.fd_col = None

        self.condition_args = ()
        self.universal_conditions = universal_conditions
        self.harmonized_rows = None
        self.harmonized_columns = None

        self.exchange_rate_exceptions = {}

        self.from_blacklist = []
        self.to_blacklist = []

    def set_table(self, tablename):
        self.tablename = tablename
        self.strings["iotable"] = tablename
        self.sectors = None
        self.exchange_rate = 1

    def set_fd_sectors(self, sectors):
        self.strings["fd_sectors"] = sqlhelper.set_repr(sectors)
        self.fd_sectors = sectors

    def set_exchange_rate(self, rate):
        self.exchange_rate = rate

    def set_exchange_rate_exception(self, sector, rate):
        self.exchange_rate_exceptions[sector] = rate

    def get_exchange_rate(self, sector):
        if sector in self.exchange_rate_exceptions:
            return self.exchange_rate_exceptions[sector]
        else:
            return self.exchange_rate

    def set_harmonized_rows(self, rows):
        self.harmonized_rows = rows

    def set_harmonized_cols(self, cols):
        self.harmonized_cols = cols

    def blacklist_from_sectors(self, from_sectors):
        self.from_blacklist = from_sectors

    def blacklist_to_sectors(self, to_sectors):
        self.to_blacklist = to_sectors

    def generate_where(self, table_alias="", extra=[]):
        conditions = self.universal_conditions[:]
        if len(table_alias) and not table_alias.endswith("."):
            table_alias = table_alias + "."
        if len(self.from_blacklist):
            conditions.append("%s%s NOT IN %s" \
                % (table_alias, self.strings["from_sector"],
                   sqlhelper.set_repr(self.from_blacklist)))
        if len(self.to_blacklist):
            conditions.append("%s%s NOT IN %s" \
                % (table_alias, self.strings["to_sector"],
                   sqlhelper.set_repr(self.to_blacklist)))
        if len(conditions) > 0:
            return " AND ".join(conditions)
        return "TRUE"

    # sectors
    def generate_sector_stmt(self):
        strings = self.strings
        strings["conditions"] = self.generate_where()
        sql = """SELECT DISTINCT %(from_sector)s
                   FROM %(iotable)s
                  WHERE %(conditions)s""" % strings

        return db.prepare(sql)

    # clear cache
    def set_condition_args(self, *args):
        self.condition_args = args
        self.sectors = None

    # refresh list if get_sectors is called with different args
    def get_sectors(self):
        if self.sectors is None:
            stmt = self.generate_sector_stmt()
            self.sectors = [row[0] for row in stmt(*self.condition_args)]
        return self.sectors

    # total output
    def sql_for_total_output(self):
        strings = self.strings
        strings["conditions"] = self.generate_where()
        sql = """SELECT %(from_sector)s AS __from_sector,
                        sum(%(value_column)s) as %(value_column)s
                   FROM %(iotable)s
                  WHERE %(conditions)s
                  GROUP BY %(from_sector)s""" % strings

        return sql

    def generate_x_stmt(self):
        return db.prepare(self.sql_for_total_output())

    def get_x(self, use_exchange_rate=False):
        x = TotalOutputMatrix(rows=self.get_sectors())
        if self.harmonized_rows is not None:
            x.set_harmonized_rows(self.harmonized_rows)

        stmt = self.generate_x_stmt()
        result = stmt(*self.condition_args)
        for row in result:
            if use_exchange_rate:
                exchange_rate = self.get_exchange_rate(row[0])
                x.set_output(row[0], float(row[1]) * exchange_rate)
            else:
                x.set_output(row[0], row[1])
        return x

    # technical coefficients
    def generate_Z_stmt(self):
        strings = self.strings
        strings["conditions"] = self.generate_where()
        sql = """SELECT %(from_sector)s, %(to_sector)s,
                        %(value_column)s 
                   FROM %(iotable)s
                  WHERE %(conditions)s
                    AND %(to_sector)s NOT IN %(fd_sectors)s""" % strings

        return db.prepare(sql)

    def get_Z(self):
        Z = NamedMatrix(square=True, rows=self.get_sectors())
        if self.harmonized_rows is not None:
            Z.set_harmonized_rows(self.harmonized_rows)

        stmt = self.generate_Z_stmt()
        result = stmt(*self.condition_args)
        for row in result:
            Z.set_element(row[0], row[1], row[2]) # from_sec, to_sec, value

        return Z

    def generate_A_stmt(self):
        strings = self.strings
        strings["x_sql"] = self.sql_for_total_output()
        strings["conditions"] = self.generate_where("z")

        sql = """SELECT z.%(from_sector)s, z.%(to_sector)s,
                        z.%(value_column)s / x.%(value_column)s as a
                   FROM %(iotable)s z,
                        (%(x_sql)s) x
                  WHERE %(conditions)s
                    AND z.%(to_sector)s NOT IN %(fd_sectors)s
                    AND z.%(to_sector)s = x.__from_sector
                    AND x.%(value_column)s <> 0""" % strings

        return db.prepare(sql)

    def get_A(self):
        A = NamedMatrix(square=True, rows=self.get_sectors())
        if self.harmonized_rows is not None:
            A.set_harmonized_rows(self.harmonized_rows)

        stmt = self.generate_A_stmt()
        result = stmt(*self.condition_args)
        for row in result:
            A.set_element(row[0], row[1], row[2]) # from_sec, to_sec, value

        return A

    def get_L(self):
        matrix_shell = self.get_A()
        A = matrix_shell.mat()

        if A.shape[0] != A.shape[1]:
            raise Exception("A is not square")
        eye = sparse.identity(A.shape[0])
        L = (eye - A).todense().getI()
        matrix_shell.matrix = L
        return matrix_shell

    def set_pce_col(self, pce_col):
        self.pce_col = pce_col

    def set_export_col(self, export_col):
        self.export_col = export_col

    def generate_Y_stmt(self):
        strings = self.strings
        strings["conditions"] = self.generate_where()
        sql = """SELECT %(from_sector)s, %(to_sector)s, %(value_column)s
                   FROM %(iotable)s
                  WHERE %(conditions)s
                    AND %(to_sector)s IN %(fd_sectors)s""" % strings
        return db.prepare(sql)

    def get_Y(self, use_exchange_rate=False):
        if self.pce_col is None or self.export_col is None:
            raise Exception("one or more final demand columns not set")

        Y = FinalDemandMatrix(self.pce_col, self.export_col,
                              rows=self.get_sectors(),
                              cols=self.fd_sectors)
        if self.harmonized_rows is not None:
            Y.set_harmonized_rows(self.harmonized_rows)

        stmt = self.generate_Y_stmt()
        result = stmt(*self.condition_args)
        for row in result:
            if use_exchange_rate:
                exchange_rate = self.get_exchange_rate(row[0])
                Y.set_element(row[0], row[1], row[2] * exchange_rate)
            else:
                Y.set_element(row[0], row[1], row[2])

        return Y

class EnvMatrixGenerator:

    def __init__(self, envtable,
                 ind_col_name="sector",
                 series_col_name="series",
                 value_col_name="value",
                 universal_conditions=[]):

        self.strings = {
            "ind_col": ind_col_name,
            "series_col": series_col_name,
            "value": value_col_name,
            }

        self.set_table(envtable)

        self.set_universal_conditions(universal_conditions)
        self.condition_args = ()

    def set_universal_conditions(self, conditions):
        if len(conditions):
            self.strings["basic_condition"] = \
                " AND ".join(conditions)
        else:
            self.strings["basic_condition"] = "TRUE"

    def set_table(self, tablename):
        self.tablename = tablename
        self.strings["envtable"] = tablename
        self.sectors = None

    # sectors
    def set_sectors(self, sectors):
        self.sectors = sectors

    def generate_sector_stmt(self):
        sql = """SELECT DISTINCT %(ind_col)s
                   FROM %(envtable)s
                  WHERE %(basic_condition)s
                  ORDER BY %(ind_col)s""" % self.strings
        return db.prepare(sql)

    # TODO: create common superclass for this and IOMatrixGenerator
    # containing the following two methods
    def set_condition_args(self, *args):
        self.condition_args = args
        self.sectors = None

    def get_sectors(self):
        if self.sectors is None:
            stmt = self.generate_sector_stmt()
            self.sectors = [row[0] for row in stmt(*self.condition_args)]
        return self.sectors

    # mapping matrix
    # TODO: stop using this, use generic selector in matrixutils instead
    def generate_map_stmt(self, maptable, env_col, other_col, conditions=[]):
        strings = {
            "maptable": maptable,
            "other_col": other_col,
            "self_col": env_col,
            }

        if len(conditions):
            strings["basic_condition"] = " AND ".join(conditions)
        else:
            strings["basic_condition"] = "TRUE"

        sql = """SELECT %(self_col)s, %(other_col)s
                   FROM %(maptable)s
                  WHERE %(basic_condition)s""" % strings
        return db.prepare(sql)

    def get_env_selector(self, maptable, env_col, other_col,
                         columns, conditions=[]):
        sel = NamedMatrix(square=False)
        sel.set_columns(columns)
        sel.set_rows(self.get_sectors())
        stmt = self.generate_map_stmt(maptable, env_col, other_col, conditions)
        result = stmt()
        for row in result:
            if sel.has_row(row[0]) and sel.has_column(row[1]):
                sel.set_element(row[0], row[1], 1)
        return sel

    # env matrix main
    def generate_env_stmt(self, series):
        strings = self.strings
        strings["series_list"] = sqlhelper.set_repr(series)

        sql = """SELECT %(ind_col)s, sum(%(value)s)
                   FROM %(envtable)s
                  WHERE %(basic_condition)s
                    AND %(series_col)s IN %(series_list)s
                  GROUP BY %(ind_col)s""" % strings

        return db.prepare(sql)

    def get_env_vector(self, series):
        if type(series) is str:
            series = [series]

        colname = "+".join(series)
        E = NamedMatrix(square=False,
                        rows=self.get_sectors(),
                        cols=[colname])
        stmt = self.generate_env_stmt(series)
        result = stmt(*self.condition_args)
        for row in result:
            E.set_element(row[0], colname, row[1])

        return E


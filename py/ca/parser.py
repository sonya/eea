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

#
# this script parses canada's unbelievably clean and consistent io
# and env tables. the website is restful too! impossible beings!
#

__all__ = ["doparse"]

import csv
from common import fileutils, parserutils, regexes, sqlhelper
from common.dbhelper import SQLTable, CSVTable
from common.dbconnect import db
from ca import config

def doparse():
    parse_codes()
    parse_env()
    parse_io()
    create_views()

def runsql(sql):
    print(sql)
    db.execute(sql)

def emissions_intensity_skip(row):
    return row[2] != "Tonnes per thousand current dollars of production"

def energy_intensity_skip(row):
    return row[2] != "Gigajoules per thousand current dollars of production"

# these dictionaries are properties of csv files
intensity_col_map = {
    "year": "Ref_Date",
    "industry": "INDUSTRY",
    "value": "Value",
    }

quantity_col_map = {
    "year": "Ref_Date",
    "industry": "SECTOR",
    "value": "Value",
    }

eea_tables = {
    "01530031": {
        # direct plus indirect greenhouse gas intensity
        "tablename": "energy_intensity",
        "col_map": intensity_col_map,
        "skip_callback": energy_intensity_skip,
        },
    "01530032": {
        "tablename": "energy_quantity",
        "col_map": quantity_col_map,
        },
    "01530033": {
        "tablename": "emissions_intensity",
        "col_map": intensity_col_map,
        "skip_callback": emissions_intensity_skip,
        },
    "01530034": {
        "tablename": "emissions_quantity",
        "col_map": quantity_col_map,
        },
    }

def parse_env():
    for (tablecode, tablespec) in eea_tables.items():
        filename = "%s-eng.csv" % tablecode
        filepath = fileutils.getcache(filename, "ca")
        csvtable = CSVTable(filepath, True)
    
        tablename = "%s.%s" % (config.SCHEMA, tablespec["tablename"])
        csvtable.create_sql_table(tablename,
                                  ["year", "industry", "value"],
                                  ["int", "varchar(255)", "float"])

        col_funcs = {"industry": get_industry_code}
        col_map = tablespec["col_map"]
        skip_callback = None
        if "skip_callback" in tablespec:
            skip_callback = tablespec["skip_callback"]
    
        csvtable.parse_to_sql(col_map, col_funcs, skip_callback)

io_col_map = {
    "year": "Ref_Date",
    "industry": "IND",
    "value": "Value",
    }

io_tables = {
    "summary": ("03810014", "03810011"),
    "sector": ("03810013", "03810012"),
    "detail": ("03810009", "03810010"),
    }

def skip_make(row):
    if row[1] != "Canada":
        return True
    if row[2] != "Outputs":
        return True
    if strip_millions(row[3]) in config.ind_blacklist:
        return True
    if strip_millions(row[4]) in config.com_blacklist:
        return True
    return False

def skip_use(row):
    if row[1] != "Canada":
        return True
    if row[2] != "Inputs":
        return True
    if strip_millions(row[3]) in config.ind_blacklist:
        return True
    if strip_millions(row[4]) in config.com_blacklist:
        return True
    return False

def skip_finaldemand(row):
    if row[1] != "Canada":
        return True
    if row[2].startswith("Total, final demand"):
        return True
    if strip_millions(row[3]) in config.com_blacklist:
        return True
    return False

def strip_millions(field):
    millions = " (x 1,000,000)"
    if field.endswith(millions):
        return field[:len(field)-len(millions)]
    return field

def get_industry_code(field):
    field = strip_millions(field)
    code = parserutils.get_code_for_title(field,
                                          "%s.ind_codes" % config.SCHEMA)

    if not code:
        print("industry", field)
    return code

def get_commodity_code(field):
    field = strip_millions(field)
    code = parserutils.get_code_for_title(field,
                                          "%s.com_codes" % config.SCHEMA)
    if not code:
        print("commodity", field)
    return code

def get_fd_industry_code(field):
    field = field.split(",")[0]
    return get_industry_code(field)

def parse_io():
    # we'll just parse the same file twice,
    # once each for make/use
    for (agglevel, (intermediate, finaldemand)) in io_tables.items():
        colnames = ["year", "industry", "commodity", "value"]

        if agglevel == "detail":
            coltypes = ["int", "varchar(15)", "varchar(15)", "float"]
            colfuncs = {
                "industry": get_industry_code,
                "commodity": get_commodity_code,
                }
        else:
            coltypes = ["int", "varchar(255)", "varchar(255)", "float"]
            colfuncs = {
                "industry": strip_millions, "commodity": strip_millions}

        # parse intermediate
        filename = "%s-eng.csv" % intermediate
        filepath = fileutils.getcache(filename, "ca")
        io_col_map["industry"] = "IND"
        if agglevel == "detail":
            io_col_map["commodity"] = "COMMOD"
        else:
            io_col_map["commodity"] = "COMM"

        csvtable = CSVTable(filepath, True, "cp1252")
        tablename = "%s.io_make_%s" % (config.SCHEMA, agglevel)
        csvtable.create_sql_table(tablename, colnames, coltypes)
        csvtable.parse_to_sql(io_col_map, colfuncs, skip_make, cascade=True)
    
        # we can reuse CSVTable for the same source file
        tablename = "%s.io_use_%s" % (config.SCHEMA, agglevel)
        csvtable.create_sql_table(tablename, colnames, coltypes)
        csvtable.parse_to_sql(io_col_map, colfuncs, skip_use)

        # parse final demand
        filename = "%s-eng.csv" % finaldemand
        filepath = fileutils.getcache(filename, "ca")
        io_col_map["commodity"] = "COMM"
        io_col_map["industry"] = "CAT"

        fdtable = CSVTable(filepath, True, "cp1252")
        tablename = "%s.io_fd_%s" % (config.SCHEMA, agglevel)
        fdtable.create_sql_table(tablename, colnames, coltypes)


        if agglevel == "detail":
            colfuncs["industry"] = get_fd_industry_code

        fdtable.parse_to_sql(io_col_map, colfuncs, skip_finaldemand)

def parse_codes():
    comcodes = parserutils.add_tracker("%s.com_codes" % config.SCHEMA, "w")
    filename = fileutils.getdatapath("commodities.csv", "ca")
    with open(filename, "r") as fh:
        csvf = csv.reader(fh)
        for row in csvf:
            if len(row) and regexes.is_num(row[0]):
                comcodes.set_code(row[0], row[1])
    comcodes.update_codes()

    maptable = SQLTable("%s.sector_map" % config.SCHEMA,
                        ["io_code", "env_code", "harmonized"],
                        ["varchar(15)", "varchar(15)", "varchar(15)"]).create()
    
    indcodes = parserutils.add_tracker("%s.ind_codes" % config.SCHEMA, "w")
    filename = fileutils.getdatapath("industries.csv", "ca")
    with open(filename, "r") as fh:
        csvf = csv.reader(fh)
        for row in csvf:
            if len(row) >= 5:
                io_code = row[0]
                if not len(io_code):
                    io_code = None
                elif len(row[1]):
                    indcodes.set_code(io_code, row[1])

                env_code = row[2]
                if not len(env_code):
                    env_code = None
                elif len(row[3]):
                    indcodes.set_code(env_code, row[3])

                harmonized = row[4]
                if len(harmonized) and regexes.is_num(harmonized):
                    indcodes.set_code(harmonized, row[5])
                    maptable.insert([io_code, env_code, harmonized])

    indcodes.update_codes()

# right now the ixi tables are still not balanced since there are 120
# commodities that appear in the use and fd tables that don't appear in
# the make table. check via
"""
select u.commodity
  from (select distinct commodity from ca.io_make_detail) m
 right outer join
       (select distinct commodity from ca.io_use_detail
  union select distinct commodity from ca.io_fd_detail) u
    on m.commodity = u.commodity
 where m.commodity is null
"""
def create_views():
    for year in config.STUDY_YEARS:
        strings = {
            "year": year,
            "make_table": "%s.io_make_detail" % config.SCHEMA,
            "use_table": "%s.io_use_detail" % config.SCHEMA,
            "fd_table": "%s.io_fd_detail" % config.SCHEMA,

            "indshare_table": "%s.indshares_%d" % (config.SCHEMA, year),
            "cxctable": "%s.cxc_%d" % (config.SCHEMA, year),

            "comshare_table": "%s.comshares_%d" % (config.SCHEMA, year),
            "ixitable": "%s.ixi_%d" % (config.SCHEMA, year),
            "va_sectors": sqlhelper.set_repr(config.value_added),
           }

        # commodity output proportions
        runsql("""CREATE OR REPLACE VIEW %(comshare_table)s AS
                   SELECT make.industry, make.commodity,
                          cast(make.value as float) / comtotal.value AS output_share
                     FROM (SELECT industry, commodity, sum(value) as value
                             FROM %(make_table)s
                            WHERE year = %(year)d
                            GROUP BY industry, commodity) make,
                          (SELECT commodity, cast(sum(value) as float) AS value
                             FROM %(make_table)s
                            WHERE year = %(year)d
                            GROUP BY commodity) comtotal
                    WHERE make.value > 0
                      AND make.commodity = comtotal.commodity""" % strings)

        # intermediate output section of transactions table
        runsql("DROP TABLE IF EXISTS %(ixitable)s" % strings)

        runsql("""
           SELECT comshare.industry AS from_sector,
                  use.industry AS to_sector,
                  cast(use.value as float) * comshare.output_share as value
             INTO %(ixitable)s
             FROM (SELECT industry, commodity, sum(value) as value
                     FROM %(use_table)s
                    WHERE year = %(year)d
                    GROUP BY industry, commodity) use,
                  %(comshare_table)s comshare
            WHERE comshare.commodity = use.commodity""" % strings)

        # final demand section of transactions table
        runsql("""INSERT INTO %(ixitable)s
          SELECT comshare.industry as from_sector,
                 --split_part(fd.industry, ',', 1) AS to_sector,
                 fd.industry as to_sector,
                 cast(fd.value as float) * comshare.output_share AS value
            FROM (SELECT split_part(industry, ',', 1) as industry,
                         commodity, sum(value) as value
                    FROM %(fd_table)s
                   WHERE year = %(year)d
                   GROUP BY split_part(industry, ',', 1), commodity) fd,
                 %(comshare_table)s comshare
           WHERE comshare.commodity = fd.commodity""" % strings)

        # value added section of transactions table
        runsql("""INSERT INTO %(ixitable)s
           SELECT commodity AS from_sector,
                  industry AS to_sector,
                  cast(sum(value) as float)
             FROM %(use_table)s use
            WHERE year = %(year)d
              AND commodity IN %(va_sectors)s
            GROUP BY industry, commodity""" % strings)

        runsql("DROP VIEW %(comshare_table)s" % strings)



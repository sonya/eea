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

# file structure:
# blank, blank, 01, 02, 03,...
# blank, blank, agriculture, animal, forestry,...
# 01, agriculture, 39433, 14729, 0,...
#

import xlrd
from tw import config
from common import fileutils, regexes, sqlhelper
from common.dbconnect import db
from common.dbhelper import SQLTable

def doparse():
    parse_codes()
    parse_io()
    parse_env()

def parse_codes():
    path = fileutils.getdatapath("sector_map.xls", "tw-env")
    wb = xlrd.open_workbook(path)
    sheets = wb.sheets()
    for sheet in sheets:
        year = int(sheet.name)
        tablename = "%s.sector_map_%d" % (config.SCHEMA, year)

        if year > 2006: # CxI only, need map between commods and inds
            colnames = ["io_sector", "env_sector", "harmonized_env",
                        "io_commod", "io_ind"]
            coltypes = ["varchar(255)"]*5
        else:
            colnames = ["io_sector", "env_sector", "harmonized_env"]
            coltypes = ["varchar(255)"]*3

        table = SQLTable(tablename, colnames, coltypes)
        table.create()
        table.truncate()
        for i in range(sheet.nrows):
            row = sheet.row_values(i)
            io_sector = row[0].strip()
            env_sector = row[1].strip()
            harmonized_env = row[2]
            if type(harmonized_env) is float:
                harmonized_env = str(int(harmonized_env))
            harmonized_env = harmonized_env.strip()
            if year > 2006:
                io_commod = row[4].strip()
                io_ind = row[5].strip()
                table.insert([io_sector, env_sector, harmonized_env,
                              io_commod, io_ind])
            else:
                table.insert([io_sector, env_sector, harmonized_env])

def parse_io():
    io_files = {
        1996: "410281134571.xls",
        1999: "4102715414971.xls",
        2001: "4122111363671.xls",
        2004: "611239581071.xls",
        2006: "9121414285971.xls",
        2007: "1139203871.xls",
        2008: "1139204871.xls",
        2009: "11229101502.xls",
        2010: "1122910141371.xls",
        }

    for (year, filename) in io_files.items():
        tablename = "%s.io_%d" % (config.SCHEMA, year)
    
        # millions are in NTD
        table = SQLTable(tablename,
                         ["from_sector", "to_sector", "millions"],
                         ["varchar(255)", "varchar(255)", "float"])
        table.create()
        table.truncate()
    
        path = fileutils.getcache(filename, "tw/%d" % year)
        wb = xlrd.open_workbook(path)
        sheet = wb.sheets()[0]
        to_codes = sheet.row_values(0)
        to_names = sheet.row_values(1)
        for rowindex in range(2, sheet.nrows):
            row = sheet.row_values(rowindex)
            from_code = row[0].strip()
            from_name = row[1].strip()
            for i in range(2, len(to_names)):
                to_name = to_names[i].strip()
                value = row[i]
                table.insert([from_name, to_name, value])

        if year == 2010:
            strings = {
                "viewname": "%s.io_view_%d" % (config.SCHEMA, year),
                "tablename": tablename,
                "maptable": "%s.sector_map_%d" % (config.SCHEMA, year),
                "to_blacklist": sqlhelper.set_repr(config.to_blacklists[year]),
                "from_blacklist":
                    sqlhelper.set_repr(config.from_blacklists[year]),
                }

            sql = """CREATE OR REPLACE VIEW %(viewname)s AS
                SELECT from_map.io_sector AS from_sector,
                       to_map.io_sector as to_sector,
                       sum(millions) as millions
                  FROM %(tablename)s io,
                       (SELECT DISTINCT io_sector, io_commod
                          FROM %(maptable)s) from_map,
                       (SELECT DISTINCT io_sector, io_ind
                          FROM %(maptable)s) to_map
                 WHERE io.to_sector NOT IN %(to_blacklist)s
                   AND io.from_sector NOT IN %(from_blacklist)s
                   AND from_map.io_commod = io.from_sector
                   AND to_map.io_ind = io.to_sector
                 GROUP BY from_map.io_sector, to_map.io_sector""" % strings

            print(sql)
            db.execute(sql)

def parse_env():
    # parse english env files
    # TODO: might want to use the energy table as well.
    # it is very comprehensive, but formatted differently and only has 2001
    
    sector_whitelist = ("Household Consumption", "Fixed Capital Formation")
    eng_env_years = [1999, 2001, 2004]
    eng_env_files = {
        "air_pol": {
            "filename": "IO_air.xls",
            "columns": ["TSP", "PM10", "SOx", "NOx", "NMHC", "CO", "Pb"],
            },
        "water_pol": {
            "filename": "IO_pol_water.xls",
            "columns": ["BOD", "COD", "SS"],
            },
        "waste_pol": {
            "filename": "IO_waste.xls",
            "columns": ["Total waste", "General waste",
                        "Hazardous waste", "Total waste - improper disposal",
                        "General waste - improper disposal",
                        "Hazardous waste - improper disposal"],
            },
        "water_use": {
            "filename": "IO_res_water.xls",
            "columns": ["Natural water", "Abstracted water"],
            },
        }

    tables_by_year = {}
    for year in eng_env_years:
        if year not in tables_by_year:
            tablename = "%s.env_%d" % (config.SCHEMA, year)
            table = SQLTable(tablename,
                             ["sector", "series", "value"],
                             ["varchar(55)", "varchar(255)", "float"])
            table.create()
            table.truncate()
            tables_by_year[year] = table
        else:
            table = tables_by_year[year]
    
        first_file = True
        for (tkey, tdata) in eng_env_files.items():
            path = fileutils.getdatapath(tdata["filename"], "tw-env")
            wb = xlrd.open_workbook(path)
            sheet = wb.sheet_by_name("year %d" % year)
            for rowindex in range(sheet.nrows):
                row = sheet.row_values(rowindex)
                if len(row) > 1 and \
                        (regexes.is_num(row[0]) or row[1] in sector_whitelist):
                    sector = row[1].strip()
                    if first_file: # these columns are repeated in every file
                        table.insert([sector, "Total Output", row[2]])
                        table.insert([sector, "Total Input", row[3]])
                        table.insert([sector, "GDP", row[4]])
                        first_file = False
                    for i in range(len(tdata["columns"])):
                        table.insert([sector, tdata["columns"][i], row[i+5]])
    
    # parse chinese env tables
    # this is file that we created by compiling older chinse data and
    # manually copying info from latest (2010) pdf files
    
    # skip 2001 because the english version is better
    sheetnames_by_year = {
        2000: ["89年空汙", "89年廢棄物"],
        2002: ["91年空汙", "91年廢棄物"],
        2003: ["92年空汙", "92年廢棄物"],
        2010: ["99年空汙", "99年水汙", "99年廢棄物"],
        }
    
    path = fileutils.getdatapath("sheets.xls", "tw-env")
    wb = xlrd.open_workbook(path)
    for (year, sheetnames) in sheetnames_by_year.items():
        tablename = "%s.env_%d" % (config.SCHEMA, year)
        table = SQLTable(tablename,
                         ["sector", "series", "value"],
                         ["varchar(55)", "varchar(255)", "float"])
        table.create()
        table.truncate()
        
        for sheetname in sheetnames:
            sheet = wb.sheet_by_name(sheetname)
            header = sheet.row_values(0)
    
            # the 2010 tables have several rows that we don't want
            should_parse = (year != 2010)
            for i in range(1, sheet.nrows):
                row = sheet.row_values(i)
                if should_parse:
                    sector = row[0].strip()
                    for i in range (1, len(header)):
                        measurement = header[i].strip()
                        value = row[i]
                        table.insert([sector, measurement, value])
    
                elif row[0] in ("依行業分", "依部門分"):
                    should_parse = True




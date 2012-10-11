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

import csv, openpyxl, os, xlrd

import common.config
from common import fileutils, sqlhelper
from common.dbconnect import db
from common.dbhelper import SQLTable
from wiod import config
from wiod.utils import CodeTracker

commodity_tracker = CodeTracker("commodity_codes")
industry_tracker = CodeTracker("industry_codes")

def doparse():
    commodity_tracker.setup()
    industry_tracker.setup()

    parse_codes()
    parse_io()
    parse_int()
    parse_env()

    commodity_tracker.update_codes()
    industry_tracker.update_codes()

    create_views()

def create_views():
    va_sectors = set(config.va_sectors.values())
    fd_sectors = set(config.fd_sectors.values())

    for year in config.STUDY_YEARS:
        strings = {
            "test_schema": common.config.TEST_SCHEMA,
            "schema": config.WIOD_SCHEMA,
            "extra_schema": "wiod_plus",
            "year": year,
            "fd_sectors": sqlhelper.set_repr(fd_sectors),
            "va_sectors": sqlhelper.set_repr(va_sectors),
            "margins": sqlhelper.set_repr(config.margin_sectors)
            }

        ### indbyind tables ignoring imports
        db.execute(
            """CREATE OR REPLACE VIEW %(schema)s.indbyind_%(year)d AS
               SELECT country, from_ind, to_ind, value
                 FROM %(schema)s.niot_%(year)d
                WHERE NOT is_import
             UNION
               SELECT country, from_ind, 'IMP', sum(value)
                 FROM %(schema)s.niot_%(year)d
                WHERE is_import
                GROUP BY country, from_ind""" % strings)

        #continue

        # co2 intensity views
        # put in test since we're just checking results
        sql = """CREATE OR REPLACE VIEW %(test_schema)s.co2_intensity_%(year)d AS
            SELECT a.country, CAST(a.gdp as int) gdp,
                   CAST(b.emissions as int) emissions,
                   b.emissions / a.gdp AS intensity
              FROM (SELECT country, sum(value) AS gdp
                      FROM %(schema)s.indbyind_%(year)d
                     WHERE from_ind not in %(va_sectors)s
                       AND to_ind in %(fd_sectors)s
                     GROUP BY country) a,
                   (SELECT country, value AS emissions
                      FROM %(schema)s.env_%(year)d where industry = 'total'
                       AND measurement = 'CO2') b
             WHERE a.country = b.country
             ORDER BY country""" % strings
        db.execute(sql)

        # commodity output proportions tables for all countries
        sql = """CREATE OR REPLACE VIEW %(schema)s.comshare_%(year)d AS
            SELECT make.country, make.commodity, make.industry,
                   make.value / totals.value AS use_share
              FROM (SELECT country, commodity, industry, value
                      FROM wiod.int_make_%(year)d
                     WHERE commodity not in %(va_sectors)s
                       AND industry not in %(margins)s) make,
                   (SELECT country, commodity, sum(value) as value
                      FROM wiod.int_make_%(year)d
                     WHERE commodity not in %(va_sectors)s
                       AND industry not in %(margins)s
                     GROUP BY country, commodity) totals
             WHERE make.country = totals.country
               AND make.commodity = totals.commodity""" % strings
        db.execute(sql)

        for country in config.countries:
            strings["country"] = country.lower()
            table = "%(extra_schema)s.%(country)s_io_import_%(year)d" % strings
            strings["io_import_table"] = table

            sql = "DROP TABLE IF EXISTS %(io_import_table)s" % strings
            db.execute(sql)

            sql = """SELECT comshare.country,
                            comshare.industry AS from_sector,
                            use.industry AS to_sector,
                            sum(use.value * comshare.use_share) AS value
                       INTO %(io_import_table)s
                       FROM %(schema)s.comshare_%(year)d comshare,
                            (SELECT from_country, industry, commodity, value
                               FROM %(schema)s.int_use_%(year)d
                              WHERE to_country = $1
                                AND from_country <> $1) use
                      WHERE comshare.country = use.from_country
                        AND comshare.commodity = use.commodity
                      GROUP BY comshare.country, comshare.industry,
                            use.industry""" % strings
    
            print(sql)
            stmt = db.prepare(sql)
            stmt(country)

def parse_codes():
    ## manually curated sector map
    table = SQLTable("%s.sector_map" % config.WIOD_SCHEMA,
                     ["io_code", "env_code", "description"],
                     ["varchar(15)", "varchar(15)", "text"]).create()
    table.truncate()

    sector_map = fileutils.getdatapath("sector_map.csv", "wiod")
    fh = open(sector_map, "r")
    csvf = csv.reader(fh)
    header = next(csvf)
    for row in csvf:
        io_code = row[0].strip()
        if not len(io_code):
            io_code = None
        env_code = row[1].strip()
        if not len(env_code):
            env_code = None
        desc = row[2].strip()
        table.insert([io_code, env_code, desc])

    ## current exchange rates
    table = SQLTable("%s.exchange_rates" % config.WIOD_SCHEMA,
                     ["country", "year", "rate"],
                     ["char(3)", "int", "float"]).create()
    table.truncate()

    path = fileutils.getcache("exr_wiod.xls", "wiod")
    wb = xlrd.open_workbook(path)
    sheet = wb.sheet_by_name("EXR")
    year_list = None
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        if len(row) < 2:
            continue
        if year_list is None:
            if type(row[0]) is str and row[0].strip() == "Country":
                year_list = [int(cell.strip("_ ")) for cell in row[2:]]
        else:
            if type(row[1]) is str and len(row[1].strip()) == 3:
                country = row[1]
                if country == "GER":
                    country = "DEU"
                for (year, value) in zip(year_list, row[2:]):
                    table.insert([country, year, value])

def parse_env():
    tables = {}

    for year in config.STUDY_YEARS:
        tablename = "%s.env_%d" % (config.WIOD_SCHEMA, year)
        colnames = ["country", "industry", "measurement", "value"]
        coltypes = ["char(3)", "varchar(15)", "varchar(31)", "float"]
        tables[year] = SQLTable(tablename, colnames, coltypes).create()
        tables[year].truncate()

    countries = sorted(config.countries.keys())
    countries.append("ROW") # rest of world

    for (series, attribs) in config.env_series.items():
        if "dir" in attribs:
            subdir = attribs["dir"]
        else:
            subdir = series
        subdir = os.path.join("wiod", subdir)
        skip_name = "skip_name" in attribs and attribs["skip_name"]

        for country in config.countries.keys():
            filename = "%s_%s_May12.xls" % (country, series)
            print(filename)
            path = fileutils.getcache(filename, subdir)
            wb = xlrd.open_workbook(path)

            for year in config.STUDY_YEARS:
                sheet = wb.sheet_by_name("%d" % year)
                measurements = sheet.row_values(0)
                if series == "EU":
                    measurements = [m + " - Gross" for m in measurements]
                elif series == "CO2":
                    measurements = ["CO2 - " + m for m in measurements]

                for i in range(1, sheet.nrows):
                    row = sheet.row_values(i)
                    if len(row[0].strip()):
                        if skip_name:
                            ind_code = row[0]
                            first_col = 1
                        else:
                            ind_name = row[0]
                            ind_code = row[1]
                            industry_tracker.set_code(ind_code, ind_name)
                            first_col = 2

                        for j in range(first_col, len(row)):
                            value = row[j]
                            if type(value) is float and value != 0:
                                measurement = measurements[j]
                                tables[year].insert(
                                    [country, ind_code, measurement, value])

def parse_io():
    ### for ind x ind tables
    tables = {}
    colnames = ["country", "from_ind", "to_ind", "is_import", "value"]
    coltypes = ["char(3)", "varchar(15)", "varchar(15)", "bool", "float"]
    for year in config.STUDY_YEARS:
        tablename = "%s.niot_%d" % (config.WIOD_SCHEMA, year)
        tables[year] = SQLTable(tablename, colnames, coltypes)#.create()
        tables[year].drop()
        tables[year].create()
        tables[year].truncate()

    va_sectors = set(config.va_sectors.values())

    for country in config.countries.keys():
        filename = "%s_NIOT_ROW_Apr12.xlsx" % country
        subdir = os.path.join("wiod", "niot")
        path = fileutils.getcache(filename, subdir)
        wb = openpyxl.load_workbook(filename=path, use_iterators=True)
        for year in config.STUDY_YEARS:
            imports = {}

            sheet = wb.get_sheet_by_name("%d" % year)
            rows = sheet.iter_rows()
            industry_row = None
            for row in rows:
                cell = row[0]
                if cell.internal_value == "(industry-by-industry)":
                    industry_row = row
                    break
            row = next(rows) # industry names
            industry_codes = []
            for (code_cell, desc_cell) in zip(industry_row, row):
                code = code_cell.internal_value
                desc = desc_cell.internal_value
                industry_codes.append(industry_tracker.set_code(code, desc))

            for row in rows:
                from_code = None
                from_desc = None
                is_import = False
                for (to_code, value_cell) in zip(industry_codes, row):
                    column = value_cell.column
                    value = value_cell.internal_value
                    # excel columns use letters
                    if column == "A":
                        from_code = value_cell.internal_value
                    elif column == "B":
                        from_desc = value_cell.internal_value
                    elif column == "C":
                        from_code = industry_tracker.set_code(
                            from_code, from_desc)
                        if not from_code:
                            break
                        if type(value) is str and value == "Imports":
                            is_import = True
                    elif (column > "D" or len(column) > 1) \
                            and to_code and value != 0:
                        tables[year].insert(
                            [country, from_code, to_code, is_import, value])

    ### for supply and use tables
    def parse_sut(sheet_name, table_prefix):
        tables = {}
        colnames = ["country", "commodity", "industry", "value"]
        coltypes = ["char(3)", "varchar(15)", "varchar(15)", "float"]
        for year in config.STUDY_YEARS:
            tablename = "%s_%d" % (table_prefix, year)
            tables[year] = SQLTable(tablename, colnames, coltypes).create()
            tables[year].truncate()
    
        for country in config.countries.keys():
            # TODO: more automated way to get this
            if country in ("AUS", "DEU", "GBR", "USA"):
                filename = "%s_SUT_Feb12.xls" % country
            else:
                filename = "%s_SUT_Jan12.xls" % country
            subdir = os.path.join("wiod", "suts")
            path = fileutils.getcache(filename, subdir)
            wb = xlrd.open_workbook(path)
    
            # extract supply and use tables at fob prices
            sheet = wb.sheet_by_name(sheet_name)
            industry_row = sheet.row_values(0)
            row = sheet.row_values(1)
            industry_codes = []
            for (code, desc) in zip(industry_row, row):
                industry_codes.append(industry_tracker.set_code(code, desc))
    
            for i in range(2, sheet.nrows):
                row = sheet.row_values(i)
                if not len(row[0].strip()):
                    continue
                year = int(row[0])
                if year not in config.STUDY_YEARS:
                    continue
                com_code = commodity_tracker.set_code(row[1], row[2])
                if not com_code:
                    continue
                for j in range(3, len(row)):
                    value = row[j]
                    ind_code = industry_codes[j]
                    if value != 0 and ind_code:
                        # commodity first
                        tables[year].insert(
                            [country, com_code, ind_code, value])

    # make tables
    parse_sut("SUP_bas", "%s.make" % config.WIOD_SCHEMA)

    # use tables
    parse_sut("USE_bas", "%s.use" % config.WIOD_SCHEMA)

def parse_int():
    for year in config.STUDY_YEARS:
        tablename = "%s.int_use_%d" % (config.WIOD_SCHEMA, year)
        colnames = [
            "from_country", "to_country", "commodity", "industry", "value"]
        coltypes = [
            "char(3)", "char(3)", "varchar(15)", "varchar(15)", "float"]
        use_table = SQLTable(tablename, colnames, coltypes).create()

        tablename = "%s.int_make_%d" % (config.WIOD_SCHEMA, year)
        colnames = ["country", "industry", "commodity", "value"]
        coltypes = ["char(3)", "varchar(15)", "varchar(15)", "float"]
        make_table = SQLTable(tablename, colnames, coltypes).create()

        filename = "IntSUT%s_row_Apr12.xls" % str(year)[2:4]
        subdir = os.path.join("wiod", "intsuts_analytic")
        path = fileutils.getcache(filename, subdir)
        wb = xlrd.open_workbook(path)

        for country in config.countries.keys():
            sheet = wb.sheet_by_name("USE_%s" % country)
            industry_row = sheet.row_values(0)
            row = sheet.row_values(1)
            industry_codes = []
            for (code, desc) in zip(industry_row, row):
                industry_codes.append(industry_tracker.set_code(code, desc))
    
            for i in range(2, sheet.nrows):
                row = sheet.row_values(i)

                # notes say Use tables are broken down by origin
                from_country = row[1]

                # stupid hack so i don't have to change char(3)
                if from_country == "ZROW":
                    from_country = "RoW"

                com_code = commodity_tracker.set_code(row[2], row[3])
                if not com_code:
                    continue
                for j in range(4, len(row)):
                    value = row[j]
                    ind_code = industry_codes[j]
                    if value != 0 and ind_code:
                        # commodity first
                        use_table.insert(
                            [from_country, country, com_code, ind_code, value])

            sheet = wb.sheet_by_name("SUP_%s" % country)
            industry_row = sheet.row_values(0)
            row = sheet.row_values(1)
            industry_codes = []
            for (code, desc) in zip(industry_row, row):
                industry_codes.append(industry_tracker.set_code(code, desc))
    
            for i in range(2, sheet.nrows):
                row = sheet.row_values(i)
                com_code = commodity_tracker.set_code(row[1], row[2])
                if not com_code:
                    continue
                for j in range(3, len(row)):
                    value = row[j]
                    ind_code = industry_codes[j]
                    if value != 0 and ind_code:
                        # industry first
                        make_table.insert(
                            [country, ind_code, com_code, value])




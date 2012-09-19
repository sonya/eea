#!/usr/bin/python3

import xlrd

from uk import config
from common import fileutils, regexes
from common.dbhelper import SQLTable
from common.dbconnect import db
from common.parserutils import HybridTableCreator

def doparse():
    parse_map()
    parse_io()
    parse_env()
    create_views()

def create_views():
    for year in config.STUDY_YEARS:
        strings = {
            "year": year,
            "schema": config.SCHEMA,
            }
        sql = """CREATE OR REPLACE VIEW %(schema)s.ixi_view_%(year)d AS
            SELECT codes.to_code as from_sector,
                   io.to_sector, sum(io.value) as value
              FROM uk.ixi_%(year)d io,
                   (SELECT DISTINCT from_code, to_code
                      FROM %(schema)s.code_map
                     WHERE from_code is not null
                       AND to_code is not null) codes
             WHERE io.from_sector = codes.from_code
             GROUP BY codes.to_code, io.to_sector""" % strings
        db.execute(sql)

def parse_map():
    table = SQLTable("%s.code_map" % config.SCHEMA,
                     ["from_code", "to_code", "env_code",
                      "harmonized", "description"],
                     ["varchar(3)", "varchar(6)", "varchar(31)",
                      "char(3)", "text"]).create()
    table.truncate()

    filename = "code_map.xls"
    path = fileutils.getdatapath(filename, "uk")
    wb = xlrd.open_workbook(path)
    sheet = wb.sheet_by_index(0)

    def sanitize_code(code):
        if type(code) is float:
            code = str(int(code))
        if not len(code):
            code = None
        return code

    for i in range(1, sheet.nrows):
        row = sheet.row_values(i)
        from_code = sanitize_code(row[0])
        to_code = sanitize_code(row[2])
        env_code = sanitize_code(row[4])
        harmonized = sanitize_code(row[6])
        desc = row[7].strip()

        table.insert([from_code, to_code, env_code, harmonized, desc])

def parse_env():
    filename = "rftghgemissions.xls"
    path = fileutils.getcache(filename, "uk")
    wb = xlrd.open_workbook(path)
    sheets = wb.sheets()

    tables = HybridTableCreator(config.SCHEMA)
    codes = tables.new_sector_codes(prefix="env_ind")

    codes.add_curated_codes({
            "Manufacture of petrochemicals": "20.1[467]+20.6",
            "Manufacture of other basic metals & casting (excl. Nuclear fuel & Aluminium)": "24.4[^26]-5",
            "Rest of repair; Installation": "33.1[^56]",
            })

    for sheet in sheets:
        series = sheet.name
        years = None
        for i in range(sheet.nrows):
            row = sheet.row_values(i)
            if len(row) < 3 or type(row[2]) is str and not len(row[2]):
                continue
            if years is None:
                if type(row[2]) is float:
                    years = row
                    for year in row[2:]:
                        #envtable.add_env_table("env", year)
                        tables.add_env_table(year)
            else:
                code = codes.set_code(row[0], row[1])
                if code:
                    for i in range(2, len(row)):
                        tables.insert_env(years[i], code, series, row[i])

    codes.update_codes()

# format of io tables is
# - supply (total output)
# - combined use (i-o)
# - final demand
# - (2004-8 only) pce product categories mapped to household final demand
# - (2004-8 only) industry by industry gross fixed capital formation

def parse_io():
    tables = HybridTableCreator(config.SCHEMA)

    codes = tables.new_sector_codes(prefix="ind")
    codes.add_curated_codes(config.curated_sectors)
    codes.blacklist_code("Differences between totals and sums of components are due to rounding")

    filename = "bb09-su-tables-1992-2003.xls"
    path = fileutils.getcache(filename, "uk")
    wb = xlrd.open_workbook(path)
    for year in range(1992, 2004):
        parse_ixi_year(tables, codes, wb, year)

    filename = "input-output-supply-and-use-tables--2004-2008.xls"
    path = fileutils.getcache(filename, "uk")
    wb = xlrd.open_workbook(path)
    for year in range(2004, 2009):
        parse_ixi_year(tables, codes, wb, year)

    codes.update_codes()

def parse_ixi_year(tables, codes, workbook, year):
    tables.add_io_table(year)

    # parse intermediate demand
    sheet = workbook.sheet_by_name("Table 2 - Int Con %d" % year)
    temp_ind_codes = None
    ind_codes = []
    ind_names = None
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        if len(row) < 3:
            continue
        if temp_ind_codes is None:
            if type(row[2]) is float or regexes.is_num(row[2]):
                temp_ind_codes = row
        elif ind_names is None:
            ind_names = row
            for (code, name) in zip(temp_ind_codes, ind_names):
                ind_codes.append(codes.set_code(code, name))
        else:
            from_code = codes.set_code(row[0], row[1])
            if from_code:
                for i in range(2, len(row)):
                    tables.insert_io(year, from_code, ind_codes[i], row[i])

    # parse final demand
    sheet = workbook.sheet_by_name("Table 2 - Final Demand %d" % year)
    fd_codes = []
    fd_names = None
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        if len(row) < 3:
            continue
        if fd_names is None:
            if row[1].strip() == "Product":
                fd_names = row
                for name in fd_names:
                    fd_codes.append(codes.set_code(None, name))
        else:
            from_code = codes.set_code(row[0], row[1])
            if from_code:
                for i in range(2, len(row)):
                    tables.insert_io(year, from_code, fd_codes[i], row[i])

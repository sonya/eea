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

import openpyxl, xlrd

from jp import config
from common import fileutils, regexes
from common.dbhelper import SQLTable
from common.parserutils import HybridTableCreator

def doparse():
    parse_io()
    parse_env()
    parse_codes()

def parse_io():
    # choose 中分類 for all io tables.
    # 中分類 for 1990 and 1995 don't break down the electronic
    # sectors as far as i would like, so use 小分類
    files = {
        1990: "l00_21.xls",
        1995: "l00_21.xls",
        2000: "io00a301.xls",
        2005: "io05a301.xls",
        }

    tables = HybridTableCreator(config.SCHEMA)

    for (year, filename) in files.items():
        # 1995 and 2000 io tables: easiest
        tables.add_io_table(year)
        codes = tables.new_sector_codes(year)

        # for 1995 use the heisei 2-7-12 file since it has more
        # harmonized sectors than the standalone 1995 file
        if year == 1995:
            sheetindex = 2
        else:
            # the first page of the heisei 2-7-12 file (used for 1990)
            # happens to be 1990 at nominal prices, matching the others
            sheetindex = 0

        path = fileutils.getcache(filename, "jp", str(year))
        wb = xlrd.open_workbook(path)
        sheet = wb.sheet_by_index(sheetindex)
        ind_names = None
        ind_codes = None
        for i in range(sheet.nrows):
            row = sheet.row_values(i)
            if ind_codes is None:
                for cell in row:
                    if cell == 1:
                        ind_codes = [str(c).strip().rjust(3, "0")
                                      for c in row]
                        break
                    if cell.strip() == "001":
                        ind_codes = row
                        break
            elif ind_names is None:
                ind_names = row
                temp_codes = [None, None]
                for i in range(2, len(row)):
                    temp_codes.append(
                        codes.set_code(ind_codes[i], row[i]))
                ind_codes = temp_codes
            else:
                from_code = row[0]
                if type(from_code) is float:
                    from_code = str(int(from_code)).rjust(3, "0")
                from_code = codes.set_code(from_code, row[1])
                if from_code:
                    for i in range(2, len(row)):
                        to_code = ind_codes[i]
                        value = row[i]
                        tables.insert_io(year, from_code, to_code, value)
 
        codes.update_codes()

def parse_env():

    files = {
        # 2005 only has 細分類 while
        1990: "ei90187p.xls",
        1995: "ei95186p.xls",
        2000: "ei2000p104v01j.xls",
        2005: "ei2005pc403jp_wt_bd.xlsx",
        }

    def series_names_from_rows(names, units):
        # since these tables are structured identically
        # we'll just do some hard coding
        series_names = []
        for i in range(3, len(names)):
            if len(names[i]):
                name = "%s (%s)" % (names[i], units[i])
            else:
                name = None
            series_names.append(name)
        return series_names

    tables = HybridTableCreator(config.SCHEMA)

    for (year, filename) in files.items():
        tables.add_env_table(year, series_max_length=255)
        codes = tables.new_sector_codes(year, "env_ind")
        codes.curate_code_from_desc("総合計", "total")
        codes.blacklist_code("total")

        path = fileutils.getcache(filename, "jp", str(year))
        if filename.endswith("xls"):
            wb = xlrd.open_workbook(path)
            # each xls file starts with ToC listing tables A-E.
            # E1: 部門別直接エネルギー消費量，エネルギー原単位を掲載
            # E2: 部門別直接CO2排出量，CO2排出原単位を掲載
            for sheetname in ("E1", "E2"):
                sheet = wb.sheet_by_name(sheetname)
                min_series_col = 4 # first col whose values interest us
                if sheetname == "E1":
                    min_series_col = 3 # GDP - only want this once
    
                series_names = series_names_from_rows(
                    sheet.row_values(0),
                    sheet.row_values(1))

                for i in range(2, sheet.nrows):
                    row = sheet.row_values(i)
                    code = row[1]
                    if type(code) is float:
                        code = str(int(code)).rjust(3, "0")
                    code = codes.set_code(code, row[2])
                    if code:
                        for (series, value) in zip(series_names, row[3:]):
                            if type(value) is float:
                                tables.insert_env(year, code, series, value)
    
        elif filename.endswith("xlsx"):
            wb = openpyxl.load_workbook(filename=path, use_iterators=True)
            # E: 部門別直接エネルギー消費量および各種GHG排出量，
            #    エネルギー原単位およびGHG原単位を掲載
            sheet = wb.get_sheet_by_name("E")
            rows = sheet.iter_rows()
            series_names = series_names_from_rows(
                [cell.internal_value for cell in next(rows)],
                [cell.internal_value for cell in next(rows)])
            for row in rows:
                code = codes.set_code(row[1].internal_value,
                                      row[2].internal_value)
                if code:
                    for (series, cell) in zip(series_names, row[3:]):
                        if cell.internal_value is not None:
                            tables.insert_env(year, code, series,
                                              cell.internal_value)

        codes.update_codes()

def parse_codes():
    # parse sector maps
    path = fileutils.getdatapath("io_env_map.xls", "jp")
    wb = xlrd.open_workbook(path)

    io_tables = {}
    env_tables = {}

    harmonized_sectors = {}
    harmonized_table = SQLTable(
        "%s.harmonized_codes" % config.SCHEMA,
        ["code", "description"],
        ["char(3)", "varchar(63)"]).create()

    for year in config.STUDY_YEARS:
        # all io codes are in one sheet, parse afterward
        io_tables[year] = SQLTable(
            "%s.io_map_%d" % (config.SCHEMA, year),
            ["io_sector", "description", "harmonized"],
            ["char(3)", "varchar(63)", "char(3)"]).create()
        io_tables[year].truncate()

        # parse env codes
        env_table = SQLTable(
            "%s.env_map_%d" % (config.SCHEMA, year),
            ["env_sector", "description", "harmonized"],
            ["varchar(7)", "varchar(63)", "char(3)"]).create()
        env_table.truncate()

        sheet = wb.sheet_by_name(str(year))
        for i in range(1, sheet.nrows):
            row = sheet.row_values(i)
            code = row[0]
            if type(code) is float:
                # 2005 codes are 5 or more digits so this just trims .0
                code = str(int(code)).rjust(3, "0")
            desc = row[1]
            h_code = row[2]
            if type(h_code) is float:
                h_code = str(int(h_code)).rjust(3, "0")
            env_table.insert([code, desc, h_code])

            if h_code not in harmonized_sectors:
                h_desc = row[3]
                harmonized_sectors[h_code] = 1
                harmonized_table.insert([h_code, h_desc])

    sheet = wb.sheet_by_name("io")
    positions = {}
    header = sheet.row_values(0)
    for i in range(len(header)):
        if type(header[i]) is float:
            positions[int(header[i])] = i
        elif header[i] == "harmonized":
            positions["harmonized"] = i

    for i in range(1, sheet.nrows):
        row = sheet.row_values(i)
        for year in config.STUDY_YEARS:
            code = row[positions[year]]
            if type(code) is float:
                code = str(int(code)).rjust(3, "0")
            if code is None or not len(code):
                continue
            desc = row[positions[year] + 1]

            h_code = row[positions["harmonized"]]
            if type(h_code) is float:
                h_code = str(int(h_code)).rjust(3, "0")

            io_tables[year].insert([code, desc, h_code])



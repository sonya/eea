#!/usr/bin/python3
#
# this script parses a pile of html files where tables
# are used in many ways to align things on the screen
# in human-readable and accessibility-unfriendly ways
#

import os, re
import bs4, xlrd
from bs4 import BeautifulSoup
from common import fileutils, regexes
from common.dbconnect import db
from common.dbhelper import SQLTable
from common.parserutils import HybridTableCreator
from cn import config

def doparse():
    parse_io()
    #parse_env()

def parse_io():
    files = {
        2005: fileutils.getdatapath("2005年42部门投入产出流量表.xls", "cn-io"),
        2007: fileutils.getdatapath(
            "0101.xls", "cn-io", "中国投入产出表2007", "excel"),
        }

    tables = HybridTableCreator(config.SCHEMA)

    for (year, filename) in files.items():
        tables.add_io_table(year)
        codes = tables.new_sector_codes(year)

        wb = xlrd.open_workbook(filename)
        # in 2005 sheet 0 is x10k RMB, 2007 has only 1 sheet @x10k RMB
        sheet = wb.sheet_by_index(0)

        ind_codes = None

        # the excel files also have this evil problem of merging
        # cells for appearance and not meaning.  we only have 2
        # years so curate them
        codes.set_code("FU101", "农村居民消费")
        codes.set_code("FU102", "城镇居民消费")
        codes.set_code("FU103", "政府消费支出")
        codes.set_code("FU201", "固定资本形成总额")
        codes.set_code("FU202", "存货增加")
        codes.set_code("GCF", "资本形成合计")
        codes.set_code("EX", "出口")

        codes.blacklist_code("TI")
        codes.blacklist_code("TII")

        for i in range(sheet.nrows):
            row = sheet.row_values(i)
            if ind_codes is None:
                for cell in row:
                    if type(cell) is str and cell.strip("0") == "1":
                        ind_codes = []
                        break
                if ind_codes is not None:
                    for cell in row[3:]:
                        if type(cell) is float:
                            cell = str(int(cell))
                        if regexes.is_num(cell) or table.has_code(cell):
                            ind_codes.append(cell)
                        else:
                            ind_codes.append(None)
            else:
                from_code = codes.set_code(row[2], row[1])
                if from_code:
                    for (value, to_code) in zip(row[3:], ind_codes):
                        if to_code is not None:
                            tables.insert_io(year, from_code, to_code, value)

        codes.update_codes()

### html parsing functions

def is_tag(node):
    return type(node) is bs4.element.Tag

def is_row(node):
    return is_tag(node) and node.name == "tr"

def is_cell(node):
    return is_tag(node) and node.name == "td"

english_filter = re.compile("(.+[^A-Za-z0-9\s&,])([A-Za-z0-9\s,&]+)")
def split_english(string):
    string = string.strip()
    match = english_filter.match(string)
    if match:
        return (match.group(1).strip(), match.group(2).strip())
    return (string, None)

# this parses all the year directories in cache dir
# even though we only have two study years (i.e. years with both
# io and env data)
def parse_env():
    cache_dirs = fileutils.getcachecontents("cn")

    for adir in cache_dirs:
        if regexes.is_num(adir):
            year = int(adir)
        else:
            continue
    
        db_table = SQLTable("cn.emissions_%d" % year,
                            ["industry_zh", "industry_en",
                             "pollutant", "amount"],
                            ["varchar(1023)", "varchar(1023)",
                             "varchar(1023)", "float"])
        db_table.drop()
        db_table.create()
    
        def insert_row(rowdata, columns, max_sector_column):
            if max_sector_column == 0:
                (ind_zh, ind_en) = split_english(rowdata[0])
            else:
                ind_zh = rowdata[0]
                ind_en = rowdata[1]
    
            for (pollutant, amount) in zip(columns[max_sector_column+1:],
                                           rowdata[max_sector_column+1:]):
                if (len(amount)):
                    db_table.insert([ind_zh, ind_en, pollutant, amount])
    
        xact = db.xact(mode="READ WRITE")
        xact.begin()
    
        subdir = os.path.join("cn", adir)
        files = fileutils.getcachecontents(subdir)
        for filename in files:
            filepath = fileutils.getcache(filename, subdir)
            fh = open(filepath, "rb") # binary b/c of non-utf encoding
            html = fh.read()
            fh.close()
            soup = BeautifulSoup(html)
    
            print(adir, filename)
            title = soup.title.string
    
            # mad maaad nested tables!
            # we'll just have to find one with a large number of rows
            # and hope that's the right one
            table = None
            for test_table in soup.find_all("table"):
                if test_table.tbody:
                    test_table = test_table.tbody
                num_rows = len(list(filter(is_row, test_table.children)))
                if num_rows > 10:
                    table = test_table
                    break
    
            columns = None
            did_have_numbers = False # true after we've parsed through
            max_sector_column = 0 # 1 if english separate, 0 otherwise
    
            prev_rowdata = None
            prev_rowspans = None
            data = []
    
            # long cell values are often expanded into the cell directly
            # below (multiple rows) resulting in rows that are blank
            # except in cells that contain overflow.
            # this necessitates to keep state using heuristics.
            insert_later = None
            insert_now = None
    
            for row in table.children:
                if not is_tag(row) or row.name != "tr":
                    continue
    
                rowspans = []
                rowdata = []
    
                # multi-row cells precede sub-parts of the pollutant
                # which can't be distinguished without their parent
                prefix = None
    
                cells = list(filter(is_cell, row.children))
                rowlen = len(cells)
    
                for cellpos in range(rowlen):
                    cell = cells[cellpos]
    
                    rowspan = 1
                    if "rowspan" in cell.attrs:
                        rowspan = int(cell["rowspan"])
    
                    cellvalue = cell.text.strip().strip(".")\
                        .replace('…', '').replace('\xa0', '')
    
                    # use previous rowspan if we have one of the buggy blank
                    # cells at the end, which don't have the proper rowspan
                    if cellpos == rowlen - 1 and \
                            len(cellvalue) == 0 and len(rowspans) > 0:
                        rowspan = rowspans[-1]
    
                    # if the cell directly before us in the previous row
                    # spanned multiple rows, create a blank space in this row.
                    # the abs difference below is used for counting down:
                    # if rowspan in previous column was 6 and current is 1
                    # the difference is -5, on the next row that will
                    # be subtracted again
                    if prev_rowspans is not None:
                        i = len(rowdata)
                        while i < len(prev_rowspans) and \
                                abs(prev_rowspans[i]) > rowspan:
                            rowdata.append('')
                            rowspans.append(-abs(
                                    abs(rowspan) - abs(prev_rowspans[i])))
                            i = len(rowdata)
    
                    rowdata.append(cellvalue)
                    rowspans.append(rowspan)
    
                # count any multi-row cells that were at the end
                if prev_rowdata is not None:
                    for i in range(len(rowdata), len(prev_rowdata)):
                        if prev_rowspans[i] > rowspan: # span of last cell
                            rowdata.append(prev_rowdata[i])
                            rowspans.append(rowspan)
    
                # remove blank cells at the end - these appear to be bugs
                while len(rowdata) and len(rowdata[-1]) == 0 and \
                        (columns is None or len(rowdata) != len(columns)):
                    rowdata.pop()
                    rowspans.pop()
    
                # end of rowdata manipulation
                prev_rowdata = rowdata
                prev_rowspans = rowspans
    
                if len(rowdata) == 0:
                    continue
    
                # ignore rows that they put above the column headers
                # we'll just special case anything we find
                if columns is None and rowdata[0].startswith("单位"):
                    prev_rowdata = None
                    prev_rowspans = None
                    continue
    
                lengths = [len(x) for x in rowdata]
                if sum(lengths) == 0: # all blank strings
                    continue
    
                # if we're sure we have columns, clean up rowdata so 
                # the multirow rules don't get applied anymore
                if sum(rowspans) == rowspan * len(rowspans):
                    rowspans = [1]*len(rowspans)
    
                has_numbers = False
                for field in rowdata:
                    if regexes.is_num(field):
                        has_numbers = True
                        did_have_numbers = True
                        break
    
                if has_numbers or insert_later is None:
                    insert_now = insert_later
                    insert_later = rowdata
                else:
                    # decide whether this row is an overflow
                    # already know sum(lengths) > 0
                    if len(rowdata) >= len(insert_later) and \
                            (lengths[0] == 0 or lengths[-1] == 0):
                        # we shouldn't see overflow on both sides
                        # because rowdata[0] should happen in a header row
                        # and rowdata[-1] must happen in a data row
                        for i in range(len(insert_later)):
                            # don't want to append to "hang ye" or "Sector"
                            if not did_have_numbers \
                                    and i > max_sector_column + 1 \
                                    and len(insert_later[i]) == 0:
                                # blank above, assume "multirow" to the left
                                insert_later[i] = insert_later[i-1] + " - "
    
                            if lengths[i]:
                                insert_later[i] += " " + rowdata[i]
    
                    # if we knocked blank cells off the previous row but
                    # we know it's actually longer from the current row
                    for i in range(len(insert_later), len(rowdata)):
                        insert_later.append(rowdata[i])
    
                #if not has_numbers and not did_have_numbers: # near BOF
                if insert_now is not None and columns is None:
                    columns = insert_now
                    insert_now = None
    
                    for i in range(len(columns)):
                        columns[i] = columns[i].replace("\n", " ")
    
                    # figure out if english names are separate or not
                    if len(columns) > 1 and columns[1].strip() == "Sector":
                        max_sector_column = 1
    
                elif insert_now is not None and len(insert_now) == len(columns):
                    insert_row(insert_now, columns, max_sector_column)
                    insert_now = None
                else:
                    # we don't want to get here - debug
                    if insert_now is not None:
                        print(len(insert_now), len(columns), insert_now)
    
            # close the loop
            if insert_later is not None and len(insert_later) == len(columns):
                insert_row(insert_later, columns, max_sector_column)
    
            print(columns)
    
        xact.commit()



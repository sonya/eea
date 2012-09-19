#!/usr/bin/python

import csv, re
from common import fileutils
from common.dbhelper import CSVTable
from common.dbconnect import db
from usa import config

def is_make(filename):
    match = re.match("make-(\d{4}).csv", filename)
    if match:
        return match.group(1)
    return False

def is_use(filename):
    match = re.match("use-(\d{4}).csv", filename)
    if match:
        return match.group(1)
    return False

def doparse():
    parse_tables()
    create_views()

def create_views():
    years = []
    files = fileutils.getcachecontents("io-annual")
    for filename in files:
        year = is_make(filename)
        if year:
            years.append(year)

    for year in years:
        strings = {
            "make_table": "%s.annual_make_%s" % (config.IO_SCHEMA, year),
            "use_table": "%s.annual_use_%s" % (config.IO_SCHEMA, year),
            "cxc_table": "%s.annual_cxc_%s" % (config.IO_SCHEMA, year),
            }

        db.execute("DROP TABLE %(cxc_table)s" % strings)

        db.execute("""SELECT from_sector, to_sector, SUM(value) AS value
          INTO %(cxc_table)s
          FROM (SELECT use.commodity AS from_sector,
                       indshare.commodity AS to_sector,
                       use.value * indshare.output_share AS value
                  FROM (SELECT make.industry,
                               make.commodity,
                               make.value / indtotal.value AS output_share
                          FROM %(make_table)s make,
                               (SELECT industry, SUM(value) AS value
                                  FROM %(make_table)s
                                 GROUP BY industry) indtotal
                         WHERE make.industry = indtotal.industry) indshare,
                       %(use_table)s use
                 WHERE indshare.industry = use.industry
              UNION
                SELECT use.commodity AS from_sector,
                       use.industry AS to_sector,
                       use.value AS value
                  FROM %(use_table)s use
                 WHERE industry NOT IN (SELECT industry
                                          FROM %(make_table)s make
                                         WHERE commodity = 'TIO')
               ) allocations
         GROUP BY from_sector, to_sector""" % strings)

def parse_tables():
    files = fileutils.getcachecontents("io-annual")
    for filename in files:
        path = fileutils.getcache(filename, "io-annual")
        print(path)
        table = CSVTable(path, False)

        make_year = is_make(filename)
        use_year = is_use(filename)
        if make_year:
            table.create_sql_table(
                "%s.annual_make_%s" % (config.IO_SCHEMA, make_year),
                ["industry", "commodity", "value"],
                ["varchar(6)", "varchar(6)", "float"])

        elif use_year:
            table.create_sql_table(
                "%s.annual_use_%s" % (config.IO_SCHEMA, use_year),
                ["commodity", "industry", "value"],
                ["varchar(6)", "varchar(6)", "float"])

        elif filename == "codes.csv":
            table.create_sql_table(
                "%s.annual_codes" % config.IO_SCHEMA,
                ["code", "description"],
                ["varchar(6)", "text"])

        else:
            continue

        table.parse_to_sql()




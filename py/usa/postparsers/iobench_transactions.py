#!/usr/bin/python3

# this script goes through the steps of recreating a commodity
# by commodity transaction table from make and use tables

from usa import bea, config
from common.dbconnect import db

def runsql(sql):
    print(sql)
    db.execute(sql)

def dopostparse():
    for year in config.STUDY_YEARS:
        create_transactions_table(year)
        create_transaction_views(year)

def strings_for_year(year):
    strings = {
        # tables from raw data
        "make_table": "%s.make_%d" % (config.IO_SCHEMA, year),
        "use_table": "%s.use_%d" % (config.IO_SCHEMA, year),

        # intermediate tables
        "indshare_table": "%s.indshares_%d" % (config.IO_SCHEMA, year),
        "intermediate": "%s.intermediate_%d" % (config.IO_SCHEMA, year),
        "finaldemand": "%s.finaldemand_%d" % (config.IO_SCHEMA, year),

        # the table we want to generate
        "xtable": "%s.transactions_%d" % (config.IO_SCHEMA, year),
        "xview": "%s.transact_view_%d" % (config.IO_SCHEMA, year),

        # other
        "import": bea.fd_sectors[year]["imports"],
        }

    if year <= 1977:
        strings["margin_fields"] = ""

    return strings

def create_transactions_table(year):
    strings = strings_for_year(year)

    ### shares of make by industry
    runsql("""
    CREATE OR REPLACE VIEW %(indshare_table)s AS
      SELECT make.industry,
             make.commodity,
             make.thousands / indtotal.thousands AS output_share
        FROM %(make_table)s make,
             (SELECT industry, sum(thousands) AS thousands
                FROM %(make_table)s
               GROUP BY industry) indtotal
       WHERE make.industry = indtotal.industry""" % strings)

    ### intermediate output portion of transactions table
    if year > 1977:
        margin_fields = [("coalesce(use.%s, 0) * " +
                          "coalesce(indshare.output_share, 0) AS %s")
                         % (fieldname, fieldname)
                         for fieldname in bea.use_table_margins]
        strings["margin_fields"] = ",\n           ".join([""] + margin_fields)

    runsql("""
    SELECT use.commodity AS from_sector,
           indshare.commodity AS to_sector,
           use.thousands * indshare.output_share AS thousands %(margin_fields)s
      INTO %(intermediate)s
      FROM %(use_table)s use, %(indshare_table)s indshare
     WHERE indshare.industry = use.industry""" % strings)

    ### final demand portion of transactions table
    if year > 1977:
        strings["margin_fields"] = ", ".join([""] + bea.use_table_margins)

    runsql("""
    SELECT commodity AS from_sector,
           industry AS to_sector,
           thousands %(margin_fields)s
      INTO %(finaldemand)s
      FROM %(use_table)s use
     WHERE industry NOT IN (SELECT distinct industry
                              FROM %(make_table)s)""" % strings)

    ### transactions table
    strings = strings_for_year(year)

    runsql("DROP TABLE IF EXISTS %s CASCADE" % strings["xtable"])

    if year > 1977:
        margin_fields = ["CAST(SUM(%s) AS INT) AS %s"
                         % (fieldname, fieldname)
                         for fieldname in bea.use_table_margins]
        strings["margin_fields"] = ",\n           ".join([""] + margin_fields)

    runsql("""
    SELECT from_sector, to_sector,
           CAST(SUM(thousands) AS BIGINT) AS thousands %(margin_fields)s
      INTO %(xtable)s
      FROM (SELECT * FROM %(intermediate)s UNION
            SELECT * FROM %(finaldemand)s) alldemand
     GROUP BY from_sector, to_sector""" % strings)

    ### cleanup
    runsql("DROP VIEW %(indshare_table)s" % strings)
    runsql("DROP TABLE %(intermediate)s" % strings)
    runsql("DROP TABLE %(finaldemand)s" % strings)

def create_transaction_views(year):
    strings = strings_for_year(year)

    if year <= 1977:
        strings["plus_margins"] = ""
        strings["minus_margins"] = ""
    else:
        strings["plus_margins"] = """ - margins
                       + truck_margin + rail_margin + water_margin + air_margin
                       + pipe_margin + gaspipe_margin
                       + wholesale_margin + retail_margin"""

        strings["minus_margins"] = """ + margins
                       - truck_margin - rail_margin - water_margin - air_margin
                       - pipe_margin - gaspipe_margin
                       - wholesale_margin - retail_margin"""

    ### transactions view

    # runsql("""
    # CREATE OR REPLACE VIEW %(xview)s AS
    #   SELECT CASE WHEN to_sector = '%(import)s' THEN to_sector
    #               ELSE from_sector END AS from_sector,
    #          CASE WHEN to_sector = '%(import)s' THEN from_sector
    #               ELSE to_sector END AS to_sector,
    #          CASE WHEN to_sector = '%(import)s' THEN - thousands
    #               ELSE thousands END AS fob,
    #          CASE WHEN to_sector = '%(import)s'
    #               THEN -thousands %(minus_margins)s
    #               ELSE thousands %(plus_margins)s END AS cif
    #     FROM %(xtable)s
    #    WHERE thousands <> 0""" % strings)

    runsql("""
    CREATE OR REPLACE VIEW %(xview)s AS
      SELECT from_sector, to_sector, thousands as fob,
             thousands %(plus_margins)s as cif
        FROM %(xtable)s
       WHERE thousands <> 0""" % strings)

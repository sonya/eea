#!/usr/bin/python

import csv, re, xlrd
from usa import config, eia, dbsetup
from common import fileutils, sqlhelper
from common.dbconnect import db

# tables by measurement
pricetable = "%s.seds_price" % config.EIA_SCHEMA
usetable = "%s.seds_use_btu" % config.EIA_SCHEMA

# we need to parse three files before we can populate the yearly
# tables
data = {}

def parse_measurement(filename, measurement, tracker):
    filepath = fileutils.getcache(filename)
    with open(filepath) as f:
        csvf = csv.reader(f)
        header = next(csvf)
        for stryear in header[2:]:
            year = int(stryear)
            if year not in data:
                data[year] = {}
    
        for row in csvf:
            if len(row) == len(header):
                if row[0] == "US":
                    msn = row[1][:4]
                    for i in range(2, len(row)):
                        year = int(header[i])
                        value = row[i].strip()
                        if len(value):
                            if msn not in data[year]:
                                data[year][msn] = {measurement: value}
                            else:
                                data[year][msn][measurement] = value

                            source = msn[0:2]
                            sector = msn[2:4]
                            insert_values = [year, source, sector, float(value)]
                            if measurement == "price":
                                tracker.insert_row(pricetable, insert_values)
                            elif measurement == "use_btu":
                                tracker.insert_row(usetable, insert_values)

def create_consolidated_tables():
    allsources = eia.fossilfuels + eia.elec_sources + \
        eia.nuclear + eia.renewables
    allsectors = ["TC", "AC", "CC", "IC", "RC"] + eia.elec_sectors

    for year in config.STUDY_YEARS:
        strings = {
            "renewables": sqlhelper.set_repr(eia.renewables),
            "elec_sources": sqlhelper.set_repr(eia.elec_sources),
            "elec_sectors": sqlhelper.set_repr(eia.elec_sectors),
            "allsources": sqlhelper.set_repr(allsources),
            "allsectors": sqlhelper.set_repr(allsectors),
            "from_table": "%s.seds_us_%d" % (config.EIA_SCHEMA, year),
            "tablename": "%s.seds_short_%d" % (config.EIA_SCHEMA, year),
            }

        db.execute("DROP TABLE IF EXISTS %(tablename)s CASCADE" % strings)
        db.execute("""
        SELECT source, sector,
               case when sum(use_btu) = 0 then 0
                    else sum(ex) / sum(use_btu) end as price,
               sum(use_btu) as use_btu,
               sum(ex) as ex
          INTO %(tablename)s
          FROM (SELECT case when source in %(renewables)s then 'RE'
                            when source in %(elec_sources)s then 'ES'
                            else source end as source,
                       case when sector in %(elec_sectors)s then 'EI'
                            else sector end as sector,
                       price, use_btu, ex
                  FROM %(from_table)s
                 WHERE source in %(allsources)s
                   AND sector in %(allsectors)s) e
         GROUP by source, sector order by source, sector""" % strings)

def doparse():
    tracker = dbsetup.MultiTableStateTracker()
    
    tracker.create_table(pricetable,
                         ["year", "source", "sector", "price"],
                         ["int", "char(2)", "char(2)", "float"],
                         cascade=True)
    tracker.create_table(usetable,
                         ["year", "source", "sector", "use_btu"],
                         ["int", "char(2)", "char(2)", "float"],
                         cascade=True)
    tracker.warmup()
    
    parse_measurement("eia/pr_all.csv", "price", tracker)
    parse_measurement("eia/use_all_btu.csv", "use_btu", tracker)
    parse_measurement("eia/ex_all.csv", "ex", tracker)
    
    tracker.flush()
    
    # tables by year
    years = sorted(data)
    for year in years:
        tablename = "eia.seds_us_%d" % year
        tracker.create_table(tablename,
                             ["source", "sector", "price", "use_btu", "ex"],
                             ["char(2)", "char(2)", "float", "float", "float"],
                             cascade=True)
        tracker.warmup()
    
        msns = sorted(data[year])
        for msn in msns:
            values = data[year][msn]
            source = msn[0:2]
            sector = msn[2:4]
            insert_values = [source, sector]
            for field in ("price", "use_btu", "ex"):
                next_value = 0 # this will turn out to help our calculations
                if field in values:
                    # convert expenditures to the same units as io table
                    if field == "ex":
                        next_value = float(values[field]) * 1000
                    else:
                        next_value = float(values[field])
                insert_values.append(next_value)
            tracker.insert_row(tablename, insert_values)
    
        tracker.flush()

    create_consolidated_tables()






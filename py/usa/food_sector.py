#!/usr/bin/python
# this has to be run after emissions.py writes out csv files

import csv

from usa import bea, config, eia, common, wiod_code_map
from common.dbconnect import db
from common import fileutils, utils, sqlhelper

old_meat_codes = ["140101", "140102", "140103", "140105"]
new_meat_codes = ["311611", "311612", "311615", "31161A"]

combined_meat_codes = old_meat_codes + new_meat_codes

for year in config.STUDY_YEARS:
    print(year)

    path = fileutils.getcache("fossil_fuel_estimates_%d.csv" % year, "usa")
    fh = open(path, "r")
    csvf = csv.reader(fh)
    io_codes = common.io_codes_for_year(year)

    data = {}
    row = next(csvf)
    for row in csvf:
        if len(row) == 6:
            sector = row[0]
            btu = row[1] # total
            #btu = row[2] # coal
            #btu = row[3] # natural gas
            #btu = row[5] # PA-nontrans
            data[sector] = float(btu)

    pce_vector = common.pce_bridge_vector(
        year, "Food and beverages purchased for off-premises consumption")
    #pce_vector = common.pce_bridge_vector(
    #    year, "Clothing and footwear")

    total_expenditure = 0
    meat_expenditure = 0

    energy_data = {}
    for row in pce_vector.get_rows():
        expenditure = pce_vector.get_element(row)
        if expenditure != 0:
            intensity = data[row]
            if row in combined_meat_codes:
                sector = io_codes[row]
                print(row, sector, intensity)

            total_expenditure += expenditure
            if row in combined_meat_codes:
                meat_expenditure += expenditure

            btu = expenditure * intensity
            energy_data[btu] = row

    print(year, total_expenditure, meat_expenditure / total_expenditure)

    btu_values = sorted(energy_data.keys(), reverse=True)
    for btu in btu_values[:10]:
        code = energy_data[btu]
        sector = io_codes[code]
        #print(code, sector, btu)

    #print(year, sum(energy_data.keys()))

    strings = {
        "tablename": "%s.transact_view_%d" % (config.IO_SCHEMA, year)
        }
    if year < 1997:
        strings["meat_codes"] = sqlhelper.set_repr(old_meat_codes)
    else:
        strings["meat_codes"] = sqlhelper.set_repr(new_meat_codes)

    stmt = db.prepare("""select from_sector, sum(fob)
                          from %(tablename)s
                         where to_sector in %(meat_codes)s
                         group by from_sector
                         order by sum(fob) desc""" % strings)
    result = stmt()
    for row in result[:10]:
        code = row[0]
        expenditure = row[1]
        #print(code, io_codes[code], expenditure)



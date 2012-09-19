import codecs, csv, re, xlrd

from common import fileutils
from common.dbhelper import SQLTable
from wiod import config

def doparse():

    tablename = "%s.world_supplement" % config.WIOD_SCHEMA
    table = SQLTable(tablename,
                     ["year", "country", "measurement", "value"],
                     ["int", "char(3)", "varchar(8)", "float"])
    table.create()
    table.truncate()

    # census data has more complete population counts
    country_fips = {
        "LU": "LUX", "US": "USA", "NL": "NLD", "AU": "AUT", "SW": "SWE",
        "CA": "CAN", "AS": "AUS", "EI": "IRL", "GM": "DEU", "BE": "BEL",
        "TW": "TWN", "DA": "DNK", "UK": "GBR", "FR": "FRA", "JA": "JPN",
        "KS": "KOR", "SP": "ESP", "CY": "CYP", "SI": "SVN", "EZ": "CZE",
        "GR": "GRC", "MT": "MLT", "PO": "PRT", "LO": "SVK", "PL": "POL",
        "EN": "EST", "HU": "HUN", "LH": "LTU", "LG": "LVA", "MX": "MEX",
        "TU": "TUR", "BR": "BRA", "RO": "ROU", "BU": "BGR", "CH": "CHN",
        "ID": "IDN", "IN": "IND", "RS": "RUS", "FI": "FIN", "IT": "ITA",
        }
    
    # this file spec is documented in the xlsx file from the archive
    path = fileutils.getcache("IDBext001.txt", "wsupp")
    with open(path, "r") as fh:
        for line in fh:
            fields = line.split("|")
            if len(fields) == 3:
                fips = fields[0]
                if fips in country_fips:
                    year = int(fields[1])
                    country = country_fips[fips]
                    table.insert([year, country, "pop", int(fields[2])])

    # worldbank data has some deflator data that imf doesn't
    worldbank = {
        "ppp_pc": "NY.GDP.PCAP.PP.KD_Indicator_MetaData_en_EXCEL.xls",
        #"gdp_pc": "NY.GDP.PCAP.CD_Indicator_MetaData_en_EXCEL.xls",
        #"dec": "PA.NUS.ATLS_Indicator_MetaData_en_EXCEL.xls",
        #"pppratio": "PA.NUS.PPPC.RF_Indicator_MetaData_en_EXCEL.xls",
        "deflator": "NY.GDP.DEFL.ZS_Indicator_MetaData_en_EXCEL.xls",
        }
    
    for (indicator, filename) in worldbank.items():
        path = fileutils.getcache(filename, "wsupp")
        wb = xlrd.open_workbook(path)
        sheet = wb.sheet_by_index(0)
        header = [int(x) for x in sheet.row_values(0)[2:]]
        for i in range(1, sheet.nrows):
            row = sheet.row_values(i)
            if row[1] in config.countries:
                country = row[1]
                for (year, value) in zip(header, row[2:]):
                    if type(value) is float and value != 0:
                        table.insert([year, country, indicator, value])

    imf_fields = (
        "LP", # population
        "PPPPC", # ppp per capita
        "NGDPRPC", # gdp per capita in constant prices
        "NGDP_D", # gdp deflator
        )

    # this is actually a csv file despite what it's called
    path = fileutils.getcache("WEOApr2012all.xls", "wsupp")

    with codecs.open(path, "r", "cp1252") as fh:
        csvf = csv.reader(fh, dialect=csv.excel_tab)
        header = next(csvf)
        year_cols = {}

        valid_year = re.compile("\d{4}")
        valid_float = re.compile("-*[\d\.,]+")

        for i in range(len(header)):
            if header[i] == "ISO":
                country_col = i
            elif header[i] == "WEO Subject Code":
                subject_col = i
            elif valid_year.match(header[i]):
                year_cols[int(header[i])] = i
            elif header[i] == "Estimates Start After":
                last_year_col = i

        for row in csvf:
            if len(row) > subject_col and row[subject_col] in imf_fields:
                field = row[subject_col]
                country = row[country_col]
                if country not in config.countries:
                    continue
                if valid_year.match(row[last_year_col]):
                    last_year = int(row[last_year_col])
                else:
                    # not clear if this means all values are estimated
                    last_year = 9999
                for (year, colnum) in year_cols.items():
                    value = row[colnum]
                    if valid_float.match(value): #and year < last_year:
                        table.insert([year, country, field,
                                      float(value.replace(",", ""))])



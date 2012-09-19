import datetime, xlrd

from common import fileutils
from common.dbhelper import SQLTable

def doparse():

    # ppp rank from
    # https://www.cia.gov/library/publications/the-world-factbook/rankorder/2004rank.html
    countries = {
        "LUX": {"fips": "LU", "ppp": 3},
        "USA": {"fips": "US", "ppp": 11},
        "NLD": {"fips": "NL", "ppp": 17},
        "AUT": {"fips": "AU", "ppp": 18},
        "SWE": {"fips": "SW", "ppp": 21},
        "CAN": {"fips": "CA", "ppp": 20},
        "AUS": {"fips": "AS", "ppp": 22},
        "IRL": {"fips": "EI", "ppp": 23},
        "DEU": {"fips": "GM", "ppp": 26},
        "TWN": {"fips": "TW", "ppp": 27},
        "BEL": {"fips": "BE", "ppp": 28},
        "DNK": {"fips": "DK", "ppp": 29},
        "FIN": {"fips": "FI", "ppp": 32},
        "GBR": {"fips": "UK", "ppp": 33},
        "FRA": {"fips": "FR", "ppp": 35},
        "JPN": {"fips": "JA", "ppp": 36},
        "KOR": {"fips": "KS", "ppp": 40},
        "ESP": {"fips": "SP", "ppp": 43},
        "ITA": {"fips": "IT", "ppp": 44},
        "CYP": {"fips": "CY", "ppp": 46},
        "SVN": {"fips": "SI", "ppp": 47},
        "CZE": {"fips": "EZ", "ppp": 50}, # EZ??
        "GRC": {"fips": "GR", "ppp": 52},
        "MLT": {"fips": "MT", "ppp": 53},
        "PRT": {"fips": "PO", "ppp": 57},
        "SVK": {"fips": "LO", "ppp": 58},
        "POL": {"fips": "PL", "ppp": 60},
        "EST": {"fips": "EN", "ppp": 61},
        "HUN": {"fips": "HU", "ppp": 63},
        "LTU": {"fips": "LH", "ppp": 65},
        "RUS": {"fips": "RS", "ppp": 71},
        "LVA": {"fips": "LG", "ppp": 75},
        "MEX": {"fips": "MX", "ppp": 85},
        "TUR": {"fips": "TU", "ppp": 86},
        "BRA": {"fips": "BR", "ppp": 92},
        "ROU": {"fips": "RO", "ppp": 97},
        "BGR": {"fips": "BU", "ppp": 101},
        "CHN": {"fips": "CH", "ppp": 121},
        "IDN": {"fips": "ID", "ppp": 156},
        "IND": {"fips": "IN", "ppp": 164},
        }
    
    tablename = "world_supplement"
    table = SQLTable(tablename,
                     ["year", "country", "pop", "gdp", "ppp"],
                     ["int", "char(3)", "int", "float", "float"]).create()
    table.truncate()
    
    country_fips = {}
    data = {}
    for (country, info) in countries.items():
        data[country] = {}
        country_fips[info["fips"]] = country
    
    # this file spec is documented in the xlsx file from the archive
    thisyear = datetime.datetime.now().year
    path = fileutils.getcache("IDBext001.txt", "wsupp")
    with open(path, "r") as fh:
        for line in fh:
            fields = line.split("|")
            if len(fields) == 3:
                fips = fields[0]
                if fips in country_fips:
                    year = int(fields[1])
                    if year >= thisyear: # we don't want future projections
                        continue
                    country = country_fips[fips]
                    data[country][year] = {"pop": int(fields[2])}
    
    worldbank = {
        "ppp": "NY.GNP.PCAP.PP.CD_Indicator_MetaData_en_EXCEL.xls",
        "gdp": "NY.GDP.PCAP.CD_Indicator_MetaData_en_EXCEL.xls",
        }
    
    for (indicator, filename) in worldbank.items():
        path = fileutils.getcache(filename, "wsupp")
        wb = xlrd.open_workbook(path)
        sheet = wb.sheet_by_index(0)
        header = [int(x) for x in sheet.row_values(0)[2:]]
        for i in range(1, sheet.nrows):
            row = sheet.row_values(i)
            if row[1] in countries:
                country = row[1]
                for (year, value) in zip(header, row[2:]):
                    # this discards years where we don't have population
                    if year in data[country] and \
                            type(value) is float and value != 0:
                        data[country][year][indicator] = value
    
    for (country, country_data) in data.items():
        for (year, year_data) in country_data.items():
            ppp = None
            gdp = None
            pop = year_data["pop"]
            if "gdp" in year_data:
                gdp = year_data["gdp"]
            if "ppp" in year_data:
                ppp = year_data["ppp"]

            table.insert([year, country, pop, gdp, ppp])

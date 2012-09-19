from common.dbhelper import SQLTable
from usa import config

TABLE_NAME = "%s.implicit_price_deflators" % config.NIPA_SCHEMA

# class representing the inflation table
class Deflators:

    def __init__(self):
        self.gdp_deflators = {}
        self.pce_deflators = {}

        table = SQLTable(TABLE_NAME,
                         ["year", "gdp", "pce"],
                         ["int", "float", "float"])
        result = table.getall()
        for row in result:
            year = row[0]
            self.gdp_deflators[year] = row[1]
            self.pce_deflators[year] = row[2]

    def get_gdp_deflator(self, year):
        return 100 / self.gdp_deflators[year]

    def get_pce_deflator(self, year):
        return 100 / self.pce_deflators[year]



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

from wiod import config
from common.dbconnect import db
import common.config

def get_imf_data():
    try:
        single = IMFData()
    except IMFData as s:
        single = s
    return single

def convert_to_2005(amount, country, year):
    return get_imf_data().current_to_chained(amount, country, year, 2005)

def get_2005_deflator(country, year):
    return get_imf_data().get_chained_deflator(country, year, 2005)

def get_chained_exrate(country, year, base_year):
    return get_imf_data.get_chained_exrate(country, year, base_year)

def get_imf_value(country, year, measurement):
    return get_imf_data().get_imf_value(country, year, measurement)

class IMFData(Exception):

    __static = None

    def __init__(self):
        if IMFData.__static:
            raise IMFData.__static

        self.rates = {}
        self.deflators = {}
        self.generic_stmt = db.prepare("""
            SELECT value FROM %s.world_supplement
             WHERE country = $1
               AND year = $2
               AND measurement = $3""" % config.WIOD_SCHEMA)

        IMFData.__static = self

    def get_imf_value(self, country, year, measurement):
        result = self.generic_stmt(country, year, measurement)
        if len(result) and len(result[0]):
            return result[0][0]
        elif common.config.DEBUG_MODE:
            print("warning: no value for %s, %d, %s"
                  % (country, year, measurement))
        return None

    def get_exchange_rate(self, country, year):
        if country not in self.rates:
            self.rates[country] = {}
        if year not in self.rates[country]:
            sql = """SELECT rate FROM %s.exchange_rates
                      WHERE country = $1
                        AND year = $2""" % config.WIOD_SCHEMA
            stmt = db.prepare(sql)
            result = stmt(country, year)
            if len(result) and len(result[0]):
                self.rates[country][year] = result[0][0]
            elif common.config.DEBUG_MODE:
                print("warning: no exchange rate for %s, %d)" % (country, year))

        return self.rates[country][year]

    def get_gdp_deflator(self, country, year):
        if country not in self.deflators:
            self.deflators[country] = {}
        if year not in self.deflators[country]:
            deflator = self.get_imf_value(country, year, "NGDP_D")
            if deflator is not None:
                self.deflators[country][year] = deflator
            else:
                deflator = self.get_imf_value(country, year, "deflator")
                if deflator is not None:
                    self.deflators[country][year] = deflator
        return self.deflators[country][year]

    def get_chained_exrate(self, country, current_year, base_year):
        exrate = self.get_exchange_rate(country, current_year)
        return exrate * self.get_chained_deflator(
            country, current_year, base_year)

    def get_chained_deflator(self, country, current_year, base_year):
        base_rate = self.get_exchange_rate(country, base_year)
        current_rate = self.get_exchange_rate(country, current_year)
        base_deflator = self.get_gdp_deflator(country, base_year)
        current_deflator = self.get_gdp_deflator(country, current_year)
        return base_rate / current_rate * base_deflator / current_deflator

    def current_to_chained(self, amount, country, current_year, base_year):
        return amount * self.get_chained_deflator(
            country, current_year, base_year)






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

# this file downloads exchange rate data from stlouisfed and generates
# python file containing the data retrieved.
# i'm too lazy to figure out whether it's a bad idea to have these data
# be gathered and stored differently from the larger datasets.

import os, re, urllib.request
import common
from common import config

code_dir = os.path.join(config.PROJECT_ROOT, "code", "py", "common")

def get_rate(country, year):
    country_file = "rates_" + country
    filepath = os.path.join(code_dir, country_file + ".py")

    if not os.path.exists(filepath):
        # TODO rates is empty when first returned
        rates = download_rates(country, filepath)
    else:
        __import__("common." + country_file)
        ratemod = getattr(common, country_file)
        rates = ratemod.rates

    return rates[year]

def download_rates(country, filepath):
    urls = {
        # ca is usd / cad, jp is usd / jpy.
        # uk is gbp / usd, eu is eur / usd
        # for now just let individual country packages remember this
        "ca": "http://research.stlouisfed.org/fred2/data/AEXCAUS.txt",
        "jp": "http://research.stlouisfed.org/fred2/data/AEXJPUS.txt",
        "uk": "http://research.stlouisfed.org/fred2/data/AEXUSUK.txt",
        "eu": "http://research.stlouisfed.org/fred2/data/AEXUSEU.txt",
        }

    url = urls[country]
    (temp, headers) = urllib.request.urlretrieve(url)

    datepat = re.compile("\d{4}-\d{2}-\d{2}")
    rates = {}
    with open(temp, "r") as fh:
        for line in fh:
            if not datepat.match(line):
                continue
            parts = line.split()
            year = parts[0].split("-")[0]
            value = float(parts[1])
            rates[year] = value

    outfile = open(filepath, "w")
    outfile.write("rates = {\n")
    outfile.write("    " + "\n    ".join(
        ["%s: %.4f," % (year, rates[year]) for year in sorted(rates.keys())]))
    outfile.write("    }")
    outfile.close()

    return rates

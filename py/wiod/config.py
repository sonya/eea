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

WIOD_SCHEMA = "wiod"
UN_SCHEMA = "un"

STUDY_YEARS = range(1995, 2010)

country_rough_sort = [
    "CHN", "USA", "RUS", "IND", "DEU", "JPN", "GBR",
    "POL", "AUS", "ITA", "CAN", "KOR", "MEX", "ESP",
    "ROU", "TWN", "IDN", "CZE", "NLD", "GRC", "TUR",
    "BRA", "FRA", "DNK", "BGR", "BEL", "HUN", "PRT",
    "EST", "IRL", "AUT", "SWE", "FIN", "SVK", "LTU",
    "SVN", "LVA", "CYP", "MLT", "LUX"
    ]

annex_b_countries = {
    -8: ["AUT", "BEL", "BGR", "CZE", "DNK", "EST",
         "FIN", "FRA", "DEU", "GRC", "IRL", "ITA",
         "LVA", "LTU", "LUX", "NLD", "PRT", "ROU", 
         "ESP", "SVK", "SVN", "SWE", "GBR"],
     -7: ["USA"],
     -6: ["CAN", "HUN", "JPN", "POL"],
     0: ["RUS"],
     8: ["AUS"],
    }

eu15 = ["AUT", "BEL", "DNK", "FRA", "FIN", "DEU", "GRC",
        "IRL", "ITA", "LUX", "NLD", "PRT", "ESP", "SWE", "GBR"]

other_eu = [
    "BGR", "CZE", "EST", "LVA", "LTU",
    "POL", "ROU", "SVK", "SVN", "HUN"]
north_am = ["USA", "CAN", "MEX"]

bric = ["BRA", "RUS", "IND", "CHN"]

other_asia = ["JPN", "KOR", "TWN"]
all_asia = ["JPN", "KOR", "TWN", "IDN", "IND", "CHN"]

non_annex_b = [
    "BRA", "MLT", "TUR", "MEX", "KOR",
    "TWN", "IDN", "IND", "CHN"]

bad_data_blacklist = ["HUN", "LUX", "MLT", "SVN"]

countries = {
    "AUS": "Australia",
    "AUT": "Austria",
    "BEL": "Belgium",
    "BGR": "Bulgaria",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CHN": "China",
    "CYP": "Cyprus",
    "CZE": "Czech Rep.",
    "DEU": "Germany",
    "DNK": "Denmark",
    "ESP": "Spain",
    "EST": "Estonia",
    "FIN": "Finland",
    "FRA": "France",
    "GBR": "UK",
    "GRC": "Greece",
    "HUN": "Hungary",
    "IDN": "Indonesia",
    "IND": "India",
    "IRL": "Ireland",
    "ITA": "Italy",
    "JPN": "Japan",
    "KOR": "Korea",
    "LTU": "Lithuania",
    "LUX": "Luxembourg",
    "LVA": "Latvia",
    "MEX": "Mexico",
    "MLT": "Malta",
    "NLD": "Netherlands",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "RUS": "Russia",
    "SVK": "Slovakia",
    "SVN": "Slovenia",
    "SWE": "Sweden",
    "TUR": "Turkey",
    "TWN": "Taiwan",
    "USA": "USA",
    }

env_series_names = {
    "Coal": ["HCOAL", "BCOAL"],
    "Electricity": ["ELECTR"],
    "Petroleum": ["CRUDE", "DIESEL", "GASOLINE", "JETFUEL",
                  "LFO", "HFO", "NAPHTA", "OTHPETRO"],
    "Natural gas": ["NATGAS"],
    "Waste": ["WASTE"],
    "CO2": ["CO2"],
    "CH4": ["CH4"],
    "NOx": ["NOX"],
    "SOx": ["SOX"],
    "NMVOC": ["NMVOC"],
    "NH3": ["NH3"],
    }

env_series = {
    "AIR": {},
    "CO2": {},
    "EM": {},
    "EU": {},
    "WAT": {
        "dir": "water",
        "skip_name": True,
        },
    }

env_sector_blacklist = (
    "total",
    "secTOT",
    "FC_HH",
    "secQ",
    )

env_sector_blacklist_hh = ("total", "secTOT", "secQ")

default_fd_sectors = (
    "CONS_h", "CONS_g", "CONS_np", "GFCF", "INVEN", "EXP")
fd_sectors_with_import = (
    "CONS_h", "CONS_g", "CONS_np", "GFCF", "INVEN", "EXP", "IMP")


# based on codes in int_sut tables. codes are missing in NIOT
# this dictionary is used for parsing
fd_sectors = {
    "Final consumption expenditure by households": "CONS_h",
    "Final consumption expenditure by non-profit organisations serving households (NPISH)": "CONS_np",
    "Final consumption expenditure by government": "CONS_g",
    "Gross fixed capital formation": "GFCF",
    "Changes in inventories and valuables": "INVEN",
    "Exports": "EXP",
    "Imports": "IMP",
    }

# based on codes in suts (separate supply and use) tables
va_sectors = {
    "Taxes less subsidies on products": "TXSP",
    "taxes less subsidies on products": "TXSP",
    "Cif/ fob adjustments on exports": "EXP_adj",
    "Direct purchases abroad by residents": "PURR",
    "Purchases on the domestic territory by non-residents": "PURNR",
    "Value added at basic prices": "VA",
    "International Transport Margins": "MARG",
    }

margin_sectors = (
    "MARG",
    "TXSP",
    "Rex",
    "ITM",
    )

# omit totals
industry_blacklist = ("DSUP_bas", "SUP_bas", "SUP_pur")
commodity_blacklist = ("DSUP_bas", "GO")

code_blacklist = (
    # specifically for NIOT xlsx tables which parse via
    # iteration instead of positions
    "(industry-by-industry)",
    ### totals in int make table
    "DSUP_bas", "SUP_bas", "SUP_pur", "GO",
    ### totals in int use table
    "INTC", # total intermediate consumption
    "CONS", # total consumption expenditures (hh, npish, gov)
    "GCF", # gross capital formation i.e. GFCF + inventory change
    "FU_pur", "USE_Pur"
    )

# for testing
STUDY_YEARS = [1995, 2009]


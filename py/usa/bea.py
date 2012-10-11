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

# file that records common things relevant to bea data

use_table_margins = [
    "margins", # negative
    "rail_margin", "truck_margin", "water_margin", "air_margin",
    "pipe_margin", "gaspipe_margin",
    "wholesale_margin", "retail_margin"]

FINAL_DEMAND = "f"
VALUE_ADDED = "v"
INTERMEDIATE_OUTPUT = "i"

fd_sectors = {
    1972: {"pce": "910000", "imports": "950000", "exports": "940000"},
    1977: {"pce": "910000", "imports": "950000", "exports": "940000"},
    1982: {"pce": "910000", "imports": "950000", "exports": "940000"},
    1987: {"pce": "910000", "imports": "950000", "exports": "940000"},
    1992: {"pce": "910000", "imports": "950000", "exports": "940000"},
    1997: {"pce": "F01000", "imports": "F05000", "exports": "F04000"},
    2002: {"pce": "F01000", "imports": "F05000", "exports": "F04000"},
    }

fd_sector_names = {
    "total": "All final demand",
    "pce": "Personal Consumption Expenditures",
    "imports": "Imports",
    "exports": "Exports",
    }

fd_sector_criteria = {
    1972: "SUBSTRING(code FROM 1 FOR 2) IN " + \
                   "('91', '92', '93', '94', '95', '96', '97', '98', '99')",
    1977: "SUBSTRING(code FROM 1 FOR 2) IN " + \
                   "('91', '92', '93', '94', '95', '96', '97', '98', '99')",
    # based on similarity to 1987
    1982: "SUBSTRING(code FROM 1 FOR 2) IN " + \
                   "('91', '92', '93', '94', '95', '96', '97', '98', '99')",
    # http://www.bea.gov/scb/pdf/national/inputout/1994/0494ied.pdf (p84)
    1987: "SUBSTRING(code FROM 1 FOR 2) IN " + \
                   "('91', '92', '93', '94', '95', '96', '97', '98', '99')",
    # http://www.bea.gov/scb/account_articles/national/1197io/appxB.htm
    1992: "SUBSTRING(code FROM 1 FOR 2) IN " + \
                   "('91', '92', '93', '94', '95', '96', '97', '98', '99')",
    1997: "code LIKE 'F%'",
    2002: "code LIKE 'F%'",
    }

va_sector_criteria = {
    1972: "code IN ('880000', '890000', '900000')",
    1977: "code IN ('880000', '890000', '900000')",
    1982: "code IN ('880000', '890000', '900000')",
    # http://www.bea.gov/scb/pdf/national/inputout/1994/0494ied.pdf (p115)
    1987: "code IN ('880000', '890000', '900000')",
    # http://www.bea.gov/scb/account_articles/national/1197io/appxB.htm
    1992: "SUBSTRING(code FROM 1 FOR 2) IN ('88', '89', '90')",
    1997: "code LIKE 'V%'",
    2002: "code LIKE 'V%'",
    }

scrap_used_codes = {
    1972: ("810000",),
    1977: ("810001", "810002"),
    1982: ("810001", "810002"),
    1987: ("810001", "810002"),
    1992: ("810001", "810002"),
    1997: ("S00401", "S00402"),
    2002: ("S00401", "S00402"),
    }

tourism_adjustment_codes = {
    1972: '830000',
    1977: '830000',
    1982: '830000',
    1987: '830001',
    1992: '830001',
    1997: 'S00600',
    2002: 'S00900',
    }

nipa_groups = [
    "Clothing and footwear",
    "Financial services and insurance",
    "Food and beverages purchased for off-premises consumption",
    "Food services and accommodations",
    "Furnishings and durable household equipment",
    "Gasoline and other energy goods",
    "Gross output of nonprofit institutions",
    "Health care",
    "Housing and utilities",
    #"Less: Receipts from sales of goods and services by nonprofit institutions",
    "Motor vehicles and parts",
    "Other durable goods",
    "Other nondurable goods",
    "Other services",
    "Recreational goods and vehicles",
    "Recreation services",
    "Transportation services",
    ]

short_nipa = {
    "Clothing and footwear": "Apparel",
    "Financial services and insurance": "Financial services",
    "Food and beverages purchased for off-premises consumption": "Food products",
    "Food services and accommodations": "Food services",
    "Gasoline and other energy goods": "Gasoline",
    "Other durable goods": "Other durables",
    "Other nondurable goods": "Other nondurables",
    "Transportation services": "Transport",
    "Housing and utilities": "Utilities",
    }

standard_sectors = {
    1972: ('540200'),
    1977: ('540200'),
    1982: ('540200'),
    1987: ('540200'),
    1992: ('540200'),
    1997: ('335222'),
    2002: ('335222'),
    }

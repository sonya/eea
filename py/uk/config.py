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

SCHEMA = "uk"
STUDY_YEARS = range(1992, 2009)

curated_sectors = {
    # value added
    "Taxes less subsidies on production": "tax",
    "Compensation of employees": "comp",
    "Gross operating surplus and mixed income": "surp",
    # final demand
    "Households": "hh",
    "Non-profit\ninstitutions serving\nhouseholds": "npish",
    "Central\ngovernment": "gov",
    "Local\ngovernment": "lgov",
    "Gross fixed\ncapital\nformation": "gfcf",
    "Valuables": "valbls",
    "Changes in inventories": "invchg",
    #"Exports of Goods"
    #"Exports of Services"
    "Total exports of goods and services": "export",
    }

fd_sectors = ["hh", "gov", "gfcf", "export", "invchg",
              "lgov", "npish", "valbls"]
pce_sector = "hh"
export_sector = "export"

va_sectors = ["tax", "comp", "surp"]

env_series = ["N2O", "CO2", "PFCs", "SF6", "GHG total", "HFCs", "CH4"]


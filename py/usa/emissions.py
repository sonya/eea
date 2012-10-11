#!/usr/bin/python3
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

import csv

from usa import bea, config, eia, common, wiod_code_map
from common import fileutils, utils
import wiod.common

wiod_comparison_data = {}

sector_large_groups = {
    "Food + agriculture": ["15t16", "AtB"],
    "Fuels": ["23"],
    "Chemicals": ["24"],
    "Basic + fab metal": ["27t28"],
    "Inland transport": ["60"],
    "Air transport": ["62"],
    "Utilties": ["E"],
    "Households": ["FC_HH"], 
    "Other manufacturing": [
        "17t18", "19", "20", "21t22", "25", "26", "29",
        "30t33", "34t35", "36t37"],
    "Services": [
        "50", "51", "52", "64", "71t74", "H", "J", "M", "N", "O"],
    }

for year in config.STUDY_YEARS:

    path = fileutils.getcache("emissions_estimates_%d.csv" % year, "usa")
    emissions_fh = open(path, "w")
    emissions_csv = csv.writer(emissions_fh)

    path = fileutils.getcache("fossil_fuel_estimates_%d.csv" % year, "usa")
    energy_fh = open(path, "w")
    energy_csv = csv.writer(energy_fh)

    # yes hybrid, yes imports, no inflation
    iogen = common.iogen_for_year(year, True, True)

    # not hybrid, yes imports, yes inflation
    iogen_normal = common.iogen_for_year(year, False, True, True)

    pce = iogen_normal.get_Y(True).get_pce()

    xn = iogen_normal.get_x(True)

    A = iogen.get_A() # direct requirements
    Z = iogen.get_Z()
    hpce = iogen.get_Y().get_pce()

    header = ["sector", "total"]
    for source in eia.modified_sources:
        if source in eia.conversion_factors:
            header.append(source)
    energy_csv.writerow(header)
    emissions_csv.writerow(header)

    agg_data = {}

    sectors = sorted(iogen_normal.get_sectors())
    hh_sector = bea.fd_sectors[year]["pce"]
    sectors.append(hh_sector)

    # need to add up split petroleum sectors in hybrid table
    pa_normal = eia.source_naics_map["PA"][year]
    pa_trans = eia.source_naics_map["PA-trans"][year]
    pa_nontrans = eia.source_naics_map["PA-nontrans"][year]

    for sector in sectors:
        ## in terms of wiod sectors
        aggsector = wiod_code_map.sector_for_naics(sector, year)
        if aggsector is not None:
            if aggsector not in agg_data:
                agg_data[aggsector] = {
                    "tons": 0,
                    "dollars": 0
                    }
            if sector == hh_sector:
                agg_data[aggsector]["dollars"] = pce.sum()
            else:
                agg_data[aggsector]["dollars"] += xn.get_element(sector)

        energy_values = []
        emissions_values = []
        for i in range(len(eia.modified_sources)):
            source = eia.modified_sources[i]
            if source not in eia.conversion_factors:
                continue

            code = eia.source_naics_map[source][year]

            if sector == hh_sector:
                btu = hpce.get_element(code)
                tons = btu * eia.conversion_factors[source]
                agg_data[aggsector]["tons"] += tons

                continue

            # add split petroleum sectors
            if sector == pa_normal:
                btu = (A.get_element(code, pa_trans) + \
                       A.get_element(code, pa_nontrans))
            else:
                btu = A.get_element(code, sector)

            # btu variable is billion btu per thousand dollar
            # since A is in same units as L

            # (bBtu * metric tons / MMBtu) per thousand dollar = tons / $
            tons = btu * eia.conversion_factors[source]

            energy_values.append(btu * 1000) # kBtu / $
            emissions_values.append(tons)

            if aggsector is not None:
                if sector == pa_normal:
                    btu = (Z.get_element(code, pa_trans) + \
                           Z.get_element(code, pa_nontrans))
                else:
                    btu = Z.get_element(code, sector)

                tons = btu * eia.conversion_factors[source]
                agg_data[aggsector]["tons"] += tons

        energy_csv.writerow([sector, sum(energy_values)] + energy_values)
        emissions_csv.writerow([sector, sum(emissions_values)] + emissions_values)

    emissions_fh.close()
    energy_fh.close()

    wiod_comparison_data[year] = agg_data

def print_co2_allyears():
    headrow = ["sector"] + [str(year) for year in config.STUDY_YEARS]
    print(" & ".join(headrow) + " \\\\")
    for sector in sorted(wiod_code_map.codes.keys()):
        row = [wiod_code_map.sector_title(sector)]
        for year in config.STUDY_YEARS:
            agg_data = wiod_comparison_data[year]
            sector_data = agg_data[sector]
            row.append(utils.add_commas(sector_data["tons"] / 1000))
            #row.append(utils.add_commas(sector_data["dollars"]))
            #row.append("%.3f" % (sector_data["tons"] / sector_data["dollars"]))
        print(" & ".join(row) + " \\NN")

vector = {}
normalizer = {}
for (year, data) in wiod_comparison_data.items():
    for (sector, secdata) in data.items():
        if sector not in vector:
            vector[sector] = {}
            normalizer[sector] = {}
        vector[sector][year] = secdata["tons"]
        normalizer[sector][year] = secdata["dollars"]

common.graph_table(
    "wiod-sectors-levels", "", vector, 1972, None, sector_large_groups)
common.graph_table(
    "wiod-sectors-intensities", "", vector, 1972,
    normalizer, sector_large_groups)

# only 2 overlapping years
def print_wiod_compare():
    usa97 = wiod_comparison_data[1997]
    usa02 = wiod_comparison_data[2002]
    
    envgen97 = wiod.common.envgen_for_year(1997, ["FC_HH"])
    envgen97.set_condition_args("USA")
    wiod97 = envgen97.get_env_vector("CO2")
    envgen02 = wiod.common.envgen_for_year(2002, ["FC_HH"])
    envgen02.set_condition_args("USA")
    wiod02 = envgen02.get_env_vector("CO2")
    
    sectors = sorted(envgen97.get_sectors())
    if "FC_HH" not in sectors:
        sectors.append("FC_HH")
    
    for sector in sectors:
        short_sector = sector.replace("sec", "")
        if short_sector in usa97:
            label = wiod_code_map.sector_title(short_sector)
            vals = []
            vals.append(usa97[short_sector]["tons"] / 1000)
            vals.append(wiod97.get_element(sector))
            vals.append(usa02[short_sector]["tons"] / 1000)
            vals.append(wiod02.get_element(sector))
            row = [label] + [utils.add_commas(val) for val in vals]
            print(" & ".join(row) + " \\NN")

print_co2_allyears()
print_wiod_compare()

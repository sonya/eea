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

import math

from usa import bea, common, config, eia
from common import utils
from common.plotutils import GNUPlot
from common.ioutils import IOMatrixGenerator
from usa.nipa import Deflators

from common.matrixutils import NamedMatrix

deflators = Deflators()

plots = {}

pce_dollars = {}
energy = {}
emissions = {}
pce_imports = {}

def print_table(vector, is_intensities):
    for group in sorted(vector.keys()):
        numerator = vector[group]

        if is_intensities:
            denominator = pce_dollars[group]
            values = ["%.2f" % (numerator[year] / denominator[year] * 1000)
                      for year in config.STUDY_YEARS]
        else:
            values = [utils.add_commas(numerator[year])
                      for year in config.STUDY_YEARS]

        print(group + " & " + " & ".join(values) + " \\NN")

def graph_table(filename, title, vector,
                base_year, is_intensities, collapse=[]):

    plot = GNUPlot(filename, title, "usa")

    data = {}
    sortby = {}
    other_category = "Other"
    max_year = max(config.STUDY_YEARS)

    other_category_numer = dict((year, 0) for year in config.STUDY_YEARS)
    other_category_denom = dict((year, 0) for year in config.STUDY_YEARS)

    for group in vector.keys():
        numerator = vector[group]

        if is_intensities:
            denominator = pce_dollars[group]
        else:
            denominator = dict((year, 1) for year in config.STUDY_YEARS)

        base_value = numerator[base_year] / denominator[base_year]

        if group in collapse:
            for year in config.STUDY_YEARS:
                other_category_numer[year] += numerator[year]

                # adding 1 for each year is fine since it's relative to the base
                other_category_denom[year] += denominator[year]

        else:
            data[group] = {}

            for year in config.STUDY_YEARS:
                data[group][year] = numerator[year] / denominator[year]

            sortby[ data[group][max_year] / data[group][base_year] ] = group

    if len(other_category_numer):
        data[other_category] = dict(
            (year, other_category_numer[year] / other_category_denom[year]) \
                for year in config.STUDY_YEARS)
        sortby[ data[other_category][max_year] /\
                    data[other_category][base_year] ] = other_category

    sorted_groups = [sortby[key] for key in sorted(sortby.keys(), reverse=True)]

    plot.add_custom_setup("set style data linespoints")
    plot.add_custom_setup("unset colorbox")
    plot.add_custom_setup("set grid")

    min_x = 5 * math.floor(min(config.STUDY_YEARS) / 5)
    max_x = 5 * math.ceil(max(config.STUDY_YEARS) / 5) + 5 # room for labels
    plot.add_custom_setup("set xrange [ %d : %d ]" % (min_x, max_x))

    interval = 1 / (len(sorted_groups) - 1)
    for i in range(len(sorted_groups)):
        plot.add_custom_setup("set style lines %d lc palette frac %.2f lw 2"
                              % (i + 1,  i * interval))
    series_values = []

    for i in range(len(sorted_groups)):
        group = sorted_groups[i]
        if group in bea.short_nipa:
            group_name = bea.short_nipa[group]
        else:
            group_name = group

        series_values.append(group_name)
        plot.suppress_title(group_name)

        base_value = data[group][base_year]
        for year in config.STUDY_YEARS:
            print(group, year, data[group][year], base_value, data[group][year] / base_value)
            plot.set_value(group_name, year,
                           data[group][year] / base_value * 100)

        plot.set_series_style(group_name, "linestyle %d" % (i + 1))

    plot.series_values = series_values
    plot.write_tables()
    plot.get_axis_specs() # make sure max_y is adjusted

    prev_pos = None
    for i in range(len(sorted_groups)):
        group = sorted_groups[i]
        if group in bea.short_nipa:
            group_name = bea.short_nipa[group]
        else:
            group_name = group

        ending_value = data[group][max_year] / data[group][base_year] * 100
        position = ending_value / plot.max_y + 0.01 # line up baseline

        # space labels out by at least 0.04 so they don't overlap
        if prev_pos is not None and prev_pos - position < 0.03:
            position = prev_pos - 0.03

        plot.add_custom_setup(
            "set label %d '%s' at graph 0.81, %.2f font 'Arial,8'"
            % (i + 1, group_name, position))

        prev_pos = position

    plot.generate_plot()

for year in config.STUDY_YEARS:
    # args: year, is_hybrid, allow_imports, adjust for inflation
    iogen = common.iogen_for_year(year, True, True, True)
    iogen_standard = common.iogen_for_year(year, False, True, True)

    energy_codes = []
    for i in range(len(eia.modified_sources)):
        source = eia.modified_sources[i]
        naics = eia.source_naics_map[source][year]
        energy_codes.append(naics)
    
    L = iogen.get_L()
    Y = iogen.get_Y() # mixed units

    ###### hybrid vectors

    import_colname = bea.fd_sectors[year]["imports"]
    import_column = Y.get_named_column(import_colname)
    # omit rows with "positive" imports
    # which are just accounting adjustments
    for row in import_column.get_rows():
        if import_column.get_element(row) > 0:
            import_column.set_element(row, import_colname, 0)
    import_column.scalar_mult_inplace(-1)

    hybrid_pce = Y.get_pce()

    fd_vectors = {
        "exports": Y.get_exports(),
        "pce": hybrid_pce,
        "imports": import_column,
        }

    ##### normal vectors

    xn = iogen_standard.get_x(True)
    Yn = iogen_standard.get_Y(True) # dollar units, adjusted

    export_n = Yn.get_exports()
    import_n = Yn.get_named_column(import_colname)
    # omit rows with "positive" imports
    for row in import_n.get_rows():
        if import_n.get_element(row) > 0:
            import_n.set_element(row, import_colname, 0)
    import_n.scalar_mult_inplace(-1)

    fd_dollars = {
        "exports": export_n.sum(),
        "pce": Yn.get_pce().sum(),
        "imports": import_n.sum(),
        }

    ###### breakdown by fd sector

    dirname = "usa-pce-energy"
    for (key, vector) in fd_vectors.items():
        fdgroup = bea.fd_sector_names[key]
        ikey = key + "-intensity"

        if key not in plots:
            plots[key] = GNUPlot(key, fdgroup + " (trillion Btu)", dirname)
            plots[key].style = "histogram"

        if ikey not in plots:
            plots[ikey] = GNUPlot(ikey, fdgroup + " (MMBtu per 2005$)", dirname)
            plots[ikey].style = "histogram"

        use_vector = L.matrix_mult(vector)

        for i in range(len(energy_codes)):
            code = energy_codes[i]
            name = eia.name_for_naics(code)
            value = use_vector.get_element(rowname=code) # bBtu
            # divide bBtu by 1000 for tBtu
            plots[key].set_value(year, name, value / 1000)
            # div bBtu by k$ for MMBtu/$
            plots[ikey].set_value(year, name, value / fd_dollars[key])

    ##### pce category breakdown

    xn_cons = xn.add(import_n).subtract(export_n)
    imp_to_cons = import_n.divide(xn_cons)

    # remove scrap and used/secondhand goods
    colname = imp_to_cons.get_columns()[0]
    for sector in bea.scrap_used_codes[year]:
        imp_to_cons.set_element(sector, colname, 0)

    # create matrix to collapse split petroleum sectors when multiplying
    # by the import ratio
    rows = iogen_standard.get_sectors()
    cols = iogen.get_sectors()
    pa_collapser = NamedMatrix(False, None, rows, cols)
    for col in cols:
        if col in rows:
            pa_collapser.set_element(col, col, 1)
        elif col == eia.source_naics_map["PA-trans"][year] or \
                col == eia.source_naics_map["PA-nontrans"][year]:
            pa_collapser.set_element(eia.source_naics_map["PA"][year], col, 1)

    conven_pce = common.pce_bridge_vector(year) # all in dollars
    conversions = {} # get btu per dollar which we will use to convert subvectors
    for code in energy_codes:
        conversions[code] = hybrid_pce.get_element(code) / \
            conven_pce.get_element(code)

    for group in bea.nipa_groups:
        Y = common.pce_bridge_vector(year, group)

        deflator = deflators.get_pce_deflator(year)
        pce = Y.sum() * deflator

        if group not in pce_imports:
            pce_imports[group] = {}

        # pce gets /1000 and /1000 again in "is_intensity" version
        # of print_table()
        pce_imports[group][year] = pa_collapser.matrix_mult(Y).\
            mult(imp_to_cons).sum() * deflator / 1000000

        pce_title = group + " (billion 2005 chained dollars)"
        if pce_title not in plots:
            plots[pce_title] = GNUPlot(group, pce_title, "usa-pce-dollars")
            plots[pce_title].style = "histogram"
        # values are saved in thousands
        plots[pce_title].set_value(year, "dollars", pce / 1000000)

        # billion btu / 1000
        consumption = group + " (trillion Btu)"
        if consumption not in plots:
            plots[consumption] = GNUPlot(group, consumption, "usa-pce-btu")
            plots[consumption].style = "histogram"

        # billion btu / thousand dollars * 1000000
        intensity = group + " (Btu per dollar)"
        if intensity not in plots:
            plots[intensity] = GNUPlot(
                group, intensity, "usa-pce-btu-per-dollar")
            plots[intensity].style = "histogram"

        # make sure units are the consistent with L
        for (code, conversion) in conversions.items():
            Y.set_element(code, "pce", Y.get_element(code) * conversion)

        use = L.matrix_mult(Y)

        if group not in energy:
            energy[group] = {}
            emissions[group] = {}
            pce_dollars[group] = {}
        if year not in energy[group]:
            energy[group][year] = 0
            emissions[group][year] = 0

        pce_dollars[group][year] = pce / 1000 # millions

        for code in energy_codes:
            btu = use.get_element(code) # bBtu

            if eia.is_fossil_fuel(code):
                energy[group][year] += btu / 1000 # tBtu
                # emission factors are kg / MMBtu
                emissions[group][year] += btu \
                    * eia.conversion_factors[source] / 1000 # kilotons

            name = eia.name_for_naics(code)
            plots[consumption].set_value(year, name, btu)
            btu_per_dollar = btu / pce * 1000000
            plots[intensity].set_value(year, name, btu_per_dollar)

#print_table(energy, False)
#print_table(energy, True) # (tBtu per $MM) * 1000 == kBtu per $

suppress_groups = [
    #"Clothing and footwear",
    "Financial services and insurance",
    "Furnishings and durable household equipment",
    "Gross output of nonprofit institutions",
    "Motor vehicles and parts",
    "Other durable goods",
    "Recreation services",
    "Recreational goods and vehicles",
    ]

graph_table("energy-levels", "", energy, 1972, False, suppress_groups)
graph_table("energy-intensities", "", energy, 1972, True, suppress_groups)

#print_table(emissions, False)
#print_table(emissions, True) # (ktons per $MM) * 1000 == tons per $MM

graph_table("emissions-levels", "", emissions, 1972, False, suppress_groups)
graph_table("emissions-intensities", "", emissions, 1972, True, suppress_groups)

#print_table(pce_imports, True)

#for (key, plot) in plots.items():
#    plot.write_tables()
#    plot.generate_plot()
    

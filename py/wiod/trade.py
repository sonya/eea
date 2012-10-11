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

# this is a very slow script
# the function structure is also ridiculously sketchy

import common.config as common_config
from wiod import common, config
from common import sqlhelper, utils
from common.matrixutils import NamedMatrix
from common.dbconnect import db
from common.dbhelper import SQLTable
from common.plotutils import GNUPlot, ScatterPlot
from wiod.plotutils import WorldMapPlot
from common import utils
import sys

import_dollar_series = "Import share of GDP"
emission_series = "Actual imported emissions"
self_emission_series = "Imported emissions under DTA"

export_dollar_series = "Export share of GDP"
export_emissions_series = "Exported emissions"

balance_plots = {}
dta_plots = {}

minyear = min(config.STUDY_YEARS)
maxyear = max(config.STUDY_YEARS)
worldmap = {
    minyear: WorldMapPlot("balance-map-%d" % minyear, "", "wiod"),
    maxyear: WorldMapPlot("balance-map-%d" % maxyear, "", "wiod"),
    }

class TradeResultsTable:

    __active = False
    __sqltable = None

    def activate():
        TradeResultsTable.__active = True
        TradeResultsTable.__sqltable = SQLTable(
            "trade_results",
            ["year", "country", "is_export", "industry", "value"],
            ["int", "char(3)", "bool", "varchar(15)", "float"])
        TradeResultsTable.__sqltable.create()
        TradeResultsTable.__sqltable.truncate()

    def insert_exports(year, country, vector):
        if not TradeResultsTable.__active:
            return

        for row in vector.get_rows():
            TradeResultsTable.__sqltable.insert(
                [year, country, True, row, vector.get_element(row)])

    def insert_imports(year, country, vector):
        if not TradeResultsTable.__active:
            return

        for row in vector.get_rows():
            TradeResultsTable.__sqltable.insert(
                [year, country, False, row, vector.get_element(row)])
        

def get_wiod_env_vector(country, year, env_series):
    strings = {
        "year": year,
        "schema": config.WIOD_SCHEMA,
        "blacklist": sqlhelper.set_repr(config.env_sector_blacklist_hh),
        "measurements": sqlhelper.set_repr(env_series),
        }

    vector = NamedMatrix(rows=common.env_sectors_with_hh, cols=["value"])

    stmt = db.prepare("""SELECT industry, sum(value)
                           FROM %(schema)s.env_%(year)d
                          WHERE country = $1
                            AND measurement IN %(measurements)s
                            AND industry NOT IN %(blacklist)s
                          GROUP BY industry""" % strings)
    result = stmt(base_country)

    for row in result:
        if row[1] is not None:
            vector.set_element(row[0], "value", row[1])

    return vector

# use "RoW" to get rest of world
def get_wiod_trade_vector(from_country, to_country):
    yearstrings = [str(year) for year in config.STUDY_YEARS]
    vector = NamedMatrix(rows=yearstrings, cols=["value"])

    strings = {"schema": config.WIOD_SCHEMA}
    for year in yearstrings:
        strings["year"] = year
        stmt = db.prepare("""SELECT sum(value)
                               FROM %(schema)s.int_use_%(year)s
                              WHERE from_country = $1 and to_country = $2"""
                          % strings)
        result = stmt(from_country, to_country)
        if len(result) and len(result[0]):
            vector.set_element(year, "value", result[0][0])

    return vector

def sum_if_not_none(matrix1, matrix2):
    if matrix1 is None:
        return matrix2
    return matrix1.add(matrix2)

def trade_ratios(base_country, env_key):
    env_series = config.env_series_names[env_key]

    other_countries = sorted(config.countries.keys())
    other_countries.remove(base_country)

    yearstrings = [str(y) for y in config.STUDY_YEARS]
    exported_y = NamedMatrix(rows=other_countries, cols=yearstrings)
    exported_E = NamedMatrix(rows=other_countries, cols=yearstrings)

    def describe_exporters():
        print("Exports by country - " + env_key)

        print("dollars")
        for country in other_countries:
            formatted = [("%.0f" %
                          exported_y.get_element(country, year)).rjust(6)
                         for year in yearstrings]
            print(country, " ".join(formatted))

        print("emissions")
        for country in other_countries:
            formatted = [("%.0f" %
                          exported_E.get_element(country, year)).rjust(6)
                         for year in yearstrings]
            print(country, " ".join(formatted))

        print("intensities")
        intensities = exported_E.divide(exported_y)
        for country in other_countries:
            formatted = [("%.2f" %
                          intensities.get_element(country, year)).rjust(6)
                         for year in yearstrings]
            print(country, " ".join(formatted))

    ### prepare plots
    env_title = env_key.replace(" ", "-")
    plot_group = "import-%s-%s" % (env_title, base_country)
    plots = {}
    for sector in common.default_env_sectors:
        sector_title = common.get_industry_title(sector)
        plots[sector] = GNUPlot("%s_%s" % (env_title, sector), "",
                                #"Imports of %s - %s" % (sector_title, env_key),
                                plot_group)
    plots["import"] = GNUPlot("%s_import" % env_title, "",
                             #"All imports - %s" % env_key,
                             plot_group)
    plots["export"] = GNUPlot("%s_export" % env_title, "",
                              #"All imports - %s" % env_key,
                              plot_group)

    def create_plots():
        for (sector, plot) in plots.items():
            plot.set_series_style(
                import_dollar_series,
                "pointtype 5 linetype rgb '#88BBFF'") # hollow circle
            plot.set_series_style(
                emission_series,
                "pointtype 7 linetype rgb '#1144FF'") # solid circle
            plot.set_series_style(
                self_emission_series,
                "pointtype 12 linetype rgb '#0000FF'")
    
            plot.set_series_style(
                export_dollar_series, "pointtype 4 linetype rgb '#CC9933'")
            plot.set_series_style(
                export_emissions_series, "pointtype 7 linetype rgb '#996600'")
    
            #plot.legend("width -8")
            plot.width = 480
            plot.height = 300

            plot.write_tables()
            plot.generate_plot()

    ### trade balance matrices
    export_balance = NamedMatrix(rows=common.default_env_sectors,
                                 cols=yearstrings)
    import_balance = NamedMatrix(rows=common.default_env_sectors,
                                 cols=yearstrings)
    all_E = NamedMatrix(rows=common.default_env_sectors,
                        cols=yearstrings)

    def describe_balance(ratios=False):
        export_total = export_balance.sum(0)
        import_total = import_balance.sum(0)
        all_total = all_E.sum(0)

        balance = export_total.subtract(import_total)

        country_name = config.countries[base_country]
        oddyears = [str(y) for y in filter(lambda x: x % 2 == 1,
                                           config.STUDY_YEARS)]

        if ratios:
            balance_ratio = balance.divide(all_total)
            print(country_name.ljust(15) + " & " + " & ".join(
                    [("%.2f" % balance_ratio.get_element("sum", y)).rjust(6)
                     for y in oddyears]) + " \\\\")
        else:
            print(country_name.ljust(15) + " & " + " & ".join(
                    [utils.add_commas(balance.get_element("sum", y)).rjust(9)
                     for y in oddyears]) + " \\\\")

    def describe_balance_intensity():
        export_total = export_balance.sum(0)
        import_total = import_balance.sum(0)
        all_total = all_E.sum(0)

        balance = export_total.subtract(import_total)
        balance_ratio = balance.divide(all_total)

        country_name = config.countries[base_country]
        years = [str(minyear), str(maxyear)]

        fields = []
        for y in years:
            balance_val = balance.get_element("sum", y)
            ratio_val = balance_ratio.get_element("sum", y)
            (gdp_val, env_val, intensity) = \
                common.get_efficiency(base_country, int(y))

            if int(y) in balance_plots:
                plot = balance_plots[int(y)]
                # ratio = exports to imports
                plot.set_value("2 ratio", base_country, ratio_val)
                plot.set_value("1 intensity", base_country, intensity)

            if int(y) in worldmap:
                worldmap[int(y)].set_country_value(base_country, balance_val)

            fields.append(utils.add_commas(balance_val))
            fields.append("%.2f" % ratio_val)
            fields.append("%.2f" % intensity)

        print(country_name.ljust(15) + " & " + " & ".join(fields) + " \\NN")

    ###
    iogen = common.iogen_for_year(config.STUDY_YEARS[0])
    envgen = common.envgen_for_year(config.STUDY_YEARS[0])

    strings = {"schema": config.WIOD_SCHEMA}

    for year in config.STUDY_YEARS:
        strings["year"] = year

        base_E = get_wiod_env_vector(base_country, year, env_series)
        all_E.set_column(str(year), base_E)

        base_E_sum = base_E.sum()

        iogen.set_table("%(schema)s.indbyind_%(year)d" % strings)
        iogen.set_condition_args(base_country)

        envgen.set_table("%(schema)s.env_%(year)d" % strings)
        envgen.set_condition_args(base_country)
        envgen.set_sectors(common.default_env_sectors)

        # prepare base country values
        y = iogen.get_Y()
        import_column = common.get_import_vector(iogen)
        base_imports = import_column.sum()
        base_gdp = y.sum()

        harmonizer = common.get_io_harmonizer(iogen)

        base_y = harmonizer.matrix_mult(y.get_total())
        x = iogen.get_x()

        E = envgen.get_env_vector(env_series)
        L = iogen.get_L()
        J = E.divide(harmonizer.matrix_mult(x), ignore_zero_denom=True)
        base_JsL = J.square_matrix_from_diag()\
            .matrix_mult(harmonizer).matrix_mult(L)

        exported = base_JsL.matrix_mult(y.get_exports())
        export_balance.set_column(str(year), exported)

        plots["export"].set_value(
            export_emissions_series, year, exported.sum() / base_E_sum)
        plots["export"].set_value(
            export_dollar_series, year, y.get_exports().sum() / base_gdp)

        # prepare other country values
        stmt = db.prepare("""SELECT from_sector, sum(value)
            FROM wiod_plus.%s_io_import_%d WHERE country = $1
             AND from_sector NOT IN ('ITM', 'IMP', 'Rex')
           GROUP BY from_sector""" % (base_country.lower(), year))

        imported_E = None
        imported_y = None
        domestic_E = None # emissions under domestic technology assumption

        for country in other_countries:
            envgen.set_condition_args(country)
            envgen.set_sectors(common.default_env_sectors)

            iogen.set_condition_args(country)
            sectors = iogen.get_sectors() # number of sectors varies by country
    
            E = envgen.get_env_vector(env_series)
            if E.mat() is None: # this country has no data for env series
                continue

            imports = NamedMatrix(rows=sectors, cols=["imports"])
            db_result = stmt(country)
            if not len(db_result):
                # we can't do any of the following with a blank import vector
                continue

            for row in db_result:
                imports.set_element(row[0], "imports", row[1])

            sel = common.get_io_harmonizer(iogen)
            x = iogen.get_x()
            L = iogen.get_L()

            J = E.divide(sel.matrix_mult(x), ignore_zero_denom=True)
            JsL = J.square_matrix_from_diag().matrix_mult(sel).matrix_mult(L)

            current_E = JsL.matrix_mult(imports)
            current_y = sel.matrix_mult(imports)

            # temporary dumb way to deal with sector mismatch
            compat_imports = NamedMatrix(rows=base_JsL.get_columns(),
                                         cols=["imports"])
            for col in base_JsL.get_columns():
                if col in sectors:
                    compat_imports.set_element(
                        col, "imports", imports.get_element(col))
            current_domestic_E = base_JsL.matrix_mult(compat_imports)

            imported_E = sum_if_not_none(imported_E, current_E)
            imported_y = sum_if_not_none(imported_y, current_y)
            domestic_E = sum_if_not_none(domestic_E, current_domestic_E)

            exported_y.set_element(country, str(year), imports.sum())
            exported_E.set_element(country, str(year), current_E.sum())

        # populate results table
        TradeResultsTable.insert_exports(year, base_country, exported)
        TradeResultsTable.insert_imports(year, base_country, imported_E)

        # generate import plots
        for sector in common.default_env_sectors:
            base_y_val = base_y.get_element(sector)
            if base_y_val > 0:
                plots[sector].set_value(
                    import_dollar_series, year,
                    imported_y.get_element(sector) / base_y_val)

            base_E_val = base_E.get_element(sector)
            if base_E_val > 0:
                plots[sector].set_value(
                    emission_series, year,
                    imported_E.get_element(sector) / base_E_val)
                plots[sector].set_value(
                    self_emission_series, year,
                    domestic_E.get_element(sector) / base_E_val)

        plots["import"].set_value(import_dollar_series, year,
                                  imported_y.sum() / base_y.sum())
        plots["import"].set_value(emission_series, year,
                                  imported_E.sum() / base_E_sum)
        plots["import"].set_value(self_emission_series, year,
                                  domestic_E.sum() / base_E_sum)

        if year in dta_plots and base_country in dta_countries:
            dta_plots[year].set_value("DTA",
                                      config.countries[base_country],
                                      imported_E.sum() / base_E_sum)
            dta_plots[year].set_value("No DTA",
                                      config.countries[base_country],
                                      domestic_E.sum() / base_E_sum)

        # this is for DTA vs non-DTA table
        #print(base_country, year,
        #      imported_E.sum(),
        #      domestic_E.sum(),
        #      imported_E.sum() / base_E_sum,
        #      domestic_E.sum() / base_E_sum)

        plots["export"].set_value(emission_series, year,
                                  imported_E.sum() / base_E_sum)

        import_balance.set_column(str(year), imported_E)

    #describe_exporters()
    #create_plots()
    #describe_balance(True)
    describe_balance_intensity()

# main
base_countries = config.countries.keys()

#env_keys = config.env_series_names.keys():
env_keys = ["CO2",]

for year in [1995, 2009]:
    dta_plots[year] = GNUPlot(
        "dta vs fta %d" % year, None, "wiod")

dta_countries = [
    "AUS", "AUT", "BEL", "BRA", "CAN", "DEU", "DNK", "ESP",
    "FIN", "FRA", "GBR", "GRC", "IDN", "IND", "ITA", "JPN",
    "KOR", "MEX", "NLD", "POL", "ROU", "RUS", "CHN",
    "TUR", "TWN", "USA"]

#for year in [1995, 2009]:
#    balance_plots[year] = ScatterPlot(
#        "balance vs intensity %d" % year, None, "wiod")    

#TradeResultsTable.activate()

for base_country in base_countries:
    if base_country in config.bad_data_blacklist:
        continue

    for env_key in env_keys:
        trade_ratios(base_country, env_key)

for (year, plot) in balance_plots.items():
    plot.legend("off")
    plot.add_custom_setup("set yrange [ -1 : 1 ]")
    plot.write_tables()
    plot.generate_plot()

for (year, plot) in dta_plots.items():
    plot.style = "histogram horizontal"
    plot.width = 640
    plot.height = 640
    plot.add_custom_setup("set yrange [ 0 : 0.5 ]")
    plot.xvalues = list(sorted(plot.xvalues))

    #plot.write_tables()
    #plot.generate_plot()

# want later plot at the top so it rotates to the right
GNUPlot.multiplot(2, 1, dta_plots[2009], dta_plots[1995])

for (year, plot) in worldmap.items():
    plot.add_custom_setup("set format cb '%.0f'") # suppress scientific notation
    plot.write_tables()
    plot.generate_plot()

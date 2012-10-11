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

import common.config as common_config
from wiod import common, config
from common import matrixutils, sqlhelper
from common.plotutils import GNUPlot

env_series = "CO2"

plots = {}
marginal_plots = {}

series_specs = {
    "CONS/Y": {
        "title": "Total personal consumption / GDP",
        "style": 'pointtype 8 linetype rgb "blue"', # empty triangle
        },
    "CONS/e": {
        "title": "Emissions due to personal consumption / total emissions",
        "style": 'pointtype 9 linetype rgb "blue"', # solid triangle
        },
    "EXP/Y": {
        "title": "Gross exports / GDP",
        "style": 'pointtype 6 linetype rgb "red"', # empty circle
        },
    "EXP/e": {
        "title": "Emissions due to gross exports / total emissions",
        "style": 'pointtype 7 linetype rgb "red"', # solid circle
        },
    }

mseries_specs = {
    "pce": {
        "title": "Direct emissions / per $ households",
        "style": 'pointtype 8 linetype rgb "blue"', # empty triangle
        },
    "pce+": {
        "title": "Direct + indirect / per $ households",
        "style": 'pointtype 9 linetype rgb "blue"', # solid triangle
        },
    "exports": {
        "title": "Direct emissions / $ gross export",
        "style": 'pointtype 6 linetype rgb "red"', # empty circle
        },
    "exports+": {
        "title": "Direct+indirect / $ gross export",
        "style": 'pointtype 7 linetype rgb "red"', # solid circle
        },
    }

for year in config.STUDY_YEARS:
    # show some output since this script takes awhile
    print(year)

    iogen = common.iogen_for_year(year)
    envgen = common.envgen_for_year(year)
    env_sectors = common.env_sectors_for_year(year)

    for (country, country_name) in config.countries.items():
        if country not in plots:
            plots[country] = GNUPlot(
                "%s_%s" % (env_series, country),
                "%s in %s" % (env_series, country_name),
                "%s-totals" % env_series)
            plot = plots[country]
            for (series, specs) in series_specs.items():
                plot.set_series_style(specs["title"], specs["style"])

            marginal_plots[country] = GNUPlot(
                "%s_%s" % (env_series, country),
                "%s in %s" % (env_series, country_name),
                env_series)
            mplot = marginal_plots[country]
            for (series, specs) in mseries_specs.items():
                mplot.set_series_style(specs["title"], specs["style"])
        else:
            mplot = marginal_plots[country]
            plot = plots[country]

        iogen.set_condition_args(country)
        envgen.set_condition_args(country)
        envgen.set_sectors(env_sectors)

        sectors = iogen.get_sectors()

        x = iogen.get_x(True)
        L = iogen.get_L()
        Y = iogen.get_Y(use_exchange_rate=True)

        E = envgen.get_env_vector(env_series)
        sel = common.get_io_harmonizer(iogen)

        # let J be intensity vector
        # for sectors that exist in env data but not in io data
        # (primarily "households with employed persons") just ignore
        J = E.divide(sel.matrix_mult(x), ignore_zero_denom=True)
        JsL = J.square_matrix_from_diag().matrix_mult(sel).matrix_mult(L)

        total_emissions = JsL.matrix_mult(Y.get_total()).sum()
        pce_emissions = JsL.matrix_mult(Y.get_pce())
        export_emissions = JsL.matrix_mult(Y.get_exports())
        gdp = Y.get_total().sum()
        plot.set_value(series_specs["CONS/Y"]["title"],
                       year, Y.get_pce().sum() / gdp)
        plot.set_value(series_specs["EXP/Y"]["title"],
                       year, Y.get_exports().sum() / gdp)
        plot.set_value(series_specs["CONS/e"]["title"],
                       year, pce_emissions.sum() / total_emissions)
        plot.set_value(series_specs["EXP/e"]["title"],
                       year, export_emissions.sum() / total_emissions)

        # averages
        pce_intensity = sel.matrix_mult(Y.get_marginal_pce()).mult(J)
        export_intensity = sel.matrix_mult(Y.get_marginal_export()).mult(J)

        mplot.set_value(mseries_specs["pce"]["title"],
                       year, pce_intensity.sum())
        mplot.set_value(mseries_specs["exports"]["title"],
                       year, export_intensity.sum())

        iY = Y.matrix_postmult(L)

        pce_intensity = sel.matrix_mult(iY.get_marginal_pce()).mult(J)
        export_intensity = sel.matrix_mult(iY.get_marginal_export()).mult(J)

        mplot.set_value(mseries_specs["pce+"]["title"],
                       year, pce_intensity.sum())
        mplot.set_value(mseries_specs["exports+"]["title"],
                       year, export_intensity.sum())

for (country, plot) in plots.items():
    plot.write_tables()
    plot.generate_plot()

for (country, plot) in marginal_plots.items():
    plot.write_tables()
    plot.generate_plot()

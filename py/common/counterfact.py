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

import sys

import common.config as common_config
import wiod.common
from common import utils
from common.matrixutils import NamedMatrix
from common.plotutils import GNUPlot

class CounterfactGenerator:

    def __init__(self, iogen, envgen):
        self.iogen = iogen
        self.envgen = envgen
        self.series_code = None

        self.levels = None
        self.intensities = None
        self.growths = None
        self.includes_indirect = None

    def get_iogen(self):
        return self.iogen

    def get_envgen(self):
        return self.envgen

    def set_series_code(self, series_code, title=None):
        if series_code != self.series_code:
            self.study_years = []
            self.Y_by_year = {}
            self.L_by_year = {}
            self.J_by_year = {}
            self.E_by_year = {} # only for descriptive stats

        self.series_code = series_code

        if title is None:
            if type(series_code) is list:
                self.env_title = " + ".join(
                    [common_config.ENV_SERIES_TITLES[code]
                     for code in series_code])
            else:
                self.env_title = common_config.ENV_SERIES_TITLES[series_code]
        else:
            self.env_title = title

    def prepare(self, year, series, 
                io_harmonizer=None, env_harmonizer=None):

        if year in self.study_years:
            return

        self.study_years.append(year)

        x = self.iogen.get_x(True)
        L = self.iogen.get_L()
        Y = self.iogen.get_Y(True)

        #xrows = set(x.get_rows())
        #irows = set(io_harmonizer.get_columns())
        #print(x.dims())
        #print(xrows.difference(irows), irows.difference(xrows))

        if io_harmonizer is not None:
            x = io_harmonizer.matrix_mult(x)
            Y = Y.matrix_postmult(io_harmonizer)
            t = io_harmonizer.transposed()
            L = io_harmonizer.matrix_mult(L).matrix_mult(t)

        E = self.envgen.get_env_vector(series)

        # some series don't have data for the given constraints
        if E.mat() is None:
            return

        if env_harmonizer is not None:
            E = env_harmonizer.matrix_mult(E)

        J = E.divide(x, True) # true removes divides by zero

        self.Y_by_year[year] = Y
        self.J_by_year[year] = J
        self.L_by_year[year] = L
        self.E_by_year[year] = E

        self.sector_titles = {}

    def set_sector_titles(self, titles):
        self.sector_titles = titles

    def get_descriptive_stats(self, include_indirect=False):
        if self.growths is None or self.includes_indirect != include_indirect:
            self.growths = {}
            self.levels = {}
            self.intensities = {}

            years = sorted(self.J_by_year.keys())
            if not len(years):
                return
    
            base_year = years[0]
            max_year = years[-1]
    
            base_E = self.E_by_year[base_year]
            base_J = self.J_by_year[base_year]
    
            self.sectors = sorted(base_E.get_rows())
            years = [max_year]
    
            for sector in self.sectors:
                sector_levels = []
                sector_intensities = []
    
                if include_indirect:
                    L_column = \
                        self.L_by_year[base_year].get_named_column(sector)
                    base_J_value = base_J.mult(L_column).sum()
                else:
                    base_J_value = base_J.get_element(sector)
                sector_intensities.append(base_J_value)
    
                base_E_value = base_E.get_element(sector)
                sector_levels.append(base_E_value)
    
                for year in years:
                    if year == base_year: continue
    
                    if include_indirect:
                        L_column = self.L_by_year[year].get_named_column(sector)
                        J_value = self.J_by_year[year].mult(L_column).sum()
                    else:
                        J_value = self.J_by_year[year].get_element(sector)
                    sector_intensities.append(J_value)
    
                    E_value = self.E_by_year[year].get_element(sector)
                    sector_levels.append(E_value)
    
                    if year == max_year and base_E_value > 0:
                        cagr = utils.cagr(
                            base_E_value, E_value, year - base_year)
                        self.growths[sector] = cagr
    
                self.intensities[sector] = sector_intensities
                self.levels[sector] = sector_levels

    def get_sector_values(self, sector, include_indirect=False):
        self.get_descriptive_stats(include_indirect)

        vals = self.levels[sector]
        indexes = range(len(vals))
        totals = [sum([self.levels[s][i] for s in self.sectors]) \
                      for i in indexes]

        percents = [100 * vals[i] / totals[i] for i in indexes]
        ivals = self.intensities[sector]

        result = {"level": vals, "percent": percents, "intensity": ivals}
        if sector in self.growths:
            result["growth"] = self.growths[sector]

        return result

    def print_sector(self, sector):
        result = self.get_sector_values(sector)
        if "growth" in result:
            growth = result["growth"]
            growth_str = " & %.3f" % growth
        else:
            growth_str = ""

        vals = result["level"]
        percents = result["percent"]
        ivals = result["intensity"]
        indexes = range(len(vals))

        def format_vals(i):
            p = percents[i]
            if p < 10:
                spacer = " ~ "
            else:
                spacer = " "
            return utils.add_commas(vals[i]) + \
                spacer + ("(%.1f\\%%)" % p) + \
                " & " + "%.3f" % ivals[i]

        title = self.get_sector_title(sector)

        print(title.ljust(18) + " & " +
              " & ".join([format_vals(i) for i in indexes]) +
              growth_str + " \\NN")

    def describe(self, include_indirect=False):
        self.get_descriptive_stats(include_indirect)

        # print rankings
        # right now we just assume there are more than 5 sectors

        rev_growths = dict((v, k) for k, v in self.growths.items())
        print("sector & %d &" % base_year +
              " & ".join([str(y).rjust(7) for y in years]) + " \\\\")
        for growth in sorted(rev_growths.keys())[-5:]:
            print_sector(rev_growths[growth])

        rev_levels = dict((row[0], k) for k, row in self.levels.items())
        print("sector & %d &" % base_year +
              " & ".join([str(y).rjust(7) for y in years]) + " \\\\")
        for level in sorted(rev_levels.keys())[-5:]:
            print_sector(rev_levels[level])

    def get_sector_title(self, sector):
        if sector in self.sector_titles:
            sector_name = self.sector_titles[sector]
        else:
            sector_name = sector
        return sector_name

    # the actual math portion of counterfact
    def do_counterfact(self, base_year, use_levels=False):
        base_L = self.L_by_year[base_year]
        base_J = self.J_by_year[base_year]
        base_Y = self.Y_by_year[base_year]
        base_Y_induced = base_Y.matrix_postmult(base_L)

        # http://stackoverflow.com/questions/3061/calling-a-function-from-a-string-with-the-functions-name-in-python
        if use_levels:
            pce_method = "get_pce"
            export_method = "get_exports"
        else:
            pce_method = "get_marginal_pce"
            export_method = "get_marginal_export"

        base_pce = getattr(base_Y_induced, pce_method)().mult(base_J).sum()
        #base_pce += base_Y_induced.get_named_column("CONS_g").mult(base_J).sum()
        base_export = getattr(base_Y_induced,
                              export_method)().mult(base_J).sum()

        pce_result = {}
        export_result = {}

        for year in self.study_years:
            if year not in self.J_by_year:
                continue

            J = self.J_by_year[year]

            # actual
            Y_induced = self.Y_by_year[year].matrix_postmult(
                self.L_by_year[year])
            pce_J = getattr(Y_induced, pce_method)().mult(J)
            #pce_J = pce_J.add(Y_induced.get_named_column("CONS_g").mult(J))
            export_J = getattr(Y_induced, export_method)().mult(J)

            pce_variations = {"A": pce_J.sum()}
            export_variations = {"A": export_J.sum()}

            # hold technology and FD constant, vary intensity
            pce_J = getattr(base_Y_induced, pce_method)().mult(J)
            #pce_J = pce_J.add(base_Y_induced.get_named_column("CONS_g").mult(J))
            export_J = getattr(base_Y_induced, export_method)().mult(J)
            pce_variations["J"] = pce_J.sum()
            export_variations["J"] = export_J.sum()

            # hold technology and intensity constant, vary final demand
            Y = self.Y_by_year[year].matrix_postmult(base_L)

            pce_J = getattr(Y, pce_method)().mult(base_J)
            #pce_J = pce_J.add(Y.get_named_column("CONS_g").mult(base_J))
            export_J = getattr(Y, export_method)().mult(base_J)

            pce_variations["Y"] = pce_J.sum()
            export_variations["Y"] = export_J.sum()
    
            # hold FD and intensity constant, vary tech
            L = self.L_by_year[year]
            Y_induced = base_Y.matrix_postmult(L)
            pce_J = getattr(Y_induced, pce_method)().mult(base_J)
            #pce_J = pce_J.add(Y_induced.get_named_column("CONS_g").mult(base_J))
            export_J = getattr(Y_induced, export_method)().mult(base_J)

            pce_variations["L"] = pce_J.sum()
            export_variations["L"] = export_J.sum()

            pce_result[year] = pce_variations
            export_result[year] = export_variations

        return (pce_result, export_result)

    def decompose_result(self, fd_result, base_year, rel_year):
        base = fd_result[base_year]["A"]
        series = fd_result[rel_year]
        shares = dict(
            (index, (series[index] - base) / base)
            for index in ["A", "J", "L", "Y"])
        return shares

    def counterfact(self, base_year, plot_group,
                    filename=None, title=None, compact=False,
                    use_levels=False):

        if base_year not in self.J_by_year:
            sys.stderr.write("cannot create counterfactuals for " + 
                             "%s at base year %d\n" % (self.env_title,
                                                       base_year))
            return

        if filename is None:
            if type(self.series_code) is str:
                filename = "%s_%d" % (self.series_code, base_year)
            else:
                filename = "%s_%d" % ("+".join(self.series_code), base_year)

        if title is None:
            #title = "Counterfactuals of %s at base year %d" \
            #    % (self.env_title, base_year)
            ptitle = ""
            etitle = ""
        else:
            ptitle = title + " - households"
            etitle = title + " - exports"

        pplot = CounterfactPlot(filename + "_pce", ptitle,
                                plot_group)
        eplot = CounterfactPlot(filename + "_export", etitle,
                                plot_group)

        for plot in (pplot, eplot):
            plot.set_base_year(base_year)
            plot.width = 800
            plot.height = 360

            #if compact:
            #    plot.compact = True
            #    plot.legend("off")
            #    plot.fontsize = 14
            #    plot.keyfontsize = 14
            #else:
            #    plot.keyfontsize = 11

            plot.legend("samplen 1")

        pplot.legend("horiz right below")
        pplot.suppress_title("L")
        pplot.suppress_title("J")

        eplot.legend("horiz left below")
        eplot.legend("width -3")
        eplot.suppress_title("A")
        eplot.suppress_title("Y")

        (pce_result, export_result) = self.do_counterfact(base_year, use_levels)

        # determine whether we need to scale down
        values = pce_result[base_year].values()
        if min(values) > 1000:
            scale_factor = 0.001
        else:
            scale_factor = 1

        for year in sorted(pce_result.keys()):
            for (indicator, value) in pce_result[year].items():
                pplot.set_value(indicator, year, value * scale_factor)
            for (indicator, value) in export_result[year].items():
                eplot.set_value(indicator, year, value * scale_factor)

        #GNUPlot.multiplot(1, 2, pplot, eplot)

        return (pce_result, export_result)

class CounterfactPlot(GNUPlot):

    def __init__(self, filename, title, group=None):
        GNUPlot.__init__(self, filename, title, group)

        self.aliases = {
            "A": "actual",
            "Y": "final demand",
            "L": "industry linkages",
            "J": "sector intensity",
            }

        styles = {
            "A": 'pointtype 7 linetype rgb "#B0C4DE"',
            "Y": 'pointtype 8 linetype rgb "#CC9900"',
            "L": 'pointtype 4 linetype rgb "#0000FF"',
            "J": 'pointtype 5 linetype rgb "#663300"',
            }

        for (indicator, series_style) in styles.items():
            series_title = self.get_series_title(indicator)
            self.set_series_style(series_title, series_style)

        self.base_year = None
        self.compact = False

        self.extra_specs = []

    def suppress_title(self, series):
        GNUPlot.suppress_title(self, self.get_series_title(series))

    def add_specs(self, spec):
        self.extra_specs.append(spec)

    def get_appearance_specs(self):
        specs = GNUPlot.get_appearance_specs(self)
        if self.compact:
            specs.append("set xtics 5")

        specs += self.extra_specs
        return specs

    def get_series_title(self, indicator):
        if indicator == "A":
            return "Actual"

        return self.aliases[indicator].capitalize()

    def set_value(self, series, x, y):
        series_title = self.get_series_title(series)
        GNUPlot.set_value(self, series_title, x, y)

    def set_base_year(self, year):
        self.base_year = year

    def get_plot_clauses(self):
        clauses = GNUPlot.get_plot_clauses(self)
        if self.base_year is not None:
            year = self.base_year
        else:
            year = min(self.xvalues)
        value = self.data[self.series_values[0]][year]
        clauses.append(str(value) + " linetype '#999999' title ''")
        return clauses


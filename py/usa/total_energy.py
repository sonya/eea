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

from common import fileutils, utils
from common.dbconnect import db
from common.plotutils import GNUPlot
from usa import bea, common, config, eia

elec_sources = {
    "CL": "Coal",
    "NG": "Natural gas",
    "NU": "Nuclear",
    "PA": "Petroleum",
    "RE": "Renewables",
    }

# customized just to plot effieicnty line
class ElectricityIntensityPlot(GNUPlot):
    def __init__(self, filename, title, group=None):
        GNUPlot.__init__(self, filename, title, group)
        self.overlay_values = {}
        self.writing_plotscript = False

    def set_overlay_value(self, x, y):
        self.overlay_values[x] = y

    def get_overlay_data_location(self):
        dataname = "%s-overlay.dat" % self.filename
        return fileutils.getcache(dataname, "gnuplot")

    def write_datafile(self):
        datafile = self.get_overlay_data_location()
        fh = open(datafile, "w")
        fh.write("year\tEfficiency\n")
        for i in range(len(self.xvalues)):
            x = self.xvalues[i]
            y = self.overlay_values[x]
            fh.write(str(x) + "\t" + str(y) + "\n")
        fh.close()

        GNUPlot.write_datafile(self)

    def get_axis_specs(self):
        specs = GNUPlot.get_axis_specs(self)
        specs.append("set y2range [ 0 : 1 ]")
        return specs

    def get_data_location(self):
        if self.writing_plotscript:
            return '< paste "%s" "%s"' % (GNUPlot.get_data_location(self),
                                          self.get_overlay_data_location())
        return GNUPlot.get_data_location(self)

    def get_plotscript_content(self):
        self.writing_plotscript = True
        content = GNUPlot.get_plotscript_content(self)
        self.writing_plotscript = False
        return content

    def get_plot_clauses(self):
        clauses = GNUPlot.get_plot_clauses(self)
        column = len(self.xvalues) + 1
        clauses.append(
            "'' using %d axis x1y2 with linespoints lc rgb 'black' title column(%d)"
            % (column, column))
        return clauses

dirname = "usa-pce-energy"

ff_plot = GNUPlot("total-ff", "Fossil fuels (trillion Btu)", dirname)
elec_plot = GNUPlot("total-elec", "Electricity (trillion Btu)", dirname)
ff_iplot = GNUPlot(
    "total-intensity-ff",
    "Fossil fuels (Btu per dollar)", dirname)
elec_iplot = GNUPlot(
    "total-intensity-elec",
    "Electricity (Btu per dollar)", dirname)

ff_plot.style = "histogram"
ff_iplot.style = "histogram"

elec_plot.style = "histogram rowstacked"
elec_iplot.style = "histogram rowstacked"

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
    Y_standard = iogen_standard.get_Y(use_exchange_rate=True)

    dirname = "usa-pce-energy"
    hybrid_vector = Y.get_total()
    gdp_value = Y_standard.get_total().sum() / 1000 # result is millions
    use_vector = L.matrix_mult(hybrid_vector)

    for i in range(len(energy_codes)):
        code = energy_codes[i]
        if eia.is_fossil_fuel(code):
            name = eia.name_for_naics(code)
            value = use_vector.get_element(rowname=code) # billion Btu
            # divide billion Btu by 1k for tBtu
            ff_plot.set_value(year, name, value / 1000)
            # div billion Btu by MM$ for kBtu/$
            ff_iplot.set_value(year, name, value / gdp_value)

    # manually generate electricity figures
    stmt = db.prepare(
        "select source, use_btu from %s.seds_short_%d where sector = 'EI'"
        % (config.EIA_SCHEMA, year))
    result = stmt()
    for row in result:
        source = row[0]
        btu = row[1] # billion Btu
        elec_plot.set_value(elec_sources[source], year, btu / 1000) # tBtu
        elec_iplot.set_value(elec_sources[source], year, btu / gdp_value)

    stmt = db.prepare(
        "select source, use_btu " + \
        "  from %s.seds_us_%d " % (config.EIA_SCHEMA, year) +
        " where (source = 'LO' and sector = 'TC') " + 
        "    or (source = 'TE' and sector = 'EI')")
    result = stmt()
    for row in result:
        if row[0] == "LO":
            losses = row[1]
        else:
            total = row[1]

    print(year, losses / total)

    # not now, the values are too flat over time to see anything
    #elec_iplot.set_overlay_value(year, 1 - losses / total)

ff_plot.write_tables()
ff_plot.generate_plot()
elec_plot.write_tables()
elec_plot.generate_plot()

ff_iplot.write_tables()
ff_iplot.generate_plot()
elec_iplot.write_tables()
elec_iplot.generate_plot()

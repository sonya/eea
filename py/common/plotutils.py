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

import os, sys, tempfile
from subprocess import Popen
import math, numpy

from common import config, fileutils

class GNUPlot:

    def __init__(self, filename, title, group=None):
        self.group = group
        self.filename = filename.replace(" ", "-")
        self.title = title
        self.data = {}
        self.image_type = config.DEFAULT_IMAGE_TYPE
        self.style = None
        self.series_values = None
        self.series_styles = {}
        self.xvalues = []
        self.width = 640
        self.height = 400

        self.axis_specs = None

        self.fontsize = 9
        self.keyfontsize = 9

        self.key_args = []
        self.suppressed_titles = []

        self.plotscript = None
        self.failed = False

        self.custom_setup = []

    def add_custom_setup(self, command):
        self.custom_setup.append(command)

    def legend(self, args):
        self.key_args.append(args)

    def suppress_title(self, series):
        self.suppressed_titles.append(series)

    def set_series_style(self, series, style):
        self.series_styles[series] = style

    def set_value(self, series, x, y):
        if type(series) is int or type(series) is float:
            series = str(series)

        if series not in self.data:
            self.data[series] = {}
        self.data[series][x] = y

        if x not in self.xvalues:
            self.xvalues.append(x)

    def get_image_location(self):
        imagename = "%s.%s" % (self.filename, self.image_type)
        if self.group is not None:
            return fileutils.getimagepath(imagename, self.group)
        else:
            return fileutils.getimagepath(imagename)

    def get_data_location(self):
        dataname = "%s.dat" % self.filename
        return fileutils.getcache(dataname, "gnuplot")

    def get_terminal_args(self):
        if self.image_type == "eps":
            return [
                "postscript eps color enhanced",
                'font "Arial"',
                ]
        elif self.image_type == "png":
            return [
                "png nocrop enhanced",
                'font "Arial" %d' % self.fontsize,
                " size %d,%d\n" % (self.width, self.height),
                ]

    def get_key_args(self):
        key_args = self.key_args[:]

        if "off" in key_args or self.image_type == "eps":
            return key_args

        key_args.append('font "Arial,%d"' % self.keyfontsize)
        return key_args

    def write_datafile(self):
        if self.series_values is None:
            self.series_values = sorted(self.data.keys())

        datapath = self.get_data_location()
        datafile = open(datapath, "w")

        # put label at the end since it might be a long string
        series_values = ['"' + value + '"' for value in self.series_values]
        datafile.write("\t".join(series_values) + "\tlabel\n")

        min_y = None
        max_y = None

        # these will determine where to place the legend
        # or if we need extra room across the board
        max_y_righthalf = None
        max_y_lefthalf = None

        # determine how many points are candidates for being covered
        # i.e. ignore the middle 25%: starting at 8 points the middle
        # 2 are ignored, at 16 the middle 4, etc.
        midpoint = len(self.xvalues) / 2
        midquarter = round(midpoint / 5) 
        lefthalf_cutoff = math.ceil(midpoint) - 1 - midquarter
        righthalf_cutoff = math.floor(midpoint) + midquarter

        for i in range(len(self.xvalues)):
            x = self.xvalues[i]
            rowdata = []

            for series in self.series_values:
                if series in self.data and x in self.data[series]:
                    rowdata.append(self.data[series][x])
                else:
                    rowdata.append("")

            func = lambda x: type(x) is int or type(x) is float \
                or type(x) is numpy.float64
            rowvalues = list(filter(func, rowdata))

            if self.style == "histogram rowstacked":
                local_min = sum(rowvalues)
                local_max = local_min
            elif self.style == "points":
                local_min = rowvalues[1]
                local_max = rowvalues[1]
            else:
                local_min = min(rowvalues)
                local_max = max(rowvalues)

            if max_y is None or max_y < local_max:
                max_y = local_max
            if min_y is None or min_y > local_min:
                min_y = local_min

            if i <= lefthalf_cutoff:
                if max_y_lefthalf is None or max_y_lefthalf < local_max:
                    max_y_lefthalf = local_max
            if i >= righthalf_cutoff:
                if max_y_righthalf is None or max_y_righthalf < local_max:
                    max_y_righthalf = local_max

            rowstrdata = [str(y) for y in rowdata]
            if type(x) is str:
                datafile.write("\t".join(rowstrdata) + '\t"' + x + '"\n')
            else:
                datafile.write("\t".join(rowstrdata) + "\t" + str(x) + "\n")

        datafile.close()

        #print(self.filename, max_y_righthalf, max_y_lefthalf, min_y, max_y)
        if max_y is None:
            self.failed = True
            return

        self.max_y = max_y * 1.1
        self.min_y = min_y
        self.max_y_lefthalf = max_y_lefthalf
        self.max_y_righthalf = max_y_righthalf

    def get_header(self):
        specs = [
            "reset",
            "set terminal %s" % " ".join(self.get_terminal_args()),
            "set output '%s'" % self.get_image_location(),
            ]

        return "\n".join(specs)

    def get_footer(self):
        return ""

    def get_appearance_specs(self):
        specs = []

        for arg in self.get_key_args():
            specs.append("set key %s" % arg)

        if self.is_histogram():
            specs.append("set style data histogram")
            specs.append("set palette gray")
            specs.append("unset colorbox")

            # rotate xtics based on arbitrary length cutoff
            xtic_len = max([len(str(series)) for series in self.xvalues])
            if self.style != "histogram horizontal" and xtic_len > 8:
                specs.append("set xtics nomirror rotate by -45")

            if self.style == "histogram rowstacked":
                specs.append("set style histogram rowstacked")
                specs.append("set boxwidth 0.75 absolute")
            elif self.style == "histogram horizontal":
                # rotated plot
                # http://gnuplot-tricks.blogspot.com/2009/10/turning-of-histogram.html
                specs.append("set xtics rotate by 90 scale 0")
                specs.append("set xtics offset -2,-%d"
                             % math.ceil(xtic_len / 2.5))

                # TODO make this work like right top, left top

                num_series = len(self.series_values)
                key_location = 1 - 0.05 * num_series
                for i in range(num_series):
                    series = self.series_values[i]
                    xtic = self.xvalues[i]
                    specs.append(
                        "set label %d '%s' at graph %.2f, 0.7 left rotate by 90"
                        % (i + 1, str(series), key_location + 0.05 * (i - 1)))

                specs.append(
                    "set key at graph %.2f, 0.7 horizontal samplen 0.1"
                    % (key_location + 0.01))

                specs.append("set y2tics rotate by 90")
                specs.append("set y2tics offset 0,-1")
                specs.append("unset ytics")

            else:
                specs.append("set style histogram clustered")

        specs.append("set style fill solid 1.00 border -1")

        if self.title and not config.SUPPRESS_PLOT_TITLES:
            # TODO: sanitize titles
            specs.append("set title '%s'" % self.title)

        return specs

    # TODO: this has a side effect on max_y
    def get_axis_specs(self):
        if self.axis_specs is not None:
            return self.axis_specs

        specs = []

        adjust = True
        for arg in self.key_args:
            argparts = arg.split()
            if arg == "off" or "out" in argparts or "below" in argparts:
                adjust = False

        # decide on y range
        if adjust:
            increase = 1.3 # threshold to add space on top
            move = 1.2     # theshold to determine where to place key
            increase_factor = 1.3
            if self.max_y_righthalf * increase > self.max_y_lefthalf and \
                self.max_y_lefthalf * increase > self.max_y_righthalf:
                # both left and right are within $increase of each other
                self.max_y *= increase_factor

            if self.max_y_righthalf > self.max_y_lefthalf * move:
                specs.append("set key left top")
            elif self.max_y_righthalf * move < self.max_y_lefthalf:
                specs.append("set key right top")

        if self.max_y < 1:
            order = int(round(math.log(self.max_y, 10)))
        else:
            order = int(math.log(self.max_y, 10))
        self.max_y = math.ceil(self.max_y / 10**order) * 10**order

        if order < 1:
            inner = "%%.%df" % abs(order)
        else:
            inner = "%d."

        if self.min_y < 0:
            self.min_y = math.floor(self.min_y / 10**order) * 10**order
            template = "set yrange [ %s : %s ] noreverse nowriteback" \
                % (inner, inner)
            specs.append(template % (self.min_y, self.max_y))
        else:
            template = "set yrange [ 0 : %s ] noreverse nowriteback" % inner
            specs.append(template % self.max_y)

        self.axis_specs = specs
        return specs

    def write_tables(self):
        self.write_datafile()
        if self.failed:
            sys.stderr.write("Invalid data for %s, aborting plot\n"
                             % self.filename)
            return

    def get_plotscript_content(self):
        content = "\n".join(self.get_appearance_specs()) + "\n" + \
            "\n".join(self.get_axis_specs()) + "\n" + \
            "\n".join(self.custom_setup) + "\n" + \
            "plot '%s' " % self.get_data_location() + \
            ", ".join(self.get_plot_clauses())
        print(content)
        return content

    def multiplot(nrows, ncols, *plots):
        for plot in plots:
            plot.write_tables()

        plotscript = tempfile.NamedTemporaryFile(mode="w",
                                                 suffix=".gnu",
                                                 delete=False)
        plotscript.write(plots[0].get_header() + "\n")
        plotscript.write("set multiplot layout %d,%d\n" % (nrows, ncols))

        for plot in plots:
            plotscript.write(plot.get_plotscript_content() + "\n")

        plotscript.write("unset multiplot\n")
        plotscript.close()

        filename = plotscript.name
        proc = Popen('gnuplot ' + filename, shell=True)
        proc.wait()

        if config.DEBUG_MODE:
            print("new plot created at %s" % plots[0].get_image_location())

        os.remove(filename)

    def is_histogram(self):
        return self.style is not None and self.style.startswith("histogram")

    def get_plot_clauses(self):
        plot_clauses = []

        # keep track of which column the series gets put in
        series_positions = {}
        num_series = len(self.series_values)
        for i in range(num_series):
            series = self.series_values[i]
            series_positions[series] = i + 1

        label_column = num_series + 1
        firstclause = True
        for i in range(num_series):
            series = self.series_values[i]
            pos = series_positions[series]
            if firstclause:
                if self.is_histogram():
                    clause = "using %d:xtic(%d) lc palette frac %.2f" \
                        % (pos, label_column, float(pos) / num_series)
                else:
                    clause = "using %d:%d" % (label_column, pos)
                firstclause = False
            else:
                if self.is_histogram():
                    clause = "'' using %d lc palette frac %.2f" \
                        % (pos, float(pos) / num_series)
                else:
                    clause = "'' using %d:%d" % (label_column, pos)

            if series in self.series_styles:
                clause += " " + self.series_styles[series]
            if series in self.suppressed_titles:
                clause += " notitle"
            elif self.style == "histogram horizontal":
                clause += " title ' '" # still want key for this series
            else:
                clause += " title column(%d)" % pos
            plot_clauses.append(clause)

        return plot_clauses

    def generate_plot(self):
        if self.failed:
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gnu",
                                         delete=False) as plotscript:

            plotscript.write(self.get_header() + "\n" +
                             self.get_plotscript_content() + "\n" +
                             self.get_footer())

            filename = plotscript.name

        proc = Popen('gnuplot ' + filename, shell=True)
        proc.wait()

        if config.DEBUG_MODE:
            print("new plot created at %s" % self.get_image_location())

        os.remove(filename)

class ScatterPlot(GNUPlot):

    def get_plot_clauses(self):
        clauses = ['using 1:2:3 with labels font "Arial,8"']
        return clauses

    def __init__(self, filename, title, group=None):
        GNUPlot.__init__(self, filename, title, group)
        self.style = "points"
        self.legend("off")



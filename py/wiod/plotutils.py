import math

from common.plotutils import GNUPlot
from common import fileutils, utils

# generate thematic map
class WorldMapPlot(GNUPlot):

    # 8-color scheme from http://www.sron.nl/~pault/
    # http://www.sron.nl/~pault/gnuplot/gnuplot-reference-lines.plt
    __better_colors = [
        "#332288",
        "#88CCEE",
        "#117733",
        "#DDCC77",
        "#CC6677",
        "#AA4499",
        "#44AA99",
        "#882255",
        ]

    # i don't think gnuplot has a way to figure out polygon
    # centroids from just the curve, so we will sadly read
    # do this from the source files
    __centroids = {
        # these curated centroids are small adjustments
        # to the default output of get_centroid
        "USA": (-93, 37.21),
        "CAN": (-96, 59),
        "IND": (79, 24),
        "LVA": (23, 56.871), # westward to avoid overlap with LTU
        "LTU": (25, 55.005), # eastward to avoid overlap with LVA
        "POL": (20, 51.7571), # eastward to avoid overlap with CZE
        "GRC": (21, 39.234), # westward to avoid overlap with BGR
        }

    __all_countries_key = "__ALL__"

    # current implementation doesn't actually get the centroid
    # just heuristic (mean x, mean y)
    def get_centroid(country):
        if country not in WorldMapPlot.__centroids:
            filename = fileutils.getdatapath(country + ".dat", "gnuplot")
            with open(filename) as f:
                longest_ring = None
                current_ring_len = 0
                total_lon = 0
                total_lat = 0

                for line in f:
                    coords = line.split()
                    # turns out the first ring is the most representative
                    # in esri's data, so we don't need to use other rings
                    if len(coords) != 2 and current_ring_len:
                        break

                    total_lon += float(coords[0])
                    total_lat += float(coords[1])
                    current_ring_len += 1

                mean_lon = total_lon / current_ring_len
                mean_lat = total_lat / current_ring_len

                WorldMapPlot.__centroids[country] = (mean_lon, mean_lat)

        return WorldMapPlot.__centroids[country]

    # use a list of tuples to keep order
    def add_tiny_barchart(self, country, value_pairs):
        if not len(self.miniplot_key_order):
            self.miniplot_key_order = [key for (key, value) in value_pairs]

        echo_columns = [
            ('\\"%s\\" ' % key) + str(value)
            for (key, value) in value_pairs]

        plot_clauses = []

        num_pairs = len(value_pairs)
        num_colors = len(WorldMapPlot.__better_colors)
        for i in range(num_pairs):
            (key, value) = value_pairs[i]

            if key not in self.miniplot_legend:
                # this is an idiotic way to assign colors
                # but it will work if value_pairs keys are uniform
                self.miniplot_legend[key] = \
                    WorldMapPlot.__better_colors[i % num_colors]
            color = self.miniplot_legend[key]

            if key != WorldMapPlot.__all_countries_key:
                if key not in self.miniplot_averages:
                    self.miniplot_averages[key] = 0
                self.miniplot_averages[key] += value

            if i == 0:
                series = '"< echo \'%s\'"' % " ".join(echo_columns)
            else:
                series = '""'

            plot_clauses.append(
                '%s using %d:xticlabels(%d) lc rgb "%s" title ""'
                % (series, i*2+2, i*2+1, color))

        self.miniplots[country] = ", ".join(plot_clauses)

    def __init__(self, filename, title, group=None):
        GNUPlot.__init__(self, filename, title, group)
        self.country_values = {}
        self.cbrange = None
        self.fillcolor = "#000066"

        self.xrange = (-180, 180)
        self.yrange = (-70, 90)

        # symbols by country
        self.miniplots = {}
        self.miniplot_legend = {}
        self.miniplot_averages = {}
        self.miniplot_key_order = []

        # graduated colors
        self.numcolors = 5  # 0 for continuous gradient
        self.binthresholds = []
        self.keytitles = {}
        self.break_method = "equal"
        self.bincolors = [ # from http://colorbrewer2.org
            "#FFFFCC", "#A1DAB4", "#41B6C4", "#2C7FB8", "#253494"
            ]

    def get_cbrange(self):
        if self.cbrange is None:
            values = self.country_values.values()
            maxval = max(values)
            minval = min(values)
            self.set_cbrange(minval, maxval)
        return self.cbrange

    def set_cbrange(self, minval, maxval):
        self.cbrange = (minval, maxval)

    def set_numcolors(self, numcolors):
        self.numcolors = numcolors
        self.bincolors = None

    def set_country_value(self, country, value):
        self.country_values[country] = value

    def write_tables(self):
        return

    def get_palette_specs(self):
        specs = []
        if self.numcolors < 1:
            specs.append(
                "set palette model XYZ functions " +
                "gray**0.35, gray**0.5, gray**0.8")
        return specs

    def get_appearance_specs(self):
        specs = [
            "unset yzeroaxis",
            "unset xtics",
            "unset ytics",
            ] + self.get_palette_specs()

        if self.numcolors < 1:
            specs.append("unset key")
        else:
            specs.append("set key left bottom")

        return specs

    def format_range(self, minval, maxval):
        # code from yrange calculation in GNUPlot class
        maxrange = maxval - minval

        if maxrange != 0: 
            if maxrange < 10:
                order = int(math.floor(math.log(maxrange, 10))) - 1
            else:
                order = int(math.log(maxrange, 10))
    
            if order < 1:
                inner = "%%.%df" % abs(order)
            else:
                inner = "%d"

                # show two sig figs
                minval = int(math.floor(float("%.1e" % minval)))
                maxval = int(math.floor(float("%.1e" % maxval)))

            return ((inner % minval), (inner % maxval))

        return None

    def get_cbrange_specs(self):
        specs = []

        (minval, maxval) = self.get_cbrange()
        cbrange = self.format_range(minval, maxval)
        if cbrange is not None:
            specs.append("set cbrange [ %s : %s ]" % (cbrange[0], cbrange[1]))
        else:
            self.set_numcolors(1)

        return specs

    def get_axis_specs(self):
        specs = [
            "set xrange [ %d : %d ]" % self.xrange,
            "set yrange [ %d : %d ]" % self.yrange,
            ]

        if self.numcolors < 1:
            specs += self.get_cbrange_specs()

        return specs

    def get_data_location(self):
        return fileutils.getdatapath("continent.dat", "gnuplot")

    def prep_bincolors(self):
        if self.bincolors is None:
            self.bincolors = {}

            rgb = utils.rgb(self.fillcolor.strip("#"))
            rgb_interval = (
                (255 - rgb[0]) / self.numcolors,
                (255 - rgb[1]) / self.numcolors,
                (255 - rgb[2]) / self.numcolors,
                )

            for i in range(self.numcolors):
                hexcolor = "#" + utils.triplet(rgb)
                self.bincolors.append(hexcolor)

                rgb = (
                    round(rgb[0] + rgb_interval[0]),
                    round(rgb[1] + rgb_interval[1]),
                    round(rgb[2] + rgb_interval[2]),
                    )

    def prep_colorspecs(self):
        if len(self.miniplots):
            self.numcolors = 1
            self.fillcolor = "#CCCCCC"

        if self.numcolors > 1:
            self.prep_bincolors()

            if self.break_method == "equal":
                items_per_bin = int(len(self.country_values) / self.numcolors)
                values = ((v, k) for (k, v) in self.country_values.items())
                sortedvalues = sorted(values)

                (prev_lb, prev_lb_country) = sortedvalues[0]
                binthresholds = [prev_lb]

                itemcounter = 1
                for (value, country) in sortedvalues[1:]:
                    if itemcounter % items_per_bin == 0:
                        binthresholds.append(value)

                        if prev_lb is not None:
                            binrange = self.format_range(prev_lb, value)
                            self.keytitles[prev_lb_country] = \
                                "%s to %s" % (binrange[0], binrange[1])

                        prev_lb = value
                        prev_lb_country = country

                    itemcounter += 1

                # there is one more threshold than titles
                for (lb, hexcolor) in zip(binthresholds, self.bincolors):
                    self.binthresholds.append((lb, hexcolor))

    def get_colorspec(self, value):
        if self.numcolors < 1:
            (minval, maxval) = self.get_cbrange()
            fraction = (value - minval) / (maxval - minval)
            return "palette frac %.2f" % fraction

        elif self.numcolors == 1:
            return "rgb '%s'" % self.fillcolor

        else:
            lasthex = None
            for (threshold, hexcolor) in self.binthresholds:
                if value < threshold:
                    break
                lasthex = hexcolor

            if lasthex is not None:
                return "rgb '%s'" % lasthex

        raise Exception("cannot find color spec for value %.3f" % value)

    def get_header(self):
        specs = GNUPlot.get_header(self)
        if len(self.miniplots):
            specs += "\n" + "\n".join([
                    "set multiplot",
                    "set style data histogram",
                    "set style fill solid border rgb 'black'",
                    "unset xtics",
                    "unset ytics",
                    ])
        return specs

    # this is really not the right place for this
    def get_footer(self):
        footer = GNUPlot.get_footer(self)
        if len(self.miniplots):
            averages = []
            for key in self.miniplot_key_order:
                value = self.miniplot_averages[key]
                averages.append((key, value / len(self.miniplots)))
            self.add_tiny_barchart(WorldMapPlot.__all_countries_key, averages)

            footerspecs = []
            width = 0.08
            height = 0.25
            for (country, plotspec) in self.miniplots.items():
                if country == WorldMapPlot.__all_countries_key:
                    plot_x = width
                    plot_y = height
                else:
                    (x, y) = WorldMapPlot.get_centroid(country)
                    plot_x = (x - self.xrange[0]) /\
                        (self.xrange[1] - self.xrange[0])
                    plot_y = (y - self.yrange[0]) /\
                        (self.yrange[1] - self.yrange[0])

                # extra plot to show scale
                if country == WorldMapPlot.__all_countries_key:
                    footerspecs += [
                        "set title '%d country average' font 'Arial,13'"
                            % (len(self.miniplots) - 1),
                        "set ytics 1",
                        "set size %.2f, %.2f" % (width + 0.02, height + 0.04),
                        ]
                else:
                    footerspecs += [
                        "set title ''",
                        "unset ytics",
                        "set size %.2f, %.2f" % (width, height),
                        ]

                footerspecs += [
                    "unset border",
                    "set key off",
                    "set yrange [ -2 : 2 ]",
                    # bars have width 0.2, start at -0.2
                    # -0.3 : 0.5 produces 0.1 left and right margin for 3 bars
                    # TODO make this depend on number of items
                    "set xrange [ -0.3 : 0.5 ]",
                    "set origin %.2f, %.2f" % (plot_x - width / 2,
                                               plot_y - height / 2),
                    "plot %s" % plotspec,
                    ]

            del(self.miniplots[WorldMapPlot.__all_countries_key])

            # show scale
            #footerspecs += [
            #    "unset border",
            #    "set yzeroaxis lw 1 lc rgb 'black'",
            #    "set ytics 1",
            #    "plot NaN",
            #    ]

            footer += "\n" + "\n".join(footerspecs) \
                + "\n" + "unset multiplot"

            #print(footer)

        return footer

    def get_plot_clauses(self):
        clauses = [
            "with lines lc rgb '#CCCCCC' title ''" # qualifier for continent
            ]

        self.prep_colorspecs()

        values = ((v, k) for (k, v) in self.country_values.items())
        for (value, country) in sorted(values, reverse=True):
            filename = fileutils.getdatapath(country + ".dat", "gnuplot")

            clauseparts = []
            clauseparts.append("'%s' with filledcurve" % filename)
            clauseparts.append("lc %s" % self.get_colorspec(value))
            if country in self.keytitles:
                clauseparts.append("title '%s'" % self.keytitles[country])
            else:
                clauseparts.append("title ''")

            # outlines
            clauses.append(" ".join(clauseparts))

            clauses.append(
                "'%s' with lines lc rgb 'black' lw 0.3 title ''" % filename)

        if len(self.miniplots):
            # keep colors in order
            inverse = dict((v, k) for (k, v) in self.miniplot_legend.items())
            for color in WorldMapPlot.__better_colors:
                if color in inverse:
                    # fake legend by plotting nonexistent data
                    clauses.append(
                        "NaN title '%s' lw 10 lc rgb '%s'"
                        % (inverse[color], color))

        return clauses

def darken_color(triplet):
    result = []

    min_rgb = min(triplet)

    for i in range(3):
        result.append(int((triplet[i] - min_rgb * 0.3) * 0.95))

    return result

class BubblePlot(GNUPlot):

    def __init__(self, filename, title, group=None):
        GNUPlot.__init__(self, filename, title, group)
        self.series_values = ["x", "y", "size", "color", "style"]
        self.style = "points"
        self.legend("off")

    def set_point(self, label, xvalue, yvalue, size, hexcolor, style=7):
        rgb = utils.rgb(hexcolor.strip("#"))

        # make colors darker for hollow points
        # styles: http://jerzak.eu/resources/sandbox/img/gnuplot-ptlt.gif
        if style not in (5, 7, 9, 11, 13, 15):
            rgb = darken_color(rgb)

        color = rgb[0] * 65536 + rgb[1] * 256 + rgb[2]

        self.set_value("x", label, xvalue)
        self.set_value("y", label, yvalue)
        self.set_value("size", label, size)
        self.set_value("color", label, color)
        self.set_value("style", label, style)

    def get_axis_specs(self):
        specs = []
        return specs

    def write_tables(self):
        # normalize point sizes
        sizes = self.data["size"]
        max_size = max(sizes.values())
        min_size = min(sizes.values())
        for key in sizes.keys():
            size = sizes[key]
            sizes[key] = math.sqrt((size - min_size) / (max_size - min_size)) * 10
        self.data["size"] = sizes
        GNUPlot.write_tables(self)

    def get_plot_clauses(self):
        plot_clauses = []

        styles = list(set(self.data["style"].values()))

        # set value to NaN if criteria doesn't match
        # http://stackoverflow.com/questions/6564561/gnuplot-conditional-plotting-plot-col-acol-b-if-col-c-x

        if len(styles) == 1:
            plot_clauses.append("using 1:2:3:4 with points pointtype %d pointsize variable lt rgb variable" % style)
        else:
            plot_clauses.append("using 1:($5==%d?$2:1/0):3:4 with points pointtype %d pointsize variable lt rgb variable" % (styles[0], styles[0]))
            for style in styles[1:]:
                plot_clauses.append("'' using 1:($5==%d?$2:1/0):3:4 with points pointtype %d pointsize variable lt rgb variable" % (style, style))
        plot_clauses.append("'' using 1:2:6 with labels font 'Arial,7'")
        plot_clauses.append("x lt rgb '#CCCCCC'")

        return plot_clauses

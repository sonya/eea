import math

from common.plotutils import GNUPlot
from common import fileutils, utils

# generate thematic map
class WorldMapPlot(GNUPlot):

    def __init__(self, filename, title, group=None):
        GNUPlot.__init__(self, filename, title, group)
        self.country_values = {}
        self.cbrange = None

    def set_cbrange(self, minval, maxval):
        self.cbrange = (minval, maxval)

    def set_country_value(self, country, value):
        self.country_values[country] = value

    def write_tables(self):
        return

    def get_appearance_specs(self):
        specs = [
            "unset key",
            "unset yzeroaxis",
            "unset xtics",
            "unset ytics",
            "set palette model XYZ functions gray**0.35, gray**0.5, gray**0.8"
            ]
        return specs

    def get_cbrange(self):
        if self.cbrange is None:
            values = self.country_values.values()
            maxval = max(values)
            minval = min(values)
            self.cbrange = (minval, maxval)
        return self.cbrange

    def get_axis_specs(self):
        specs = [
            "set xrange [ -180 : 180 ]",
            "set yrange [ -70 : 90 ]",
            ]

        (minval, maxval) = self.get_cbrange()

        # code from yrange calculation in GNUPlot
        maxrange = maxval - minval
        if maxrange < 10:
            order = int(math.floor(math.log(maxrange, 10))) - 1
        else:
            order = int(math.log(maxrange, 10))

        if order < 1:
            inner = "%%.%df" % abs(order)
        else:
            inner = "%d."

        template = "set cbrange [ %s : %s ]" \
            % (inner, inner)
        specs.append(template % (minval, maxval))

        return specs

    def get_data_location(self):
        return fileutils.getdatapath("continent.dat", "gnuplot")

    def get_plot_clauses(self):
        clauses = ["with lines lc rgb '#CCCCCC'"] # qualifier for continent
        (minval, maxval) = self.get_cbrange()
        for (country, value) in self.country_values.items():
            filename = fileutils.getdatapath(country + ".dat", "gnuplot")
            fraction = (value - minval) / (maxval - minval)
            clauses.append(
                "'%s' with filledcurve lc palette frac %.2f"
                % (filename, fraction))

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

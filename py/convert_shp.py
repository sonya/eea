# This is a script that converts world continent and country boundary
# shapefiles into a format that can be plotted with GNUPlot.
#
# This has used specifically with the Continents and Country boundaries
# (generalized) shapefiles from the ESRI Data and Maps (2010) collection,
# which should be available to users with an ESRI license.
#

import sys
from parsers.shp import ShpParser

class GNUPlotShpParser(ShpParser):

    def write_data(self, filename=None, filters=[]):
        if filename is None:
            filename = "out.dat"
        outf = open(filename, "w")

        for feature in self.features:
            stop = False
            if len(filters):
                properties = feature["properties"]
                for (key, values) in filters:
                    prop = properties[key]
                    if prop not in values:
                        stop = True

            if stop:
                continue

            geometry = feature["geometry"]
            geomtype = geometry["type"]
            coords = geometry["coordinates"]

            if geomtype == "Polygon":
                for ring in geometry["coordinates"]:
                    for (lon, lat) in ring:
                        outf.write("%.2f  %.2f\n" % (lon, lat))
                    outf.write("\n")

continent_filters = [
    ("CONTINENT", [
            "Africa",
            "Australia",
            "Asia",
            "North America",
            "Oceania",
            "South America",
            "Europe"])]

if len(sys.argv) > 1:
    filename = sys.argv[1]
    parser = GNUPlotShpParser(filename)
    parser.read_header()
    parser.read_all_records()
    parser.write_data()

else:
    countries = [
        "IND", "CHN", "IDN", "LVA", "BGR", "ROU", "LTU",
        "BRA", "RUS", "EST", "TUR", "POL", "MEX", "SVK",
        "HUN", "TWN", "CZE", "KOR", "SVN", "MLT", "PRT",
        "GRC", "IRL", "CYP", "ESP", "FIN", "GBR", "SWE",
        "FRA", "ITA", "AUS", "BEL", "AUT", "CAN", "DEU",
        "JPN", "DNK", "NLD", "USA", "LUX",
        ]

    filename = "country"
    parser = GNUPlotShpParser(filename)
    parser.read_header()
    parser.read_all_records()

    for country in countries:
        parser.write_data(
            filename=country + ".dat",
            filters=[("ISO_3DIGIT", [country])])



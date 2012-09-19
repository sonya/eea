import math

from usa import bea, config, eia
from common.dbconnect import db
from usa.nipa import Deflators
from common.ioutils import IOMatrixGenerator
from common.matrixutils import NamedMatrix
from common.plotutils import GNUPlot

deflators = Deflators()

def io_codes_for_year(year):
    codes = {}
    stmt = db.prepare("select * from %s.codes_%d" % (config.IO_SCHEMA, year))
    result = stmt()
    for row in result:
        codes[row[0]] = row[1]

    return codes

def pce_bridge_vector(year, pcegroup=None):
    view = "%s.nipa_pce_%d" % (config.IO_SCHEMA, year)

    iogen = iogen_for_year(year, True, True, True) # just to get sectors
    vector = NamedMatrix(False, rows=iogen.get_sectors(), cols=["pce"])

    if pcegroup is None: # get total
        stmt = db.prepare(
            "SELECT commodity, sum(value) FROM %s GROUP BY commodity" % view)
        result = stmt()
    else:
        stmt = db.prepare(
            "SELECT commodity, value FROM %s WHERE pcegroup = $1" % view)
        result = stmt(pcegroup)

    for row in result:
        vector.set_element(row[0], "pce", row[1])

    return vector

def fd_sectors_for_year(year, is_hybrid):
    if is_hybrid:
        strings = {
            "code_table": "hybrid_codes_%d" % year,
            "x_table": "hybrid_transactions_%d" % year,
            }

        stmt = db.prepare("""
            SELECT code
              FROM %(code_table)s
             WHERE (code IN (SELECT distinct from_sector from %(x_table)s)
                 OR code IN (SELECT distinct to_sector from %(x_table)s))
               AND sector_type = $1
             ORDER BY code""" % strings)

        result = stmt(bea.FINAL_DEMAND)

    else:
        strings = {
            "code_table": "%s.codes_%d" % (config.IO_SCHEMA, year),
            #"x_table": "%s.transact_view_%d" % (config.IO_SCHEMA, year),
            "fd_criteria": bea.fd_sector_criteria[year],
            }

        stmt = db.prepare(
            "SELECT code FROM %(code_table)s WHERE %(fd_criteria)s" % strings)

        result = stmt()

    return [row[0] for row in result]

def iogen_for_year(year,
                   is_hybrid=False,
                   allow_imports=True,
                   adjust_for_inflation=False):

    if is_hybrid:
        transaction_table = "hybrid_transactions_%d" % year
        value_column_name = "expenditure"
    else:
        transaction_table = "%s.transact_view_%d" % (config.IO_SCHEMA, year)
        value_column_name = "fob"

    fd_codes = fd_sectors_for_year(year, is_hybrid)

    iogen = IOMatrixGenerator(
        transaction_table=transaction_table,
        from_sector_name="from_sector",
        to_sector_name="to_sector",
        value_column_name=value_column_name,
        final_demand_sectors=fd_codes)
    iogen.set_pce_col(bea.fd_sectors[year]["pce"])
    iogen.set_export_col(bea.fd_sectors[year]["exports"])

    from_blacklist = [bea.tourism_adjustment_codes[year]]
    to_blacklist = [bea.tourism_adjustment_codes[year]]
    if year in (1972, 1977, 1982):
        from_blacklist.append("780300")
        to_blacklist.append("780300")

    if not allow_imports:
        to_blacklist.append(bea.fd_sectors[year]["imports"])

    iogen.blacklist_from_sectors(from_blacklist)
    iogen.blacklist_to_sectors(to_blacklist)

    if adjust_for_inflation:
        iogen.set_exchange_rate(deflators.get_gdp_deflator(year))

    return iogen

# TODO: make matrices.py use this also
def graph_table(filename, title, vector,
                base_year, intensity_divisor, sector_groups):

    plot = GNUPlot(filename, title, "usa")

    data = {}
    sortby = {}

    numerators = {}
    denominators = {}

    for key in sector_groups.keys():
        data[key] = {}
        denominators[key] = dict((year, 0) for year in config.STUDY_YEARS)
        numerators[key] = dict((year, 0) for year in config.STUDY_YEARS)

    max_year = max(config.STUDY_YEARS)
    for sector in vector.keys():
        print(sector)
        numerator = vector[sector]

        for (key, sectors) in sector_groups.items():
            if sector in sectors:
                for year in config.STUDY_YEARS:
                    if intensity_divisor is not None:
                        denominators[key][year] += \
                            intensity_divisor[sector][year]
                    else:
                        denominators[key][year] += 1

                    numerators[key][year] += numerator[year]
                break

    for key in sector_groups.keys():
        print(key, denominators[key])
        data[key] = dict(
            (year, numerators[key][year] / denominators[key][year])
            for year in config.STUDY_YEARS)
        sortby[ data[key][max_year] / data[key][base_year] ] = key

    sorted_groups = [sortby[key] for key in sorted(sortby.keys(), reverse=True)]

    plot.add_custom_setup("set style data linespoints")
    plot.add_custom_setup("unset colorbox")

    min_x = 5 * math.floor(min(config.STUDY_YEARS) / 5)
    max_x = 5 * math.ceil(max(config.STUDY_YEARS) / 5) + 5 # room for labels
    plot.add_custom_setup("set xrange [ %d : %d ]" % (min_x, max_x))

    interval = 1 / (len(sorted_groups) - 1)
    for i in range(len(sorted_groups)):
        plot.add_custom_setup("set style lines %d lc palette frac %.2f lw 2"
                              % (i + 1,  i * interval))
    series_values = []

    def name_for_group(group):
        if group in bea.short_nipa:
            group_name = bea.short_nipa[group]
        else:
            group_name = group
        return group_name

    for i in range(len(sorted_groups)):
        group = sorted_groups[i]
        group_name = name_for_group(group)

        series_values.append(group_name)
        plot.suppress_title(group_name)
        base_value = data[group][base_year]
        for year in config.STUDY_YEARS:
            plot.set_value(group_name, year,
                           data[group][year] / base_value * 100)

        plot.set_series_style(group_name, "linestyle %d" % (i + 1))

    plot.series_values = series_values
    plot.write_tables()
    plot.get_axis_specs() # make sure max_y is adjusted

    prev_pos = None
    for i in range(len(sorted_groups)):
        group = sorted_groups[i]
        group_name = name_for_group(group)

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

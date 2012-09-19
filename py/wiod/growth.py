#!/usr/bin/python3

from wiod import config, common
from common.dbconnect import db
from common import imfdata, sqlhelper, utils
from common.plotutils import GNUPlot, ScatterPlot
import usa.config

def do_overview_table(sortby):
    minyear = min(config.STUDY_YEARS)
    maxyear = max(config.STUDY_YEARS)

    data = {}
    reverse_data = {}
    for (country, name) in config.countries.items():
        (env_i, gdp_i, intensity_i) = common.get_efficiency(
            country, minyear, "env", "gdp")
        (env_f, gdp_f, intensity_f) = common.get_efficiency(
            country, maxyear, "env", "gdp")

        if sortby == "growth":
            pop_i = common.get_national_value(country, minyear, "pop")
            pop_f = common.get_national_value(country, maxyear, "pop")
            ppp_i = common.get_national_value(country, minyear, "ppppc")
            ppp_f = common.get_national_value(country, maxyear, "ppppc")

            percap_i = env_i / pop_i * 1000
            percap_f = env_f / pop_f * 1000

            growth = intensity_f - intensity_i
            pgrowth = percap_f - percap_i
            reverse_data[ppp_i] = name
            data[name] = [
                utils.add_commas(val).rjust(10) for val in (ppp_i, ppp_f)]
            data[name] += [
                "%.2f" % val for val in (intensity_i, intensity_f, growth,
                                         percap_i, percap_f, pgrowth)]

        else: # end year intensity
            reverse_data[intensity_f] = name
            data[name] = [
                utils.add_commas(val).rjust(10)
                for val in (gdp_i, gdp_f, env_i, env_f)]
            data[name] += ["%.2f" % val for val in (intensity_i, intensity_f)]

    for key in sorted(reverse_data.keys()):
        country = reverse_data[key]
        vals = data[country]
        print(country.ljust(18) + " & " + " & ".join(vals) + " \\NN")

def do_import_table():
    minyear = min(config.STUDY_YEARS)
    maxyear = max(config.STUDY_YEARS)
    sector = 'CONS_h'

    fd = {}
    fd_imports = {}

    for year in (minyear, maxyear):
        strings = {
            "schema": config.WIOD_SCHEMA,
            "year": year,
            }

        stmt = db.prepare(
            """SELECT country, sum(value)
                 FROM %(schema)s.niot_%(year)d
                WHERE to_ind = $1
                  AND is_import = $2
                GROUP BY country""" % strings)

        fd[year] = {}
        fd_imports[year] = {}

        for (country, value) in stmt(sector, True):
            fd_imports[year][country] = value
            fd[year][country] = value

        for (country, value) in stmt(sector, False):
            fd[year][country] += value

    shares = {}
    for (country, total) in fd[maxyear].items():
        share = fd_imports[maxyear][country] / total
        shares[share] = country

    sorted_shares = sorted(shares.keys(), reverse=True)
    midpoint = int(len(sorted_shares) / 2)
    for i in range(midpoint):
        values = []
        for index in (i, i + midpoint):
            country = shares[sorted_shares[index]]
            minval = imfdata.convert_to_2005(
                fd_imports[minyear][country], country, minyear)
            maxval = imfdata.convert_to_2005(
                fd_imports[maxyear][country], country, maxyear)
            minshare = fd_imports[minyear][country] / fd[minyear][country]
            maxshare = fd_imports[maxyear][country] / fd[maxyear][country]

            values += [
                config.countries[country],
                utils.add_commas(minval), utils.add_commas(maxval),
                "%.1f" % (minshare * 100), "%.1f" % (maxshare * 100),
                ""] # want blank space between two halves

        values.pop() # remove trailing empty string
        print(" & ".join(values) + " \\NN")


def do_kyoto_table():
    minyear = min(config.STUDY_YEARS)
    maxyear = max(config.STUDY_YEARS)

    minstrings = {
        "schema": config.WIOD_SCHEMA,
        "year": minyear,
        "fd_sectors": sqlhelper.set_repr(config.default_fd_sectors),
        }
    maxstrings = minstrings.copy()
    maxstrings["year"] = maxyear

    envsql = """SELECT value FROM %(schema)s.env_%(year)d
                 WHERE country = $1 AND measurement = $2
                   AND industry = 'total'"""

    envstmt_i = db.prepare(envsql % minstrings)
    envstmt_f = db.prepare(envsql % maxstrings)

    un_stmt = db.prepare(
        "SELECT value FROM %s.mdg_emissions" % config.UN_SCHEMA +
        " WHERE country = $1 AND year = $2")

    data = {}
    (eu_i, eu_f, un_eu_90, un_eu_i, un_eu_f) = (0, 0, 0, 0, 0)
    for (country, name) in config.countries.items():
        env_i = envstmt_i(country, "CO2")[0][0]
        env_f = envstmt_f(country, "CO2")[0][0]
        percent = (env_f - env_i) / env_i * 100

        (un_env_90, un_env_91, un_env_i, un_env_f,
         un_percent, un_percent_90) = \
            (0, 0, 0, 0, None, None)
        result = un_stmt(country, 1990)
        if len(result):
            un_env_90 = result[0][0]
        else:
            # use 1991 as a proxy for 1990 for some countries if applicable
            # germany is the only annex b country that is applicable
            # so hopefully it won't mess up eu15 calculation too much
            result = un_stmt(country, 1991)
            if len(result):
                un_env_91 = result[0][0]
        result = un_stmt(country, minyear)
        if len(result):
            un_env_i = result[0][0]
        result = un_stmt(country, maxyear)
        if len(result):
            un_env_f = result[0][0]

        if un_env_i and un_env_f:
            un_percent = (un_env_f - un_env_i) / un_env_i * 100

        if un_env_90 and un_env_f:
            un_percent_90 = (un_env_f - un_env_90) / un_env_90 * 100

        data[country] = (env_i, env_f, percent, un_percent, un_percent_90)

        if country in config.eu15:
            eu_i += env_i
            eu_f += env_f
            un_eu_i += un_env_i
            un_eu_f += un_env_f
            if un_env_90:
                un_eu_90 += un_env_90
            else:
                un_eu_90 += un_env_91

    eu_percent = (eu_f - eu_i) / eu_i * 100
    un_eu_percent = (un_eu_f - un_eu_i) / un_eu_i * 100
    un_eu_percent_90 = (un_eu_f - un_eu_90) / un_eu_90 * 100

    print("%s & %s & %s & %d\\%% & %.1f\\%% & %.1f\\%% & %.1f \\NN" %
          ("EU-15".ljust(18),
           utils.add_commas(eu_i).rjust(9),
           utils.add_commas(eu_f).rjust(9),
           -8, eu_percent, un_eu_percent, un_eu_percent_90))

    for (target, countries) in config.annex_b_countries.items():
        for country in countries:
            vals = data[country]
            if vals[4] is None:
                percent_90 = ""
            else:
                percent_90 = "%.1f" % vals[4]
            print("%s & %s & %s & %d\\%% & %.1f\\%% & %.1f & %s \\NN" %
                  (config.countries[country].ljust(18),
                   utils.add_commas(vals[0]).rjust(9),
                   utils.add_commas(vals[1]).rjust(9),
                   target, vals[2], vals[3], percent_90))

def do_plots():
    for (name, measurements) in config.env_series_names.items():
        data = {}
        for year in config.STUDY_YEARS:
            strings = {
                "schema": config.WIOD_SCHEMA,
                "year": year,
                "fd_sectors": sqlhelper.set_repr(config.default_fd_sectors),
                "measurements": sqlhelper.set_repr(measurements),
                "nipa_schema": usa.config.NIPA_SCHEMA,
                }
    
            stmt = db.prepare(
                """SELECT a.country, a.series, b.gdp,
                          a.series / b.gdp as intensity
                     FROM (SELECT country, sum(value) as series
                             FROM %(schema)s.env_%(year)d
                            WHERE industry = 'total'
                              AND measurement in %(measurements)s
                            GROUP BY country) a,
                          (SELECT aa.country, sum(value) * deflator as gdp
                             FROM %(schema)s.indbyind_%(year)d aa,
                                  (SELECT 100 / gdp as deflator
                                     FROM %(nipa_schema)s.implicit_price_deflators
                                    WHERE year = $1) bb
                            WHERE to_ind in %(fd_sectors)s
                            GROUP BY aa.country, deflator) b
                    WHERE a.country = b.country
                      AND a.series is not null
                    ORDER BY a.series / b.gdp""" % strings)
    
            for row in stmt(year):
                country = row[0]
                intensity = row[3]
                if country not in data:
                    data[country] = {}
                data[country][year] = intensity
    
        slopes = {}
        for (country, country_data) in data.items():
            n = len(country_data.keys())
    
            if n < 2:
                continue
    
            sum_y = sum(country_data.values())
            sum_x = sum(country_data.keys())
            slope = (n * sum([k * v for (k, v) in country_data.items()]) \
                     - sum_x * sum_y) / \
                    (n * sum([k * k for k in country_data.keys()]) - sum_x)
    
            slopes[country] = slope * 1000000
    
        years = "%d-%d" % (config.STUDY_YEARS[0], config.STUDY_YEARS[-1])
        i = 0
        binsize = 8
        plot = None
        for (country, slope) in sorted(slopes.items(), key=lambda x: x[1]):
            if i % binsize == 0:
                if plot is not None:
                    plot.write_tables()
                    plot.generate_plot()
    
                tier = i / binsize + 1
                plot = GNUPlot("tier%d" % tier, "",
                               #"%s intensity from %s, tier %d" \
                               #    % (name, years, tier),
                               "wiod-%s" % name.replace(" ", "-"))
    
                plot.legend("width -5")
    
            for year in config.STUDY_YEARS:
                if year in data[country]:
                    plot.set_value(
                        "%s (%.2f)" % (config.countries[country], slope),
                        year,
                        data[country][year])
    
            i += 1
    
        if plot is not None:
            plot.write_tables()
            plot.generate_plot()

def do_kuznets_plot():
    minyear = min(config.STUDY_YEARS)
    maxyear = max(config.STUDY_YEARS)

    plot = ScatterPlot("gdp vs emissions change", None, "wiod")

    for country in config.countries:
        gdp_pop = common.get_national_value(country, minyear, "ppppc")
        (env_i, denom_i, intensity_i) = common.get_efficiency(
            country, minyear, "env", "gdp")
        (env_f, denom_f, intensity_f) = common.get_efficiency(
            country, maxyear, "env", "gdp")

        # numbers are just for sorting which goes on x axis
        plot.set_value("1 ppp per capita", country, gdp_pop)
        plot.set_value("2 emiss change", country, intensity_f - intensity_i)

    plot.write_tables()
    plot.generate_plot()

    for year in (minyear, maxyear):
        plot = ScatterPlot("gdp vs emissions %d" % year, None, "wiod")

        for country in config.countries:
            gdp_pop = common.get_national_value(country, year, "ppppc")
            env_pop = common.get_efficiency(country, year, "env", "gdp")

            plot.set_value("1 gdp per capita", country, gdp_pop)
            plot.set_value("2 emissions per capita", country, env_pop[2])

        plot.write_tables()
        plot.generate_plot()

#do_overview_table()
do_overview_table("growth")
#do_import_table()
#do_kyoto_table()
#do_plots()

#do_kuznets_plot()


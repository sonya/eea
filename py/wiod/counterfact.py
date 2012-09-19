import common.config as common_config
from wiod import common, config
from common import matrixutils, sqlhelper, imfdata
from common.counterfact import CounterfactGenerator
from common.plotutils import ScatterPlot
from wiod.plotutils import WorldMapPlot, BubblePlot
from usa.nipa import Deflators

use_levels = True

intense_sectors = [
    "secE", # utilities
    "sec27t28", # basic & fab min
    "sec26", # other nonmetallic mineral
    "secC", # mining
    "sec60", # inland transport
    "sec62", # air transport
    "secAtB", # agriculture
    "sec23", # fuels
    "sec24", # chemicals
    ]

def do_cfact(country, env_key):
    base_year = config.STUDY_YEARS[0]
    env_series = config.env_series_names[env_key]

    deflators = Deflators()
    iogen = common.iogen_for_year(base_year)
    envgen = common.envgen_for_year(base_year)
    env_sectors = common.env_sectors_for_year(base_year)

    iogen.set_condition_args(country)
    envgen.set_condition_args(country)

    cfgen = CounterfactGenerator(iogen, envgen)
    if env_key in common_config.ENV_SERIES_TITLES:
        env_title = common_config.ENV_SERIES_TITLES[env_key]
    else:
        env_title = env_key
    cfgen.set_series_code(env_series, env_title)
    
    for year in config.STUDY_YEARS:
        iogen = cfgen.get_iogen()
        envgen = cfgen.get_envgen()

        iotable = "%s.indbyind_%d" % (config.WIOD_SCHEMA, year)
        iogen.set_table(iotable)
        envtable = "%s.env_%d" % (config.WIOD_SCHEMA, year)
        envgen.set_table(envtable)
        envgen.set_sectors(env_sectors)

        iogen.set_exchange_rate(imfdata.get_2005_deflator(country, year))
        #iogen.set_exchange_rate(deflators.get_gdp_deflator(year))

        cfgen.prepare(year, env_series,
                      io_harmonizer=common.get_io_harmonizer(iogen))

    sector_titles = common.get_sector_names(True)
    # hack to get countries to print instead of sector names
    for key in sector_titles:
        sector_titles[key] = config.countries[country]
    cfgen.set_sector_titles(sector_titles)

    #cfgen.describe()
    for sector in intense_sectors:
        if sector == "sec26" and country == "IDN":
            continue # this is really just for aesthetics

        values = cfgen.get_sector_values(sector)
        if country in config.eu15:
            color = "#B1E6B1"
        elif country in config.other_eu:
            color = "#9FB5F5"
        elif country in config.north_am:
            color = "#E3B668"
        elif country in config.all_asia:
            color = "#FFFF80"
        else:
            color = "#C0B3C9"

        if values["level"][-1] > 10000:
            leveldiff = values["level"][-1] - values["level"][0]
            style = 7
            if leveldiff < 0:
                style = 6

            bubblecharts[sector].set_point(
                country, values["intensity"][0],
                values["intensity"][-1], abs(leveldiff), color, style)

    #    cfgen.print_sector(sector)


    series_abbr = env_key.replace(" ", "-")
    if use_levels:
        filename = "%s_%s-abs_%d" % (series_abbr, country, base_year)
    else:
        filename = "%s_%s_%d" % (series_abbr, country, base_year)
    #title = config.countries[country]
    title = None
    (pce_result, export_result) = cfgen.counterfact(
        base_year, "cfact-" + series_abbr,
        filename, title, compact=False,
        use_levels=use_levels)

    result = cfgen.decompose_result(
        pce_result, base_year, max(config.STUDY_YEARS)) # A, J, L, Y
    for (key, value) in result:
        worldmaps["pce-" + key].set_country_value(country, value)

    result = cfgen.decompose_result(
        export_result, base_year, max(config.STUDY_YEARS)) # A, J, L, Y
    for (key, value) in result:
        worldmaps["export-" + key].set_country_value(country, value)

worldmaps = {}

if use_levels:
    group = "wiod-sda"
else:
    group = "wiod-sda-intensity"

for fdtype in ("export", "pce"):
    worldmaps[fdtype + "-A"] = WorldMapPlot(fdtype + "-actual", "", group)
    worldmaps[fdtype + "-J"] = WorldMapPlot(fdtype + "-intensity", "", group)
    worldmaps[fdtype + "-L"] = WorldMapPlot(fdtype + "-structure", "", group)
    worldmaps[fdtype + "-Y"] = WorldMapPlot(fdtype + "-fd", "", group)

bubblecharts = {}
for sector in intense_sectors:
    bubblecharts[sector] = BubblePlot(sector, "", "wiod-descriptive")

for country in config.country_rough_sort:
    if country in config.bad_data_blacklist:
        continue

    #for (key, series) in config.env_series_names.items():
    for key in ["CO2"]:
        do_cfact(country, key)

for (measurement, plot) in worldmaps.items():
    plot.write_tables()
    plot.generate_plot()

for (sector, plot) in bubblecharts.items():
    plot.add_custom_setup(
        "set xlabel '%d intensity (kilotons per $MM chained 2005 USD)'" % min(config.STUDY_YEARS))
    plot.add_custom_setup(
        "set ylabel '%d intensity (kilotons per $MM chained 2005 USD)'" % max(config.STUDY_YEARS))
    plot.add_custom_setup("set label 'y = x' at graph 0.9, 0.9 rotate by 35")

    plot.write_tables()
    plot.generate_plot()


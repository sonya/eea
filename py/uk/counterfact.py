import wiod.common
import common.more_exchange_rates as exrate
from uk import config
from common import matrixutils, sqlhelper
from common.dbconnect import db
from common.ioutils import IOMatrixGenerator, EnvMatrixGenerator
from common.counterfact import CounterfactGenerator

iogen = IOMatrixGenerator(
    transaction_table="%s.ixi_view_%d" % (config.SCHEMA, config.STUDY_YEARS[0]),
    from_sector_name="from_sector",
    to_sector_name="to_sector",
    value_column_name="value",
    final_demand_sectors=config.fd_sectors)
iogen.set_pce_col(config.pce_sector)
iogen.set_export_col(config.export_sector)

io_harmonizer = matrixutils.generate_selector_matrix(
    "%s.code_map" % config.SCHEMA,
    iogen.get_sectors(), "to_code", "harmonized",
    ["to_code is not null"])

envgen = EnvMatrixGenerator(
    envtable="%s.env_%d" % (config.SCHEMA, config.STUDY_YEARS[0]),
    ind_col_name="sector",
    series_col_name="series",
    value_col_name="value")

cfgen = CounterfactGenerator(iogen, envgen)

for env_series_code in config.env_series:
    cfgen.set_series_code(env_series_code)
    
    for year in config.STUDY_YEARS:
        iogen = cfgen.get_iogen()
        iogen.set_table("%s.ixi_view_%d" % (config.SCHEMA, year))
    
        exchange_rate = wiod.common.get_exchange_rate("GBR", year)
        if exchange_rate is None:
            exchange_rate = exrate.get_rate("uk", year)

        # k tons / (M pounds * exchange_rate) = k tons / million usd
        iogen.set_exchange_rate(exchange_rate)
    
        envgen = cfgen.get_envgen()
        envgen.set_table("%s.env_%d" % (config.SCHEMA, year))
    
        # we need to keep building this up because
        # some years are missing sectors
        env_harmonizer = matrixutils.generate_selector_matrix(
            "%s.code_map" % config.SCHEMA,
            envgen.get_sectors(), "env_code", "harmonized",
            ["env_code is not null"])
    
        series = env_series_code
    
        cfgen.prepare(year, series, io_harmonizer, env_harmonizer)
    
    sector_titles = {}
    stmt = db.prepare("select distinct harmonized, description" +
                      "  from %s.code_map order by harmonized" % config.SCHEMA)
    for row in stmt():
        sector_titles[row[0]] = row[1]
    
    cfgen.set_sector_titles(sector_titles)
    cfgen.describe()
    cfgen.describe(True)
    cfgen.counterfact(1995, "uk")




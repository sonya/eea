from wiod import config
from common import matrixutils, sqlhelper, imfdata
from common.dbconnect import db
from common.ioutils import IOMatrixGenerator, EnvMatrixGenerator
from usa import wiod_code_map

def get_national_value(country, year, measurement, env_series="CO2"):
    strings = {
        "schema": config.WIOD_SCHEMA,
        "year": year,
        "fd_sectors": sqlhelper.set_repr(config.default_fd_sectors),
        }

    if measurement == "env":
        envsql = """SELECT value FROM %(schema)s.env_%(year)d
                     WHERE country = $1 AND measurement = $2
                       AND industry = 'total'"""
        envstmt = db.prepare(envsql % strings)
        return envstmt(country, env_series)[0][0]

    if measurement == "gdp":
        gdpsql = """SELECT sum(value) FROM %(schema)s.indbyind_%(year)d
                     WHERE country = $1 AND to_ind in %(fd_sectors)s"""
        gdpstmt = db.prepare(gdpsql % strings)
        gdp = gdpstmt(country)[0][0]
        return imfdata.convert_to_2005(gdp, country, year)

    if measurement == "ppppc":
        ppppc = imfdata.get_imf_value(country, year, "ppp_pc")
        if ppppc is None:
            # above is worldbank version. imf version might not be chained
            ppppc = imfdata.get_imf_value(country, year, "PPPPC")
        return ppppc

    if measurement == "pop":
        return imfdata.get_imf_value(country, year, "pop")

    return imfdata.get_imf_value(country, year, measurement)

def get_efficiency(country, year,
                   numerator="env", denominator="gdp",
                   env_series="CO2"):

    numer_val = get_national_value(country, year, numerator, env_series)
    denom_val = get_national_value(country, year, denominator, env_series)

    return (numer_val, denom_val, numer_val / denom_val)

# CodeTracker is too messy for for read-only
def get_industry_title(code):
    stmt = db.prepare(
        "select description from %s.industry_codes where code = $1"
        % config.WIOD_SCHEMA)
    result = stmt(code)
    return result[0][0]

def iogen_for_year(year):
    iogen = IOMatrixGenerator(
        transaction_table="%s.indbyind_%d" % (config.WIOD_SCHEMA, year),
        from_sector_name="from_ind",
        to_sector_name="to_ind",
        value_column_name="value",
        final_demand_sectors=config.default_fd_sectors,
        universal_conditions=["country = $1"])
    iogen.set_pce_col("CONS_h")
    iogen.set_export_col("EXP")
    return iogen

def get_import_vector(iogen):
    fd_sectors = ["IMP"]
    iogen.set_fd_sectors(fd_sectors)
    Y = iogen.get_Y()
    iogen.set_fd_sectors(config.default_fd_sectors)
    return Y

def envgen_for_year(year, additional_sectors=[]):
    blacklist = list(config.env_sector_blacklist)
    for sector in additional_sectors:
        blacklist.remove(sector)
    env_sector_blacklist = sqlhelper.set_repr(blacklist)
    return EnvMatrixGenerator(
        envtable="%s.env_%d" % (config.WIOD_SCHEMA, year),
        ind_col_name="industry",
        series_col_name="measurement",
        value_col_name="value",
        universal_conditions=[
            "industry NOT IN " + env_sector_blacklist,
            "country = $1"
            ])

def env_sectors_for_year(year, include_hh=False):
    if include_hh:
        blacklist = config.env_sector_blacklist_hh
    else:
        blacklist = config.env_sector_blacklist
    envgen = EnvMatrixGenerator(
        envtable="%s.env_%d" % (config.WIOD_SCHEMA, year),
        ind_col_name="industry",
        series_col_name="measurement",
        value_col_name="value",
        universal_conditions=[
            "industry NOT IN " + sqlhelper.set_repr(blacklist),
            ])
    return envgen.get_sectors()

def get_io_harmonizer(iogen):
    env_blacklist = sqlhelper.set_repr(config.env_sector_blacklist)
    sel = matrixutils.generate_selector_matrix(
        "%s.sector_map" % config.WIOD_SCHEMA,
        iogen.get_sectors(), "io_code", "env_code",
        ["io_code is not null", "env_code is not null",
         "env_code not in %s" % env_blacklist])
    return sel

def get_sector_names(include_sec=False):
    sector_names = {}

    if include_sec:
        compartor = "LIKE"
    else:
        compartor = "NOT LIKE"

    stmt = db.prepare(
        "SELECT code, description " + \
        "  FROM %s.industry_codes" % config.WIOD_SCHEMA + \
        " WHERE code %s 'sec%%'" % compartor)

    for row in stmt():
        if row[0] not in config.industry_blacklist and \
                row[0] not in config.commodity_blacklist:
            sector_name = row[1]

            # replace long titles with custom titles we did for usa
            shortsector = row[0].replace("sec", "")
            if shortsector in wiod_code_map.codes:
                sector_name = wiod_code_map.codes[shortsector]["title"]

            sector_names[row[0]] = sector_name

    return sector_names

default_env_sectors = env_sectors_for_year(config.STUDY_YEARS[0])
env_sectors_with_hh = env_sectors_for_year(config.STUDY_YEARS[0], True)

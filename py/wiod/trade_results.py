from common.dbconnect import db
from common import sqlhelper, utils
from wiod import config

sector_titles = {
   "sec15t16": "Food, Beverages, Tobacco",
   "sec17t18": "Textile Products",
   "sec19":    "Leather and Footwear",
   "sec20":    "Wood and Products",
   "sec21t22": "Pulp, Paper, Printing, Publishing",
   "sec23":    "Coke, Refined Petroleum, Nuclear Fuel",
   "sec24":    "Chemical Products",
   "sec25":    "Rubber and Plastics",
   "sec26":    "Other Non-Metallic Mineral",
   "sec27t28": "Basic and Fabricated Metal",
   "sec29":    "Machinery, n.e.c.",
   "sec30t33": "Electrical and Optical Equipment",
   "sec34t35": "Transport Equipment",
   "sec36t37": "Manufacturing, Nec; Recycling",
   "sec50":    "Motor Vehicle Services",
   "sec51":    "Wholesale Trade",
   "sec52":    "Retail Trade",
   "sec60":    "Inland Transport",
   "sec61":    "Water Transport",
   "sec62":    "Air Transport",
   "sec63":    "Auxiliary Transport Services",
   "sec64":    "Post and Telecommunications",
   "sec70":    "Real Estate Activities",
   "sec71t74": "Other Business Activities",
   "secAtB":   "Agriculture, Hunting, Forestry, Fishing",
   "secC":     "Mining and Quarrying",
   "secE":     "Electricity, Gas and Water Supply",
   "secF":     "Construction",
   "secH":     "Hotels and Restaurants",
   "secJ":     "Financial Intermediation",
   "secL":     "Public Admin and Defence",
   "secM":     "Education",
   "secN":     "Health and Social Work",
   "secO":     "Other Services",
   "secP":     "Private Households",
}

# result rows must be (year, industry, value, share)
def print_result(result, minyear, maxyear):
    data = {}
    sort = {}
    for row in result:
        year = row[0]
        industry = row[1]
        value = row[2]
        percent = row[3]

        if industry not in data:
            data[industry] = {}
        data[industry][year] = (value, percent)
        if year == maxyear:
            sort[percent] = industry

    for percent in sorted(sort.keys(), reverse=True):
        industry = sort[percent]
        if industry in sector_titles:
            ind_name = sector_titles[industry]
        elif "sec" + industry in sector_titles:
            ind_name = sector_titles["sec" + industry]
        else:
            print(industry)
        data_i = data[industry][minyear]
        data_f = data[industry][maxyear]
        if data_f[1] >= 1: # suppress sectors with <1% of total
            print(ind_name.ljust(20) + " & %s & %.1f & %s & %.1f \\NN" %
                  (utils.add_commas(data_i[0]), data_i[1],
                   utils.add_commas(data_f[0]), data_f[1]))

def world_trade_stats(is_import):
    minyear = min(config.STUDY_YEARS)
    maxyear = max(config.STUDY_YEARS)

    clauses = []

    for year in (minyear, maxyear):
        strings = {
            "year": year,
            "table": "%s.niot_%d" % (config.WIOD_SCHEMA, year),
            }

        if is_import:
            strings["where"] = "is_import IS true"
        else:
            strings["where"] = "to_ind = 'EXP'"

        clauses.append(
            """SELECT %(year)d, from_ind, sum(value),
                      100 * sum(value) / (SELECT sum(value)
                                            FROM %(table)s
                                           WHERE %(where)s)
                 FROM %(table)s
                WHERE %(where)s
                GROUP BY from_ind""" % (strings))

    stmt = db.prepare("\n UNION \n".join(clauses))
    print()
    print_result(stmt(), minyear, maxyear)

def trade_sector_stats(countries, is_export):
    minyear = min(config.STUDY_YEARS)
    maxyear = max(config.STUDY_YEARS)

    strings = {
        "minyear": minyear,
        "maxyear": maxyear,
        "schema": config.WIOD_SCHEMA,
        "is_export": is_export,
        "countries": sqlhelper.set_repr(countries),
        "blacklist": sqlhelper.set_repr(config.bad_data_blacklist),
        }

    if is_export:
        strings["view"] = "export_view"
        strings["is_export_str"] = "true"
    else:
        strings["view"] = "import_view"
        strings["is_export_str"] = "false"

    db.execute("""CREATE OR REPLACE VIEW %(view)s AS
    SELECT year, industry, sum(value) as value
      FROM trade_results
     WHERE is_export is %(is_export_str)s
       AND country IN %(countries)s
       AND country NOT IN %(blacklist)s
     GROUP BY year, industry""" % strings)

    stmt = db.prepare("""
    SELECT a.year, a.industry, a.value, a.value / b.value * 100
      FROM %(view)s a,
           (SELECT year, sum(value) as value
              FROM %(view)s
             GROUP BY year) b
     WHERE a.year in (%(minyear)d, %(maxyear)d)
       AND a.year = b.year""" % strings)

    print()
    print(countries)
    print()
    print_result(stmt(), minyear, maxyear)

    #db.execute("DROP VIEW %(view)s" % strings)

#world_trade_stats(True)
#world_trade_stats(False)

#trade_sector_stats(config.annex_b_countries[-8], True)
#trade_sector_stats(config.annex_b_countries[-8], False)

# this is just usa
#trade_sector_stats(config.annex_b_countries[-7], True)
#trade_sector_stats(config.annex_b_countries[-7], False)

# canada, hungary, japan, poland
#trade_sector_stats(config.annex_b_countries[-6], True)
#trade_sector_stats(config.annex_b_countries[-6], False)

# this is just russia
#trade_sector_stats(config.annex_b_countries[0], True)
#trade_sector_stats(config.annex_b_countries[0], False)

# this is just australia
#trade_sector_stats(config.annex_b_countries[8], True)
#trade_sector_stats(config.annex_b_countries[8], False)

#trade_sector_stats(config.eu15, True)
#trade_sector_stats(config.eu15, False)

trade_sector_stats(config.other_eu, True)
trade_sector_stats(config.other_eu, False)

#trade_sector_stats(config.north_am, True)
#trade_sector_stats(config.north_am, False)

#trade_sector_stats(config.bric, True)
#trade_sector_stats(config.bric, False)

#trade_sector_stats(["CHN"], True)
#trade_sector_stats(["CHN"], False)

#trade_sector_stats(config.other_asia, True)
#trade_sector_stats(config.other_asia, False)

#trade_sector_stats(config.non_annex_b, True)
#trade_sector_stats(config.non_annex_b, False)


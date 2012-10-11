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

import wiod.common
import common.more_exchange_rates as exrate
from jp import config
from common import matrixutils, sqlhelper
from common.dbconnect import db
from common.ioutils import IOMatrixGenerator, EnvMatrixGenerator
from common.counterfact import CounterfactGenerator

iogen = IOMatrixGenerator(
    transaction_table=None,
    from_sector_name="from_sector",
    to_sector_name="to_sector",
    value_column_name="value")

envgen = EnvMatrixGenerator(
    envtable=None,
    ind_col_name="sector",
    series_col_name="series",
    value_col_name="value")

sector_titles = {}
stmt = db.prepare("select distinct harmonized, description" +
                  "  from jp.io_map_1990 order by harmonized")
for row in stmt():
    sector_titles[row[0]] = row[1]

cfgen = CounterfactGenerator(iogen, envgen)

for series_code in config.env_series.keys():
    cfgen.set_series_code(series_code)
    
    for year in config.STUDY_YEARS:
        iogen = cfgen.get_iogen()
        iogen.set_table("%s.ixi_%d" % (config.SCHEMA, year))
        iogen.set_fd_sectors(config.fd_sectors[year])
        iogen.blacklist_from_sectors(config.from_blacklists[year])
        iogen.blacklist_to_sectors(config.to_blacklists[year])
        iogen.set_pce_col(config.pce_sector[year])
        iogen.set_export_col(config.export_sector[year])
    
        exchange_rate = wiod.common.get_exchange_rate("JPN", year)
        if exchange_rate is None:
            exchange_rate = 1 / exrate.get_rate("jp", year)

        # tons co2 / (M jpy * exchange rate) = tons co2 / M usd
        # GJ / (M jpy * exchange rate) = GJ / M usd
        # exchange_rate * 1000 gives us kilotons and terrajoules
        iogen.set_exchange_rate(exchange_rate * 1000)
    
        envgen = cfgen.get_envgen()
        envgen.set_table("%s.env_%d" % (config.SCHEMA, year))
    
        env_harmonizer = matrixutils.generate_selector_matrix(
            "%s.env_map_%d" % (config.SCHEMA, year),
            envgen.get_sectors(), "env_sector", "harmonized")
        io_harmonizer = matrixutils.generate_selector_matrix(
            "%s.io_map_%d" % (config.SCHEMA, year),
            iogen.get_sectors(), "io_sector", "harmonized")
    
        series = config.env_series[series_code][year]
    
        cfgen.prepare(year, series, io_harmonizer, env_harmonizer)
    
    cfgen.set_sector_titles(sector_titles)
    cfgen.describe()
    cfgen.describe(True)
    cfgen.counterfact(1995, "jp")




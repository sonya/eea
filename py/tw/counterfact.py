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
from tw import config
from common import matrixutils, sqlhelper
from common.ioutils import IOMatrixGenerator, EnvMatrixGenerator
from common.counterfact import CounterfactGenerator

iogen = IOMatrixGenerator(
    transaction_table=None,
    from_sector_name="from_sector",
    to_sector_name="to_sector",
    value_column_name="millions")

envgen = EnvMatrixGenerator(
    envtable=None,
    ind_col_name="sector",
    series_col_name="series",
    value_col_name="value")

cfgen = CounterfactGenerator(iogen, envgen)

for series_code in config.env_series.keys():
    cfgen.set_series_code(series_code)

    for year in config.STUDY_YEARS:
        iotable = "%s.io_%d" % (config.SCHEMA, year)
        if year > 2006:
            # use fake IxI table
            iotable = "%s.io_view_%d" % (config.SCHEMA, year)
        iogen = cfgen.get_iogen()
        iogen.set_table(iotable)
        iogen.set_fd_sectors(config.final_demand[year])
        iogen.blacklist_from_sectors(config.from_blacklists[year])
        iogen.blacklist_to_sectors(config.to_blacklists[year])
        iogen.set_harmonized_rows(config.io_harmonized_sectors[year])

        exchange_rate = wiod.common.get_exchange_rate("TWN", year)
        # tons / (million ntd * exchange_rate) = tons / M usd
        iogen.set_exchange_rate(exchange_rate)
        iogen.set_pce_col(config.pce_sector[year])
        iogen.set_export_col(config.export_sector[year])
    
        envtable = "%s.env_%d" % (config.SCHEMA, year)
        envgen = cfgen.get_envgen()
        envgen.set_table(envtable)
        env_blacklist = sqlhelper.set_repr(config.env_blacklist[year])
        env_condition = "sector NOT IN " + env_blacklist
        envgen.set_universal_conditions([env_condition])
    
        map_table = "%s.sector_map_%d" % (config.SCHEMA, year)
        env_harmonizer = matrixutils.generate_selector_matrix(
            map_table, envgen.get_sectors(), "env_sector", "harmonized_env")
        io_harmonizer = matrixutils.generate_selector_matrix(
            map_table, iogen.get_sectors(), "io_sector", "harmonized_env")
    
        series = config.env_series_for_code(series_code, year)
        cfgen.prepare(year, series, io_harmonizer, env_harmonizer)
    
    cfgen.describe()
    cfgen.describe(True)
    cfgen.counterfact(1999, "tw")




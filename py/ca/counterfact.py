#!/usr/bin/python3
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

import common.more_exchange_rates as exrate
import wiod.common
from ca import config
from common import matrixutils, sqlhelper
from common.dbconnect import db
from common.matrixutils import NamedMatrix
from common.ioutils import IOMatrixGenerator, EnvMatrixGenerator
from common.counterfact import CounterfactGenerator

iogen = IOMatrixGenerator(
    transaction_table="%s.ixi_%d" % (config.SCHEMA, config.STUDY_YEARS[0]),
    final_demand_sectors=config.fd_sectors)
iogen.set_pce_col(config.pce_sector)
iogen.set_export_col(config.export_sector)

envgen = EnvMatrixGenerator(
    envtable="%s.emissions_quantity" % config.SCHEMA,
    ind_col_name="industry",
    series_col_name="1") # we just have emissions, no series, need hack

cfgen = CounterfactGenerator(iogen, envgen)

cfgen.set_series_code(["1"], "emissions")
    
for year in config.STUDY_YEARS:
    print(year)
    iogen = cfgen.get_iogen()
    iogen.set_table("%s.ixi_%d" % (config.SCHEMA, year))

    exchange_rate = wiod.common.get_exchange_rate("CAN", year)
    if exchange_rate is None:
        exchange_rate = exrate.get_rate("ca", year)

    iogen.set_exchange_rate(exchange_rate)
    
    envgen = cfgen.get_envgen()
    envgen.set_universal_conditions([
            "year = %d" % year,
            "industry not in %s" % sqlhelper.set_repr(config.env_blacklist),
            ])

    io_harmonizer = matrixutils.generate_selector_matrix(
        "%s.sector_map" % config.SCHEMA,
        iogen.get_sectors(), "io_code", "harmonized",
        ["io_code is not null"])

    env_harmonizer = matrixutils.generate_selector_matrix(
        "%s.sector_map" % config.SCHEMA,
        envgen.get_sectors(), "env_code", "harmonized",
        ["env_code is not null"])

    series = ["1"]
    
    cfgen.prepare(year, series, io_harmonizer, env_harmonizer)
    
sector_titles = {}
stmt = db.prepare("select distinct code, description" +
                  "  from %s.ind_codes order by code" % config.SCHEMA)
for row in stmt():
    sector_titles[row[0]] = row[1]
    
cfgen.set_sector_titles(sector_titles)
cfgen.describe()
cfgen.describe(True)
cfgen.counterfact(1997, "ca")


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

SCHEMA = "ca"
STUDY_YEARS = range(1997, 2009)

ind_blacklist = ('Total industries',)
com_blacklist = (
    'Total commodities',
    'Total, final demand',
    )

margins = (
    'Pipeline transportation',
    'Retailing margins',
    )

value_added = (
    "460", "461", "462", "463", "464",
    "465", "466", "467", "468", "469",
    )

fd_sectors = (
    "F01", "F02", "F03", "F04", "F05", "F07", "F10")

pce_sector = "F01"
export_sector = "F04"
import_sector = "F05"

env_blacklist = ("Z01", "Z02", "Z03")


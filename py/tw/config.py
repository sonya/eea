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

# years with io data:
# 70 (1981)
# 73 (1984)
# 75 (1986) 
# 78 (1989)
# 80 (1991) @ 39, 150, 569 sectors
# 83 (1994) @ 39, 150 sectors
# 85 (1996) @ 45, 160, 596 sectors
# 88 (1999) @ 45, 160 sectors
# 90 (2001) @ 49, 162, 610 sectors
# 93 (2004) @ 49, 161 sectors
# 96 (2006) @ 52, 166, 554 sectors
#
# CxI only: 95 (2006), 96 (2007), 97 (2008), 98 (2009), 99 (2010)
#
# chinese env data: 89 (2000), 90 (2001), 91 (2002), 99 (2010)
# english env data: 1999, 2001, 2004

SCHEMA = "tw"
STUDY_YEARS = [1999, 2001, 2004, 2010] # years with both io and env

# sectors
final_demand = {
    1999: (
        "家計消費",     # households (pce)
        "政府消費",     # government
        "固定資本形成", # fixed capital formation
        "存貨變動",     # inventory change
        "海關輸出",     # exports (via customs)
        "非海關輸出",   # exports (not via custom)
        ),
    2001: (
	"家計消費", "政府消費", "固定資本形成",
        "存貨變動", "海關輸出", "非海關輸出",
        ),
    2004: (
        "家計消費", "政府消費", "固定資本形成",
        "存貨變動", "海關輸出", "非海關輸出",
        ),
    2010: (
       "民間消費", "政府消費", "固定資本形成",
       "存貨變動", "商品及服務輸出",
        ),
    }

pce_sector = {
    1999: "家計消費",
    2001: "家計消費",
    2004: "家計消費",
    2010: "民間消費",
    }

# use exports via customs. non-customs exports includes e.g. spending
# by tourists. http://www.stat.gov.tw/ct.asp?xItem=10882&ctNode=2404
export_sector = {
    1999: "海關輸出",
    2001: "海關輸出",
    2004: "海關輸出",
    2010: "商品及服務輸出",
    }

from_blacklists = {
    1999: (
        "中間投入", "原始投入", "投入合計", # subtotals
        # value added
        "勞動報酬", # labor
        "營業盈餘", "利息", "租金", "移轉支出", "基金", "利潤", # profit
        "資本消耗", # capex
        "間接稅", "貨物稅淨額", "進口稅淨額", "加值型營業稅", "其他稅捐", # tax
        "調整項目", # adjustment
        ),
    2001: (
        "中間投入", "原始投入", "投入合計",
        "勞動報酬",
        "營業盈餘", "利息", "租金", "移轉支出", "基金", "利潤",
        "資本消耗",
        "間接稅", "貨物稅淨額", "進口稅淨額", "加值型營業稅", "其他稅捐",
        "調整項目",
        ),
    2004: (
        "中間投入", "原始投入", "投入合計",
        "勞動報酬",
        "營業盈餘", "利息", "租金", "移轉支出", "基金", "利潤",
        "資本消耗",
        "間接稅", "貨物稅淨額", "進口稅淨額", "加值型營業稅", "其他稅捐",
        "調整項目",
        ),
    2010: (
        "中間投入", "原始投入", "投入合計",
        "受僱人員報酬", "營業盈餘", "固定資本消耗", "間接稅淨額", # value added
        ),
    }

to_blacklists = {
    1999: (
        "中間需要合計", "最終需要合計", "國內生產總值", # subtotals
        "", # total output; col header has image saying "總需要 = 媲供給"
        "海關輸入", "非海關輸入", # imports, recorded as positive numbers
        ),
    2001: (
        "中間需要合計", "最終需要合計", "國內生產總值",
        "", "海關輸入", "非海關輸入",
        ),
    2004: (
       "中間需要合計", "最終需要合計", "國內生產總值",
       "", "海關輸入", "非海關輸入",
        ),
    2010: (
       "中間需要合計", "最終需要合計", "總需要‖總供給", "國內生產總額", # subtotals
       "商品及服務輸入", # imports
       "進口稅淨額",    # tariffs
       "商業差距",      # business differences
       "國內運費",      # domestic shipping
       "加值型營業稅",  # value-added taxes
       "生產面誤差項",  # something differences
        ),
    }

# sometimes equivalent sectors are entered with slightly different
# names between input/output sectors. use input (commodity) as standard
io_harmonized_sectors = {
    1999: {
        "皮製品": "皮革及皮製品",
        "家用電機電子產品": "家用電子電器產品",
        "燃氣": "燃 氣",
        # the following sectors only differ across years
        "運輸倉儲": "運輸倉儲通信",
        },
    2001: {
        "燃氣": "燃 氣",
        # the following sectors only differ across years
        "電子零配件": "電子零組件",
        },
    2004: {
        "燃氣": "燃 氣",
        # the following sectors only differ across years
        "電子零配件": "電子零組件",
        },
    2010: {
        # these are just here so we can use common industry names
        # to years with the old sector division
        "燃氣": "氣體燃料供應業",
        "電力": "電力供應業",
        "電子零配件": "電子零組件製造業", 
        "運輸倉儲": "運輸倉儲業",
        "礦產": "礦業及土石採取業",
        "非金屬礦物製品": "非金屬礦物製品製造業",
        "房屋工程": "營造業",
        },
    }

env_series = {
    "CO": {
        2010: "一氧化碳（CO）",
        },
    "NOx": {
        2010: "氮氧化物（NOx）",
        },
    "TSP": {
        2010: "總懸浮微粒（TSP）",
        },
    "SOx": {
        2010: "硫氧化物（SOx）",
        },
    "BOD": {
        2010: "生化需氧量（BOD）",
        },
    "waste": {
        1999: "Total waste",
        2001: "Total waste",
        2004: "Total waste",
        2010: "廢棄物產生量",
        },
    "waste-hi": {
        1999: "Hazardous waste - improper disposal",
        2001: "Hazardous waste - improper disposal",
        2004: "Hazardous waste - improper disposal",
        2010: "未妥善處理量：有害",
        },
    }

env_blacklist = {
    1999: ("Household Consumption", "Fixed Capital Formation"),
    2001: ("Household Consumption", "Fixed Capital Formation"),
    2004: ("Household Consumption", "Fixed Capital Formation"),
    2010: ("政府", "家庭"),
    }

interesting_industries = {
    # local
    "燃氣": "Gas distribution",
    "電力": "Electricity distribution",
    "運輸倉儲": "Transportation and warehousing",
    "房屋工程": "Construction",
    # exports
    "電子零配件": "Electronic components/parts",
    "礦產": "Minerals",
    "非金屬礦物製品": "Nonmetallic mineral products",
    }

harmonized_env_sectors = [
    "15", "16", "17", "18", "19", "20", "21t22", "23", "24", "25",
    "26", "27", "28", "29", "30t33", "34t35", "36t37", "40", "41",
    "51t52", "AtB", "C", "F", "H", "I", "JKO", "L", "MtN",
    ]

def env_series_for_code(code, year):
    env_aliases = env_series[code]
    if year in env_aliases:
        series = env_aliases[year]
    else:
        series = code
    return series


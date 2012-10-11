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

from common.dbhelper import SQLTable

def get_code_for_title(title, tablename):
    return get_instance().get_code_for_title(title, tablename)

def get_title_for_code(code, tablename):
    return get_instance().get_title_for_code(code, tablename)

def add_tracker(tablename, mode):
    return get_instance().add_tracker(tablename, mode)

# this is a weird way to implement singletons...
# http://www.python.org/workshops/1997-10/proceedings/savikko.html
def get_instance():
    try:
        single = StaticCodes()
    except StaticCodes as s:
        single = s
    return single

class StaticCodes(Exception):

    __static = None

    def __init__(self):
        if StaticCodes.__static:
            raise StaticCodes.__static

        self.code_trackers = {}
        StaticCodes.__static = self

    def get_instance():
        return StaticCodes.__static

    def add_tracker(self, tablename, mode):
        self.code_trackers[tablename] = SectorCodes(tablename, mode).setup()
        return self.code_trackers[tablename]

    def get_title_for_code(self, code, tablename):
        if tablename not in self.code_trackers:
            self.add_tracker(tablename, "r")

        return self.code_trackers[tablename].get_title_for_code(code)

    def get_code_for_title(self, title, tablename):
        if tablename not in self.code_trackers:
            self.add_tracker(tablename, "r")

        return self.code_trackers[tablename].get_code_for_title(title)

class SectorCodes:

    def __init__(self, codetablename, mode="r"):
        self.mode = mode

        self.codetable = SQLTable(
            codetablename,
            ["code", "description"],
            ["varchar(15)", "varchar(255)"])

        self.code_dict = {}
        self.reverse_code_dict = {}

        self.setup()

    def setup(self):
        if self.mode == "w":
            # invalid codes or codes that we don't want to record
            self.code_blacklist = []

            # if we want to override the code provided with something
            # we make up (or from another set) based on the description
            self.manual_codes = {}

            self.codetable.create()

        # get existing codes from db
        for (code, desc) in self.codetable.getall():
            self.code_dict[code] = desc
            self.reverse_code_dict[desc] = code

        return self

    # for write mode
    def blacklist_code(self, code):
        self.code_blacklist.append(code)

        if code in self.code_dict:
            del self.code_dict[code]

    def set_blacklist(self, code_blacklist):
        self.code_blacklist = []
        for code in code_blacklist:
            self.blacklist_code(code)

    def curate_code_from_desc(self, desc, code):
        self.manual_codes[desc] = code

        self.code_dict[code] = desc
        self.reverse_code_dict[desc] = code

    def add_curated_codes(self, curated_codes):
        for (desc, code) in curated_codes.items():
            self.curate_code_from_desc(desc, code)

    # returns the code used if it was recognized, false otherwise
    def set_code(self, code, desc):
        if type(code) is str:
            code = code.strip()
        elif type(code) is float:
            code = str(int(code))

        if type(desc) is str:
            desc = desc.strip()

        if desc in self.manual_codes:
            code = self.manual_codes[desc]

        if code is None or not len(code):
            if desc is None or not len(desc): # ignore empty args
                return False
            else:
                return False
        elif code in self.code_blacklist:
            return False

        if code in self.code_dict and self.code_dict[code] != desc:
            # this is to check for blatant differences
            print(self.code_dict[code], "=>", desc)
        self.code_dict[code] = desc

        # there may be more than one description for the same code
        self.reverse_code_dict[desc] = code

        return code

    def has_code(self, code):
        return code in self.code_dict

    def get_code_for_title(self, desc):
        if desc in self.reverse_code_dict:
            return self.reverse_code_dict[desc]

    def get_title_for_code(self, code):
        if self.has_code(code):
            return self.code_dict[code]
        return False

    def update_codes(self):
        if self.mode != "w":
            raise Exception("SectorCodes created in read-only mode")

        self.codetable.truncate()
        for code in sorted(self.code_dict.keys()):
            desc = self.code_dict[code]
            self.codetable.insert([code, desc])

class HybridTableCreator:

    def __init__(self, schema):
        self.schema = schema
        self.io_prefix = "ixi"
        self.env_prefix = "env"
        self.io_tables = {}
        self.env_tables = {}

    def new_sector_codes(self, year=None, prefix=None):
        if prefix is None:
            prefix = self.io_prefix

        if year is None:
            tablename = "%s.%s_codes" % (self.schema, prefix)
        else:
            tablename = "%s.%s_codes_%d" % (self.schema, prefix, year)

        return add_tracker(tablename, "w")

    def valid_year(self, year):
        if type(year) is str and not regexes.is_int(year):
            raise Exception("invalid year " + str(year))
        year = int(year)
        if year < 1800 or year > 2050:
            raise Exception("invalid year " + str(year))
        return year

    def add_env_table(self, year, sector_max_length=15,
                      series_max_length=15):

        year = self.valid_year(year)
        if year not in self.env_tables:
            tablename = "%s.%s_%d" % (self.schema, self.env_prefix, year)
            colnames = ["sector", "series", "value"]
            coltypes = [
                "varchar(%d)" % sector_max_length,
                "varchar(%d)" % series_max_length,
                "float"
                ]
            self.env_tables[year] = SQLTable(
                tablename, colnames, coltypes).create()
            self.env_tables[year].truncate()

    def insert_env(self, year, sector, series, value):
        if sector and series and value != 0:
            self.env_tables[year].insert([sector, series, value])

    def add_io_table(self, year, sector_max_length=15):
        year = self.valid_year(year)
        if year not in self.io_tables:
            tablename = "%s.%s_%d" % (self.schema, self.io_prefix, year)
            colnames = ["from_sector", "to_sector", "value"]
            coltypes = [
                "varchar(%d)" % sector_max_length,
                "varchar(%d)" % sector_max_length,
                "float"]
            self.io_tables[year] = SQLTable(
                tablename, colnames, coltypes).create()
            self.io_tables[year].truncate()

    def insert_io(self, year, from_sector, to_sector, value):
        if from_sector and to_sector and value != 0:
            self.io_tables[year].insert([from_sector, to_sector, value])

from common.dbhelper import SQLTable
from wiod import config
from common.dbconnect import db

class CodeTracker:
    def __init__(self, name):
        self.name = name
        self.table = SQLTable(
            "%s.%s" % (config.WIOD_SCHEMA, name),
            ["code", "description"],
            ["varchar(15)", "varchar(255)"])
        self.code_dict = None

    def setup(self):
        self.table.create()
        self.get_codes()

    # get existing codes from db
    def get_codes(self):
        if self.code_dict is None:
            self.code_dict = {}
        for (code, desc) in self.table.getall():
            self.code_dict[code] = desc

    def get_desc_for_code(self, code):
        if code in self.code_dict:
            return self.code_dict[code]
        return None

    # returns the code used if it was recognized, false otherwise
    def set_code(self, code, desc):
        if type(code) is str:
            code = code.strip()
        elif type(code) is float:
            code = str(int(code))

        if type(desc) is str:
            desc = desc.strip()

        if code is None or not len(code):
            if desc is None or not len(desc): # ignore empty args
                return False
            elif desc in config.fd_sectors: # choose manual codes
                code = config.fd_sectors[desc]
            elif desc in config.va_sectors: # choose manual codes
                code = config.va_sectors[desc]
            else:
                return False
        elif code in config.code_blacklist: # ignore invalid values for codes
            return False

        if code in self.code_dict and self.code_dict[code] != desc:
            print(self.code_dict[code], desc)
        self.code_dict[code] = desc

        return code

    def update_codes(self):
        self.table.truncate()
        for code in sorted(self.code_dict.keys()):
            desc = self.code_dict[code]
            self.table.insert([code, desc])

#!/usr/bin/python3

import csv, os, re, xlrd
import common.config
from common.dbconnect import db
from usa import bea, config, eia
from common import fileutils
from usa.dbsetup import TableStateTracker

def doparse():
    parse_nipa_data()
    create_views()

def parse_nipa_data():
    test_view = "%s.nipa_groups" % common.config.TEST_SCHEMA
    db.execute("DROP VIEW IF EXISTS %s" % test_view)

    # get table for pce category harmonization
    trailing_pat = re.compile('(.+) \(.*\d.*\)$')
    
    nipa_code_map = {}
    filename = fileutils.getdatapath("nipa_code_map.csv", "usa")
    fh = open(filename)
    csvf = csv.reader(fh)
    for row in csvf:
        if len(row) == 2:
            harmonized = row[0]
            trailing = trailing_pat.match(harmonized)
            if trailing:
                harmonized = trailing.group(1)
            nipa_code_map[row[1]] = harmonized
    fh.close()
    
    # get nipa series codes from underlying detail tables
    tracker = TableStateTracker()
    tracker.create_table("%s.pce_codes" % config.NIPA_SCHEMA,
                         ["code", "parent", "description"],
                         ["char(7)", "char(7)", "text"],
                         True)

    number_pat = re.compile('^\d+$')
    trailing_pat = re.compile('(.+) \(.*\d.*\)$')
    
    filename = fileutils.getcache("Section2All_underlying.csv", "bea", "nipa")
    fh = open(filename)
    csvf = csv.reader(fh)
    is_in_table = False
    
    code_stack = [None]
    indent_stack = [-1]
    
    # the code mapping has been done such that each item is at least at
    # three levels of disaggregation below the top, i.e. there is always
    # an ancestor at the second level. we only want to keep track of the
    # ancestor at the third level (root is zero)
    # the first level below root has goods and services
    # the second level has durable goods, nondurable goods, and services.
    reverse_code_dict = {}
    second_level_nodes = []
    
    for row in csvf:
        if len(row):
            if not is_in_table:
                if row[0].startswith("Table 2.4.5U"):
                    is_in_table = True
            else:
                if row[0].startswith("Table 2.4.5U"):
                    # we only need to go through one instance of this table
                    break
                else:
                    if number_pat.match(row[0]) and len(row) > 2:
                        title = row[1].lstrip()
    
                        # these are duplicate codes
                        if title.startswith("Market-based PCE"):
                            continue
    
                        code = row[2]
                        current_indent = len(row[1]) - len(title)
    
                        while current_indent <= indent_stack[-1]:
                            indent_stack.pop()
                            code_stack.pop()
    
                        indent_stack.append(current_indent)
                        code_stack.append(code)
    
                        if len(code_stack) > 1:
                            parent = code_stack[-2]
                        else:
                            parent = None
    
                        title = title.strip()
                        trailing = trailing_pat.match(title)
                        if trailing:
                            title = trailing.group(1)
                        
                        if len(code_stack) > 4:
                            reverse_code_dict[title] = code_stack[3]
                        else:
                            reverse_code_dict[title] = code
    
                        tracker.insert_row((code, parent, title))
    
    tracker.flush()
    fh.close()
    
    # table for price deflators
    
    tracker.create_table("%s.implicit_price_deflators" % config.NIPA_SCHEMA,
                         ["year", "gdp", "pce"],
                         ["int", "float", "float"])
    
    filename = fileutils.getcache("Section1all_csv.csv", "bea/nipa")
    fh = open(filename)
    csvf = csv.reader(fh)
    is_in_table = False
    
    data = {} # we need to parse two rows before we can populate
    years = {}
    
    for row in csvf:
        if len(row):
            if not is_in_table:
                if row[0].startswith("Table 1.1.9"):
                    is_in_table = True
            else:
                if row[0].startswith("Table 1.1.9"):
                    # this is seasonally adjusted version of the same table
                    break
                else:
                    if row[0] == "Line":
                        for i in range(len(row)):
                            if number_pat.match(row[i]):
                                year = int(row[i])
                                years[year] = i
                                data[year] = {}
    
                    elif number_pat.match(row[0]) and len(row) > 2:
                        title = row[1].lstrip()
                        if title == "Gross domestic product":
                            column = "gdp"
                        elif title == "Personal consumption expenditures":
                            column = "pce"
                        else:
                            continue
    
                        for (year, colindex) in years.items():
                            data[year][column] = float(row[colindex])
    
    for (year, results) in data.items():
        tracker.insert_row([year, results["gdp"], results["pce"]])
    
    tracker.flush()
    fh.close()
    
    # parse pce bridge
    
    class IONIPAStateTracker(TableStateTracker):
    
        def flush(self):
            TableStateTracker.flush(self)
            if self.fh is not None and not self.fh.closed:
                self.fh.close()
    
        def __init__(self):
            TableStateTracker.__init__(self)
            self.fh = None
            self.code_dict = None
    
            self.value_columns = [
                "prod_val",
                "rail_margin",
                "truck_margin",
                "water_margin",
                "air_margin",
                "pipe_margin",
                "gaspipe_margin",
                "wholesale_margin",
                "retail_margin",
                "purchase_val"
                ]
    
            self.old_style_field_map = {
                "Producers' Value": "prod_val",
                "MfgExciseTax": "prod_val",
                "RailMargin": "rail_margin",
                "TruckMargin": "truck_margin",
                "WaterMargin": "water_margin",
                "AirMargin": "air_margin",
                "PipeMargin": "pipe_margin",
                "WholesaleMargin": "wholesale_margin",
                "WholesaleTax": "wholesale_margin",
                "RetailMargin": "retail_margin",
                "RetailSalesTax": "retail_margin",
                "OtherRetailTax": "retail_margin",
                "Purchasers' Value": "purchase_val",
                }
    
        def set_filename(self, filename):
            path = fileutils.getcache(filename, str(self.year))
            self.filename = path
    
        def set_year(self, year):
            self.flush()
            self.year = year
            tablename = "%s.pcebridge_%d" % (config.IO_SCHEMA, year)
            fields = ["pce_code", "commodity"] + self.value_columns
            types = ["varchar(6)", "varchar(6)"] + \
                ["bigint"]*len(self.value_columns)
            self.create_table(tablename, fields, types)
    
        def setup_for_codes(self):
            self.code_dict = {}
    
        def flush_codes(self):
            if self.code_dict is not None:
                tablename = "%s.nipa_codes_%d" % (config.IO_SCHEMA, self.year)
                self.create_table(tablename,
                                  ["pce_code", "nipa_group", "description"],
                                  ["varchar(6)", "char(7)", "text"])
                for (code, raw_desc) in self.code_dict.items():
    
                    desc = raw_desc
                    if desc.endswith('(s.)') or desc.endswith('(d.)'):
                        desc = desc[:-4].strip()
                    elif desc.endswith('(n.d.)'):
                        desc = desc[:-6].strip()
    
                    if desc in nipa_code_map:
                        desc = nipa_code_map[desc]
    
                    if desc in reverse_code_dict:
                        nipa_code = reverse_code_dict[desc]
                    else:
                        nipa_code = None
                    #self.current_stmt(code, nipa_code, raw_desc)
                    self.table.insert([code, nipa_code, raw_desc])
    
                self.code_dict = None
                self.flush()
    
        def insert_code_row(self, code, desc):
            # workaround for the way excel interprets numbers as floats
            # when we know the codes should be strings
            if type(code) is float:
                code = int(code)
    
            self.code_dict[str(code)] = desc.strip()
    
        def insert_row(self, pce_code, commod, dollar_values, factor=1):
            # workaround for the way excel interprets numbers as floats
            # when we know the codes should be strings
            if type(pce_code) is float:
                pce_code = int(pce_code)
    
            values = [str(pce_code).strip(), commod.strip()]
            for column in self.value_columns:
                if column in dollar_values:
                    if factor == 1:
                        values.append(dollar_values[column])
                    else:
                        values.append(int(float(dollar_values[column]) * factor))
                else:
                    values.append(None)
            #self.current_stmt(*values)
            self.table.insert(values)
    
        def parse_old_style_xls(self, year):
            self.set_year(year)
            self.set_filename("%d_PCE_Commodity.xls" % self.year)
            wb = xlrd.open_workbook(self.filename)
    
            # parse pce bridge data
            sheet = wb.sheet_by_name("%d PCE Workfile - Commodity" % self.year)
            field_indexes = {}
            pce_code_idx = 0
            commod_idx = 2
            for rowindex in range(sheet.nrows):
                row = sheet.row_values(rowindex)
                if len(row) > 1:
                    if "PCE Category" in row:
                        pce_code_idx = row.index("PCE Category")
                        if "Commodity" in row:
                            commod_idx = row.index("Commodity")
                        for i in range(len(row)):
                            xls_col = row[i]
                            if xls_col in self.old_style_field_map:
                                colname = self.old_style_field_map[xls_col]
                                if colname not in field_indexes:
                                    field_indexes[colname] = []
                                field_indexes[colname].append(i)
                    elif len(field_indexes):
                        pce_code = row[pce_code_idx]
                        commod = str(int(row[commod_idx])).rjust(6, "0")
                        values = {}
                        for (field, columns) in field_indexes.items():
                            # doclumentation says units are in 100,000 dollars
                            # but the orders of magnitude don't match up with
                            # later years if we use 100
                            components = [int(float(row[column] * 1000))
                                          for column in columns]
                            value = 0
                            for component in components:
                                value += component
                            values[field] = value
                        self.insert_row(pce_code, commod, values)
    
            # parse codes from neighboring worksheet
            self.setup_for_codes()
            sheet = wb.sheet_by_name("%d PCE Category Descriptions" % self.year)
            code_idx = None
            desc_idx = None
            for rowindex in range(sheet.nrows):
                row = sheet.row_values(rowindex)
                if len(row) > 1:
                    codetab = "PCE Category Code"
                    codetab2 = "%s - %d" % (codetab, self.year)
                    if codetab in row or codetab2 in row:
                        if codetab in row:
                            code_idx = row.index(codetab)
                        else:
                            code_idx = row.index(codetab2)
                        desctab = "PCE Category Description - %d" % self.year
                        if desctab in row:
                            desc_idx = row.index(desctab)
                        else:
                            desctab = "PCE Category Description"
                            if desctab in row:
                                desc_idx = row.index(desctab)
                    elif code_idx is not None and desc_idx is not None:
                        code = row[code_idx]
                        desc = str(row[desc_idx])
                        self.insert_code_row(code, desc)
            self.flush_codes()
    
        def get_file_handle(self, filetype, options={}):
            if filetype == "txt":
                self.fh = open(self.filename)
                return self.fh
            elif filetype == "csv":
                self.fh = open(self.filename)
                if "delim" in options:
                    csvf = csv.reader(self.fh, delimiter=options["delim"])
                else:
                    csvf = csv.reader(self.fh)
                return csvf
            elif filetype == "xls":
                wb = xlrd.open_workbook(self.filename)
                return wb
    
        def parse_text(self, rowcallback):
            path = fileutils.getcache(filename, str(self.year))
            f = open(path)
            for line in f:
                rowcallback(line, this)
            f.close()
    
    tracker = IONIPAStateTracker()
    tracker.parse_old_style_xls(1967)
    tracker.parse_old_style_xls(1972)
    tracker.parse_old_style_xls(1977)
    tracker.parse_old_style_xls(1982)
    
    tracker.set_year(1987)
    tracker.set_filename("tbld-87.dat")
    fh = tracker.get_file_handle("txt")
    for line in fh:
        if len(line) < 103:
            continue
        commod = line[0:6]
        pce_code = line[14:18]
        values = {
            "prod_val": line[21:30],
            "rail_margin": line[30:39],
            "truck_margin": line[39:48],
            "water_margin": line[48:57],
            "air_margin": line[57:66],
            "pipe_margin": line[66:75],
            "wholesale_margin": line[75:84],
            "retail_margin": line[84:93],
            "purchase_val": line[93:102],
            }
        tracker.insert_row(pce_code, commod, values, 1000)
    
    tracker.setup_for_codes()
    tracker.set_filename("io-nipa.doc")
    fh = tracker.get_file_handle("txt")
    for line in fh:
        if len(line) < 27:
            continue
        code = line[0:4].strip()
        desc = line[26:].strip()
        tracker.insert_code_row(code, desc)
    tracker.flush_codes()
    
    tracker.set_year(1992)
    tracker.set_filename("TabD.txt")
    fh = tracker.get_file_handle("csv", {"delim": "\t"})
    for row in fh:
        values = {
            "prod_val": row[4],
            "rail_margin": row[5],
            "truck_margin": row[6],
            "water_margin": row[7],
            "air_margin": row[8],
            "pipe_margin": row[9],
            "gaspipe_margin": row[10],
            "wholesale_margin": row[11],
            "retail_margin": row[12],
            "purchase_val": row[13],
            }
        tracker.insert_row(row[2], row[0], values, 1000)
    
    tracker.setup_for_codes()
    tracker.set_filename("IO-NIPA.txt")
    fh = tracker.get_file_handle("csv", {"delim": "\t"})
    for row in fh:
        code = row[0]
        desc = row[4]
        tracker.insert_code_row(code, desc)
    tracker.flush_codes()
    
    tracker.set_year(1997)
    tracker.set_filename("AppendixC_Detail.txt")
    fh = tracker.get_file_handle("csv", {"delim": ","})
    for row in fh:
        values = {
            "prod_val": row[3],
            "rail_margin": row[4],
            "truck_margin": row[5],
            "water_margin": row[6],
            "air_margin": row[7],
            "pipe_margin": row[8],
            "gaspipe_margin": row[9],
            "wholesale_margin": row[10],
            "retail_margin": row[11],
            "purchase_val": row[12],
            }
        tracker.insert_row(row[1], row[0], values, 1000)
    
    tracker.setup_for_codes()
    tracker.set_filename("IO-NIPA_PCE.txt")
    fh = tracker.get_file_handle("csv", {"delim": ","})
    for row in fh:
        code = row[1]
        desc = row[2]
        tracker.insert_code_row(code, desc)
    tracker.flush_codes()
    
    tracker.set_year(2002)
    tracker.setup_for_codes() # do this simultaneously since it's all one file
    tracker.set_filename("2002_PCE_Bridge.xls")
    wb = tracker.get_file_handle("xls")
    naics_pat = re.compile('[A-Z0-9]{6}')
    sheet = wb.sheet_by_name("PCE_Bridge_Detail")
    pce_codes = []
    for rowindex in range(sheet.nrows):
        row = sheet.row_values(rowindex)
        if len(row) == 13 and naics_pat.match(row[1]):
            pce_desc = row[0]
            # we don't need the distinction between households and
            # nonprofit institutions service households
            parts = pce_desc.split('-')
            if len(parts) > 1:
                lastpart = parts[-1].strip()
                if lastpart == 'HH' or lastpart == 'NPISH':
                    pce_desc = '-'.join(parts[:-1])
            pce_desc = pce_desc.strip()
    
            if pce_desc in pce_codes:
                pce_code = pce_codes.index(pce_desc)
            else:
                pce_code = len(pce_codes)
                pce_codes.append(pce_desc)
                tracker.insert_code_row(str(pce_code), pce_desc)
            
            values = {
                "prod_val": row[3],
                "rail_margin": row[4],
                "truck_margin": row[5],
                "water_margin": row[6],
                "air_margin": row[7],
                "pipe_margin": row[8],
                "gaspipe_margin": row[9],
                "wholesale_margin": row[10],
                "retail_margin": row[11],
                "purchase_val": row[12],
                }
            tracker.insert_row(str(pce_code), row[1], values, 1000)
    
    tracker.flush_codes()

def create_views():
    test_view = "%s.nipa_groups" % common.config.TEST_SCHEMA

    subqueries = []
    for year in config.STUDY_YEARS:
        subqueries.append(
            """SELECT %d AS year, nipa_group, description
                 FROM %s.nipa_codes_%d""" % (year, config.IO_SCHEMA, year))

    db.execute("CREATE OR REPLACE VIEW %s AS %s"
               % (test_view, "\n UNION\n".join(subqueries)))

    for year in config.STUDY_YEARS:
        strings = {
            "view_name": "%s.nipa_pce_%d" % (config.IO_SCHEMA, year),
            "bridge_table": "%s.pcebridge_%d" % (config.IO_SCHEMA, year),
            "code_table": "%s.nipa_codes_%d" % (config.IO_SCHEMA, year),
            "groups_table": "%s.pce_codes" % config.NIPA_SCHEMA,
            "pa_naics": eia.source_naics_map['PA'][year],
            "pa_trans_naics": eia.source_naics_map['PA-trans'][year],
            "pa_nontrans_naics": eia.source_naics_map['PA-nontrans'][year],
            "tourism_adjustment": bea.tourism_adjustment_codes[year],
            }
    
        # make sure gasoline/motor fuel purchases are allocated
        # among the split commodities we made for petroleum
        #
        # fortunately the group description for gasoline in all years
        # all start with "Gasoline" or "GASOLINE"
        sql = """
CREATE OR REPLACE VIEW %(view_name)s AS
    SELECT commodity, pcegroup,
           cast(sum(prod_val) as float) as value
      FROM (SELECT CASE
                   WHEN UPPER(codes.description) LIKE 'GASOLINE%%'
                    AND commodity = '%(pa_naics)s' THEN '%(pa_trans_naics)s'
                   WHEN commodity = '%(pa_naics)s' THEN '%(pa_nontrans_naics)s'
                   ELSE bridge.commodity END AS commodity,
                   bridge.prod_val,
                   groups.description as pcegroup
              FROM %(bridge_table)s bridge,
                   %(code_table)s codes,
                   %(groups_table)s groups
             WHERE bridge.pce_code = codes.pce_code
               AND bridge.commodity <> '%(tourism_adjustment)s'
               AND codes.nipa_group = groups.code) a
     GROUP BY commodity, pcegroup""" % strings

        db.execute(sql)

#!/usr/bin/python3

import csv, re
from usa import config
from common import fileutils
from dbsetup import TableStateTracker

# get nipa series codes from underlying detail tables
tracker = TableStateTracker()
tracker.create_table("%s.pce_codes" % config.NIPA_SCHEMA,
                     ["code", "parent", "description"],
                     ["char(7)", "char(7)", "text"])

number_pat = re.compile('^\d+$')
trailing_pat = re.compile('(.+) \(.*\d.*\)$')

filename = fileutils.getcache("Section2All_underlying.csv", "bea/nipa")
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

#!/usr/bin/python3
#
# the dictionary exchange_rates below was generated from the following code:

"""
import re, urllib.request

(temp, headers) = urllib.request.urlretrieve(
    "http://research.stlouisfed.org/fred2/data/EXJPUS.txt")

datepat = re.compile("\d{4}-\d{2}-\d{2}")
rates = {}
with open(temp, "r") as fh:
    for line in fh:
        if not datepat.match(line):
            continue
        parts = line.split()
        year = parts[0].split("-")[0]
        value = float(parts[1])

        if year not in rates:
            rates[year] = []
        rates[year].append(value)

print("exchange_rates = {")
print("    " + "\n    ".join(
        ["%s: %.1f," % (year, sum(rates[year]) / len(rates[year]))
         for year in sorted(rates.keys())]))
print("    }")
"""

exchange_rates = {
    1971: 348.0,
    1972: 303.1,
    1973: 271.4,
    1974: 291.9,
    1975: 296.8,
    1976: 296.5,
    1977: 268.4,
    1978: 210.5,
    1979: 219.2,
    1980: 226.6,
    1981: 220.4,
    1982: 249.1,
    1983: 237.4,
    1984: 237.6,
    1985: 238.5,
    1986: 168.5,
    1987: 144.6,
    1988: 128.1,
    1989: 138.0,
    1990: 144.8,
    1991: 134.5,
    1992: 126.7,
    1993: 111.2,
    1994: 102.2,
    1995: 94.1,
    1996: 108.8,
    1997: 121.1,
    1998: 130.8,
    1999: 113.7,
    2000: 107.8,
    2001: 121.5,
    2002: 125.3,
    2003: 115.9,
    2004: 108.2,
    2005: 110.1,
    2006: 116.3,
    2007: 117.8,
    2008: 103.4,
    2009: 93.6,
    2010: 87.8,
    2011: 79.7,
    2012: 79.7,
    }

# based on code from http://stackoverflow.com/questions/1823058/how-to-print-number-with-commas-as-thousands-separators-in-python-2-x

import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def add_commas(x, num_digits=0):
    template = "%%.%df" % num_digits
    return locale.format(template, x, grouping=True)

def cagr(from_val, to_val, interval):
    return pow(to_val / from_val, 1 / interval) - 1

# hex color conversion code from
# http://stackoverflow.com/questions/4296249/how-do-i-convert-a-hex-triplet-to-an-rgb-tuple-and-back
HEX = '0123456789abcdef'
HEX2 = dict((a+b, HEX.index(a)*16 + HEX.index(b)) for a in HEX for b in HEX)

def rgb(triplet):
    triplet = triplet.lower()
    return (HEX2[triplet[0:2]], HEX2[triplet[2:4]], HEX2[triplet[4:6]])

def triplet(rgb):
    return format((rgb[0]<<16)|(rgb[1]<<8)|rgb[2], '06x')




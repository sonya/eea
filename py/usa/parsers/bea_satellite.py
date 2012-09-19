#!/usr/bin/python3

# following hanson and somwaru
# http://ae761-s.agecon.purdue.edu/resources/download/645.pdf
# we use tourism accounts to attempt to eliminate the
# "Rest of the world adjustment to final uses" which causes
# problems when calculating total output because it is defined
# to sum to zero.

# 1992: http://www.bea.gov/scb/account_articles/national/0798ied/maintext.htm
# 1997: http://www.bea.gov/scb/pdf/national/inputout/2000/0700tta.pdf


import csv, re, xlrd
import fileutils


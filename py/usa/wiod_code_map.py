import re

codes = {
    "AtB": {
        "title": "Agriculture etc.",
        "rules": {
            1972: "^0[1234]",
            1997: "^11",
            }
        },
    "C": {
        "title": "Mining \\& quarrying",
        "rules": {
            1972: "^(0[56789]|10)",
            1997: "^21",
            }
        },
    "F": {
        "title": "Construction",
        "rules": {
            1972: "^1[12]",
            1997: "^23",
            }
        },
    "15t16": {
        "title": "Food, bev, tobacco",
        "rules": {
            1972: "^1[45]",
            1997: "^31[12]",
            }
        },
    "17t18": {
        "title": "Textiles \\& products",
        "rules": {
            1972: "^1[6789]",
            1997: "^31[345]",
            }
        },
    "20": {
        "title": "Wood \\& products",
        "rules": {
            1972: "^2[0123]",
            1997: "^321",
            }
        },
    "21t22": {
        "title": "Pulp, paper, printing",
        "rules": {
            1972: "^2[456]",
            1997: "^32[23]",
            }
        },
    "24": {
        "title": "Chemicals \\& products",
        "rules": {
            1972: "^(2[789]|30)",
            1997: "^325",
            }
        },
    "23": {
        "title": "Coke, petrol, nucl Fuel",
        "rules": {
            1972: "^31",
            1997: "^324",
            }
        },
    "25": {
        "title": "Rubber \\& plastics",
        "rules": {
            1972: "^32",
            1997: "^326",
            }
        },
    "19": {
        "title": "Leather \\& footwear",
        "rules": {
            1972: "^3[34]",
            1997: "^316",
            }
        },
    "26": {
        "title": "Other nonmetall min.",
        "rules": {
            1972: "^3[56]",
            1997: "^327",
            }
        },
    "27t28": {
        "title": "Basic \\& fab metal",
        "rules": {
            # 130[24567] is ammunition \\& small arms, under 332 in naics
            1972: "^(130[24567]|3[789]|4[012])",
            1997: "^33[12]",
            }
        },
    "29": {
        "title": "Machinery, n.e.c.",
        "rules": {
            1972: "^(4[3456789]|50)",
            1997: "^333",
            }
        },
    "30t33": {
        "title": "Electr \\& optical equip",
        "rules": {
            1972: "^(5[12345678]|6[23])",
            1997: "^33[45]",
            }
        },
    "34t35": {
        "title": "Transport equipment",
        "rules": {
            # 1301 is missles, 1303 is tanks, both under 336 in naics
            1972: "^(130[13]|59|6[01])",
            1997: "^336",
            }
        },
    "36t37": {
        "title": "Manufacturing n.e.c.",
        "rules": {
            1972: "^64",
            1997: "^33[7-9]",
            }
        },
    "60": {
        "title": "Inland transport",
        "rules": {
            1972: "^650[123]",
            1997: "^48[245]",
            }
        },
    "61": {
        "title": "Water transport",
        "rules": {
            1972: "^6504",
            1997: "^483",
            }
        },
    "62": {
        "title": "Air transport",
        "rules": {
            1972: "^6505",
            1997: "^481",
            }
        },
    "63": {
        "title": "Transport services",
        "rules": {
            1972: "^650[67]",
            1997: "^48[6A]",
            }
        },
    "64": {
        "title": "Post \\& telecomm",
        "rules": {
            1972: "^(6[67])",
            1997: "^(49[12]|513)",
            2002: "^(49[12]|51[57])",
            }
        },
    "E": {
        "title": "Utilities",
        "rules": {
            1972: "^68",
            1997: "^22",
            }
        },
    "51": {
        "title": "Wholesale trade",
        "rules": {
            1972: "^6901",
            1997: "^42",
            }
        },
    "52": {
        "title": "Retail trade",
        "rules": {
            1972: "^6902",
            1997: "^4A",
            }
        },
    "J": {
        "title": "Finance",
        "rules": {
            1972: "^70",
            1997: "^52",
            }
        },
    "70": {
        "title": "Real estate",
        "rules": {
            1972: "^71",
            1997: "^531",
            }
        },
    "71t74": {
        "title": "Other bus. activities",
        "rules": {
            1972: "^7(202|3)",
            1997: "^(51[124]|5[456]|811[234])",
            2002: "^(51[12689]|5[456]|811[234])",
            }
        },
    "H": {
        "title": "Hotels \\& Restaurants",
        "rules": {
            1972: "^7(201|4)",
            1997: "^72",
            }
        },
    "50": {
        "title": "Motor vehicle services",
        "rules": {
            1972: "^75",
            1997: "^8111",
            }
        },
    "N": {
        "title": "Health \\& social work",
        "rules": {
            1972: "^770[12356789]",
            1997: "^62",
            }
        },
    "M": {
        "title": "Education",
        "rules": {
            1972: "^7704",
            1997: "^61",
            }
        },
    "O": {
        "title": "Other services",
        "rules": {
            1972: "^7(6|203)",
            1997: "^(71|81[234]|53[23])",
            }
        },
    "L": {
        "title": "Public administration",
        "rules": {
            1972: "^(7[89]|82)",
            1997: "^S00[125]",
            2002: "^S00[12567]",
            }
        },
    "FC_HH": {
        "title": "Household consumption",
        "rules": {
            1972: "910000",
            1997: "F01000",
            }
        },

    }

def sector_for_naics(naics, year):
    for (large_code, large_attribs) in codes.items():
        if year == 2002 and 2002 in large_attribs["rules"]:
            rule = large_attribs["rules"][2002]
        elif year >= 1997:
            rule = large_attribs["rules"][1997]
        else:
            rule = large_attribs["rules"][1972]
    
        if re.compile(rule).match(naics):
            return large_code

def sector_title(code):
    return codes[code]["title"]

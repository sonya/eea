# common things relevant to eia data

# http://www.eia.gov/oiaf/1605/coefficients.html
conversion_factors = {
    "CL": 93.98, # industrial sector value, others similar
    "NG": 53.06, # weighted national average
    "PA-trans": 71.26, # motor gasoline value
    "PA-nontrans": 73.15, # middle distillate fuels
    }

sources = ("ES", "CL", "NG", "PA")
modified_sources = ["ES", "CL", "NG", "PA-trans", "PA-nontrans"]
modified_source_names = {
    "ES": "Electricity",
    "CL": "Coal",
    "NG": "Natural gas",
    "PA-trans": "Petroleum (transport)",
    "PA-nontrans": "Petroleum (other)",
    }

aviation_petroleum = ["JF", "AV"]
other_petroleum = ["DF", "KS", "LG", "MG", "RF", "DK", "LU", "AR", "PO", "PC"]
renewables = ["GE", "HY", "SO", "WY", "WD", "WS"]
nuclear = ["NU"]
elec_sources = ["ES", "LO"]
elec_sectors = ["EI", "EG"]
fossilfuels = ["PA", "NG", "CL"]

valid_sectors_by_source = {
    "ES": {
        "res": "RC", 
        "com": "CC",
        "elec": "IC",
        "trans": "AC",
        #"coke": "IC",
        "ind": "IC"},
    # EIA records no coal use by transportation sector after 1977.
    # (coal price tech notes)
    # transportation sector is included in industrial from 1978.
    # (coal use tech notes)
    "CL": {
        "res": "RC",
        "com": "CC",
        "elec": "EI",
        "trans": "IC",
        #"coke": "KC",
        "ind": "IC"},
    "PA": {
        "res": "RC",
        "com": "CC",
        "elec": "EI",
        "trans": "AC",
        #"coke": "IC",
        "ind": "IC"},
    "NG": {
        "res": "RC",
        "com": "CC",
        "elec": "EI",
        "trans": "AC",
        #"coke": "IC",
        "ind": "IC"},
    }

sector_naics_map_old = {
    "ind": "code IN ('940000', '950000')", # exports, imports
    "res": "code IN ('710100', '840000', '910000')",
    "elec": "code IN ('680100', '780200', '790200')", #, '993005')",
    "com": """SUBSTRING(code FROM 1 FOR 1) IN ('7', '8', '9')
           OR SUBSTRING(code FROM 1 FOR 2) IN ('66', '67', '69')""",
    "trans": "code LIKE '65%' OR code IN ('790100') ", # '993003') ",
    }

sector_naics_map = {
    "ind": "code IN ('F05000', 'F04000')", # exports, imports
    "res": "code IN ('814000', 'F01000', 'S00800')",
    "elec": "code IN ('221100', 'S00101', 'S00202')",
    "com": """SUBSTRING(code FROM 1 FOR  1) IN ('5', '6', '7', '8', 'S')
           OR SUBSTRING(code FROM 1 FOR 2) IN ('42', '49', '4A')
           OR SUBSTRING(code FROM 1 FOR 3) IN ('F06', 'F07', 'F08', 'F09')""",
           #OR SUBSTRING(code FROM 1 FOR 4) IN ('2212', '2213')""",
    #"coke": "code IN ('324110', '324199')",
    "trans": "code LIKE '48%' OR code = 'S00201' ",
    }

air_transportation_codes = {
    1972: '650500',
    1977: '650500',
    1982: '650500',
    1987: '650500',
    1992: '650500',
    1997: '481000',
    2002: '481000'
    }

source_naics_map = {
    'PA': {
        1972: '310100',
        1977: '310101',
        1982: '310101',
        1987: '310101',
        1992: '310101',
        1997: '324110',
        2002: '324110'},
    'NG': {
        1972: '680200',
        1977: '680200',
        1982: '680200',
        1987: '680200',
        1992: '680202',
        1997: '221200',
        2002: '221200'},
    'ES': {
        1972: '680100',
        1977: '680100',
        1982: '680100',
        1987: '680100',
        1992: '680100',
        1997: '221100',
        2002: '221100'},
    'CL': {
        1972: '070000',
        1977: '070000',
        1982: '070000',
        1987: '070000',
        1992: '070000',
        1997: '212100',
        2002: '212100'},
    'PA-trans': {
        1972: '31010A',
        1977: '31010A',
        1982: '31010A',
        1987: '31010A',
        1992: '31010A',
        1997: '32411A',
        2002: '32411A'},
    'PA-nontrans': {
        1972: '31010B',
        1977: '31010B',
        1982: '31010B',
        1987: '31010B',
        1992: '31010B',
        1997: '32411B',
        2002: '32411B'},
    }


def name_for_naics(source_naics):
    for (eia_source, naics_list) in source_naics_map.items():
        if source_naics in naics_list.values():
            return modified_source_names[eia_source]

def is_fossil_fuel(source):
    # test against EIA sources
    if (source in fossilfuels) or (source in ["PA-trans", "PA-nontrans"]):
        return True
    # test against NAICS
    for (eia_source, naics_list) in source_naics_map.items():
        if eia_source != "ES" and source in naics_list.values():
            return True
    return False
    


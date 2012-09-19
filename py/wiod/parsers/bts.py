import csv

from common import fileutils
from common.dbhelper import SQLTable
from wiod import config

def doparse():
    carrier_countries = {
        #"-": "", # Unknown
        "1I": "USA", # Sky Trek International Airlines
        "2T": "CAN", # Canada 3000 Airlines Ltd.
        "3Z": "USA", # Tatonduk Outfitters Limited d/b/a Everts Air Alaska and Everts Air Cargo
        "5X": "USA", # United Parcel Service
        "5Y": "USA", # Atlas Air Inc.
        "6F": "GBR", # Laker Airways Inc.
        #"6U": "", # Air Ukraine
        #"6Y": "", # Nicaraguense De Aviacion Sa
        #"7P": "", # Apa International Air S.A. (dominican rep)
        #"7Z": "", # Lb Limited
        "8C": "USA", # Air Transport International
        "AA": "USA", # American Airlines Inc.
        "AC": "CAN", # Air Canada
        #"ADB": "", # Antonov Company (ukraine)
        "AF": "FRA", # Compagnie Nat'l Air France
        "AI": "IND", # National Aviation Company of India Limited d/b/a Air India
        "AM": "MEX", # Aeromexico
        #"AQQ": "", # Air Charter (Safa)
        #"AR": "", # Aerolineas Argentinas
        "AS": "USA", # Alaska Airlines Inc.
        #"AT": "", # Royal Air Maroc (morocco)
        #"AV": "", # Aerovias Nac'l De Colombia
        "AY": "FIN", # Finnair Oy
        "AZ": "ITA", # Compagnia Aerea Italiana
        #"All Rows": "", # All Rows (including those not displayed)
        "BA": "GBR", # British Airways Plc
        #"BBQ": "", # Balair Ag (swiss)
        "BCQ": "CAN", # Bradley Air Services Ltd.
        #"BG": "", # Biman Bangladesh Airlines
        "BQ": "MEX", # Aeromar C. Por A.
        "BR": "TWN", # Eva Airways Corporation
        #"BW": "", # Caribbean Airlines Limited (trinidad and tobago)
        "BY": "GBR", # Britannia Airways Ltd.
        "CA": "CHN", # Air China
        #"CC": "", # Air Atlanta Icelandic
        "CDQ": "USA", # Kitty Hawk International
        #"CF": "", # Compan. De Aviacion Faucett (peru)
        "CI": "TWN", # China Airlines Ltd.
        #"CLQ": "", # Aero Transcolombiana
        #"CM": "", # Compania Panamena (Copa)
        "CO": "USA", # Continental Air Lines Inc.
        "CP (1)": "CAN", # Canadian Airlines International Ltd.
        "CS": "USA", # Continental Micronesia
        "CV": "LUX", # Cargolux Airlines International S.A
        #"CVQ": "", # Caraven S.A.
        #"CX": "", # Cathay Pacific Airways Ltd. (hong kong, includes pre 1997)
        "CYQ": "FRA", # Corse Air International (assuming corsair)
        "CZ": "CHN", # China Southern Airlines
        "DE": "DEU", # Condor Flugdienst
        "DHQ": "GBR", # DHL Aero Expresso
        "DL": "USA", # Delta Air Lines Inc.
        #"ED": "", # Andes (ecuador or argentina)
        "EH": "ESP", # Saeta Airlines
        "EI": "IRL", # Aer Lingus Plc
        #"EOQ": "", # Aeroservicios Ecuatorianos
        "ER": "USA", # Astar USA, LLC
        #"EU": "", # Ecuatoriana De Aviacion
        #"EXQ": "", # Export Air Del Peru S.A.
        "EZ": "TWN", # Evergreen International Inc.
        "F9": "USA", # Frontier Airlines Inc.
        "FCQ": "USA", # Falcon Air Express
        #"FF": "", # Tower Air Inc.
        #"FI": "", # Icelandair
        #"FJ": "", # Air Pacific Ltd. (fiji)
        "FNQ": "USA", # Fine Airlines Inc.
        #"FQ": "", # Air Aruba
        #"FS": "", # Serv De Trans Aereos Fuegui (argentina)
        "FX": "USA", # Federal Express Corporation
        #"G3": "", # Aerochago S.A.
        "GA": "IDN", # P.T. Garuda Indonesian Arwy
        "GD": "MEX", # Transp. Aereos Ejecutivos
        #"GF": "", # Gulf Air Company (bahrain)
        #"GH": "", # Ghana Airways Corporation
        "GJ (1)": "MEX", # Mexicargo
        "GL": "USA", # Miami Air International
        "GR": "USA", # Gemini Air Cargo Airways
        #"GU": "", # Aviateca (guatemala)
        #"GY": "", # Guyana Airways Corporation
        "H2": "BEL", # City Bird
        "H5": "RUS", # Magadan Airlines
        "HA": "USA", # Hawaiian Airlines Inc.
        "HAQ": "DEU", # Hapag Lloyd Flug.
        "HCQ": "USA", # Av Atlantic
        #"HFQ": "", # Haiti Air Freight Intl
        "HLQ": "AUS", # Heavylift Cargo Airlines Lt
        "HP": "USA", # America West Airlines Inc. (Merged with US Airways 9/05. Stopped reporting 10/07.)
        #"HY": "", # Uzbekistan Airways
        "IB": "ESP", # Iberia Air Lines Of Spain
        #"ITQ": "", # Interamericana De Aviacion (uruguay)
        "IW": "FRA", # Air Liberte Aka Aom Minerve
        #"JAQ": "", # Jamaica Air Freighters
        "JD": "JPN", # Japan Air System Co. Ltd.
        "JI (1)": "USA", # Midway Airlines Inc.
        "JK": "ESP", # Spanair S.A.
        "JKQ": "USA", # Express One International Inc.
        "JL": "JPN", # Japan Air Lines Co. Ltd.
        #"JM": "", # Air Jamaica Limited
        "JR": "USA", # Aero California
        "JW": "CAN", # Arrow Air Inc.
        "JZ": "JPN", # Japan Air Charter Co. Ltd.
        "K8 (1)": "NLD", # Dutch Caribbean Airlines
        "KE": "KOR", # Korean Air Lines Co. Ltd.
        "KH": "USA", # Aloha Air Cargo
        #"KI": "", # Time Air Ltd. (south africa)
        "KL": "NLD", # Klm Royal Dutch Airlines
        #"KP": "", # Kiwi International
        "KR": "USA", # Kitty Hawk Aircargo
        "KTQ": "TUR", # Turks Air Ltd.
        #"KU": "", # Kuwait Airways Corp.
        "KW": "USA", # Carnival Air Lines Inc.
        #"KX": "", # Cayman Airways Limited
        "KZ": "JPN", # Nippon Cargo Airlines
        #"LA": "", # Lan-Chile Airlines
        #"LB": "", # Lloyd Aereo Boliviano S. A.
        "LGQ": "MEX", # Lineas Aereas Allegro
        "LH": "DEU", # Lufthansa German Airlines
        "LO": "POL", # Polskie Linie Lotnicze
        #"LR": "", # Lacsa (costa rica)
        #"LSQ": "", # Lineas Aereas Suramerican (colombia)
        "LT": "DEU", # Luftransport-Unternehmen
        #"LU": "", # Air Atlantic Dominicana
        #"LY": "", # El Al Israel Airlines Ltd.
        "LZ": "BGR", # Balkan Bulgarian Airlines
        "M6": "USA", # Amerijet International
        "M7": "MEX", # Aerotransportes Mas De Crga
        "MA": "HUN", # Malev Hungarian Airlines
        "MG": "USA", # Champion Air
        #"MH": "", # Malaysian Airline System
        #"ML": "", # Aero Costa Rica
        "MP": "NLD", # Martinair Holland N.V.
        #"MS": "", # Egyptair
        "MT": "GBR", # Thomas Cook Airlines Uk Ltd.
        "MT (1)": "GBR", # Flying Colours Airlines Ltd.
        "MU": "CHN", # China Eastern Airlines
        #"MUQ": "", # Aerolineas Mundo (columbia)
        "MX": "MEX", # Compania Mexicana De Aviaci
        #"MYQ": "", # Lineas Aereas Mayas (Lamsa)
        #"N5 (1)": "", # Nations Air Express Inc.
        "NA": "USA", # North American Airlines
        "NG": "DEU", # Lauda Air Luftfahrt Ag
        "NH": "JPN", # All Nippon Airways Co.
        "NK": "USA", # Spirit Air Lines
        "NW": "USA", # Northwest Airlines Inc.
        "NWQ": "USA", # N. W. Territorial Airways
        #"NZ": "", # Air New Zealand
        "OA": "GRC", # Olympic Airways
        #"OI": "", # Prestige Airways (uae)
        "OK": "CZE", # Czech Airlines
        #"ON": "", # Air Nauru
        "OS": "AUT", # Austrian Airlines
        "OW": "USA", # Executive Airlines
        "OZ": "KOR", # Asiana Airlines Inc.
        "PA (2)": "USA", # Pan American World Airways
        "PCQ": "USA", # Pace Airlines
        #"PIQ": "", # Pacific International Airlines (ambiguous: usa, panama)
        #"PK": "", # Pakistan International Airlines
        #"PL": "", # Aero Peru
        "PNQ": "USA", # Panagra Airways
        "PO": "USA", # Polar Air Cargo Airways
        #"PR": "", # Philippine Airlines Inc.
        "PRQ": "USA", # Florida West Airlines Inc.
        "PT": "USA", # Capital Cargo International
        #"PY": "", # Surinam Airways Limited
        "Q7": "BEL", # Sobelair
        "QF": "AUS", # Qantas Airways Ltd.
        "QK": "CAN", # Jazz Aviation LP
        #"QN": "", # Royal Air (ambiguous)
        "QO": "MEX", # Aeromexpress
        "QQ": "USA", # Reno Air Inc.
        #"QT": "", # Transportes Aereos Mercantiles Panamericanos S.A (colombia)
        "QTQ": "IRL", # Aer Turas Teoranta
        "QX": "USA", # Horizon Air
        "RD": "USA", # Ryan International Airlines
        "REQ": "USA", # Renown Aviation
        "RG": "BRA", # Varig S. A.
        #"RJ": "", # Alia-(The) Royal Jordanian
        #"RK": "", # Air Afrique
        "RNQ": "GBR", # Mytravel Airways
        "RO": "ROU", # Tarom Romanian Air Transpor
        #"SA": "", # South African Airways
        "SAQ": "USA", # Southern Air Transport Inc.
        "SEQ": "GBR", # Sky Service F.B.O.
        "SIQ": "LUX", # Premiair
        "SK": "SWE", # Scandinavian Airlines Sys.
        "SM": "USA", # Sunworld International Airlines
        "SN (1)": "BEL", # Sabena Belgian World Air.
        "SPQ": "USA", # Sun Pacific International
        #"SQ": "", # Singapore Airlines Ltd.
        #"SR": "", # Swissair Transport Co. Ltd.
        "SU": "RUS", # Aeroflot Russian Airlines
        #"SV": "", # Saudi Arabian Airlines Corp
        "SX (1)": "MEX", # Aeroejecutivo S.A.
        "SY": "USA", # Sun Country Airlines d/b/a MN Airlines
        "T9": "USA", # TransMeridian Airlines
        #"TA": "", # Taca International Airlines (el savador)
        "TCQ": "USA", # Express.Net Airlines
        #"TG": "", # Thai Airways International Ltd.
        "TK": "TUR", # Turk Hava Yollari A.O.
        "TKQ": "USA", # Trans-Air-Link Corporation
        "TNQ": "USA", # Emery Worldwide Airlines
        "TP": "PRT", # Tap-Portuguese Airlines
        "TR": "BRA", # Transbrasil S.A.
        "TRQ": "SWE", # Blue Scandinavia Ab
        "TS": "CAN", # Air Transat
        "TW": "USA", # Trans World Airways LLC
        #"TZ": "", # ATA Airlines d/b/a ATA (iran)
        "TZQ": "GBR", # First Choice Airways
        "U7": "USA", # USA Jet Airlines Inc.
        "UA": "USA", # United Air Lines Inc.
        #"UD": "", # Fast Air Carrier Ltd.
        "UN": "RUS", # Transaero Airlines
        #"UP": "", # Bahamasair Holding Limited
        "US": "USA", # US Airways Inc. (Merged with America West 9/05. Reporting for both starting 10/07.)
        "UX": "ESP", # Air Europa
        #"UYQ": "", # Aerolineas Uruguayas S.A.
        #"VA (1)": "", # Venezuelan International Airways
        #"VC": "", # Servicios Avensa (venezuela)
        #"VE": "", # Aerovias Venezolanas-Avensa
        "VIQ": "RUS", # Volga-Dnepr Airlines
        "VP": "BRA", # Viacao Aerea Sao Paulo
        #"VR": "", # Transportes Aereos De Cabo (cape verde)
        "VS": "GBR", # Virgin Atlantic Airways
        #"VX (1)": "", # Aces Airlines (colombia)
        #"W7": "", # Western Pacific Airlines (solomon islands)
        #"WD": "", # Halisa Air (haiti)
        "WE": "USA", # Centurion Cargo Inc.
        "WO": "USA", # World Airways Inc.
        #"XC": "", # Air Caribbean (1)
        "XE": "USA", # ExpressJet Airlines Inc. (1)
        "XJ": "USA", # Mesaba Airlines
        "XP": "USA", # Casino Express
        "YX (1)": "USA", # Midwest Airline, Inc.
        "ZB": "USA", # Monarch Airlines
        #"ZUQ": "", # Zuliana De Aviacion (venezuela)
        "ZX (1)": "CAN", # Airbc Ltd.
        }

    tablename = "air_carriers"
    table = SQLTable(
        tablename,
        ["year", "carrier", "series", "value"],
        ["int", "varchar(15)", "varchar(15)", "int"])
    table.create()
    table.truncate()

    carriers = {}

    for year in config.STUDY_YEARS:
        for filestem in ["freight", "passengers"]:
            filename = filestem + str(year) + ".csv"
            path = fileutils.getcache(filename, "bts")
            with open(path) as fh:
                csvf = csv.reader(fh)
                next(csvf)
                header = next(csvf)
                for row in csvf:
                    if len(row) == 3:
                        carrier = row[0]
                        #carrier_name = row[1]
                        if carrier in carrier_countries:
                            country = carrier_countries[carrier]
                            value = int(row[2])
                            table.insert([year, country, filestem, value])




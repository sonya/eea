SCHEMA = "uk"
STUDY_YEARS = range(1992, 2009)

curated_sectors = {
    # value added
    "Taxes less subsidies on production": "tax",
    "Compensation of employees": "comp",
    "Gross operating surplus and mixed income": "surp",
    # final demand
    "Households": "hh",
    "Non-profit\ninstitutions serving\nhouseholds": "npish",
    "Central\ngovernment": "gov",
    "Local\ngovernment": "lgov",
    "Gross fixed\ncapital\nformation": "gfcf",
    "Valuables": "valbls",
    "Changes in inventories": "invchg",
    #"Exports of Goods"
    #"Exports of Services"
    "Total exports of goods and services": "export",
    }

fd_sectors = ["hh", "gov", "gfcf", "export", "invchg",
              "lgov", "npish", "valbls"]
pce_sector = "hh"
export_sector = "export"

va_sectors = ["tax", "comp", "surp"]

env_series = ["N2O", "CO2", "PFCs", "SF6", "GHG total", "HFCs", "CH4"]


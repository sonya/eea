DEBUG_MODE = True
#DEBUG_MODE = False

# GNUPlot options
DEFAULT_IMAGE_TYPE = "png" # png, eps
SUPPRESS_PLOT_TITLES = True

DB_NAME = "eea"
DB_PORT = ":5432"

TEST_SCHEMA = "test"  # schema for creating verification tables

PROJECT_ROOT = __PROJECT_ROOT__

# things below here probably don't need to be changed much

DATA_DIR = PROJECT_ROOT + "/data"
DATA_CACHE_DIR = PROJECT_ROOT + "/data/cache"

ENV_SERIES_TITLES = {
    "EU": "gross energy use",
    "CO": "carbon monoxide (CO)",
    "CO2": "CO_2",
    "CH4": "methane (CH_4)",
    "N2O": "nitrous oxide (N_2O)",
    "SF6": "sulfur hexafluoride (SF_6)",
    "PFCs": "perfluorinated compounds (PFCs)",
    "HFCs": "hydroflurocarbons (HFCs)",
    "GHG total": "greenhouse gas total",
    "NOx": "nitrogen oxides (NO_x)",
    "SOx": "sulfur oxides (SO_x)",
    "BOD": "biochemical oxygen demand (BOD)",
    "TSP": "total suspended particulates (TSP)",
    "NMVOC": "non-methane volatile organic compounds",
    "NH3": "ammonia (NH_3)",
    "waste": "total waste",
    "waste-hi": "hazardous waste - improperly disposed",
    }



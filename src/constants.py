"""Static constants and configuration used across the project."""

########################################################
# DIRECTORIES
########################################################

DATA_DIR = "assignment lists"  # Folder containing input CSV files
OUTPUT_DIR = "results"  # Folder where JSON/CSV outputs are written

########################################################
# DATES
########################################################

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

DATE_FORMAT = "%Y-%m-%d"

########################################################
# CSV PARSING
########################################################

# Entries treated as "no one assigned"
EMPTY_VALUES = ["", "-", " - "]

# Column names assigned to the CSV (first row is skipped on load)
FIELD_NAMES = [
    "Game",
    "Date",
    "Time",
    "Field",
    "Home Team",
    "Away Team",
    "Status",
    "Referee",
    "Referee 2",
    "Assistant 1",
    "Assistant 2",
    "4th Referee",
    "Supervisor",
    "Schedule",
]

# Maps internal role keys to CSV column names
ROLE_COLS = {
    "ref1": "Referee",
    "ref2": "Referee 2",
    "ar1": "Assistant 1",
    "ar2": "Assistant 2",
    "ref4": "4th Referee",
}

# Columns used to compute crew pairings (on-field crew only)
CREW_COLS = ["Referee", "Referee 2", "Assistant 1", "Assistant 2"]

# Status symbols stripped from role columns
STATUS_SYMBOLS = ["✅", "⌛"]

########################################################
# GAME LEVELS
########################################################

# Game levels in ascending order of difficulty to ref
LEVELS_PREFIX_LVL = [
    "",
    "U9",
    "U10",
    "U11",
    "U12",
    "U13",
    "U14",
    "CDC9F",
    "CDC9M",
    "CDC10F",
    "CDC10M",
    "CDC11FD2",
    "CDC11FD1",
    "CDC11MD2",
    "CDC11MD1",
    "CDC12FD2",
    "CDC12FD1",
    "CDC12MD2",
    "CDC12MD1",
    "F13LR",
    "M13LR",
    "F13IRD2",
    "F13IRD1",
    "M13IRD2",
    "M13IRD1",
    "LSF",
    "F14IV",
    "M14IV",
    "F14LR",
    "M14LR",
    "F14IR",
    "M14IR",
    "F15IV",
    "M15IV",
    "F15LR",
    "M15LR",
    "F15IR",
    "M15IR",
    "F16IV",
    "M16IV",
    "LSM",
]

# Same prefixes sorted by descending length (longest match first)
LEVELS_PREFIX_LEN = sorted(LEVELS_PREFIX_LVL, key=len, reverse=True)

########################################################
# LOCATIONS
########################################################

# Trailing field identifiers stripped to get the main park name
FIELD_SUFFIXES_TO_STRIP = [
    " - 1",
    " - 2",
    " - 3",
    " - A",
    " - B",
    " - C",
    " - Synthétique",
    " (SYNTH)",
]

# Locations excluded from the field distribution stats
EXCLUDED_LOCATIONS = ["Edouard VII", "TBA", "", "Unknown/TBA"]

UNKNOWN_LOCATION = "Unknown/TBA"
DOME_LOCATION = "Dôme Centre Multisport"

########################################################
# ANALYSIS SETTINGS
########################################################

# Only pairings with MORE than this many games together are exported
MIN_PAIRING_GAMES = 2
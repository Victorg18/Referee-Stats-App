import itertools
import json
import numpy as np
import pandas as pd

########################################################
# PROGRAM CONSTANTS AND VARIABLES
########################################################

# Write Correct file path
file_path = "april_to_july_assignment.csv"

# List of day of the week
weekday_names = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Create list of entries to skip
empty_values = ["", "-", " - "]

# List of games level in ascending order of difficulty to ref
levels_prefix_lvl = [
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

# List of games level in descending order of length
levels_prefix_len = sorted(levels_prefix_lvl, key=len, reverse=True)

# Global info trackers
field_distribution = {}
crew_pairings = {}  # Key: "Name A & Name B", Value: Count
games_by_date = {}  # Key: "2026-05-02", Value: Count
total_games_per_weekday = {day: 0 for day in weekday_names}
unique_dates_per_weekday = (
    {}
)  # Uses pandas grouping for unique calendar dates

# Create dictionary of dictionary to store ref info
ref_data = {}

# Global stats dict
global_stats = {
    "total_games": 0,
    "total_slots": 0,
    "filled_slots": 0,
    "missing_slots": 0,
    "coverage": "",
    "supervised_games": 0,
    "unique_refs": 0,
    "avg_games": 0,
    "unique_supervisors": 0,
    "slots_by_role": {"ref1": 0, "ar1": 0, "ar2": 0, "ref2": 0, "ref4": 0},
    "filled_by_role": {"ref1": 0, "ar1": 0, "ar2": 0, "ref2": 0, "ref4": 0},
    "missing_by_role": {"ref1": 0, "ar1": 0, "ar2": 0, "ref2": 0, "ref4": 0},
}

# List of active referees in csv
ref_list = []

########################################################
# HELPER FUNCTIONS
########################################################


# Helper function to get level prefix of a game
def get_prefix(game_str):
    """Helper function to find which prefix the game string starts with.

    Iterates backwards through the prefix list to match the longest prefix
    first
    """
    if not isinstance(game_str, str):
        return ""
    for prefix in levels_prefix_len:
        if prefix and game_str.startswith(prefix):
            return prefix
    return ""  # Default backup if nothing matches


# Helper function to clean up field names
def get_location_name(field_str):
    """Groups specific field names into their main park/location names."""
    if not field_str or field_str in empty_values or pd.isna(field_str):
        return "Unknown/TBA"

    location = str(field_str)

    # Clean up "Dôme Centre Multisport" variations
    if "Dôme Centre Multisport" in location:
        return "Dôme Centre Multisport"

    # Remove common trailing field identifiers like " - 1", " - 2", " - A", " - B", " - Synthétique"
    suffixes_to_strip = [
        " - 1",
        " - 2",
        " - 3",
        " - A",
        " - B",
        " - C",
        " - Synthétique",
        " (SYNTH)",
    ]
    for suffix in suffixes_to_strip:
        if location.endswith(suffix):
            location = location.replace(suffix, "")
    return location.strip()


########################################################
# CSV Parsing and Data Collection (Pandas Accelerated)
########################################################

df = pd.DataFrame()

try:
    # Column mapping & CSV loading
    fieldNames = [
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

    # Read CSV with pandas, skip first row as per original DictReader logic
    df = pd.read_csv(
        file_path,
        skiprows=1,
        names=fieldNames,
        header=None,
        dtype=str,
        encoding="utf-8",
    )

    # Clean date column and drop invalid date rows
    df["Date_Parsed"] = pd.to_datetime(
        df["Date"], format="%Y-%m-%d", errors="coerce"
    )
    df = df.dropna(subset=["Date_Parsed"]).copy()

    # Clean string checkmarks from all role columns
    role_cols = {
        "ref1": "Referee",
        "ref2": "Referee 2",
        "ar1": "Assistant 1",
        "ar2": "Assistant 2",
        "ref4": "4th Referee",
    }

    for col in list(role_cols.values()) + ["Supervisor"]:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.replace("✅", "", regex=False)
            .str.replace("⌛", "", regex=False)
            .str.strip()
        )

    # Calculate Game level ranks using Categorical typing for fast comparisons
    df["Prefix"] = df["Game"].apply(get_prefix)
    prefix_dtype = pd.CategoricalDtype(
        categories=levels_prefix_lvl, ordered=True
    )
    df["Prefix_Rank"] = df["Prefix"].astype(prefix_dtype)

    ################## Use data from CSV ##################

    global_stats["total_games"] = len(df)

    # Role Parsing & Global Slot counts
    for role_key, col in role_cols.items():
        series = df[col]
        # Total slots defined as non-empty in original CSV
        non_empty_mask = series != ""
        filled_mask = ~series.isin(empty_values)

        global_stats["slots_by_role"][role_key] = int(non_empty_mask.sum())
        global_stats["filled_by_role"][role_key] = int(filled_mask.sum())
        global_stats["missing_by_role"][role_key] = int(
            (non_empty_mask & ~filled_mask).sum()
        )

    global_stats["total_slots"] = sum(global_stats["slots_by_role"].values())
    global_stats["filled_slots"] = sum(global_stats["filled_by_role"].values())
    global_stats["missing_slots"] = sum(
        global_stats["missing_by_role"].values()
    )

    # Collect list of all unique officials
    all_officials_series = pd.concat(
        [df[c] for c in list(role_cols.values()) + ["Supervisor"]]
    )
    unique_officials = set(
        all_officials_series[~all_officials_series.isin(empty_values)].unique()
    )

    # Has supervisor mask
    has_sup_mask = ~df["Supervisor"].isin(empty_values)

    # Populate ref_data dictionary
    for official in unique_officials:
        # Match where official worked in any role
        c_ref1 = df["Referee"] == official
        c_ref2 = df["Referee 2"] == official
        c_ar1 = df["Assistant 1"] == official
        c_ar2 = df["Assistant 2"] == official
        c_ref4 = df["4th Referee"] == official
        c_sup = df["Supervisor"] == official

        central_mask = c_ref1 | c_ref2
        ar_mask = c_ar1 | c_ar2
        ref4_mask = c_ref4
        all_worked_mask = central_mask | ar_mask | ref4_mask

        # Compute statistics using vectorized pandas boolean indexing
        total_games = int(all_worked_mask.sum())
        central_count = int(central_mask.sum())
        ar_count = int(ar_mask.sum())
        ref4_count = int(ref4_mask.sum())
        games_supervised = int(c_sup.sum())

        # Supervised games while acting as field referee
        times_supervised = int((all_worked_mask & has_sup_mask).sum())

        # Dates range
        working_dates = df.loc[all_worked_mask | c_sup, "Date_Parsed"]
        oldest_game = str(working_dates.min())[:10]
        newest_game = str(working_dates.max())[:10]

        # Highest level game extraction
        highest_central = ""
        if central_count > 0:
            sub_df = df.loc[central_mask, ["Game", "Prefix_Rank"]]
            sorted_df = sub_df.sort_values(by=["Prefix_Rank"], ascending=[False])
            highest_central = str(sorted_df["Game"].iloc[0])

        highest_ar = ""
        if ar_count > 0:
            sub_df = df.loc[ar_mask, ["Game", "Prefix_Rank"]]
            sorted_df = sub_df.sort_values(by=["Prefix_Rank"], ascending=[False])
            highest_ar = str(sorted_df["Game"].iloc[0])

        # Save profile
        ref_data[official] = {
            "name": official,
            "total_games": total_games,
            "central_count": central_count,
            "ar_count": ar_count,
            "4th_ref_count": ref4_count,
            "highest_central_game": highest_central,
            "highest_ar_game": highest_ar,
            "oldest_game": oldest_game,
            "newest_game": newest_game,
            "games_supervised": games_supervised,
            "times_supervised": times_supervised,
        }

        # Track ref_list for CSV output
        if " " in official:
            first_name, family_name = official.split(" ", 1)
        else:
            first_name, family_name = official, ""
        ref_list.append({"First Name": first_name, "Last Name": family_name})

    global_stats["unique_refs"] = len(unique_officials)
    global_stats["unique_supervisors"] = sum(
        1 for v in ref_data.values() if v["games_supervised"] > 0
    )
    global_stats["supervised_games"] = int(has_sup_mask.sum())

    ################## Field Distribution & Pairings ##################

    df["Clean_Location"] = df["Field"].apply(get_location_name)
    field_counts = df[
        ~df["Clean_Location"].isin(["Edouard VII", "TBA", "", "Unknown/TBA"])
    ]["Clean_Location"].value_counts()
    field_distribution = field_counts.to_dict()

    # Crew pairing counts
    crew_cols = ["Referee", "Referee 2", "Assistant 1", "Assistant 2"]
    for _, row in df[crew_cols].iterrows():
        active_crew = [
            name for name in row.values if name and name not in empty_values
        ]
        if len(active_crew) >= 2:
            for pair in itertools.combinations(sorted(active_crew), 2):
                pair_key = f"{pair[0]} & {pair[1]}"
                crew_pairings[pair_key] = crew_pairings.get(pair_key, 0) + 1

    # Date aggregations
    games_by_date = df["Date"].value_counts().to_dict()

except FileNotFoundError:
    print("That file was not found")
except PermissionError:
    print("You do not have permission to read that file")

########################################################
# Additional Calculation and parsing for json conversion
########################################################

################## Official Stats ##################

# Convert the dictionary of dictionaries into a list of dictionaries
referee_json_list = list(ref_data.values())

################## Global Stats ##################

# Calculate and add coverage percentage
if global_stats["total_slots"] > 0:
    global_stats["coverage"] = (
        round(
            global_stats["filled_slots"]
            / global_stats["total_slots"]
            * 10000
        )
    ) / 100

# Get sum of all games
sum_of_all_games = sum(prof["total_games"] for prof in ref_data.values())

# Calculate the average number of games per referee
if global_stats["unique_refs"] > 0:
    global_stats["avg_games"] = round(
        sum_of_all_games / global_stats["unique_refs"]
    )

# Add field distribution:
global_stats["field distribution"] = dict(
    sorted(field_distribution.items(), key=lambda x: x[1], reverse=True)
)

# Get total games & averages per weekday using Pandas
if not df.empty:
    df["Weekday"] = df["Date_Parsed"].dt.day_name()
    weekday_totals = df["Weekday"].value_counts().to_dict()
    weekday_unique_dates = df.groupby("Weekday")["Date"].nunique().to_dict()
else:
    weekday_totals = {}
    weekday_unique_dates = {}

weekday_averages = {}
busiest_day_name = ""
max_total_games = -1

for day in weekday_names:
    total_games = weekday_totals.get(day, 0)
    unique_day_count = weekday_unique_dates.get(day, 0)

    total_games_per_weekday[day] = total_games
    if unique_day_count > 0:
        weekday_averages[day] = int(round(total_games / unique_day_count, 0))
    else:
        weekday_averages[day] = 0

    if total_games > max_total_games:
        max_total_games = total_games
        busiest_day_name = day

# Add day stats to global dict
global_stats["busiest_day_of_week"] = busiest_day_name
global_stats["total_games_by_weekday"] = total_games_per_weekday
global_stats["average_games_by_weekday"] = weekday_averages

################## Official Pairings ##################

# Filter out pairings that have 2 or fewer games together
frequent_pairings = {
    pair: count for pair, count in crew_pairings.items() if count > 2
}

# Sort the filtered pairings from most frequent to least frequent
sorted_pairings = dict(
    sorted(frequent_pairings.items(), key=lambda item: item[1], reverse=True)
)

########################################################
# Writing to json
########################################################

# Open a new file and write the list as JSON
with open("referee_stats.json", "w", encoding="utf-8") as json_file:
    json.dump(referee_json_list, json_file, indent=4, ensure_ascii=False)
    print("Successfully saved data to referee_stats.json")

# Open a new file and write the list as JSON
with open("global_stats.json", "w", encoding="utf-8") as json_file:
    json.dump(global_stats, json_file, indent=4, ensure_ascii=False)
    print("Successfully saved data to global_stats.json")

# Open a new file and write the list as JSON
with open("crew_pairings.json", "w", encoding="utf-8") as json_file:
    json.dump(sorted_pairings, json_file, indent=4, ensure_ascii=False)
    print("Successfully saved data to crew_pairings.json (Filtered: > 2 games)")

# Open a new file and write the list as csv
pd.DataFrame(ref_list).to_csv("ref_list.csv", index=False, encoding="utf-8")
print("Successfully saved list of referees to ref_list.csv")

########################################################
# Helper function to get data from referee stats
########################################################


def get_top_referees(n=10):
    """Returns the top N referees sorted by total games officiated."""
    sorted_refs = sorted(
        ref_data.values(), key=lambda x: x["total_games"], reverse=True
    )
    return sorted_refs[:n]


def get_top_supervisors(n=5):
    """Returns the top N supervisors sorted by games supervised."""
    sorted_sups = sorted(
        ref_data.values(), key=lambda x: x["games_supervised"], reverse=True
    )
    return sorted_sups[:n]


def get_official_profile(name):
    """Retrieves the full profile for a given official by name."""
    return ref_data.get(name, f"Official '{name}' not found.")


print("\n--- TOP 10 REFEREES BY TOTAL GAMES ---")
for rank, ref in enumerate(get_top_referees(10), start=1):
    print(
        f"{rank:2d}. {ref['name']:<20} | Games: {ref['total_games']} "
        f"(Central: {ref['central_count']}, AR: {ref['ar_count']})"
    )

print("\n--- TOP SUPERVISOR ---")
top_sup = get_top_supervisors(5)
if top_sup:
    sup = top_sup[0]
    print(f"Name: {sup['name']}")
    print(f"Games Supervised: {sup['games_supervised']}")

print("\n--- FULL PROFILE LOOKUP ---")
print("\n--------------------------------------------")
while True:
    ref_name = input("Enter a referee name: ")
    profile = get_official_profile(ref_name)
    if isinstance(profile, dict):
        print(json.dumps(profile, indent=4, ensure_ascii=False))
    else:
        print(profile)
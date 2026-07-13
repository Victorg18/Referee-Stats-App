import csv
import json
from datetime import datetime

########################################################
# PROGRAM CONSTANTS AND VARIABLES
########################################################

# Write Correct file path
file_path = "large_sample.csv"

# Create list of entries to skip
empty_values = ["", "-", " - "]

# List of games level in ascending order of difficulty to ref
levels_prefix_lvl = ["", "U9", "U10", "U11", "U12", "U13", "U14", "CDC9F", "CDC9M", "CDC10F", "CDC10M", 
                 "CDC11FD2", "CDC11FD1", "CDC11MD2", "CDC11MD1", "CDC12FD2", "CDC12FD1", "CDC12MD2", "CDC12MD1", 
                 "F13LR", "M13LR", "F13IRD2", "F13IRD1", "M13IRD2", "M13IRD1", "LSF" , "F14IV", "M14IV", "F14LR", "M14LR", "F14IR", "M14IR", 
                 "F15IV", "M15IV", "F15LR", "M15LR", "F15IR", "M15IR", "F16IV", "M16IV", "LSM"]

# List of games level in descending order of length
levels_prefix_len = sorted(levels_prefix_lvl, key=len, reverse=True)

# Create dictionary of dictionary to store ref info
ref_data = {}

# Global stats dict
global_stats = {
    "total_games": 0,
    "total_slots": 0,
    "filled_slots": 0,
    "missing_slots": 0,
    "coverage": 0,
    "supervised_games": 0,
    "unique_refs": 0,
    "unique_supervisors": 0,
    "avg_games": 0,
    "slots_by_role": {
        "ref": 0,
        "ar1": 0,
        "ar2": 0
    },
    "filled_by_role": {
        "ref": 0,
        "ar1": 0,
        "ar2": 0
    },
    "missing_by_role": {
        "ref": 0,
        "ar1": 0,
        "ar2": 0
    }
}

########################################################
# HELPER FUNCTIONS
########################################################

# Function to get level prefix of a game
def get_prefix(game_str):
    """
    Helper function to find which prefix the game string starts with.
    Iterates backwards through the prefix list to match the longest prefix first 
    """

    # Sort by length descending so longer prefix match first
    for prefix in levels_prefix_len:
        if prefix and game_str.startswith(prefix):
            return prefix
    return "" # Default backup if nothing matches


# Function to compare the levels of two games and return highest game
def compare_game(game1, game2):

    # Get level prefix from game
    pre1 = get_prefix(game1)
    pre2 = get_prefix(game2)

    # Get rank (index) of levels
    rank1 = levels_prefix_lvl.index(pre1)
    rank2 = levels_prefix_lvl.index(pre2)

    if rank1 < rank2:
        return game2
    else:
        return game1
    
def create_official(official, initial_date):
    global_stats["unique_refs"] += 1
    ref_data[official] = {
        "name": official,
        "total_games": 0,
        "central_count": 0,
        "ar_count": 0,
        "highest_central_game": "",
        "highest_ar_game": "",
        "oldest_game": initial_date,
        "newest_game": initial_date,
        "games_supervised": 0,
        "times_supervised": 0
        }

########################################################
# CSV Parsing and Data Collection
########################################################

try:
    with open(file_path, mode="r", encoding="utf-8") as csv_file:

        # Determine columns name (second referee collumn changed to "Referee 2" for clarity)
        fieldNames = ['Game', 'Date', 'Time', 'Field', 'Home Team', 'Away Team', 'Status', 'Referee', 'Referee 2', 'Assistant 1', 'Assistant 2', '4th Referee', 'Supervisor', 'Schedule']
        
        # Create reader, read using DictReader, and assign correct field names
        csv_reader = csv.DictReader(csv_file, fieldnames = fieldNames)

        # Skip first line of file
        next(csv_reader)

        # Loop over csv
        for row in csv_reader:

            ################## Data from CSV ##################

            # Get variables from csv
            game = row['Game'] 
            date_str = row['Date']
            ref  = row['Referee'].rstrip('✅ ')
            ar1  = row['Assistant 1'].rstrip('✅ ')
            ar2  = row['Assistant 2'].rstrip('✅ ')
            sup = row['Supervisor'].rstrip('✅ ')

            #Parse the date ONCE per row
            try:
                current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue    # Skip rows with malformed dates


            ################## Use data from CSV ##################

            # Increase total stats
            global_stats["total_games"] += 1

            # Role parsing
            roles = {"ref": ref, "ar1": ar1, "ar2": ar2}

            # Increase official stat for every positions:
            for role_key, official_name in roles.items():
                if official_name != "":
                    global_stats["total_slots"] += 1
                    global_stats["slots_by_role"][role_key] += 1
                    
                    if official_name in empty_values:
                        global_stats["missing_slots"] += 1
                        global_stats["missing_by_role"][role_key] += 1
                    else:
                        global_stats["filled_slots"] += 1
                        global_stats["filled_by_role"][role_key] += 1

            # Create new dict entry for all new officials not already in dict
            for official in [ref, ar1, ar2, sup]:
                if official not in ref_data and official not in empty_values:
                    create_official(official, current_date)
            
            # Update Count + game dates
            for role_key, official in roles.items():
                if official not in empty_values:
                    profile = ref_data[official]
                    profile["total_games"] += 1

                    # Increase supervised count if game had a supervisor
                    if sup not in empty_values:
                        profile["times_supervised"] += 1
                
                    #Update oldest and newest games
                    if current_date < profile["oldest_game"]:
                        profile["oldest_game"] = current_date
                    if current_date > profile["newest_game"]:
                        profile["newest_game"] = current_date

            # Position Specific updates
            if ref not in empty_values:
                ref_data[ref]["central_count"] += 1
                ref_data[ref]["highest_central_game"] = compare_game(ref_data[ref]["highest_central_game"], game)

            for ar in [ar1, ar2]:
                if ar not in empty_values:
                    ref_data[ar]["ar_count"] +=1
                    ref_data[ar]["highest_ar_game"] = compare_game(ref_data[ar]["highest_ar_game"], game)

            if sup in ref_data and sup not in empty_values:
                if ref_data[sup]["games_supervised"] == 0:
                    global_stats["unique_supervisors"] += 1
                global_stats["supervised_games"] += 1
                ref_data[sup]["games_supervised"] += 1

except FileNotFoundError:
    print("That file was not found")
except PermissionError:
    print("You do not have permission to read that file")


########################################################
# Writing to json
########################################################

# Final conversion of date objects back into strings for clean JSON export
for official_profile in ref_data.values():
    official_profile["oldest_game"] = official_profile.pop("oldest_game").strftime("%Y-%m-%d")
    official_profile["newest_game"] = official_profile.pop("newest_game").strftime("%Y-%m-%d")

# Convert the dictionary of dictionaries into a list of dictionaries
referee_json_list = list(ref_data.values())

# Open a new file and write the list as JSON
with open("referee_stats.json", "w", encoding="utf-8") as json_file:
    # 'indent=4' formats it nicely to read easily
    json.dump(referee_json_list, json_file, indent=4, ensure_ascii=False)

    print("Successfully saved data to referee_stats.json")


# Calculation for additional global stats
global_stats["coverage"] = (round(global_stats["filled_slots"]/global_stats["total_slots"] * 10000))/100
sum_of_all_games = 0
for official_profile in ref_data.values():
    # Grab the total games field you already calculated for this specific ref
    sum_of_all_games += official_profile["total_games"]
global_stats["avg_games"] = round(sum_of_all_games/global_stats["unique_refs"])


# Open a new file and write the list as JSON
with open("global_stats.json", "w", encoding="utf-8") as json_file:
    # 'indent=4' formats it nicely to read easily
    json.dump(global_stats, json_file, indent=4, ensure_ascii=False)

    print("Successfully saved data to global_stats.json")


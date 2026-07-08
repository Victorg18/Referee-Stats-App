import csv
import json
from datetime import datetime

########################################################
# PROGRAM CONSTANTS AND VARIABLES
########################################################

# Write Correct file path
file_path = "large_sample.csv"

# Create dictionary of dictionary to store ref info
ref_data = {}

# Create list of entries to skip
empty_values = ["", "-", " - "]

# List of games level in ascending order of difficulty to ref
levels_prefix_lvl = ["", "U9", "U10", "U11", "U12", "U13", "U14", "CDC9F", "CDC9M", "CDC10F", "CDC10M", 
                 "CDC11FD2", "CDC11FD1", "CDC11MD2", "CDC11MD1", "CDC12FD2", "CDC12FD1", "CDC12MD2", "CDC12MD1", 
                 "F13LR", "M13LR", "F13IRD2", "F13IRD1", "M13IRD2", "M13IRD1", "LSF" , "F14IV", "M14IV", "F14LR", "F14LR", "M14IR", "M14IR", 
                 "F15IV", "M15IV", "F15LR", "F15LR", "M15IR", "M15IR", "F16IV", "M16IV", "LSM"]

# List of games level in descending order of length
levels_prefix_len = sorted(levels_prefix_lvl, key=len, reverse=True)



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
            # Get variables from csv
            game = row['Game'] 
            date_str = row['Date']
            #date = datetime.strptime(row['Date'], "%Y-%m-%d").date()
            ref  = row['Referee'].rstrip('✅ ')
            ar1  = row['Assistant 1'].rstrip('✅ ')
            ar2  = row['Assistant 2'].rstrip('✅ ')
            sup = row['Supervisor'].rstrip('✅ ')


            # Create new dict entry for all new officials not already in dict
            for official in [ref, ar1, ar2]:
                if official not in ref_data and official not in empty_values:
                    ref_data[official] = {
                    "name": official,
                    "total_games": 0,
                    "central_count": 0,
                    "ar_count": 0,
                    "highest_central_game": "",
                    "highest_ar_game": "",
                    "oldest_game": date_str,
                    "newest_game": date_str,
                    "games_supervised": 0,
                    "times_supervised": 0
                    }
            
            # Create new dict entry for supervisor not already in dict
            if sup not in ref_data and sup not in empty_values:
                ref_data[sup] = {
                    "name": sup,
                    "total_games": 0,
                    "central_count": 0,
                    "ar_count": 0,
                    "highest_central_game": "",
                    "highest_ar_game": "",
                    "oldest_game": date_str,
                    "newest_game": date_str,
                    "games_supervised": 0,
                    "times_supervised": 0
                    }
                
            # Update Count + game dates
            for official in [ref, ar1, ar2]:
                if official not in empty_values:
                    ref_data[official]["total_games"] += 1

                    # Increase supervised count if game had a supervisor
                    if sup not in empty_values:
                        ref_data[official]["times_supervised"] += 1
                
                    ## Update oldest and newest games ##
                    # Convert game date in string to date object for comparaison
                    current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    # Turn strings in dict to date objects
                    saved_oldest = datetime.strptime(ref_data[official]["oldest_game"], "%Y-%m-%d").date()
                    saved_newest = datetime.strptime(ref_data[official]["newest_game"], "%Y-%m-%d").date()

                    # Check if current date is older than previous oldest date
                    if current_date < saved_oldest:
                        ref_data[official]["oldest_game"] = date_str
                
                    # Check if current date is newer than previous newest date
                    if current_date > saved_newest:
                        ref_data[official]["newest_game"] = date_str

            # Position Specific updates
            if ref not in empty_values:
                ref_data[ref]["central_count"] += 1
                ref_data[ref]["highest_central_game"] = compare_game(ref_data[ref]["highest_central_game"], game)


            for ar in [ar1, ar2]:
                if ar not in empty_values:
                    ref_data[ar]["ar_count"] +=1
                    ref_data[ar]["highest_ar_game"] = compare_game(ref_data[ar]["highest_ar_game"], game)

            if sup in ref_data and sup not in empty_values:
                ref_data[sup]["games_supervised"] += 1
except FileNotFoundError:
    print("That file was not found")
except PermissionError:
    print("You do not have permission to read that file")


# Convert the dictionary of dictionaries into a list of dictionaries
final_json_list = list(ref_data.values())

# Open a new file and write the list as JSON
with open("referee_stats.json", "w", encoding="utf-8") as json_file:
    # 'indent=4' formats it nicely to read easily
    json.dump(final_json_list, json_file, indent=4, ensure_ascii=False)

    print("Successfully saved data to referee_stats.json")


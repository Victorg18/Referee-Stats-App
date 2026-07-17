import csv
import json
from datetime import datetime

########################################################
# PROGRAM CONSTANTS AND VARIABLES
########################################################

# Write Correct file path
file_path = "large_sample.csv"

# List of day of the week
weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Create list of entries to skip
empty_values = ["", "-", " - "]

# List of games level in ascending order of difficulty to ref
levels_prefix_lvl = ["", "U9", "U10", "U11", "U12", "U13", "U14", "CDC9F", "CDC9M", "CDC10F", "CDC10M", 
                 "CDC11FD2", "CDC11FD1", "CDC11MD2", "CDC11MD1", "CDC12FD2", "CDC12FD1", "CDC12MD2", "CDC12MD1", 
                 "F13LR", "M13LR", "F13IRD2", "F13IRD1", "M13IRD2", "M13IRD1", "LSF" , "F14IV", "M14IV", "F14LR", "M14LR", "F14IR", "M14IR", 
                 "F15IV", "M15IV", "F15LR", "M15LR", "F15IR", "M15IR", "F16IV", "M16IV", "LSM"]

# List of games level in descending order of length
levels_prefix_len = sorted(levels_prefix_lvl, key=len, reverse=True)

# Global info trackers
field_distribution = {}
crew_pairings = {} # Key: "Name A & Name B", Value: Count
games_by_date = {}  # Key: "2026-05-02", Value: Count
total_games_per_weekday = {day: 0 for day in weekday_names}
unique_dates_per_weekday = {day: set() for day in weekday_names} # Uses a set to count unique calendar dates

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
    "slots_by_role": {
        "ref": 0,
        "ar1": 0,
        "ar2": 0,
        "ref2": 0,
        "ref4": 0
    },
    "filled_by_role": {
        "ref": 0,
        "ar1": 0,
        "ar2": 0,
        "ref2": 0,
        "ref4": 0
    },
    "missing_by_role": {
        "ref": 0,
        "ar1": 0,
        "ar2": 0,
        "ref2": 0,
        "ref4": 0
    }
}

########################################################
# HELPER FUNCTIONS
########################################################

# Helper function to get level prefix of a game
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

# Helper function to compare the levels of two games and return highest game
def compare_game(game1, game2):
    """Compare the level of two games and return the highest level one"""  
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
    
# Helper function to create new official dict
def create_official(official, initial_date):
    """Create a new dict for official not registered yet"""
    global_stats["unique_refs"] += 1
    ref_data[official] = {
        "name": official,
        "total_games": 0,
        "central_count": 0,
        "ar_count": 0,
        "4th_ref_count": 0,
        "highest_central_game": "",
        "highest_ar_game": "",
        "oldest_game": initial_date,
        "newest_game": initial_date,
        "games_supervised": 0,
        "times_supervised": 0
        }

# Helper function to clean up field names
def get_location_name(field_str):
    """Groups specific field names into their main park/location names."""
    if not field_str or field_str in empty_values:
        return "Unknown/TBA"
        
    location = field_str
    
    # Clean up "Dôme Centre Multisport" variations
    if "Dôme Centre Multisport" in location:
        return "Dôme Centre Multisport"
        
    # Remove common trailing field identifiers like " - 1", " - 2", " - A", " - B", " - Synthétique"
    suffixes_to_strip = [" - 1", " - 2", " - 3", " - A", " - B", " - C", " - Synthétique", " (SYNTH)"]
    for suffix in suffixes_to_strip:
        if location.endswith(suffix):
            location = location.replace(suffix, "")  
    return location.strip()

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
            ref1 = row['Referee'].rstrip('✅ ')
            ref2 = row['Referee 2'].rstrip('✅ ')
            ar1  = row['Assistant 1'].rstrip('✅ ')
            ar2  = row['Assistant 2'].rstrip('✅ ')
            ref4 = row['4th Referee'].rstrip('✅ ')
            sup = row['Supervisor'].rstrip('✅ ')


            # Parse the date once per row
            try:
                current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue    # Skip rows with malformed dates


            ################## Use data from CSV ##################

            # Increase total stats
            global_stats["total_games"] += 1

            # Role parsing
            roles = {"ref": ref1, "ref2": ref2, "ar1": ar1, "ar2": ar2, "ref4": ref4}

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
            for official in [ref1, ref2, ar1, ar2, ref4, sup]:
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
            for ref in [ref1, ref2]:
                if ref not in empty_values:
                    ref_data[ref]["central_count"] += 1
                    ref_data[ref]["highest_central_game"] = compare_game(ref_data[ref]["highest_central_game"], game)
            for ar in [ar1, ar2]:
                if ar not in empty_values:
                    ref_data[ar]["ar_count"] +=1
                    ref_data[ar]["highest_ar_game"] = compare_game(ref_data[ar]["highest_ar_game"], game)
            if ref4 not in empty_values:
                ref_data[ref4]["4th_ref_count"] +1
            if sup in ref_data and sup not in empty_values:
                if ref_data[sup]["games_supervised"] == 0:
                    global_stats["unique_supervisors"] += 1
                global_stats["supervised_games"] += 1
                ref_data[sup]["games_supervised"] += 1

            #
            # Additional global info
            #

            location_name = get_location_name(row['Field'])

            # Tally fields
            if location_name not in ["Edouard VII", "TBA", ""]:
                field_distribution[location_name] = field_distribution.get(location_name, 0) + 1

            # Create a list of active on-field officials for this game
            current_crew = [ref1, ar1, ar2]
            # Filter out empty values so we only look at actual people
            active_crew = [name for name in current_crew if name not in empty_values]

            # We need at least 2 people to make a pairing
            if len(active_crew) >= 2:
                # Loop through the crew to find every unique combination of pairs
                for i in range(len(active_crew)):
                    for j in range(i + 1, len(active_crew)):
                        person1 = active_crew[i]
                        person2 = active_crew[j]
                        
                        # Sort alphabetically so the pairing key is always identical
                        sorted_pair = sorted([person1, person2])
                        pair_key = f"{sorted_pair[0]} & {sorted_pair[1]}"
                        
                        # Increment the pairing count
                        crew_pairings[pair_key] = crew_pairings.get(pair_key, 0) + 1
            
            # Track total games per individual calendar date
            games_by_date[date_str] = games_by_date.get(date_str, 0) + 1

except FileNotFoundError:
    print("That file was not found")
except PermissionError:
    print("You do not have permission to read that file")

########################################################
# Additional CAlculation and parsing for json conversion
########################################################

################## Official Stats ##################

# Final conversion of date objects back into strings for clean JSON export
for official_profile in ref_data.values():
    official_profile["oldest_game"] = official_profile.pop("oldest_game").strftime("%Y-%m-%d")
    official_profile["newest_game"] = official_profile.pop("newest_game").strftime("%Y-%m-%d")

# Convert the dictionary of dictionaries into a list of dictionaries
referee_json_list = list(ref_data.values())

################## Global Stats ##################

# Calculate and add coverage percentage
if global_stats["total_slots"] > 0:
    global_stats["coverage"] = ((round(global_stats["filled_slots"]/global_stats["total_slots"] * 10000))/100)

# Get sum of all games
sum_of_all_games = 0
for official_profile in ref_data.values():
    # Grab the total games field you already calculated for this specific ref
    sum_of_all_games += official_profile["total_games"]

# Calculate the average number of games per referee
if global_stats["unique_refs"] > 0:
    global_stats["avg_games"] = round(sum_of_all_games/global_stats["unique_refs"])

# Add previously calculated field distribution to the dict:
global_stats["field distribution"] = dict(sorted(field_distribution.items(), key=lambda x: x[1], reverse=True))

# Filter out days with less than 3 games
big_days = {date: count for date, count in games_by_date.items() if count > 3}
sorted_days = dict(sorted(big_days.items(), key=lambda item: item[1], reverse=True))

# Get total games per weekday
for specific_date_str, game_count in games_by_date.items():
    # Convert string back to a date object to find the weekday
    date_obj = datetime.strptime(specific_date_str, "%Y-%m-%d").date()
    weekday_name = weekday_names[date_obj.weekday()] # 0 = Monday, 6 = Sunday
    
    total_games_per_weekday[weekday_name] += game_count
    unique_dates_per_weekday[weekday_name].add(specific_date_str)

# Calculate averages and find the busiest day
weekday_averages = {}
busiest_day_name = ""
max_total_games = -1

for day in weekday_names:
    total_games = total_games_per_weekday[day]
    unique_day_count = len(unique_dates_per_weekday[day])
    
    # Calculate average
    if global_stats["total_slots"] > 0:
        weekday_averages[day] = round(total_games / unique_day_count, 0)
    else:
        weekday_averages[day] = 0
    weekday_averages[day] = int(weekday_averages[day])
    
    # Track which day had the absolute highest total workload overall
    if total_games > max_total_games:
        max_total_games = total_games
        busiest_day_name = day

# Add previously calculated day stats to global dict
global_stats["busiest_day_of_week"] = busiest_day_name
global_stats["total_games_by_weekday"] = total_games_per_weekday
global_stats["average_games_by_weekday"] = weekday_averages


################## Official Pairings ##################

# Filter out pairings that have 2 or fewer games together
frequent_pairings = {pair: count for pair, count in crew_pairings.items() if count > 2}

# Sort the filtered pairings from most frequent to least frequent
sorted_pairings = dict(sorted(frequent_pairings.items(), key=lambda item: item[1], reverse=True))

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

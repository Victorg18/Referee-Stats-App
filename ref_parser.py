import csv
from collections import Counter

# Write Correct file path
file_path = "small_sample.csv"

# Create empty counters for referee positions
ref_counts = Counter()
ar_counts = Counter()
total_counts = Counter()


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
            date = row['Date']
            ref  = row['Referee'].rstrip('✅ ')
            ar1  = row['Assistant 1'].rstrip('✅ ')
            ar2  = row['Assistant 2'].rstrip('✅ ')
            sup = row['Supervisor'].rstrip('✅ ')

            # Add to ref positions count
            if ref:
                ref_counts[ref] += 1
                total_counts[ref] += 1
            if ar1:
                ar_counts[ar1] += 1
                total_counts[ar1] += 1
            if ar2:
                ar_counts[ar2] += 1
                total_counts[ar2] += 1

            # Print parsed csv
            #print(f"Game: {game:<8} | Time: {date:<12} | Ref: {ref:<35} | AR1: {ar1:<35} | AR2: {ar2:<35}")

        #for ref, count in ref_counts.items():
            #print(f"{ref}: {count}")
        #for ar, count in ar_counts.items():
            #print(f"{ar}: {count}")

        # Print total number of ref that had games
        unique_ref_count = len(total_counts)
        print(f"Total number of different officials: {unique_ref_count - 1}")
        print("-" * 45)

        # Print total number of matches per ref
        print(f"{'Official Name':<25} | {'Total Games':<10}")
        for official, count in total_counts.most_common():
            print(f"{official:<35} | {count:<10}")





















except FileNotFoundError:
    print("That file was not found")
except PermissionError:
    print("You do not have permission to read that file")

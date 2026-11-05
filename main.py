"""Entry point: prompts for a CSV file, then runs parse -> analyze -> export."""

import sys
from pathlib import Path

from src.analyzer import analyze
from src.constants import DATA_DIR
from src.exporter import export_results
from src.parser import load_assignments


def prompt_for_csv(data_dir=DATA_DIR):
    """Ask the user for a filename and return the full, validated Path.

    Exits the program if the file can't be found.
    """
    data_dir = Path(data_dir)

    filename = input(
        "Enter the CSV filename to analyze (e.g., last_year.csv): "
    ).strip()

    # Clean up quotes if dragged & dropped
    filename_clean = filename.strip("\"'")

    # Automatically append .csv if the user didn't type it
    if not filename_clean.lower().endswith(".csv"):
        filename_clean += ".csv"

    file_path = data_dir / filename_clean

    if not file_path.is_file():
        print(
            f"Error: Could not find '{file_path}'. Please make sure the "
            f"file exists inside the '{data_dir}' folder."
        )
        sys.exit(1)

    return file_path


def main():
    file_path = prompt_for_csv()

    # Load and clean the data
    try:
        df = load_assignments(file_path)
    except FileNotFoundError:
        print("That file was not found")
        sys.exit(1)
    except PermissionError:
        print("You do not have permission to read that file")
        sys.exit(1)

    if df.empty:
        print("No valid games were found in that file. Nothing to analyze.")
        sys.exit(1)

    # Analyze, then write the results
    results = analyze(df)
    export_results(results)


if __name__ == "__main__":
    main()
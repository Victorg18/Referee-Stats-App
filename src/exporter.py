"""Handles directory creation and writing outputs to JSON/CSV."""

import json
from pathlib import Path

import pandas as pd

from .constants import MIN_PAIRING_GAMES, OUTPUT_DIR


########################################################
# HELPER FUNCTIONS
########################################################


def _create_output_dir(output_dir=OUTPUT_DIR):
    """Create the results directory if it doesn't exist and return its Path."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(data, file_path):
    """Write data to a JSON file (UTF-8, indented, accents preserved)."""
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)


########################################################
# PUBLIC API
########################################################


def export_results(results, output_dir=OUTPUT_DIR):
    """Write all analysis results to JSON and CSV files.

    Args:
        results: dict returned by analyzer.analyze(), with the keys
            "referees", "global_stats", "pairings", and "ref_list".
        output_dir: folder to write the files into (created if missing).

    Returns:
        The Path of the output directory.
    """
    out = _create_output_dir(output_dir)

    # Referee stats JSON
    _write_json(results["referees"], out / "referee_stats.json")
    print(f"Successfully saved data to {out}/referee_stats.json")

    # Global stats JSON
    _write_json(results["global_stats"], out / "global_stats.json")
    print(f"Successfully saved data to {out}/global_stats.json")

    # Crew pairings JSON
    _write_json(results["pairings"], out / "crew_pairings.json")
    print(
        f"Successfully saved data to {out}/crew_pairings.json "
        f"(Filtered: > {MIN_PAIRING_GAMES} games)"
    )

    # Referee list CSV
    pd.DataFrame(results["ref_list"]).to_csv(
        out / "ref_list.csv", index=False, encoding="utf-8"
    )
    print(f"Successfully saved list of referees to {out}/ref_list.csv")

    return out
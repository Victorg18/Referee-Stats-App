"""CSV loading, pandas data cleaning, and date filtering."""

from pathlib import Path

import pandas as pd

from .constants import (
    CREW_COLS,
    DATE_FORMAT,
    DOME_LOCATION,
    EMPTY_VALUES,
    FIELD_NAMES,
    FIELD_SUFFIXES_TO_STRIP,
    LEVELS_PREFIX_LEN,
    LEVELS_PREFIX_LVL,
    ROLE_COLS,
    STATUS_SYMBOLS,
    UNKNOWN_LOCATION,
)

# Every column that can hold a person's name
OFFICIAL_COLS = list(ROLE_COLS.values()) + ["Supervisor"]


########################################################
# HELPER FUNCTIONS
########################################################


def get_prefix(game_str):
    """Find which level prefix the game string starts with.

    Iterates through the prefixes from longest to shortest so the longest
    matching prefix wins.
    """
    if not isinstance(game_str, str):
        return ""
    for prefix in LEVELS_PREFIX_LEN:
        if prefix and game_str.startswith(prefix):
            return prefix
    return ""  # Default backup if nothing matches


def get_location_name(field_str):
    """Group specific field names into their main park/location names."""
    if not field_str or field_str in EMPTY_VALUES or pd.isna(field_str):
        return UNKNOWN_LOCATION

    location = str(field_str)

    # Clean up "Dôme Centre Multisport" variations
    if DOME_LOCATION in location:
        return DOME_LOCATION

    # Remove trailing field identifiers like " - 1", " - A", " - Synthétique"
    for suffix in FIELD_SUFFIXES_TO_STRIP:
        if location.endswith(suffix):
            location = location.replace(suffix, "")
    return location.strip()


########################################################
# CLEANING STEPS
########################################################


def _read_csv(file_path):
    """Read the raw CSV, skipping the first row and assigning column names."""
    return pd.read_csv(
        file_path,
        skiprows=1,
        names=FIELD_NAMES,
        header=None,
        dtype=str,
        encoding="utf-8",
    )


def _filter_valid_dates(df):
    """Parse the Date column and drop rows with an invalid date."""
    df["Date_Parsed"] = pd.to_datetime(
        df["Date"], format=DATE_FORMAT, errors="coerce"
    )
    return df.dropna(subset=["Date_Parsed"]).copy()


def _clean_official_columns(df):
    """Strip status symbols and whitespace from all role columns."""
    for col in OFFICIAL_COLS:
        cleaned = df[col].fillna("").astype(str)
        for symbol in STATUS_SYMBOLS:
            cleaned = cleaned.str.replace(symbol, "", regex=False)
        df[col] = cleaned.str.strip()
    return df


def _drop_cancelled_games(df):
    """Remove games where every referee/supervisor slot is empty."""
    has_any_referee = ~df[OFFICIAL_COLS].isin(EMPTY_VALUES).all(axis=1)
    return df[has_any_referee].copy()


def _add_game_levels(df):
    """Add the level prefix and an ordered rank for fast comparisons."""
    df["Prefix"] = df["Game"].apply(get_prefix)
    prefix_dtype = pd.CategoricalDtype(
        categories=LEVELS_PREFIX_LVL, ordered=True
    )
    df["Prefix_Rank"] = df["Prefix"].astype(prefix_dtype)
    return df


def _add_locations(df):
    """Add a Clean_Location column grouping fields into main parks."""
    df["Clean_Location"] = df["Field"].apply(get_location_name)
    return df


########################################################
# PUBLIC API
########################################################


def load_assignments(file_path):
    """Load and clean an assignment CSV.

    Args:
        file_path: Path (or str) to the CSV file.

    Returns:
        A cleaned DataFrame with extra columns: Date_Parsed, Prefix,
        Prefix_Rank, and Clean_Location.

    Raises:
        FileNotFoundError: if the file does not exist.
        PermissionError: if the file cannot be read.
    """
    df = _read_csv(Path(file_path))
    df = _filter_valid_dates(df)
    df = _clean_official_columns(df)
    df = _drop_cancelled_games(df)
    df = _add_game_levels(df)
    df = _add_locations(df)
    return df
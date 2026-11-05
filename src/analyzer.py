"""Computes global stats, referee profiles, averages, and crew pairings."""

import itertools

import pandas as pd

from .constants import (
    CREW_COLS,
    EMPTY_VALUES,
    EXCLUDED_LOCATIONS,
    MIN_PAIRING_GAMES,
    ROLE_COLS,
    WEEKDAY_NAMES,
)
from .parser import OFFICIAL_COLS

# Key order used in the role breakdowns of the global stats JSON
ROLE_KEY_ORDER = ["ref1", "ar1", "ar2", "ref2", "ref4"]


########################################################
# GLOBAL STATS TEMPLATE
########################################################


def _new_global_stats():
    """Return a fresh global stats dictionary."""
    return {
        "total_games": 0,
        "total_slots": 0,
        "filled_slots": 0,
        "missing_slots": 0,
        "coverage": "",
        "supervised_games": 0,
        "unique_refs": 0,
        "avg_games": 0,
        "unique_supervisors": 0,
        "slots_by_role": {key: 0 for key in ROLE_KEY_ORDER},
        "filled_by_role": {key: 0 for key in ROLE_KEY_ORDER},
        "missing_by_role": {key: 0 for key in ROLE_KEY_ORDER},
    }


########################################################
# SLOT COUNTS
########################################################


def _compute_slot_stats(df, global_stats):
    """Fill in total/filled/missing slot counts, overall and by role."""
    global_stats["total_games"] = len(df)

    for role_key, col in ROLE_COLS.items():
        series = df[col]
        # Total slots defined as non-empty in the original CSV
        non_empty_mask = series != ""
        filled_mask = ~series.isin(EMPTY_VALUES)

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

    # Coverage percentage (two decimals)
    if global_stats["total_slots"] > 0:
        global_stats["coverage"] = (
            round(
                global_stats["filled_slots"]
                / global_stats["total_slots"]
                * 10000
            )
        ) / 100


########################################################
# REFEREE PROFILES
########################################################


def _highest_game(df, mask):
    """Return the highest-level game name among rows matching the mask."""
    if not mask.any():
        return ""
    sub_df = df.loc[mask, ["Game", "Prefix_Rank"]]
    sorted_df = sub_df.sort_values(by=["Prefix_Rank"], ascending=[False])
    return str(sorted_df["Game"].iloc[0])


def _split_name(official):
    """Split a full name into first name and family name."""
    if " " in official:
        first_name, family_name = official.split(" ", 1)
    else:
        first_name, family_name = official, ""
    return first_name, family_name


def _build_referee_profiles(df) -> tuple[dict, list]:
    """Build a profile for every official found in the data, sorted alphabetically.

    Returns:
        ref_data: dict of {name: profile dict}
        ref_list: list of {"First Name", "Last Name"} dicts for CSV output
    """
    ref_data = {}
    ref_list = []

    # Collect all unique officials and sort them alphabetically by name
    all_officials_series = pd.concat([df[c] for c in OFFICIAL_COLS])
    unique_officials = sorted(
        list(set(all_officials_series[~all_officials_series.isin(EMPTY_VALUES)].unique()))
    )

    has_sup_mask = ~df["Supervisor"].isin(EMPTY_VALUES)

    for official in unique_officials:
        # Match where the official worked in any role
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

        # Date range (includes supervised games)
        working_dates = df.loc[all_worked_mask | c_sup, "Date_Parsed"]

        ref_data[official] = {
            "name": official,
            "total_games": int(all_worked_mask.sum()),
            "central_count": int(central_mask.sum()),
            "ar_count": int(ar_mask.sum()),
            "4th_ref_count": int(ref4_mask.sum()),
            "highest_central_game": _highest_game(df, central_mask),
            "highest_ar_game": _highest_game(df, ar_mask),
            "oldest_game": str(working_dates.min())[:10],
            "newest_game": str(working_dates.max())[:10],
            "games_supervised": int(c_sup.sum()),
            # Games worked as a referee/AR/4th that had a supervisor present
            "times_supervised": int((all_worked_mask & has_sup_mask).sum()),
        }

        first_name, family_name = _split_name(official)
        ref_list.append({"First Name": first_name, "Last Name": family_name})

    # Ensure ref_list is also sorted alphabetically by First Name (or Last Name if preferred)
    ref_list = sorted(ref_list, key=lambda x: (x["First Name"], x["Last Name"]))

    return ref_data, ref_list


########################################################
# FIELD DISTRIBUTION AND PAIRINGS
########################################################


def _compute_field_distribution(df):
    """Count games per location, sorted from most to least games."""
    field_counts = df[~df["Clean_Location"].isin(EXCLUDED_LOCATIONS)][
        "Clean_Location"
    ].value_counts()
    return dict(
        sorted(field_counts.to_dict().items(), key=lambda x: x[1], reverse=True)
    )


def _compute_crew_pairings(df):
    """Count how many games each pair of officials worked together.

    Only pairings with more than MIN_PAIRING_GAMES games are kept,
    sorted from most to least frequent.
    """
    crew_pairings = {}

    for _, row in df[CREW_COLS].iterrows():
        active_crew = [
            name for name in row.values if name and name not in EMPTY_VALUES
        ]
        if len(active_crew) >= 2:
            for pair in itertools.combinations(sorted(active_crew), 2):
                pair_key = f"{pair[0]} & {pair[1]}"
                crew_pairings[pair_key] = crew_pairings.get(pair_key, 0) + 1

    frequent_pairings = {
        pair: count
        for pair, count in crew_pairings.items()
        if count > MIN_PAIRING_GAMES
    }
    return dict(
        sorted(frequent_pairings.items(), key=lambda item: item[1], reverse=True)
    )


########################################################
# WEEKDAY STATS
########################################################


def _compute_weekday_stats(df):
    """Compute total/average games per weekday and the busiest day."""
    if not df.empty:
        weekdays = df["Date_Parsed"].dt.day_name()
        weekday_totals = weekdays.value_counts().to_dict()

        # Total weeks between first and last game (inclusive of both days)
        min_date = df["Date_Parsed"].min()
        max_date = df["Date_Parsed"].max()
        total_days = (max_date - min_date).days + 1
        total_weeks = max(total_days / 7.0, 1.0)  # Avoid division by zero
    else:
        weekday_totals = {}
        total_weeks = 1.0

    total_games_per_weekday = {}
    weekday_averages = {}
    busiest_day_name = ""
    max_total_games = -1

    for day in WEEKDAY_NAMES:
        total_games = weekday_totals.get(day, 0)
        total_games_per_weekday[day] = total_games

        # Divide total games on this weekday by total weeks in the span
        weekday_averages[day] = int(round(total_games / total_weeks))

        if total_games > max_total_games:
            max_total_games = total_games
            busiest_day_name = day

    return busiest_day_name, total_games_per_weekday, weekday_averages


########################################################
# PUBLIC API
########################################################


def analyze(df):
    """Run every analysis on the cleaned DataFrame.

    Args:
        df: DataFrame returned by parser.load_assignments().

    Returns:
        A dict with:
            "referees":      list of referee profile dicts
            "global_stats":  global statistics dict
            "pairings":      filtered, sorted crew pairings dict
            "ref_list":      list of {"First Name", "Last Name"} dicts
    """
    global_stats = _new_global_stats()

    # Slots and coverage
    _compute_slot_stats(df, global_stats)

    # Individual referee profiles
    ref_data, ref_list = _build_referee_profiles(df)

    global_stats["unique_refs"] = len(ref_data)
    global_stats["unique_supervisors"] = sum(
        1 for v in ref_data.values() if v["games_supervised"] > 0
    )
    global_stats["supervised_games"] = int(
        (~df["Supervisor"].isin(EMPTY_VALUES)).sum()
    )

    # Average games per referee
    if global_stats["unique_refs"] > 0:
        sum_of_all_games = sum(p["total_games"] for p in ref_data.values())
        global_stats["avg_games"] = round(
            sum_of_all_games / global_stats["unique_refs"]
        )

    # Field distribution
    global_stats["field distribution"] = _compute_field_distribution(df)

    # Weekday stats
    busiest_day, totals_by_day, averages_by_day = _compute_weekday_stats(df)
    global_stats["busiest_day_of_week"] = busiest_day
    global_stats["total_games_by_weekday"] = totals_by_day
    global_stats["average_games_by_weekday"] = averages_by_day

    return {
        "referees": list(ref_data.values()),
        "global_stats": global_stats,
        "pairings": _compute_crew_pairings(df),
        "ref_list": ref_list,
    }
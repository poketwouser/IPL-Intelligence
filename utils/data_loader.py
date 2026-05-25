"""Centralized data loader using Parquet files with caching."""
import os
import pandas as pd
import functools

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@functools.lru_cache(maxsize=1)
def load_data():
    """Load all datasets from parquet files. Returns dict of DataFrames."""
    processed = os.path.join(DATA_DIR, "processed")
    cleaned = os.path.join(DATA_DIR, "cleaned")

    # Load matches — prefer imputed parquet
    matches_path = os.path.join(processed, "matches_imputed.parquet")
    if not os.path.exists(matches_path):
        matches_path = os.path.join(processed, "matches.parquet")
    if not os.path.exists(matches_path):
        matches_path = os.path.join(cleaned, "matches.csv")
        matches = pd.read_csv(matches_path)
    else:
        matches = pd.read_parquet(matches_path)

    # Load deliveries
    del_path = os.path.join(processed, "deliveries.parquet")
    if not os.path.exists(del_path):
        del_path = os.path.join(cleaned, "deliveries.csv")
        deliveries = pd.read_csv(del_path)
    else:
        deliveries = pd.read_parquet(del_path)

    # Load venue coordinates
    venue_path = os.path.join(cleaned, "venue_coords.csv")
    venues = pd.read_csv(venue_path) if os.path.exists(venue_path) else pd.DataFrame()

    # ─── Normalize columns ────────────────────────────────────────────────────
    # Ensure consistent column names (parquet might have different naming)
    # Standard: Id, Season, Team1, Team2, Winner, etc. for matches
    # Standard: Match_Id, Inning, Batting_Team, Bowling_Team, Over, Ball, Batter, Bowler, etc.

    # Normalize Season to int
    if "Season" in matches.columns:
        matches["Season"] = pd.to_numeric(matches["Season"], errors="coerce").astype("Int64")
    if "Id" in matches.columns:
        matches["Id"] = pd.to_numeric(matches["Id"], errors="coerce")
    if "Match_Id" in deliveries.columns:
        deliveries["Match_Id"] = pd.to_numeric(deliveries["Match_Id"], errors="coerce")
    if "Over" in deliveries.columns:
        deliveries["Over"] = pd.to_numeric(deliveries["Over"], errors="coerce").fillna(0).astype(int)
    if "Date" in matches.columns:
        matches["Date"] = pd.to_datetime(matches["Date"], errors="coerce")

    # Build season map for deliveries
    if "Id" in matches.columns and "Season" in matches.columns:
        season_map = matches.set_index("Id")["Season"].to_dict()
        deliveries["Season"] = deliveries["Match_Id"].map(season_map)

    # Normalize venues to match venue_coords.csv
    if "Venue" in matches.columns:
        venue_mapping = {
            "Ma Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium",
            "Ma Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium",
            "Ma Chidambaram Stadium": "MA Chidambaram Stadium",
            "Dr Dy Patil Sports Academy, Mumbai": "Dr DY Patil Sports Academy",
            "Dr Dy Patil Sports Academy": "Dr DY Patil Sports Academy",
            "Dr. Y.S. Rajasekhara Reddy Aca-Vdca Cricket Stadium": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
            "Dr. Y.S. Rajasekhara Reddy Aca-Vdca Cricket Stadium, Visakhapatnam": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
            "Supersport Park": "SuperSport Park",
            "St George'S Park": "St George's Park",
            "Punjab Cricket Association Is Bindra Stadium, Mohali": "Punjab Cricket Association IS Bindra Stadium",
            "Punjab Cricket Association Is Bindra Stadium": "Punjab Cricket Association IS Bindra Stadium",
            "Punjab Cricket Association Is Bindra Stadium, Mohali, Chandigarh": "Punjab Cricket Association IS Bindra Stadium",
            "Jsca International Stadium Complex": "JSCA International Stadium Complex",
            "Outsurance Oval": "OUTsurance Oval",
        }
        matches["Venue"] = matches["Venue"].replace(venue_mapping)

    def fix_initials(name):
        if not isinstance(name, str):
            return name
        parts = name.split()
        if len(parts) > 1 and len(parts[0]) in [2, 3] and parts[0].isalpha():
            if parts[0][0].isupper() and parts[0][1:].islower():
                parts[0] = parts[0].upper()
        return " ".join(parts)

    for col in ["Venue", "Player_Of_Match"]:
        if col in matches.columns:
            matches[col] = matches[col].apply(fix_initials)

    for col in ["Batter", "Bowler", "Non_Striker", "Player_Dismissed"]:
        if col in deliveries.columns:
            deliveries[col] = deliveries[col].apply(fix_initials)

    impact_path = os.path.join(processed, "impact_players.parquet")
    if os.path.exists(impact_path):
        impact_players = pd.read_parquet(impact_path)
    else:
        impact_players = pd.DataFrame()

    return {
        "matches": matches,
        "deliveries": deliveries,
        "venues": venues,
        "impact_players": impact_players,
    }


def get_matches():
    return load_data()["matches"]

def get_deliveries():
    return load_data()["deliveries"]

def get_venues():
    return load_data()["venues"]

def get_team_list(matches=None):
    """Get sorted unique list of teams from matches."""
    if matches is None:
        matches = get_matches()
    teams = set()
    for col in ["Team1", "Team2"]:
        if col in matches.columns:
            teams.update(matches[col].dropna().unique())
    invalid = {"No Result", "No Toss", " ", "", "nan"}
    return sorted([t for t in teams if t not in invalid])

def get_player_list(deliveries=None):
    """Get sorted unique list of players."""
    if deliveries is None:
        deliveries = get_deliveries()
    players = set()
    if "Batter" in deliveries.columns:
        players.update(deliveries["Batter"].dropna().unique())
    if "Bowler" in deliveries.columns:
        players.update(deliveries["Bowler"].dropna().unique())
    return sorted(players)

def get_season_range(matches=None):
    """Get (min_season, max_season) tuple."""
    if matches is None:
        matches = get_matches()
    seasons = matches["Season"].dropna()
    return int(seasons.min()), int(seasons.max())

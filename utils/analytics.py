"""
Cricket analytics engine — all statistical computations.
Ported from notebooks P06, P07, P08, P09 with corrections.
"""
import pandas as pd
import numpy as np
from utils.constants import NON_BOWLER_DISMISSALS, INVALID_BALL_EXTRAS


# ─── Valid Ball Filter ────────────────────────────────────────────────────────
def valid_ball_mask(df):
    """Returns boolean mask for valid deliveries (excluding wides/no-balls)."""
    if "Extras_Type" not in df.columns:
        return pd.Series(True, index=df.index)
    return ~df["Extras_Type"].isin(INVALID_BALL_EXTRAS)


def is_bowler_wicket(df):
    """Returns boolean mask for wickets credited to the bowler."""
    mask = (df["Is_Wicket"] == 1) & (df["Player_Dismissed"].notna())
    if "Dismissal_Kind" in df.columns:
        mask = mask & (~df["Dismissal_Kind"].isin(NON_BOWLER_DISMISSALS))
    return mask


# ─── Role Detection ──────────────────────────────────────────────────────────
def classify_player_role(player, deliveries):
    """
    Classify a player as Batter, Bowler, All-rounder, or WK-Batter.
    Based on batting/bowling contribution ratios.
    """
    bat_balls = len(deliveries[(deliveries["Batter"] == player) & valid_ball_mask(deliveries)])
    bowl_balls = len(deliveries[(deliveries["Bowler"] == player) & valid_ball_mask(deliveries)])

    if bat_balls == 0 and bowl_balls == 0:
        return "Unknown"

    total = bat_balls + bowl_balls
    bat_pct = bat_balls / total if total else 0
    bowl_pct = bowl_balls / total if total else 0

    # Count bowler wickets and batting runs for secondary classification
    bowl_df = deliveries[deliveries["Bowler"] == player]
    bowler_wkts = is_bowler_wicket(bowl_df).sum()

    bat_df = deliveries[(deliveries["Batter"] == player) & valid_ball_mask(deliveries)]
    bat_runs = int(bat_df["Batsman_Runs"].sum()) if not bat_df.empty else 0

    # Heuristic thresholds
    if bowl_balls < 30 and bowler_wkts < 3:
        return "Batter"
    if bat_balls < 30:
        return "Bowler"

    # Even if bowling dominates by ball count, players with significant batting
    # contributions (500+ runs AND 50+ innings) are All-rounders
    bat_innings = bat_df["Match_Id"].nunique() if not bat_df.empty else 0
    if bowl_pct > 0.65 and bat_runs >= 500 and bat_innings >= 30:
        return "All-rounder"
    # Bowling all-rounders: significant wickets even though they bat more
    if bat_pct > 0.65 and bowler_wkts >= 30:
        return "All-rounder"

    if bat_pct > 0.65:
        return "Batter"
    if bowl_pct > 0.65:
        return "Bowler"
    return "All-rounder"


# ─── Batting Summary ─────────────────────────────────────────────────────────
def batting_summary(player, deliveries):
    """Compute comprehensive batting stats for a player."""
    bat_del = deliveries[deliveries["Batter"] == player]
    if bat_del.empty:
        return {"innings": 0, "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
                "sr": 0, "boundary_pct": 0, "average": 0, "high_score": 0,
                "fifties": 0, "hundreds": 0}

    valid = bat_del[valid_ball_mask(bat_del)]
    runs = int(valid["Batsman_Runs"].sum())
    balls = len(valid)
    fours = int((valid["Batsman_Runs"] == 4).sum())
    sixes = int((valid["Batsman_Runs"] == 6).sum())
    innings = bat_del["Match_Id"].nunique()

    # Per-innings scores
    match_runs = valid.groupby("Match_Id")["Batsman_Runs"].sum()
    scores = match_runs.values
    high_score = int(scores.max()) if len(scores) else 0
    fifties = int((scores >= 50).sum())
    hundreds = int((scores >= 100).sum())

    # Dismissals
    dismissals = len(bat_del[(bat_del["Is_Wicket"] == 1) & (bat_del["Player_Dismissed"] == player)])
    average = round(runs / dismissals, 2) if dismissals else runs

    return {
        "innings": innings, "runs": runs, "balls": balls, "fours": fours, "sixes": sixes,
        "sr": round(runs / balls * 100, 1) if balls else 0,
        "boundary_pct": round((fours + sixes) / balls * 100, 1) if balls else 0,
        "average": average, "high_score": high_score,
        "fifties": fifties, "hundreds": hundreds,
    }


# ─── Bowling Summary ─────────────────────────────────────────────────────────
def bowling_summary(player, deliveries):
    """Compute comprehensive bowling stats for a player."""
    bowl_del = deliveries[deliveries["Bowler"] == player]
    if bowl_del.empty:
        return {"innings": 0, "wickets": 0, "economy": 0, "sr": "-",
                "dot_pct": 0, "runs_conceded": 0, "best": "-"}

    valid = bowl_del[valid_ball_mask(bowl_del)]
    balls = len(valid)
    runs_conceded = int(valid["Total_Runs"].sum())
    wkts = int(is_bowler_wicket(bowl_del).sum())
    dots = int((valid["Total_Runs"] == 0).sum())
    innings = bowl_del["Match_Id"].nunique()

    # Best figures per match
    wkt_per_match = bowl_del[is_bowler_wicket(bowl_del)].groupby("Match_Id").size()
    best_w = int(wkt_per_match.max()) if not wkt_per_match.empty else 0

    overs = balls / 6
    return {
        "innings": innings, "wickets": wkts,
        "economy": round(runs_conceded / overs, 2) if overs else 0,
        "sr": round(balls / wkts, 1) if wkts else "-",
        "dot_pct": round(dots / balls * 100, 1) if balls else 0,
        "runs_conceded": runs_conceded,
        "best": f"{best_w}/" + str(0),
    }


# ─── Season-wise Player Stats (CORRECTED FORM) ──────────────────────────────
def player_season_batting(player, deliveries):
    """Season-wise batting metrics (corrected form analysis)."""
    bat = deliveries[deliveries["Batter"] == player].copy()
    if bat.empty or "Season" not in bat.columns:
        return pd.DataFrame()

    valid = bat[valid_ball_mask(bat)]
    season_stats = valid.groupby("Season").agg(
        runs=("Batsman_Runs", "sum"),
        balls=("Batsman_Runs", "count"),
        fours=("Batsman_Runs", lambda x: (x == 4).sum()),
        sixes=("Batsman_Runs", lambda x: (x == 6).sum()),
    ).reset_index()

    # Innings and dismissals per season
    innings = bat.groupby("Season")["Match_Id"].nunique().reset_index(name="innings")
    dismissals = bat[(bat["Is_Wicket"] == 1) & (bat["Player_Dismissed"] == player)].groupby("Season").size().reset_index(name="dismissals")

    season_stats = season_stats.merge(innings, on="Season", how="left").merge(dismissals, on="Season", how="left").fillna(0)
    season_stats["sr"] = np.where(season_stats["balls"] > 0, round(season_stats["runs"] / season_stats["balls"] * 100, 1), 0)
    season_stats["average"] = np.where(season_stats["dismissals"] > 0, round(season_stats["runs"] / season_stats["dismissals"], 1), season_stats["runs"])
    season_stats["boundary_pct"] = np.where(season_stats["balls"] > 0, round((season_stats["fours"] + season_stats["sixes"]) / season_stats["balls"] * 100, 1), 0)

    return season_stats.sort_values("Season")


def player_season_bowling(player, deliveries):
    """Season-wise bowling metrics (corrected form analysis)."""
    bowl = deliveries[deliveries["Bowler"] == player].copy()
    if bowl.empty or "Season" not in bowl.columns:
        return pd.DataFrame()

    valid = bowl[valid_ball_mask(bowl)]
    season_stats = valid.groupby("Season").agg(
        balls=("Total_Runs", "count"),
        runs_conceded=("Total_Runs", "sum"),
        dots=("Total_Runs", lambda x: (x == 0).sum()),
    ).reset_index()

    # Wickets per season (bowler-credited only)
    wkt_mask = is_bowler_wicket(bowl)
    wkts = bowl[wkt_mask].groupby("Season").size().reset_index(name="wickets")
    innings = bowl.groupby("Season")["Match_Id"].nunique().reset_index(name="innings")

    season_stats = season_stats.merge(wkts, on="Season", how="left").merge(innings, on="Season", how="left").fillna(0)
    season_stats["overs"] = season_stats["balls"] / 6
    season_stats["economy"] = np.where(season_stats["overs"] > 0, round(season_stats["runs_conceded"] / season_stats["overs"], 2), 0)
    season_stats["sr"] = np.where(season_stats["wickets"] > 0, round(season_stats["balls"] / season_stats["wickets"], 1), 0)
    season_stats["dot_pct"] = np.where(season_stats["balls"] > 0, round(season_stats["dots"] / season_stats["balls"] * 100, 1), 0)
    season_stats["bowl_avg"] = np.where(season_stats["wickets"] > 0, round(season_stats["runs_conceded"] / season_stats["wickets"], 1), 0)

    return season_stats.sort_values("Season")


# ─── Phase Breakdown ─────────────────────────────────────────────────────────
def phase_label(over):
    if over <= 6:
        return "PP"
    elif over <= 15:
        return "Middle"
    return "Death"


def player_phase_batting(player, deliveries):
    """Phase-wise batting breakdown."""
    bat = deliveries[(deliveries["Batter"] == player) & valid_ball_mask(deliveries)].copy()
    if bat.empty:
        return pd.DataFrame(columns=["phase", "runs", "balls", "sr"])
    bat["phase"] = bat["Over"].apply(phase_label)
    agg = bat.groupby("phase").agg(runs=("Batsman_Runs", "sum"), balls=("Batsman_Runs", "count")).reset_index()
    agg["sr"] = np.where(agg["balls"] > 0, round(agg["runs"] / agg["balls"] * 100, 1), 0)
    return agg


def player_phase_bowling(player, deliveries):
    """Phase-wise bowling breakdown."""
    bowl = deliveries[(deliveries["Bowler"] == player) & valid_ball_mask(deliveries)].copy()
    if bowl.empty:
        return pd.DataFrame(columns=["phase", "runs_conceded", "balls", "economy"])
    bowl["phase"] = bowl["Over"].apply(phase_label)
    agg = bowl.groupby("phase").agg(runs_conceded=("Total_Runs", "sum"), balls=("Total_Runs", "count")).reset_index()
    agg["economy"] = np.where(agg["balls"] > 0, round(agg["runs_conceded"] / (agg["balls"] / 6), 2), 0)
    return agg


# ─── Dismissal Breakdown ─────────────────────────────────────────────────────
def dismissal_breakdown(player, deliveries):
    """Dismissal types for a batter."""
    dismissed = deliveries[(deliveries["Is_Wicket"] == 1) & (deliveries["Player_Dismissed"] == player)]
    if dismissed.empty or "Dismissal_Kind" not in dismissed.columns:
        return pd.DataFrame(columns=["kind", "count"])
    counts = dismissed["Dismissal_Kind"].value_counts().reset_index()
    counts.columns = ["kind", "count"]
    return counts


# ─── Player's Most Frequent Team ─────────────────────────────────────────────
def get_player_team(player, deliveries):
    """Determine the team a player is most associated with."""
    freq = {}
    bat = deliveries[deliveries["Batter"] == player]
    if not bat.empty and "Batting_Team" in bat.columns:
        for team, cnt in bat["Batting_Team"].value_counts().items():
            freq[team] = freq.get(team, 0) + cnt
    bowl = deliveries[deliveries["Bowler"] == player]
    if not bowl.empty and "Bowling_Team" in bowl.columns:
        for team, cnt in bowl["Bowling_Team"].value_counts().items():
            freq[team] = freq.get(team, 0) + cnt
    if freq:
        return max(freq, key=freq.get)
    return "Unknown"


# ─── Head-to-Head Stats ──────────────────────────────────────────────────────
def head_to_head_stats(team_a, team_b, matches, deliveries, season_range):
    """Compute H2H statistics between two teams."""
    m = matches.copy()
    d = deliveries.copy()

    # Filter to H2H matches
    if team_a and team_b:
        m = m[((m["Team1"] == team_a) & (m["Team2"] == team_b)) |
              ((m["Team1"] == team_b) & (m["Team2"] == team_a))]
    elif team_a:
        m = m[(m["Team1"] == team_a) | (m["Team2"] == team_a)]
    elif team_b:
        m = m[(m["Team1"] == team_b) | (m["Team2"] == team_b)]

    if season_range:
        m = m[(m["Season"] >= season_range[0]) & (m["Season"] <= season_range[1])]

    if m.empty:
        return None

    d = d[d["Match_Id"].isin(m["Id"])]

    total = len(m)
    t1_wins = int((m["Winner"] == team_a).sum()) if team_a else 0
    t2_wins = int((m["Winner"] == team_b).sum()) if team_b else 0
    ties = int((m["Result"] == "Tie").sum()) if "Result" in m.columns else 0
    no_result = int((m["Result"] == "No Result").sum()) if "Result" in m.columns else 0

    # Toss impact
    toss_match_win = ((m["Toss_Winner"] == m["Winner"]).mean() * 100) if len(m) else 0

    # Season-wise wins
    season_wins = m.groupby(["Season", "Winner"]).size().unstack(fill_value=0) if not m.empty else pd.DataFrame()

    # Margin distributions
    m_copy = m.copy()
    m_copy["Result_Margin"] = pd.to_numeric(m_copy.get("Result_Margin", 0), errors="coerce").fillna(0)
    run_margins = m_copy[m_copy["Result"] == "Runs"]["Result_Margin"].tolist() if "Result" in m_copy.columns else []
    wkt_margins = m_copy[m_copy["Result"] == "Wickets"]["Result_Margin"].tolist() if "Result" in m_copy.columns else []

    # Top 3 batters and bowlers in H2H
    top_bat = d.groupby(["Batter", "Batting_Team"])["Batsman_Runs"].sum().reset_index().nlargest(3, "Batsman_Runs")
    top_bowl = d[d["Is_Wicket"] == 1].groupby(["Bowler", "Bowling_Team"]).size().reset_index(name="Wickets").nlargest(3, "Wickets")

    # Top venues
    top_venues = m["Venue"].value_counts().head(3).reset_index()
    top_venues.columns = ["Venue", "Matches"]

    return {
        "total": total, "t1_wins": t1_wins, "t2_wins": t2_wins,
        "ties": ties, "no_result": no_result,
        "toss_win_pct": round(toss_match_win, 1),
        "season_wins": season_wins,
        "run_margins": run_margins, "wkt_margins": wkt_margins,
        "top_bat": top_bat, "top_bowl": top_bowl,
        "top_venues": top_venues,
        "matches_df": m, "deliveries_df": d,
    }


# ─── PvP Stats ────────────────────────────────────────────────────────────────
def player_vs_player_stats(batter, bowler, deliveries, season_range=None):
    """Ball-by-ball matchup stats between a batter and bowler."""
    df = deliveries[(deliveries["Batter"] == batter) & (deliveries["Bowler"] == bowler)].copy()

    if season_range and "Season" in df.columns:
        df = df[(df["Season"] >= season_range[0]) & (df["Season"] <= season_range[1])]

    if df.empty:
        return None

    valid = df[valid_ball_mask(df)]
    balls = len(valid)
    runs = int(valid["Batsman_Runs"].sum())
    dots = int((valid["Total_Runs"] == 0).sum())
    fours = int((valid["Batsman_Runs"] == 4).sum())
    sixes = int((valid["Batsman_Runs"] == 6).sum())
    dismissals = int(is_bowler_wicket(df).sum())

    return {
        "balls": balls, "runs": runs,
        "sr": round(runs / balls * 100, 1) if balls else 0,
        "dot_pct": round(dots / balls * 100, 1) if balls else 0,
        "fours": fours, "sixes": sixes, "dismissals": dismissals,
        "deliveries": df,
    }


# ─── Impact Player Analytics ─────────────────────────────────────────────────

def impact_player_scores(deliveries, matches, season=None):
    """
    Calculate Impact Player scores — measures how much a player's
    contribution exceeds the team average in matches they play.

    Impact Score = (Player's runs + wickets*25) / team_avg per match.
    Higher = more impact per game appearance.
    """
    d = deliveries.copy()
    m = matches.copy()

    if season:
        m = m[m["Season"] == season]
        d = d[d["Match_Id"].isin(m["Id"])]

    if d.empty:
        return pd.DataFrame()

    # Per-match player contribution
    bat_contrib = (d.groupby(["Match_Id", "Batter"])["Batsman_Runs"]
                   .sum().reset_index()
                   .rename(columns={"Batter": "Player", "Batsman_Runs": "bat_runs"}))

    wkt_df = d[is_bowler_wicket(d)]
    bowl_contrib = (wkt_df.groupby(["Match_Id", "Bowler"]).size()
                    .reset_index(name="wickets")
                    .rename(columns={"Bowler": "Player"}))

    # Merge
    contrib = bat_contrib.merge(bowl_contrib, on=["Match_Id", "Player"], how="outer").fillna(0)
    contrib["impact_raw"] = contrib["bat_runs"] + contrib["wickets"] * 25

    # Aggregate by player
    player_impact = contrib.groupby("Player").agg(
        matches=("Match_Id", "nunique"),
        total_runs=("bat_runs", "sum"),
        total_wickets=("wickets", "sum"),
        total_impact=("impact_raw", "sum"),
        avg_impact=("impact_raw", "mean"),
        max_impact=("impact_raw", "max"),
    ).reset_index()

    player_impact = player_impact[player_impact["matches"] >= 10]
    player_impact["impact_score"] = round(player_impact["avg_impact"], 1)
    player_impact = player_impact.sort_values("impact_score", ascending=False)

    return player_impact


def phase_impact_analysis(deliveries, matches, season=None):
    """
    Analyzes which game phase (Powerplay, Middle, Death) players
    contribute most impact in. Returns phase-wise contribution breakdown.
    """
    d = deliveries.copy()
    m = matches.copy()

    if season:
        m = m[m["Season"] == season]
        d = d[d["Match_Id"].isin(m["Id"])]

    if d.empty:
        return pd.DataFrame()

    d["phase"] = d["Over"].apply(
        lambda o: "Powerplay" if o <= 6 else ("Middle" if o <= 15 else "Death")
    )

    # Phase batting
    phase_bat = (d.groupby(["Batter", "phase"])["Batsman_Runs"]
                 .agg(["sum", "count"])
                 .reset_index()
                 .rename(columns={"Batter": "Player", "sum": "runs", "count": "balls"}))
    phase_bat["sr"] = round(phase_bat["runs"] / phase_bat["balls"] * 100, 1)

    # Phase wickets
    wkt_df = d[is_bowler_wicket(d)]
    phase_bowl = (wkt_df.groupby(["Bowler", "phase"]).size()
                  .reset_index(name="wickets")
                  .rename(columns={"Bowler": "Player"}))

    # Merge
    phase_data = phase_bat.merge(phase_bowl, on=["Player", "phase"], how="outer").fillna(0)
    phase_data["impact"] = phase_data["runs"] + phase_data["wickets"] * 25

    return phase_data


def team_impact_strategy(deliveries, matches, season=None):
    """
    Compares how each team distributes impact across phases.
    Returns team-phase-level RPO and boundary percentages.
    """
    d = deliveries.copy()
    m = matches.copy()

    if season:
        m = m[m["Season"] == season]
        d = d[d["Match_Id"].isin(m["Id"])]

    if d.empty:
        return pd.DataFrame()

    d["phase"] = d["Over"].apply(
        lambda o: "Powerplay" if o <= 6 else ("Middle" if o <= 15 else "Death")
    )
    d["boundary"] = d["Batsman_Runs"].isin([4, 6])

    team_phase = d.groupby(["Batting_Team", "phase"]).agg(
        runs=("Batsman_Runs", "sum"),
        balls=("Batsman_Runs", "count"),
        boundaries=("boundary", "sum"),
    ).reset_index()

    team_phase["rpo"] = round(team_phase["runs"] / (team_phase["balls"] / 6), 2)
    team_phase["boundary_pct"] = round(team_phase["boundaries"] / team_phase["balls"] * 100, 1)

    return team_phase


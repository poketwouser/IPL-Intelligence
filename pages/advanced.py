"""Advanced Analytics Lab — experimental metrics and deep-dive charts."""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data
from utils.constants import THEME, apply_dark_theme

dash.register_page(__name__, path="/advanced", name="Analytics Lab", order=6)

DATA = load_data()
M = DATA["matches"]
D = DATA["deliveries"]


def build():
    m, d = M.copy(), D.copy()

    # ─── Win Probability by Over (chasing) ────────────────────────────────────
    match_winners = m.set_index("Id")["Winner"].to_dict()
    inn2 = d[d["Inning"] == 2]
    match_overs = {}
    for _, row in inn2.iterrows():
        mid = row["Match_Id"]
        ov = row["Over"]
        if mid not in match_overs:
            match_overs[mid] = {}
        if ov not in match_overs[mid]:
            match_overs[mid][ov] = {"team": row["Batting_Team"], "runs": 0}
        match_overs[mid][ov]["runs"] += row["Total_Runs"]

    over_data = {o: {"total": 0, "wins": 0} for o in range(1, 21)}
    for mid, overs in match_overs.items():
        winner = match_winners.get(mid)
        first_entry = list(overs.values())[0]
        chasing_team = first_entry["team"]
        won = winner == chasing_team
        for ov in overs:
            if 1 <= ov <= 20:
                over_data[ov]["total"] += 1
                if won:
                    over_data[ov]["wins"] += 1

    wp_overs = sorted(over_data.keys())
    wp_pct = [round(over_data[o]["wins"] / over_data[o]["total"] * 100, 1) if over_data[o]["total"] else 50 for o in wp_overs]

    fig_wp = go.Figure(go.Scatter(
        x=wp_overs, y=wp_pct, mode="lines+markers", fill="tozeroy",
        fillcolor="rgba(0,180,216,0.1)", line=dict(color="#00b4d8", width=3, shape="spline"),
        marker=dict(size=8, color="#00b4d8")))
    fig_wp.add_shape(type="line", x0=0, x1=20, y0=50, y1=50,
                     line=dict(color="rgba(255,255,255,0.2)", dash="dash"))
    apply_dark_theme(fig_wp, title="Chasing Team Win Probability by Over", height=360,
                     yaxis=dict(title="Win %", range=[0, 100]),
                     xaxis=dict(title="Over", tickmode="linear", dtick=1))

    # ─── Match Total Distribution ─────────────────────────────────────────────
    match_totals = d.groupby("Match_Id")["Total_Runs"].sum().values
    fig_dist = go.Figure(go.Histogram(x=match_totals, nbinsx=30,
                                       marker=dict(color="rgba(255,183,3,0.6)", line=dict(color="#ffb703", width=1))))
    apply_dark_theme(fig_dist, title="Match Total Runs Distribution", height=360,
                     xaxis=dict(title="Total Runs"), yaxis=dict(title="Frequency"))

    # ─── Scoring Patterns by Over ─────────────────────────────────────────────
    over_stats = d.groupby("Over").agg(
        total=("Batsman_Runs", "count"),
        boundaries=("Batsman_Runs", lambda x: ((x == 4) | (x == 6)).sum()),
        dots=("Batsman_Runs", lambda x: (x == 0).sum()),
    ).reset_index()
    over_stats = over_stats[(over_stats["Over"] >= 1) & (over_stats["Over"] <= 20)]
    over_stats["boundary_pct"] = round(over_stats["boundaries"] / over_stats["total"] * 100, 1)
    over_stats["dot_pct"] = round(over_stats["dots"] / over_stats["total"] * 100, 1)

    fig_scoring = go.Figure()
    fig_scoring.add_trace(go.Scatter(x=over_stats["Over"], y=over_stats["boundary_pct"],
                                      mode="lines+markers", name="Boundary %",
                                      line=dict(color="#ffd166", width=2), marker=dict(size=6)))
    fig_scoring.add_trace(go.Scatter(x=over_stats["Over"], y=over_stats["dot_pct"],
                                      mode="lines+markers", name="Dot Ball %",
                                      line=dict(color="#00b4d8", width=2), marker=dict(size=6)))
    apply_dark_theme(fig_scoring, title="Scoring Patterns by Over", height=360,
                     xaxis=dict(title="Over", tickmode="linear", dtick=1),
                     yaxis=dict(title="Percentage"),
                     legend=dict(x=0.5, y=1.15, xanchor="center", orientation="h"))

    # ─── Toss Impact Analysis ─────────────────────────────────────────────────
    toss_data = m.copy()
    toss_data["toss_match"] = toss_data["Toss_Winner"] == toss_data["Winner"]
    toss_season = toss_data.groupby("Season")["toss_match"].mean().reset_index()
    toss_season["pct"] = round(toss_season["toss_match"] * 100, 1)

    fig_toss = go.Figure(go.Scatter(x=toss_season["Season"], y=toss_season["pct"],
                                     mode="lines+markers", line=dict(color=THEME["accent"], width=3, shape="spline"),
                                     marker=dict(size=8)))
    fig_toss.add_shape(type="line", x0=toss_season["Season"].min(), x1=toss_season["Season"].max(),
                       y0=50, y1=50, line=dict(color="rgba(255,255,255,0.2)", dash="dash"))
    apply_dark_theme(fig_toss, title="Toss Winner → Match Winner % by Season", height=360,
                     yaxis=dict(title="Win %", range=[30, 70]),
                     xaxis=dict(title="Season", dtick=1))

    # ─── Phase Dominance Across Seasons ───────────────────────────────────────
    d_copy = d.copy()
    d_copy["phase"] = d_copy["Over"].apply(lambda o: "PP" if o <= 6 else ("Middle" if o <= 15 else "Death"))
    phase_season = d_copy.groupby(["Season", "phase"]).agg(
        runs=("Batsman_Runs", "sum"), balls=("Batsman_Runs", "count")
    ).reset_index()
    phase_season["rpo"] = round(phase_season["runs"] / (phase_season["balls"] / 6), 2)

    fig_phase = go.Figure()
    phase_colors = {"PP": "#FFD700", "Middle": "#1E90FF", "Death": "#DC143C"}
    for phase in ["PP", "Middle", "Death"]:
        pdf = phase_season[phase_season["phase"] == phase]
        fig_phase.add_trace(go.Scatter(x=pdf["Season"], y=pdf["rpo"], mode="lines+markers",
                                        name=phase, line=dict(color=phase_colors[phase], width=2)))
    apply_dark_theme(fig_phase, title="Run Rate by Phase Across Seasons", height=360,
                     xaxis=dict(dtick=1), yaxis=dict(title="Runs per Over"))

    return html.Div([
        html.H2("🔬 Advanced Analytics Lab", className="page-header"),
        html.P("Experimental metrics, simulations, and deep-dive analytics",
               style={"textAlign": "center", "color": "rgba(255,255,255,0.4)", "fontSize": "13px", "marginBottom": "20px"}),
        html.Div(dcc.Graph(figure=fig_wp, config={"displayModeBar": False}), className="glass-card mb-3"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_dist, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_scoring, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_toss, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_phase, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
    ])


layout = build()

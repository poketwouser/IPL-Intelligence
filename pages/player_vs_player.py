"""Player vs Player Page — ported from P09 notebook."""
import dash
from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_player_list, get_season_range
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme, PHASE_COLORS, INVALID_BALL_EXTRAS, NON_BOWLER_DISMISSALS
from utils.analytics import player_vs_player_stats, get_player_team, valid_ball_mask

dash.register_page(__name__, path="/player-vs-player", name="Player v Player", order=4)

DATA = load_data()
PLAYERS = get_player_list(DATA["deliveries"])
SMIN, SMAX = get_season_range(DATA["matches"])

layout = html.Div([
    html.H2("🎯 Player vs Player Matchup", className="page-header"),
    html.Div([
        html.Div([
            html.Label("Batter", className="kpi-label mb-1"),
            dcc.Dropdown(id="pvp-batter", options=[{"label": p, "value": p} for p in PLAYERS],
                         placeholder="Select Batter"),
        ], style={"flex": "1", "minWidth": "200px"}),
        html.Div([
            html.Label("Bowler", className="kpi-label mb-1"),
            dcc.Dropdown(id="pvp-bowler", options=[{"label": p, "value": p} for p in PLAYERS],
                         placeholder="Select Bowler"),
        ], style={"flex": "1", "minWidth": "200px"}),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "12px"}),
    html.Div([
        html.Label("Season Range", className="kpi-label mb-1"),
        dcc.RangeSlider(id="pvp-season", min=SMIN, max=SMAX, step=1,
                        value=[SMIN, SMAX],
                        marks={y: str(y) for y in range(SMIN, SMAX + 1, 2)}),
    ], className="mb-3"),
    html.Div(id="pvp-kpis"),
    html.Div(id="pvp-charts"),
])


@callback(
    Output("pvp-kpis", "children"),
    Output("pvp-charts", "children"),
    Input("pvp-batter", "value"),
    Input("pvp-bowler", "value"),
    Input("pvp-season", "value"),
)
def update_pvp(batter, bowler, season):
    if not batter or not bowler or batter == bowler:
        return html.P("Select a batter and a bowler", className="text-center text-muted py-4"), None

    result = player_vs_player_stats(batter, bowler, DATA["deliveries"], season)
    if result is None:
        return html.P("No matchup data found.", className="text-center text-muted py-4"), None

    bt = get_player_team(batter, DATA["deliveries"])
    bwt = get_player_team(bowler, DATA["deliveries"])

    def kpi(label, val, clr):
        return html.Div([html.Div(label, className="kpi-label"),
                          html.Div(str(val), className="kpi-value", style={"color": clr})], className="kpi-card")

    kpis = html.Div([
        kpi(f"{batter.split()[-1]}", team_abbr(bt), team_color(bt)),
        kpi(f"{bowler.split()[-1]}", team_abbr(bwt), team_color(bwt)),
        kpi("Balls", result["balls"], THEME["text"]),
        kpi("Runs", result["runs"], THEME["neon_green"]),
        kpi("SR", result["sr"], THEME["neon_blue"]),
        kpi("Dismissals", result["dismissals"], THEME["neon_red"]),
        kpi("4s / 6s", f"{result['fours']} / {result['sixes']}", THEME["accent"]),
        kpi("Dot %", f"{result['dot_pct']}%", "#94a3b8"),
    ], className="kpi-row")

    # Charts
    df = result["deliveries"]
    valid = df[valid_ball_mask(df)]

    # Outcome distribution
    outcome_colors = {"0": "#7f8c8d", "1": "#3498db", "2": "#2980b9", "3": "#2ecc71",
                      "4": "#f39c12", "6": "#e74c3c", "W": "#c0392b"}
    counts = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "6": 0, "W": 0}
    for _, row in valid.iterrows():
        if row["Is_Wicket"] == 1 and pd.notna(row.get("Player_Dismissed")) and \
           row.get("Dismissal_Kind") not in NON_BOWLER_DISMISSALS:
            counts["W"] += 1
        else:
            k = str(int(row["Batsman_Runs"]))
            counts[k] = counts.get(k, 0) + 1

    fig_outcome = go.Figure(go.Bar(
        x=list(counts.keys()), y=list(counts.values()),
        marker_color=[outcome_colors.get(k, "#888") for k in counts.keys()],
        text=list(counts.values()), textposition="outside"))
    apply_dark_theme(fig_outcome, title="Ball Outcomes", height=320, showlegend=False)

    # Phase SR
    phases = {"Powerplay": {"runs": 0, "balls": 0}, "Middle": {"runs": 0, "balls": 0}, "Death": {"runs": 0, "balls": 0}}
    for _, row in valid.iterrows():
        p = "Powerplay" if row["Over"] <= 6 else ("Middle" if row["Over"] <= 15 else "Death")
        phases[p]["runs"] += row["Batsman_Runs"]
        phases[p]["balls"] += 1
    phase_data = [{"phase": p, "sr": round(v["runs"] / v["balls"] * 100, 1) if v["balls"] else 0}
                  for p, v in phases.items()]
    fig_phase = go.Figure(go.Bar(
        x=[d["phase"] for d in phase_data], y=[d["sr"] for d in phase_data],
        marker_color=[PHASE_COLORS.get(p["phase"], "#888") for p in phase_data],
        text=[d["sr"] for d in phase_data], textposition="outside"))
    apply_dark_theme(fig_phase, title="Phase Strike Rate", height=320, showlegend=False)

    # Over profile
    over_data = {}
    for _, row in valid.iterrows():
        o = row["Over"]
        if o not in over_data:
            over_data[o] = {"runs": 0, "balls": 0}
        over_data[o]["runs"] += row["Batsman_Runs"]
        over_data[o]["balls"] += 1
    overs = sorted(over_data.keys())
    avg_runs = [round(over_data[o]["runs"] / over_data[o]["balls"], 2) for o in overs]

    fig_over = go.Figure(go.Scatter(x=overs, y=avg_runs, mode="lines+markers",
                                     line=dict(color="#00FFFF", shape="spline"), marker=dict(size=8)))
    apply_dark_theme(fig_over, title="Avg Runs by Over", height=320)

    charts = html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig_outcome, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_phase, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_over, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row three-col"),
    ])

    return kpis, charts

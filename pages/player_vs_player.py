"""
Player vs Player — Premium matchup arena with outcome charts and phase analysis.
"""

import dash
from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_player_list, get_season_range
from utils.constants import team_abbr, team_color, apply_dark_theme, PHASE_COLORS, NON_BOWLER_DISMISSALS
from utils.analytics import player_vs_player_stats, get_player_team, valid_ball_mask
from utils.components import (
    page_hero, controls_bar, control_group,
    matchup_arena, stat_card, insight_card,
)

dash.register_page(__name__, path="/player-vs-player", name="Player v Player", order=4)

DATA    = load_data()
PLAYERS = get_player_list(DATA["deliveries"])
SMIN, SMAX = get_season_range(DATA["matches"])

layout = html.Div([
    page_hero(
        "🎯 MATCHUP ARENA",
        "Batter ", "vs Bowler",
        subtitle="Select any batter and bowler to see their full head-to-head confrontation — ball by ball, phase by phase.",
    ),

    controls_bar(
        control_group(
            "🏏 Batter",
            dcc.Dropdown(id="pvp-batter",
                         options=[{"label": p, "value": p} for p in PLAYERS],
                         placeholder="Select Batter…", className="dark-dropdown"),
        ),
        control_group(
            "🎯 Bowler",
            dcc.Dropdown(id="pvp-bowler",
                         options=[{"label": p, "value": p} for p in PLAYERS],
                         placeholder="Select Bowler…", className="dark-dropdown"),
        ),
        control_group(
            "Season Range",
            dcc.RangeSlider(id="pvp-season", min=SMIN, max=SMAX, step=1,
                            value=[SMIN, SMAX],
                            marks={y: str(y) for y in range(SMIN, SMAX+1, 3)},
                            tooltip={"placement": "bottom"}),
        ),
    ),

    html.Div(id="pvp-arena"),
    html.Div(id="pvp-kpis"),
    html.Div(id="pvp-charts"),
])

@callback(
    Output("pvp-batter", "options"),
    Output("pvp-bowler", "options"),
    Input("pvp-season", "value"),
)
def update_pvp_dropdowns(season_range):
    if not season_range:
        return dash.no_update, dash.no_update
        
    s0, s1 = season_range
    m = DATA["matches"]
    d = DATA["deliveries"]
    
    # Filter matches within the season range
    m_filtered = m[(m["Season"] >= s0) & (m["Season"] <= s1)]
    d_filtered = d[d["Match_Id"].isin(m_filtered["Id"])]
    
    valid_batters = sorted(d_filtered["Batter"].dropna().unique().tolist())
    valid_bowlers = sorted(d_filtered["Bowler"].dropna().unique().tolist())
    
    bat_options = [{"label": p, "value": p} for p in valid_batters]
    bowl_options = [{"label": p, "value": p} for p in valid_bowlers]
    
    return bat_options, bowl_options
@callback(
    Output("pvp-arena",  "children"),
    Output("pvp-kpis",   "children"),
    Output("pvp-charts", "children"),
    Input("pvp-batter",  "value"),
    Input("pvp-bowler",  "value"),
    Input("pvp-season",  "value"),
)
def update_pvp(batter, bowler, season):
    if not batter or not bowler or batter == bowler:
        return (
            html.P("Select a batter and a different bowler to begin.",
                   style={"textAlign": "center", "color": "rgba(255,255,255,0.3)",
                          "fontFamily": "'JetBrains Mono',monospace", "fontSize": "0.82rem",
                          "padding": "48px 0"}),
            None, None,
        )

    actual_latest = int(DATA["matches"]["Season"].max()) if not DATA["matches"].empty else 2024
    result = player_vs_player_stats(batter, bowler, DATA["deliveries"], season)
    if result is None:
        return (
            html.P(f"No head-to-head data found. Note: Data coverage currently ends at {actual_latest}.",
                   style={"textAlign": "center", "color": "rgba(255,255,255,0.3)",
                          "fontFamily": "'JetBrains Mono',monospace", "padding": "40px"}),
            None, None,
        )

    bt   = get_player_team(batter, DATA["deliveries"])
    bwt  = get_player_team(bowler, DATA["deliveries"])
    bat_c  = team_color(bt)  or "#00d4ff"
    bowl_c = team_color(bwt) or "#ff4757"

    # Matchup arena
    arena = matchup_arena(
        batter=batter, batter_team=bt,
        bowler=bowler, bowler_team=bwt,
        balls=result["balls"], runs=result["runs"],
        sr=result["sr"], dismissals=result["dismissals"],
    )

    # Stat cards
    kpis = html.Div([
        stat_card(str(result["balls"]),       "Balls Faced",  "🔴", "#f5a623"),
        stat_card(str(result["runs"]),        "Runs",         "🏏", bat_c),
        stat_card(str(result["sr"]),          "Strike Rate",  "⚡", "#00d4ff"),
        stat_card(str(result["dismissals"]),  "Dismissals",   "🎯", bowl_c),
        stat_card(str(result["fours"]),       "Fours",        "4️⃣", "#ffd700"),
        stat_card(str(result["sixes"]),       "Sixes",        "6️⃣", "#00ff87"),
        stat_card(f"{result['dot_pct']}%",    "Dot Ball %",   "⚫", "#a855f7"),
    ], className="stat-grid stagger-in", style={"marginBottom": "28px"})

    # Charts
    df    = result["deliveries"]
    valid = df[valid_ball_mask(df)]

    # Outcome distribution
    OUTCOME_COLORS = {
        "0": "#4a5568", "1": "#3b82f6", "2": "#2563eb",
        "3": "#22c55e", "4": "#f5a623", "6": "#ef4444", "W": "#b91c1c",
    }
    counts = {k: 0 for k in ["0","1","2","3","4","6","W"]}
    for _, row in valid.iterrows():
        if (row["Is_Wicket"] == 1 and pd.notna(row.get("Player_Dismissed")) and
                row.get("Dismissal_Kind") not in NON_BOWLER_DISMISSALS):
            counts["W"] += 1
        else:
            k = str(int(row["Batsman_Runs"]))
            if k in counts:
                counts[k] += 1

    fig_outcome = go.Figure(go.Bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        marker=dict(color=[OUTCOME_COLORS.get(k, "#888") for k in counts],
                    opacity=0.85, line=dict(width=0)),
        text=list(counts.values()),
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.55)", size=11),
        hovertemplate="Outcome %{x}: %{y} times<extra></extra>",
    ))
    apply_dark_theme(fig_outcome, title="Ball Outcome Distribution", height=300,
                     showlegend=False,
                     xaxis=dict(showgrid=False),
                     yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))

    # Phase strike rate
    phases = {"Powerplay": {"runs": 0, "balls": 0},
               "Middle":   {"runs": 0, "balls": 0},
               "Death":    {"runs": 0, "balls": 0}}
    for _, row in valid.iterrows():
        p = "Powerplay" if row["Over"] <= 6 else ("Middle" if row["Over"] <= 15 else "Death")
        phases[p]["runs"]  += row["Batsman_Runs"]
        phases[p]["balls"] += 1

    phase_data = [
        {"phase": p, "sr": round(v["runs"] / v["balls"] * 100, 1) if v["balls"] else 0}
        for p, v in phases.items()
    ]

    fig_phase = go.Figure(go.Bar(
        x=[d["phase"] for d in phase_data],
        y=[d["sr"]    for d in phase_data],
        marker=dict(
            color=[PHASE_COLORS.get(d["phase"], "#888") for d in phase_data],
            opacity=0.85, line=dict(width=0),
        ),
        text=[d["sr"] for d in phase_data],
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.55)", size=11),
        hovertemplate="%{x}<br>SR: %{y}<extra></extra>",
    ))
    apply_dark_theme(fig_phase, title="Phase Strike Rate", height=300,
                     showlegend=False,
                     xaxis=dict(showgrid=False),
                     yaxis=dict(title="Strike Rate", gridcolor="rgba(255,255,255,0.04)"))

    # Over profile (avg runs)
    over_acc = {}
    for _, row in valid.iterrows():
        o = row["Over"]
        if o not in over_acc:
            over_acc[o] = {"runs": 0, "balls": 0}
        over_acc[o]["runs"]  += row["Batsman_Runs"]
        over_acc[o]["balls"] += 1

    overs    = sorted(over_acc.keys())
    avg_runs = [round(over_acc[o]["runs"] / over_acc[o]["balls"], 2) for o in overs]

    fig_over = go.Figure(go.Scatter(
        x=overs, y=avg_runs,
        mode="lines+markers",
        line=dict(color=bat_c, width=2.5, shape="spline"),
        marker=dict(size=8, color=bat_c,
                    line=dict(width=1.5, color="rgba(0,0,0,0.3)")),
        fill="tozeroy", fillcolor=f"rgba({int(bat_c[1:3],16)},{int(bat_c[3:5],16)},{int(bat_c[5:7],16)},0.09)" if bat_c.startswith("#") and len(bat_c)==7 else "rgba(245,166,35,0.09)",
        hovertemplate="Over %{x}<br>Avg Runs/Ball: %{y:.2f}<extra></extra>",
    ))
    apply_dark_theme(fig_over, title="Avg Runs per Ball by Over", height=300,
                     xaxis=dict(title="Over", showgrid=False),
                     yaxis=dict(title="Avg Runs/Ball", gridcolor="rgba(255,255,255,0.04)"),
                     showlegend=False)

    charts = html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig_outcome, config={"displayModeBar": False}),
                     className="glass-card"),
            html.Div(dcc.Graph(figure=fig_phase, config={"displayModeBar": False}),
                     className="glass-card"),
            html.Div(dcc.Graph(figure=fig_over, config={"displayModeBar": False}),
                     className="glass-card"),
        ], className="chart-row three-col reveal"),

        insight_card(
            "MATCHUP ANALYSIS",
            f"{batter} faces {bowler} with a strike rate of {result['sr']} — "
            f"dismissed {result['dismissals']} time(s) in {result['balls']} balls. "
            f"Dot ball percentage: {result['dot_pct']}%.",
        ),
    ])

    return arena, kpis, charts

"""
Head-to-Head Page — Premium rivalry dashboard with season trends.
"""

import dash
from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_team_list, get_season_range
from utils.constants import team_abbr, team_color, apply_dark_theme
from utils.components import (
    page_hero, controls_bar, control_group,
    rivalry_header, stat_card, insight_card,
)

try:
    from scipy import stats
    HAVE_KDE = True
except ImportError:
    HAVE_KDE = False

dash.register_page(__name__, path="/head-to-head", name="Head to Head", order=2)

DATA  = load_data()
TEAMS = get_team_list(DATA["matches"])
SMIN, SMAX = get_season_range(DATA["matches"])

layout = html.Div([
    page_hero(
        "⚔️ HEAD TO HEAD",
        "Rivalry ", "Decoded",
        subtitle="Pick two franchises and let the data tell the story — wins, margins, top performers, and season arcs.",
    ),

    controls_bar(
        control_group(
            "Quick Rivalry",
            dcc.Dropdown(
                id="h2h-preset",
                options=[
                    {"label": "MI vs CSK (El Clasico)", "value": "Mumbai Indians|Chennai Super Kings"},
                    {"label": "RCB vs CSK (Southern Derby)", "value": "Royal Challengers Bangalore|Chennai Super Kings"},
                    {"label": "MI vs RCB", "value": "Mumbai Indians|Royal Challengers Bangalore"},
                    {"label": "KKR vs RCB", "value": "Kolkata Knight Riders|Royal Challengers Bangalore"}
                ],
                placeholder="Select Preset", 
                className="dark-dropdown"
            ),
        ),
        control_group(
            "Team A",
            dcc.Dropdown(id="h2h-team-a",
                         options=[{"label": t, "value": t} for t in TEAMS],
                         placeholder="Select Team A", className="dark-dropdown"),
        ),
        html.Div(
            html.Button("⇄", id="h2h-swap", n_clicks=0, style={
                "background": "rgba(255,255,255,0.05)", "border": "1px solid rgba(255,255,255,0.2)", 
                "color": "white", "borderRadius": "50%", "width": "42px", "height": "42px", 
                "cursor": "pointer", "fontSize": "1.2rem", "marginTop": "22px",
                "transition": "all 0.3s ease"
            }),
            style={"display": "flex", "alignItems": "center", "justifyContent": "center"}
        ),
        control_group(
            "Team B",
            dcc.Dropdown(id="h2h-team-b",
                         options=[{"label": t, "value": t} for t in TEAMS],
                         placeholder="Select Team B", className="dark-dropdown"),
        ),
        control_group(
            "Season Range",
            html.Div(
                dcc.RangeSlider(id="h2h-season", min=SMIN, max=SMAX, step=1,
                                value=[SMIN, SMAX],
                                marks={y: str(y) for y in range(SMIN, SMAX+1, 2)},
                                tooltip={"placement": "bottom", "always_visible": False},
                                className="dark-slider"),
                style={"padding": "0 10px", "minWidth": "300px"} # Prevent clipping
            )
        ),
    ),

    html.Div(id="h2h-rivalry"),
    html.Div(id="h2h-kpis"),
    html.Div(id="h2h-plots"),
])


@callback(
    Output("h2h-team-a", "value"),
    Output("h2h-team-b", "value"),
    Input("h2h-preset", "value"),
    Input("h2h-swap", "n_clicks"),
    dash.State("h2h-team-a", "value"),
    dash.State("h2h-team-b", "value"),
    prevent_initial_call=True
)
def handle_h2h_controls(preset, swap_clicks, team_a, team_b):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
        
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "h2h-preset" and preset:
        t1, t2 = preset.split("|")
        return t1, t2
        
    if trigger_id == "h2h-swap":
        return team_b, team_a
        
    return dash.no_update, dash.no_update


@callback(
    Output("h2h-rivalry", "children"),
    Output("h2h-kpis",    "children"),
    Output("h2h-plots",   "children"),
    Input("h2h-team-a",   "value"),
    Input("h2h-team-b",   "value"),
    Input("h2h-season",   "value"),
)
def update_h2h(ta, tb, season):
    if not season:
        return no_update, no_update, no_update

    m   = DATA["matches"].copy()
    d   = DATA["deliveries"].copy()
    s0, s1 = season

    # Filter matches
    if ta and tb:
        m = m[((m["Team1"] == ta) & (m["Team2"] == tb)) |
              ((m["Team1"] == tb) & (m["Team2"] == ta))]
    elif ta:
        m = m[(m["Team1"] == ta) | (m["Team2"] == ta)]
    elif tb:
        m = m[(m["Team1"] == tb) | (m["Team2"] == tb)]

    m = m[(m["Season"] >= s0) & (m["Season"] <= s1)]

    actual_latest = int(DATA["matches"]["Season"].max()) if not DATA["matches"].empty else 2024
    if m.empty:
        empty_msg = html.P(
            f"No matches found for this selection. Note: Data coverage currently ends at {actual_latest}.",
            style={"textAlign": "center", "color": "rgba(255,255,255,0.35)",
                   "padding": "40px", "fontFamily": "'JetBrains Mono',monospace"},
        )
        return None, empty_msg, None

    d   = d[d["Match_Id"].isin(m["Id"])]

    total = len(m)
    t1w   = int((m["Winner"] == ta).sum()) if ta else 0
    t2w   = int((m["Winner"] == tb).sum()) if tb else 0
    ties  = int((m.get("Result", pd.Series(dtype=str)) == "Tie").sum())
    nr    = int((m.get("Result", pd.Series(dtype=str)) == "No Result").sum())
    ca    = team_color(ta) or "#00d4ff"
    cb    = team_color(tb) or "#ff4757"

    # Rivalry header
    riv_hdr = rivalry_header(ta or "Team A", tb or "Team B", t1w, t2w, total) if (ta and tb) else None

    # Stat cards
    kpis = html.Div([
        stat_card(str(total), "Matches Played", "🏟️", "#f5a623"),
        stat_card(str(t1w),   f"{team_abbr(ta) or 'A'} Wins", "🏆", ca),
        stat_card(str(t2w),   f"{team_abbr(tb) or 'B'} Wins", "🏆", cb),
        stat_card(str(ties),  "Ties",     "🤝", "#ffd700"),
        stat_card(str(nr),    "No Result","❌", "#94a3b8"),
    ], className="stat-grid stagger-in", style={"marginBottom": "28px"})

    plots = []

    def _wrap(fig, cls="glass-card"):
        return html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}), className=cls)

    # Win comparison bar
    fig_win = go.Figure(go.Bar(
        x=[team_abbr(ta) or "A", team_abbr(tb) or "B"],
        y=[t1w, t2w],
        marker=dict(color=[ca, cb], opacity=0.82, line=dict(width=0)),
        text=[t1w, t2w],
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.6)", size=13),
        hovertemplate="%{x}: %{y} wins<extra></extra>",
    ))
    apply_dark_theme(fig_win, title="Win Comparison", height=280,
                     showlegend=False,
                     xaxis=dict(showgrid=False),
                     yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))

    # Toss gauge
    toss_pct = round((m["Toss_Winner"] == m["Winner"]).mean() * 100, 1) if len(m) else 50
    fig_toss_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=toss_pct,
        number={"suffix": "%", "font": {"color": "#f5a623", "size": 36,
                                        "family": "Orbitron, monospace"}},
        gauge={
            "axis":  {"range": [0,100], "tickfont": {"color": "rgba(255,255,255,0.4)", "size": 10}},
            "bar":   {"color": "#f5a623"},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,40],  "color": "rgba(255,71,87,0.08)"},
                {"range": [40,60], "color": "rgba(255,255,255,0.04)"},
                {"range": [60,100],"color": "rgba(0,255,135,0.08)"},
            ],
        },
        title={"text": "Toss Winner → Match Winner %",
               "font": {"color": "rgba(255,255,255,0.6)", "size": 13}},
    ))
    apply_dark_theme(fig_toss_g, height=280)

    plots.append(html.Div([
        _wrap(fig_win, "glass-card"),
        _wrap(fig_toss_g, "glass-card"),
    ], className="chart-row two-col reveal"))

    # Season trend
    st = m.groupby(["Season","Winner"]).size().unstack(fill_value=0)
    fig_trend = go.Figure()
    for col in st.columns:
        if col and str(col) != "nan":
            fig_trend.add_trace(go.Scatter(
                x=st.index, y=st[col],
                name=team_abbr(col) or str(col),
                mode="lines+markers",
                line=dict(color=team_color(col) or "#888", width=2.5, shape="spline"),
                marker=dict(size=7),
                hovertemplate="Season %{x}<br>Wins: %{y}<extra></extra>",
            ))
    apply_dark_theme(fig_trend, title="Season-wise Wins", height=300,
                     xaxis=dict(dtick=1, showgrid=False),
                     yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))
    plots.append(html.Div(_wrap(fig_trend, "glass-card"),
                           className="reveal", style={"marginBottom": "18px"}))

    # Margin distribution
    m2 = m.copy()
    m2["Result_Margin"] = pd.to_numeric(m2.get("Result_Margin", 0), errors="coerce").fillna(0)
    runs_df = m2[m2.get("Result", pd.Series(dtype=str)) == "Runs"] if "Result" in m2 else pd.DataFrame()
    wkts_df = m2[m2.get("Result", pd.Series(dtype=str)) == "Wickets"] if "Result" in m2 else pd.DataFrame()

    fig_margin = make_subplots(rows=1, cols=2,
                               subplot_titles=("Defending — Won by Runs", "Chasing — Won by Wickets"))
    if not runs_df.empty:
        fig_margin.add_trace(go.Histogram(
            x=runs_df["Result_Margin"], nbinsx=15,
            marker=dict(color="rgba(245,166,35,0.65)", line=dict(width=0)),
            hovertemplate="Margin: %{x} runs<br>Count: %{y}<extra></extra>",
        ), 1, 1)
    if not wkts_df.empty:
        fig_margin.add_trace(go.Histogram(
            x=wkts_df["Result_Margin"], nbinsx=10,
            marker=dict(color="rgba(0,212,255,0.65)", line=dict(width=0)),
            hovertemplate="Margin: %{x} wkts<br>Count: %{y}<extra></extra>",
        ), 1, 2)
    apply_dark_theme(fig_margin, title="Match Margin Distribution", height=300, showlegend=False)
    plots.append(html.Div(_wrap(fig_margin, "glass-card"),
                           className="reveal", style={"marginBottom": "18px"}))

    # Top performers
    if not d.empty:
        top_bats = (d.groupby(["Batter","Batting_Team"])["Batsman_Runs"]
                    .sum().reset_index().nlargest(3, "Batsman_Runs")
                    .sort_values("Batsman_Runs", ascending=True))
        top_bats["display"] = top_bats.apply(lambda r: f"{r['Batter']} · {team_abbr(r['Batting_Team'])}", axis=1)
        top_bats["color"]   = top_bats["Batting_Team"].apply(team_color)

        fig_bat = go.Figure(go.Bar(
            x=top_bats["Batsman_Runs"], y=top_bats["display"],
            orientation="h",
            marker=dict(color=top_bats["color"].tolist(), opacity=0.8, line=dict(width=0)),
            text=top_bats["Batsman_Runs"],
            textposition="outside",
            textfont=dict(color="rgba(255,255,255,0.5)", size=11),
            hovertemplate="%{y}: %{x} runs<extra></extra>",
        ))
        apply_dark_theme(fig_bat, title="Top 3 Batters (H2H Runs)", height=240,
                         xaxis=dict(showgrid=False),
                         margin=dict(l=180, r=60, t=44, b=36))

        top_bowls = (d[d["Is_Wicket"] == 1]
                     .groupby(["Bowler","Bowling_Team"]).size().reset_index(name="Wickets")
                     .nlargest(3, "Wickets").sort_values("Wickets", ascending=True))
        top_bowls["display"] = top_bowls.apply(lambda r: f"{r['Bowler']} · {team_abbr(r['Bowling_Team'])}", axis=1)
        top_bowls["color"]   = top_bowls["Bowling_Team"].apply(team_color)

        fig_bowl = go.Figure(go.Bar(
            x=top_bowls["Wickets"], y=top_bowls["display"],
            orientation="h",
            marker=dict(color=top_bowls["color"].tolist(), opacity=0.8, line=dict(width=0)),
            text=top_bowls["Wickets"],
            textposition="outside",
            textfont=dict(color="rgba(255,255,255,0.5)", size=11),
            hovertemplate="%{y}: %{x} wickets<extra></extra>",
        ))
        apply_dark_theme(fig_bowl, title="Top 3 Bowlers (H2H Wickets)", height=240,
                         xaxis=dict(showgrid=False),
                         margin=dict(l=180, r=60, t=44, b=36))

        plots.append(html.Div([
            _wrap(fig_bat,  "glass-card"),
            _wrap(fig_bowl, "glass-card"),
        ], className="chart-row two-col reveal"))

    # Venues
    venue_counts = m["Venue"].value_counts().head(5).reset_index()
    venue_counts.columns = ["Venue", "Matches"]
    venue_counts["short"] = venue_counts["Venue"].str[:30]
    fig_venues = go.Figure(go.Bar(
        x=venue_counts["short"], y=venue_counts["Matches"],
        marker=dict(color="rgba(245,166,35,0.65)", line=dict(width=0)),
        text=venue_counts["Matches"],
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.5)", size=11),
        hovertemplate="%{x}: %{y} matches<extra></extra>",
    ))
    apply_dark_theme(fig_venues, title="Top Venues for this Matchup", height=260,
                     xaxis=dict(showgrid=False, tickangle=-20),
                     yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                     showlegend=False)
    plots.append(html.Div(_wrap(fig_venues, "glass-card"),
                           className="reveal", style={"marginBottom": "18px"}))

    # Insight
    if ta and tb and total >= 5:
        leader     = ta if t1w > t2w else tb
        leader_wins = max(t1w, t2w)
        plots.append(insight_card(
            "RIVALRY SUMMARY",
            f"{team_abbr(leader)} lead this rivalry with {leader_wins} wins from {total} encounters. "
            f"Toss advantage: {toss_pct}% of toss winners also win the match in this fixture.",
        ))

    return riv_hdr, kpis, html.Div(plots)

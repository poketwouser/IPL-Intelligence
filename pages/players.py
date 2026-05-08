"""Player Analysis Page — ported from P08 with corrected role detection and season-wise form."""
import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_player_list, get_season_range
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme, PHASE_COLORS
from utils.analytics import (
    classify_player_role, batting_summary, bowling_summary,
    player_season_batting, player_season_bowling,
    player_phase_batting, player_phase_bowling,
    dismissal_breakdown, get_player_team,
)

dash.register_page(__name__, path="/players", name="Player Analysis", order=3)

DATA = load_data()
PLAYERS = get_player_list(DATA["deliveries"])
SMIN, SMAX = get_season_range(DATA["matches"])

layout = html.Div([
    html.H2("🏏 Player Analysis", className="page-header"),
    html.Div([
        html.Div([
            html.Label("Select Player", className="kpi-label mb-1"),
            dcc.Dropdown(id="pa-player", options=[{"label": p, "value": p} for p in PLAYERS],
                         value="V Kohli" if "V Kohli" in PLAYERS else PLAYERS[0]),
        ], style={"flex": "1", "minWidth": "250px"}),
        html.Div([
            html.Label("Season Range", className="kpi-label mb-1"),
            dcc.RangeSlider(id="pa-season", min=SMIN, max=SMAX, step=1,
                            value=[SMIN, SMAX],
                            marks={y: str(y) for y in range(SMIN, SMAX + 1, 2)},
                            tooltip={"placement": "bottom"}),
        ], style={"flex": "2"}),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "16px", "alignItems": "flex-end"}),
    html.Div(id="pa-kpi"),
    html.Div(id="pa-charts"),
])


@callback(
    Output("pa-kpi", "children"),
    Output("pa-charts", "children"),
    Input("pa-player", "value"),
    Input("pa-season", "value"),
)
def update_player(player, season_range):
    if not player:
        return None, None

    d_all = DATA["deliveries"]
    m_all = DATA["matches"]

    # Filter by season
    s0, s1 = season_range
    season_ids = m_all[(m_all["Season"] >= s0) & (m_all["Season"] <= s1)]["Id"]
    d = d_all[d_all["Match_Id"].isin(season_ids)]

    role = classify_player_role(player, d)
    team = get_player_team(player, d)
    clr = team_color(team)
    bat = batting_summary(player, d)
    bowl = bowling_summary(player, d)

    # ─── KPI Card ────────────────────────────────────────────────────────────
    def mkv(label, val):
        return html.Span([html.Span(f"{label}: ", style={"fontWeight": "600"}), html.Span(str(val)), html.Br()])

    bat_kpis = html.Div([
        html.H6("🏏 Batting", style={"color": "#3EC1D3", "fontWeight": "600"}),
        html.P([
            mkv("Runs", bat["runs"]), mkv("Innings", bat["innings"]),
            mkv("SR", bat["sr"]), mkv("Avg", bat["average"]),
            mkv("4s / 6s", f"{bat['fours']} / {bat['sixes']}"),
            mkv("HS", bat["high_score"]), mkv("50s / 100s", f"{bat['fifties']} / {bat['hundreds']}"),
        ], style={"fontSize": "13px", "marginBottom": "0"}),
    ]) if role in ("Batter", "All-rounder") else None

    bowl_kpis = html.Div([
        html.H6("🎯 Bowling", style={"color": "#F76C6C", "fontWeight": "600"}),
        html.P([
            mkv("Wickets", bowl["wickets"]), mkv("Innings", bowl["innings"]),
            mkv("Economy", bowl["economy"]), mkv("SR", bowl["sr"]),
            mkv("Dot %", f"{bowl['dot_pct']}%"),
        ], style={"fontSize": "13px", "marginBottom": "0"}),
    ]) if role in ("Bowler", "All-rounder") else None

    kpi_card = html.Div([
        html.Div([
            html.H5(f"{player}  •  {team_abbr(team)}", style={"fontWeight": "700", "color": clr}),
            html.Small(f"Role: {role}", style={"color": "rgba(255,255,255,0.5)"}),
        ]),
        html.Hr(style={"borderColor": clr, "opacity": "0.3"}),
        html.Div([bat_kpis, bowl_kpis], style={"display": "flex", "gap": "24px", "flexWrap": "wrap"}),
    ], className="glass-card mb-3", style={"border": f"1px solid {clr}"})

    # ─── Charts ──────────────────────────────────────────────────────────────
    charts = []

    # SEASON-WISE FORM (CORRECTED: not innings-by-innings)
    if role in ("Batter", "All-rounder"):
        sb = player_season_batting(player, d)
        if not sb.empty:
            # Season Runs bar
            fig_runs = px.bar(sb, x="Season", y="runs", title="Season-wise Runs",
                              text="runs", color_discrete_sequence=[clr])
            fig_runs.update_traces(textposition="outside")
            apply_dark_theme(fig_runs, height=340, xaxis=dict(dtick=1))

            # Season SR + Average trend
            fig_form = go.Figure()
            fig_form.add_trace(go.Scatter(x=sb["Season"], y=sb["sr"], mode="lines+markers",
                                          name="Strike Rate", line=dict(color="#00b4d8", width=2)))
            fig_form.add_trace(go.Scatter(x=sb["Season"], y=sb["average"], mode="lines+markers",
                                          name="Average", line=dict(color="#ffd166", width=2), yaxis="y2"))
            apply_dark_theme(fig_form, title="Batting Form — SR & Average by Season", height=340,
                             yaxis=dict(title="Strike Rate"), yaxis2=dict(title="Average", overlaying="y", side="right"),
                             xaxis=dict(dtick=1))

            charts.append(html.Div([
                html.Div(dcc.Graph(figure=fig_runs, config={"displayModeBar": False}), className="glass-card"),
                html.Div(dcc.Graph(figure=fig_form, config={"displayModeBar": False}), className="glass-card"),
            ], className="chart-row two-col"))

    if role in ("Bowler", "All-rounder"):
        sw = player_season_bowling(player, d)
        if not sw.empty:
            fig_wkts = px.bar(sw, x="Season", y="wickets", title="Season-wise Wickets",
                              text="wickets", color_discrete_sequence=["#f94144"])
            fig_wkts.update_traces(textposition="outside")
            apply_dark_theme(fig_wkts, height=340, xaxis=dict(dtick=1))

            fig_bowl_form = go.Figure()
            fig_bowl_form.add_trace(go.Scatter(x=sw["Season"], y=sw["economy"], mode="lines+markers",
                                                name="Economy", line=dict(color="#00b4d8", width=2)))
            fig_bowl_form.add_trace(go.Scatter(x=sw["Season"], y=sw["dot_pct"], mode="lines+markers",
                                                name="Dot Ball %", line=dict(color="#ffd166", width=2), yaxis="y2"))
            apply_dark_theme(fig_bowl_form, title="Bowling Form — Economy & Dot% by Season", height=340,
                             yaxis=dict(title="Economy"), yaxis2=dict(title="Dot %", overlaying="y", side="right"),
                             xaxis=dict(dtick=1))

            charts.append(html.Div([
                html.Div(dcc.Graph(figure=fig_wkts, config={"displayModeBar": False}), className="glass-card"),
                html.Div(dcc.Graph(figure=fig_bowl_form, config={"displayModeBar": False}), className="glass-card"),
            ], className="chart-row two-col"))

    # Dismissal Breakdown (only for batters/all-rounders)
    if role in ("Batter", "All-rounder"):
        db = dismissal_breakdown(player, d)
        if not db.empty:
            fig_dismiss = px.pie(db, names="kind", values="count", title="Dismissal Breakdown",
                                 color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            apply_dark_theme(fig_dismiss, height=340)
        else:
            fig_dismiss = go.Figure()
            apply_dark_theme(fig_dismiss, title="Dismissal Breakdown", height=340)
    else:
        fig_dismiss = None

    # Phase Breakdown
    if role in ("Batter", "All-rounder"):
        bp = player_phase_batting(player, d)
        if not bp.empty:
            fig_bphase = px.bar(bp, x="phase", y="runs", title="Batting by Phase",
                                color="phase", color_discrete_map=PHASE_COLORS, text="sr")
            fig_bphase.update_traces(texttemplate="SR: %{text}", textposition="outside")
            apply_dark_theme(fig_bphase, height=340, showlegend=False)
        else:
            fig_bphase = None
    else:
        fig_bphase = None

    if role in ("Bowler", "All-rounder"):
        blp = player_phase_bowling(player, d)
        if not blp.empty:
            fig_bowlphase = px.bar(blp, x="phase", y="economy", title="Economy by Phase",
                                   color="phase", color_discrete_map=PHASE_COLORS, text="economy")
            fig_bowlphase.update_traces(texttemplate="%{text}", textposition="outside")
            apply_dark_theme(fig_bowlphase, height=340, showlegend=False)
        else:
            fig_bowlphase = None
    else:
        fig_bowlphase = None

    # Add phase/dismissal row
    phase_row_items = []
    if fig_dismiss:
        phase_row_items.append(html.Div(dcc.Graph(figure=fig_dismiss, config={"displayModeBar": False}), className="glass-card"))
    if fig_bphase:
        phase_row_items.append(html.Div(dcc.Graph(figure=fig_bphase, config={"displayModeBar": False}), className="glass-card"))
    if fig_bowlphase:
        phase_row_items.append(html.Div(dcc.Graph(figure=fig_bowlphase, config={"displayModeBar": False}), className="glass-card"))

    if phase_row_items:
        ncols = len(phase_row_items)
        col_class = "two-col" if ncols == 2 else ("three-col" if ncols >= 3 else "full-width")
        charts.append(html.Div(phase_row_items, className=f"chart-row {col_class}"))

    return kpi_card, html.Div(charts)

"""
Player Analysis Page — FIFA-style profile card with real images,
performance meters, radar charts, premium form charts.
"""

import dash
from dash import html, dcc, Input, Output, callback
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
from utils.components import (
    page_hero, controls_bar, control_group,
    player_profile_card, section_header, insight_card, _rgba,
)

try:
    from utils.player_images import get_player_image_url
except ImportError:
    def get_player_image_url(name): return None

dash.register_page(__name__, path="/players", name="Player Analysis", order=3)

DATA    = load_data()
PLAYERS = get_player_list(DATA["deliveries"])
SMIN, SMAX = get_season_range(DATA["matches"])

_default_player = next(
    (p for p in ["V Kohli", "SK Raina", "RG Sharma"] if p in PLAYERS),
    PLAYERS[0] if PLAYERS else ""
)

layout = html.Div([
    page_hero(
        "🏏 PLAYER ANALYSIS",
        "Player ", "Intelligence",
        subtitle="Career stats, form trends, phase breakdowns, and dismissal patterns — all in one view.",
    ),

    # Controls
    controls_bar(
        control_group(
            "Select Player",
            dcc.Dropdown(
                id="pa-player",
                options=[{"label": p, "value": p} for p in PLAYERS],
                value=_default_player,
                clearable=False,
                style={"color": "black"},
            ),
        ),
        control_group(
            "Season Range",
            dcc.RangeSlider(
                id="pa-season", min=SMIN, max=SMAX, step=1,
                value=[SMIN, SMAX],
                marks={y: str(y) for y in range(SMIN, SMAX + 1, 3)},
                tooltip={"placement": "bottom"},
            ),
        ),
    ),

    # Dynamic sections
    html.Div(id="pa-profile"),
    html.Div(id="pa-charts"),
])


def _performance_meter(label, value, max_val, color="#f5a623"):
    """Create an animated performance meter bar."""
    pct = min(100, round(value / max_val * 100, 1)) if max_val else 0
    return html.Div([
        html.Div(label, className="perf-meter-label"),
        html.Div([
            html.Div(
                className="perf-meter-fill",
                style={"width": "0%", "background": f"linear-gradient(90deg, {color}, {color}cc)"},
                **{"data-width": f"{pct}%"}
            ),
        ], className="perf-meter-bar"),
        html.Div(str(round(value, 1)), className="perf-meter-value"),
    ], className="perf-meter")


def _radar_chart(bat_stats, bowl_stats, clr):
    """Create a radar chart for player stats."""
    categories = []
    values = []

    if bat_stats:
        # Normalize stats to 0-100 scale
        sr = min(100, bat_stats.get("sr", 0) / 2)
        avg = min(100, bat_stats.get("average", 0) / 0.6)
        bp = min(100, bat_stats.get("boundary_pct", 0) * 3)
        categories += ["Strike Rate", "Average", "Boundary%"]
        values += [sr, avg, bp]

    if bowl_stats and bowl_stats.get("wickets", 0) > 0:
        eco = max(0, 100 - (bowl_stats.get("economy", 10) - 5) * 15)
        dp = min(100, bowl_stats.get("dot_pct", 0) * 2)
        categories += ["Economy", "Dot Ball%"]
        values += [eco, dp]

    if not categories:
        return None

    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor=_rgba(clr, 0.13),
        line=dict(color=clr, width=2),
        marker=dict(size=6, color=clr),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="rgba(255,255,255,0.06)",
                tickfont=dict(size=8, color="rgba(255,255,255,0.3)"),
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                tickfont=dict(color="rgba(255,255,255,0.5)", size=10),
            ),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30),
        height=280,
    )
    return fig


@callback(
    Output("pa-profile", "children"),
    Output("pa-charts",  "children"),
    Input("pa-player",  "value"),
    Input("pa-season",  "value"),
)
def update_player(player, season_range):
    if not player:
        return None, None

    d_all = DATA["deliveries"]
    m_all = DATA["matches"]
    s0, s1 = season_range
    season_ids = m_all[(m_all["Season"] >= s0) & (m_all["Season"] <= s1)]["Id"]
    d = d_all[d_all["Match_Id"].isin(season_ids)]

    role  = classify_player_role(player, d)
    team  = get_player_team(player, d)
    clr   = team_color(team) or "#f5a623"
    bat   = batting_summary(player, d)
    bowl  = bowling_summary(player, d)
    image_url = get_player_image_url(player)

    # Profile card with image
    bat_stats  = bat  if role in ("Batter",  "All-rounder") else None
    bowl_stats = bowl if role in ("Bowler",  "All-rounder") else None

    # Build enhanced profile with performance meters
    profile_children = [
        player_profile_card(player, team, role, bat_stats, bowl_stats, image_url=image_url),
    ]

    # Performance meters
    meters = []
    if bat_stats and bat.get("runs", 0) > 0:
        meters.append(_performance_meter("SR", bat["sr"], 200, clr))
        meters.append(_performance_meter("AVG", bat["average"], 60, clr))
        meters.append(_performance_meter("BDY%", bat["boundary_pct"], 40, "#00D4FF"))
    if bowl_stats and bowl.get("wickets", 0) > 0:
        meters.append(_performance_meter("ECO", max(0, 12 - bowl["economy"]) if isinstance(bowl["economy"], (int, float)) else 0, 12, "#ff4757"))
        meters.append(_performance_meter("DOT%", bowl["dot_pct"], 60, "#a855f7"))

    if meters:
        profile_children.append(
            html.Div(meters, className="glass-card reveal", style={"marginBottom": "24px"})
        )

    # Radar chart
    radar_fig = _radar_chart(bat_stats, bowl_stats, clr)
    if radar_fig:
        profile_children.append(
            html.Div(
                dcc.Graph(figure=radar_fig, config={"displayModeBar": False}),
                className="glass-card reveal-scale", style={"marginBottom": "24px", "maxWidth": "400px"}
            )
        )

    profile = html.Div(profile_children)

    # ── Charts ───────────────────────────────────────────────────────────────
    charts = []

    def _chart_wrap(fig, cls="glass-card"):
        return html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}), className=cls)

    # Batting form
    if role in ("Batter", "All-rounder"):
        sb = player_season_batting(player, d)
        if not sb.empty:
            fig_runs = px.bar(sb, x="Season", y="runs", title=f"Season-wise Runs — {player}",
                              text="runs", color_discrete_sequence=[clr])
            fig_runs.update_traces(
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.55)", size=11),
                marker_line_width=0,
            )
            apply_dark_theme(fig_runs, height=320,
                             xaxis=dict(dtick=1, showgrid=False),
                             yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))

            fig_form = go.Figure()
            fig_form.add_trace(go.Scatter(
                x=sb["Season"], y=sb["sr"], name="Strike Rate",
                mode="lines+markers",
                line=dict(color="#00d4ff", width=2.5, shape="spline"),
                marker=dict(size=7, color="#00d4ff"),
                hovertemplate="Season %{x}<br>SR: %{y:.1f}<extra></extra>",
            ))
            fig_form.add_trace(go.Scatter(
                x=sb["Season"], y=sb["average"], name="Average",
                mode="lines+markers",
                line=dict(color="#f5a623", width=2.5, shape="spline"),
                marker=dict(size=7, color="#f5a623"),
                yaxis="y2",
                hovertemplate="Season %{x}<br>Avg: %{y:.1f}<extra></extra>",
            ))
            apply_dark_theme(fig_form, height=320,
                             title="Batting Form — Strike Rate & Average",
                             yaxis=dict(title="Strike Rate"),
                             yaxis2=dict(title="Average", overlaying="y", side="right", showgrid=False),
                             xaxis=dict(dtick=1, showgrid=False),
                             legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

            charts.append(html.Div([
                _chart_wrap(fig_runs, "glass-card"),
                _chart_wrap(fig_form, "glass-card"),
            ], className="chart-row two-col reveal"))

    # Bowling form
    if role in ("Bowler", "All-rounder"):
        sw = player_season_bowling(player, d)
        if not sw.empty:
            fig_wkts = px.bar(sw, x="Season", y="wickets",
                              title=f"Season-wise Wickets — {player}",
                              text="wickets",
                              color_discrete_sequence=["#ff4757"])
            fig_wkts.update_traces(
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.55)", size=11),
                marker_line_width=0,
            )
            apply_dark_theme(fig_wkts, height=320,
                             xaxis=dict(dtick=1, showgrid=False),
                             yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))

            fig_bform = go.Figure()
            fig_bform.add_trace(go.Scatter(
                x=sw["Season"], y=sw["economy"], name="Economy",
                mode="lines+markers",
                line=dict(color="#00d4ff", width=2.5, shape="spline"),
                marker=dict(size=7),
                hovertemplate="Season %{x}<br>Eco: %{y:.2f}<extra></extra>",
            ))
            fig_bform.add_trace(go.Scatter(
                x=sw["Season"], y=sw["dot_pct"], name="Dot %",
                mode="lines+markers",
                line=dict(color="#f5a623", width=2.5, shape="spline"),
                marker=dict(size=7),
                yaxis="y2",
                hovertemplate="Season %{x}<br>Dot%%: %{y:.1f}<extra></extra>",
            ))
            apply_dark_theme(fig_bform, height=320,
                             title="Bowling Form — Economy & Dot Ball %",
                             yaxis=dict(title="Economy"),
                             yaxis2=dict(title="Dot %", overlaying="y", side="right", showgrid=False),
                             xaxis=dict(dtick=1, showgrid=False),
                             legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

            charts.append(html.Div([
                _chart_wrap(fig_wkts, "glass-card"),
                _chart_wrap(fig_bform, "glass-card"),
            ], className="chart-row two-col reveal"))

    # Phase + Dismissal row
    phase_items = []

    if role in ("Batter", "All-rounder"):
        db = dismissal_breakdown(player, d)
        if not db.empty:
            fig_dis = px.pie(
                db, names="kind", values="count",
                title="Dismissal Breakdown", hole=0.5,
                color_discrete_sequence=["#f5a623","#00d4ff","#ff4757","#a855f7","#00ff87","#ff6b35"],
            )
            fig_dis.update_traces(
                textfont=dict(size=11, color="white"),
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
            apply_dark_theme(fig_dis, height=320)
            phase_items.append(_chart_wrap(fig_dis, "glass-card"))

        bp = player_phase_batting(player, d)
        if not bp.empty:
            fig_bphase = px.bar(
                bp, x="phase", y="runs", title="Batting by Phase",
                color="phase",
                color_discrete_map=PHASE_COLORS,
                text="sr",
            )
            fig_bphase.update_traces(
                texttemplate="SR: %{text:.0f}",
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.55)", size=11),
                marker_line_width=0,
            )
            apply_dark_theme(fig_bphase, height=320, showlegend=False)
            phase_items.append(_chart_wrap(fig_bphase, "glass-card"))

    if role in ("Bowler", "All-rounder"):
        blp = player_phase_bowling(player, d)
        if not blp.empty:
            fig_bowlphase = px.bar(
                blp, x="phase", y="economy", title="Economy by Phase",
                color="phase",
                color_discrete_map=PHASE_COLORS,
                text="economy",
            )
            fig_bowlphase.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.55)", size=11),
                marker_line_width=0,
            )
            apply_dark_theme(fig_bowlphase, height=320, showlegend=False)
            phase_items.append(_chart_wrap(fig_bowlphase, "glass-card"))

    if phase_items:
        ncols = len(phase_items)
        col_class = {1: "full-width", 2: "two-col", 3: "three-col"}.get(ncols, "two-col")
        charts.append(html.Div(phase_items, className=f"chart-row {col_class} reveal"))

    # Insight
    if role in ("Batter", "All-rounder") and bat.get("runs", 0) >= 500:
        sr_val = bat.get("sr", 0)
        avg_val = bat.get("average", 0)
        sixes   = bat.get("sixes", 0)
        charts.append(insight_card(
            "BATTER PROFILE",
            f"{player} has scored {bat['runs']:,} runs at an average of {avg_val} "
            f"and a strike rate of {sr_val}, hitting {sixes} sixes in IPL history.",
        ))
    elif role in ("Bowler", "All-rounder") and bowl.get("wickets", 0) >= 20:
        eco = bowl.get("economy", 0)
        charts.append(insight_card(
            "BOWLER PROFILE",
            f"{player} has taken {bowl['wickets']} wickets at an economy of {eco} "
            f"with a dot ball percentage of {bowl.get('dot_pct', 0)}%.",
        ))

    return profile, html.Div(charts)

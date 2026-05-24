"""
Teams Page — Immersive team hero with trophy cabinet, rankings, and charts.
"""

import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_team_list, get_season_range
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme
from utils.components import (
    page_hero, controls_bar, control_group,
    stat_card, section_header, trophy_cabinet,
    rankings_list, ranking_row, insight_card,
)

dash.register_page(__name__, path="/teams", name="Teams", order=5)

DATA  = load_data()
TEAMS = get_team_list(DATA["matches"])
SMIN, SMAX = get_season_range(DATA["matches"])


def _team_hero(team, clr, total, wins, losses, win_pct, titles_count, toss_wins, title_years):
    """Full-width team hero banner with identity, stats, and trophies."""
    abbr = team_abbr(team) or team[:3].upper()
    try:
        from utils.components import _hex_to_rgb
        r, g, b = _hex_to_rgb(clr)
        glow = f"rgba({r},{g},{b},0.12)"
        border_c = f"rgba({r},{g},{b},0.3)"
    except Exception:
        glow = "rgba(245,166,35,0.12)"
        border_c = "rgba(245,166,35,0.3)"

    return html.Div([
        # Background glow
        html.Div(style={
            "position": "absolute", "inset": "0",
            "background": f"radial-gradient(ellipse 70% 80% at 10% 50%, {glow} 0%, transparent 60%)",
            "pointerEvents": "none",
        }),
        html.Div(style={
            "position": "absolute", "top": "0", "left": "0", "right": "0", "height": "3px",
            "background": f"linear-gradient(90deg, {clr}, transparent)",
        }),
        # Content
        html.Div([
            # Left: identity
            html.Div([
                html.Div(abbr, style={
                    "fontFamily": "'Orbitron', sans-serif",
                    "fontSize": "clamp(3rem, 8vw, 6rem)",
                    "fontWeight": "900",
                    "color": clr,
                    "letterSpacing": "0.06em",
                    "lineHeight": "1",
                    "filter": f"drop-shadow(0 0 24px {clr})",
                }),
                html.Div(team, style={
                    "fontFamily": "'Space Grotesk', sans-serif",
                    "fontSize": "0.9rem",
                    "color": "rgba(255,255,255,0.5)",
                    "letterSpacing": "0.04em",
                    "marginTop": "6px",
                }),
                html.Div([
                    html.Span(f"🏆 {titles_count} IPL Title{'s' if titles_count != 1 else ''}",
                              className="badge badge-gold",
                              style={"marginTop": "12px", "display": "inline-block"}),
                ]),
            ], style={"flex": "1"}),
            # Center: stats
            html.Div([
                _mini_stat(str(total), "Matches"),
                _mini_stat(str(wins), "Wins", clr),
                _mini_stat(f"{win_pct}%", "Win Rate", clr),
                _mini_stat(str(toss_wins), "Toss Wins"),
            ], style={"display": "flex", "gap": "24px", "flexWrap": "wrap",
                      "alignItems": "center", "justifyContent": "center"}),
            # Right: trophies
            html.Div([
                html.Div("TITLE YEARS", style={
                    "fontFamily": "'JetBrains Mono', monospace",
                    "fontSize": "0.62rem",
                    "letterSpacing": "0.14em",
                    "color": "rgba(255,255,255,0.35)",
                    "textTransform": "uppercase",
                    "marginBottom": "8px",
                }),
                trophy_cabinet(title_years),
            ], style={"flex": "1", "textAlign": "right"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "32px",
                  "flexWrap": "wrap", "position": "relative", "zIndex": "1"}),
    ], className="glass-card chart-card reveal", style={
        "marginBottom": "24px",
        "borderColor": border_c,
        "position": "relative",
        "overflow": "hidden",
        "padding": "28px 32px",
    })


def _mini_stat(val, lbl, color="#ffffff"):
    return html.Div([
        html.Div(val, style={
            "fontFamily": "'Orbitron', sans-serif",
            "fontSize": "1.8rem", "fontWeight": "700",
            "color": color, "lineHeight": "1",
        }),
        html.Div(lbl, style={
            "fontFamily": "'JetBrains Mono', monospace",
            "fontSize": "0.62rem", "textTransform": "uppercase",
            "letterSpacing": "0.1em", "color": "rgba(255,255,255,0.4)",
            "marginTop": "4px",
        }),
    ], style={"textAlign": "center"})


layout = html.Div([
    page_hero(
        "🛡️ TEAM ANALYTICS",
        "Franchise ", "Intelligence",
        subtitle="Title tallies, win rates, top performers, venue dominance — every franchise, every season.",
    ),

    controls_bar(
        control_group(
            "Select Team",
            dcc.Dropdown(
                id="ta-team",
                options=[{"label": t, "value": t} for t in TEAMS],
                value="Mumbai Indians" if "Mumbai Indians" in TEAMS else TEAMS[0],
                clearable=False,
                style={"color": "black"},
            ),
        ),
    ),

    html.Div(id="ta-hero"),
    html.Div(id="ta-kpis"),
    html.Div(id="ta-charts"),
])


@callback(
    Output("ta-hero",   "children"),
    Output("ta-kpis",   "children"),
    Output("ta-charts", "children"),
    Input("ta-team",    "value"),
)
def update_team(team):
    if not team:
        return None, None, None

    m   = DATA["matches"]
    d   = DATA["deliveries"]
    clr = team_color(team) or "#f5a623"

    tm     = m[(m["Team1"] == team) | (m["Team2"] == team)]
    total  = len(tm)
    wins   = int((tm["Winner"] == team).sum())
    losses = total - wins - int((tm.get("Result", "").eq("No Result")).sum()) - int((tm.get("Result", "").eq("Tie")).sum())
    win_pct= round(wins / total * 100, 1) if total else 0

    titles_count = 0
    title_years  = []
    if "Match_Type" in m.columns:
        finals = m[m["Match_Type"] == "Final"]
        won    = finals[finals["Winner"] == team]
        titles_count = len(won)
        if "Date" in won.columns:
            title_years = sorted(pd.to_datetime(won["Date"], errors="coerce").dt.year.dropna().astype(int).tolist())
        elif "Season" in won.columns:
            title_years = sorted(won["Season"].dropna().astype(int).tolist())

    toss_wins = int((tm["Toss_Winner"] == team).sum())

    # Hero banner
    hero = _team_hero(team, clr, total, wins, losses, win_pct, titles_count, toss_wins, title_years)

    # Season performance chart
    tc  = tm.copy()
    tc["is_win"] = (tc["Winner"] == team).astype(int)
    sw  = tc.groupby("Season")["is_win"].sum().reset_index(name="Wins")
    sm  = tm.groupby("Season").size().reset_index(name="Matches")
    sw  = sw.merge(sm, on="Season")
    sw["Win%"] = round(sw["Wins"] / sw["Matches"] * 100, 1)

    fig_season = go.Figure()
    fig_season.add_trace(go.Bar(
        x=sw["Season"], y=sw["Wins"], name="Wins",
        marker=dict(color=clr, opacity=0.75, line=dict(width=0)),
        hovertemplate="Season %{x}<br>Wins: %{y}<extra></extra>",
    ))
    fig_season.add_trace(go.Scatter(
        x=sw["Season"], y=sw["Win%"], name="Win %",
        mode="lines+markers", yaxis="y2",
        line=dict(color="#f5a623", width=2.5, shape="spline"),
        marker=dict(size=7, color="#f5a623"),
        hovertemplate="Season %{x}<br>Win%%: %{y}<extra></extra>",
    ))
    apply_dark_theme(fig_season,
                     title=f"{team_abbr(team)} — Season-by-Season Performance",
                     height=320,
                     yaxis=dict(title="Wins", gridcolor="rgba(255,255,255,0.04)"),
                     yaxis2=dict(title="Win %", overlaying="y", side="right", showgrid=False),
                     xaxis=dict(dtick=1, showgrid=False),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"),
                     barmode="group")

    # Top scorers
    team_del  = d[d["Batting_Team"] == team]
    top_bat   = team_del.groupby("Batter")["Batsman_Runs"].sum().nlargest(10).reset_index()
    max_runs  = int(top_bat["Batsman_Runs"].max()) if not top_bat.empty else 1

    fig_topbat = go.Figure(go.Bar(
        x=top_bat["Batsman_Runs"][::-1],
        y=top_bat["Batter"][::-1],
        orientation="h",
        marker=dict(color=clr, opacity=0.8, line=dict(width=0)),
        text=top_bat["Batsman_Runs"][::-1],
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.5)", size=11),
        hovertemplate="%{y}: %{x} runs<extra></extra>",
    ))
    apply_dark_theme(fig_topbat, height=360,
                     title=f"Top Run Scorers — {team_abbr(team)}",
                     xaxis=dict(showgrid=False),
                     margin=dict(l=160, r=60, t=44, b=36))

    # Top wicket takers
    team_bowl = d[d["Bowling_Team"] == team]
    wkt_mask  = (
        (team_bowl["Is_Wicket"] == 1) &
        team_bowl["Player_Dismissed"].notna() &
        (~team_bowl["Dismissal_Kind"].isin(["Run Out","Retired Hurt","Retired Out","Obstructing The Field"]))
    )
    top_bowl = team_bowl[wkt_mask].groupby("Bowler").size().nlargest(10).reset_index(name="Wickets")

    fig_topbowl = go.Figure(go.Bar(
        x=top_bowl["Wickets"][::-1],
        y=top_bowl["Bowler"][::-1],
        orientation="h",
        marker=dict(color="#ff4757", opacity=0.8, line=dict(width=0)),
        text=top_bowl["Wickets"][::-1],
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.5)", size=11),
        hovertemplate="%{y}: %{x} wickets<extra></extra>",
    ))
    apply_dark_theme(fig_topbowl, height=360,
                     title=f"Top Wicket Takers — {team_abbr(team)}",
                     xaxis=dict(showgrid=False),
                     margin=dict(l=160, r=60, t=44, b=36))

    # Venue performance
    tm_v = tm.copy()
    tm_v["is_win"] = (tm_v["Winner"] == team).astype(int)
    vp = (tm_v.groupby("Venue")
               .agg(matches=("is_win","count"), wins=("is_win","sum"))
               .reset_index())
    vp["win_pct"] = round(vp["wins"] / vp["matches"] * 100, 1)
    vp = vp[vp["matches"] >= 3].nlargest(8, "matches")
    vp["short_venue"] = vp["Venue"].str[:28]

    fig_venue = go.Figure()
    fig_venue.add_trace(go.Bar(
        x=vp["short_venue"], y=vp["matches"], name="Matches",
        marker=dict(color="rgba(255,255,255,0.12)", line=dict(width=0)),
    ))
    fig_venue.add_trace(go.Bar(
        x=vp["short_venue"], y=vp["wins"], name="Wins",
        marker=dict(color=clr, opacity=0.75, line=dict(width=0)),
    ))
    apply_dark_theme(fig_venue, height=320,
                     title=f"Venue Performance (min 3 matches)",
                     barmode="group",
                     xaxis=dict(tickangle=-35, showgrid=False),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    # Rankings rows for top batters
    bat_rows = [
        ranking_row(i+1, row["Batter"], int(row["Batsman_Runs"]), max_runs, "", clr)
        for i, (_, row) in enumerate(top_bat.head(8).iterrows())
    ]

    kpis = html.Div()  # hero already shows KPIs

    charts = html.Div([
        html.Div([
            dcc.Graph(figure=fig_season, config={"displayModeBar": False})
        ], className="glass-card chart-card reveal", style={"marginBottom": "18px"}),

        html.Div([
            html.Div(dcc.Graph(figure=fig_topbat, config={"displayModeBar": False}),
                     className="glass-card"),
            html.Div(dcc.Graph(figure=fig_topbowl, config={"displayModeBar": False}),
                     className="glass-card"),
        ], className="chart-row two-col reveal"),

        html.Div([
            dcc.Graph(figure=fig_venue, config={"displayModeBar": False})
        ], className="glass-card chart-card reveal", style={"marginTop": "18px", "marginBottom": "18px"}),

        insight_card(
            "TEAM INSIGHT",
            f"{team} have won {wins} of {total} matches ({win_pct}% win rate) "
            f"and claimed {titles_count} IPL title{'s' if titles_count != 1 else ''} — "
            f"winning the toss {toss_wins} times across their history.",
        ),
    ])

    return hero, kpis, charts

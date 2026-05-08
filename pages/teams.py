"""Teams Analytics Page."""
import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_team_list, get_season_range
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme

dash.register_page(__name__, path="/teams", name="Teams", order=5)

DATA = load_data()
TEAMS = get_team_list(DATA["matches"])
SMIN, SMAX = get_season_range(DATA["matches"])

layout = html.Div([
    html.H2("🛡️ Team Analytics", className="page-header"),
    html.Div([
        html.Div([
            html.Label("Select Team", className="kpi-label mb-1"),
            dcc.Dropdown(id="ta-team", options=[{"label": t, "value": t} for t in TEAMS],
                         value="Mumbai Indians" if "Mumbai Indians" in TEAMS else TEAMS[0]),
        ], style={"flex": "1", "minWidth": "250px"}),
    ], className="mb-3"),
    html.Div(id="ta-kpis"),
    html.Div(id="ta-charts"),
])


@callback(
    Output("ta-kpis", "children"),
    Output("ta-charts", "children"),
    Input("ta-team", "value"),
)
def update_team(team):
    if not team:
        return None, None

    m = DATA["matches"]
    d = DATA["deliveries"]

    # Team matches
    tm = m[(m["Team1"] == team) | (m["Team2"] == team)]
    total = len(tm)
    wins = int((tm["Winner"] == team).sum())
    losses = total - wins - int((tm["Result"] == "No Result").sum()) - int((tm["Result"] == "Tie").sum())
    win_pct = round(wins / total * 100, 1) if total else 0
    titles_count = 0
    if "Match_Type" in m.columns:
        finals = m[m["Match_Type"] == "Final"]
        titles_count = int((finals["Winner"] == team).sum())

    # Home/Away
    toss_wins = int((tm["Toss_Winner"] == team).sum())
    bat_first_wins = int(((tm["Toss_Winner"] == team) & (tm["Toss_Decision"] == "Bat") & (tm["Winner"] == team)).sum())
    field_first_wins = int(((tm["Toss_Winner"] == team) & (tm["Toss_Decision"] == "Field") & (tm["Winner"] == team)).sum())

    clr = team_color(team)

    def kpi(label, val, c):
        return html.Div([html.Div(label, className="kpi-label"),
                          html.Div(str(val), className="kpi-value", style={"color": c})], className="kpi-card")

    kpis = html.Div([
        kpi("Matches", total, THEME["text"]),
        kpi("Wins", wins, THEME["neon_green"]),
        kpi("Losses", losses, THEME["neon_red"]),
        kpi("Win %", f"{win_pct}%", clr),
        kpi("Titles", titles_count, THEME["accent"]),
        kpi("Toss Wins", toss_wins, THEME["neon_blue"]),
    ], className="kpi-row")

    # Season-wise wins
    tm_copy = tm.copy()
    tm_copy["is_win"] = (tm_copy["Winner"] == team).astype(int)
    sw = tm_copy.groupby("Season")["is_win"].sum().reset_index(name="Wins")
    sm = tm.groupby("Season").size().reset_index(name="Matches")
    sw = sw.merge(sm, on="Season")
    sw["Win%"] = round(sw["Wins"] / sw["Matches"] * 100, 1)

    fig_season = go.Figure()
    fig_season.add_trace(go.Bar(x=sw["Season"], y=sw["Wins"], name="Wins", marker_color=clr))
    fig_season.add_trace(go.Scatter(x=sw["Season"], y=sw["Win%"], mode="lines+markers",
                                     name="Win %", yaxis="y2", line=dict(color=THEME["accent"], width=2)))
    apply_dark_theme(fig_season, title=f"{team_abbr(team)} — Season Performance", height=360,
                     yaxis=dict(title="Wins"), yaxis2=dict(title="Win %", overlaying="y", side="right"),
                     xaxis=dict(dtick=1), barmode="group")

    # Top scorers for this team
    team_del = d[d["Batting_Team"] == team]
    top_bat = team_del.groupby("Batter")["Batsman_Runs"].sum().nlargest(8).reset_index()
    fig_topbat = go.Figure(go.Bar(x=top_bat["Batsman_Runs"][::-1], y=top_bat["Batter"][::-1],
                                   orientation="h", marker_color=clr, text=top_bat["Batsman_Runs"][::-1], textposition="outside"))
    apply_dark_theme(fig_topbat, title="Top Run Scorers (for team)", height=340, xaxis=dict(showgrid=False))

    # Top wicket takers for this team
    team_bowl = d[d["Bowling_Team"] == team]
    wkt_mask = (team_bowl["Is_Wicket"] == 1) & (team_bowl["Player_Dismissed"].notna()) & \
               (~team_bowl["Dismissal_Kind"].isin(["Run Out", "Retired Hurt", "Retired Out", "Obstructing The Field"]))
    top_bowl = team_bowl[wkt_mask].groupby("Bowler").size().nlargest(8).reset_index(name="Wickets")
    fig_topbowl = go.Figure(go.Bar(x=top_bowl["Wickets"][::-1], y=top_bowl["Bowler"][::-1],
                                    orientation="h", marker_color="#f44336", text=top_bowl["Wickets"][::-1], textposition="outside"))
    apply_dark_theme(fig_topbowl, title="Top Wicket Takers (for team)", height=340, xaxis=dict(showgrid=False))

    # Venue performance
    tm_v = tm.copy()
    tm_v["is_win"] = (tm_v["Winner"] == team).astype(int)
    venue_perf = tm_v.groupby("Venue").agg(matches=("is_win", "count"), wins=("is_win", "sum")).reset_index()
    venue_perf["win_pct"] = round(venue_perf["wins"] / venue_perf["matches"] * 100, 1)
    venue_perf = venue_perf[venue_perf["matches"] >= 3].nlargest(8, "matches")

    fig_venue = go.Figure()
    fig_venue.add_trace(go.Bar(x=venue_perf["Venue"].str[:25], y=venue_perf["matches"], name="Matches", marker_color="rgba(255,255,255,0.15)"))
    fig_venue.add_trace(go.Bar(x=venue_perf["Venue"].str[:25], y=venue_perf["wins"], name="Wins", marker_color=clr))
    apply_dark_theme(fig_venue, title="Venue Performance (min 3 matches)", height=340, barmode="group",
                     xaxis=dict(tickangle=-45))

    charts = html.Div([
        html.Div(dcc.Graph(figure=fig_season, config={"displayModeBar": False}), className="glass-card mb-3"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_topbat, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_topbowl, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
        html.Div(dcc.Graph(figure=fig_venue, config={"displayModeBar": False}), className="glass-card mb-3"),
    ])

    return kpis, charts

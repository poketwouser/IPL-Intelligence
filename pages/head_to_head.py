"""Head-to-Head Page — ported from P07 notebook."""
import dash
from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_team_list, get_season_range
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme

try:
    from scipy import stats
    HAVE_KDE = True
except ImportError:
    HAVE_KDE = False

dash.register_page(__name__, path="/head-to-head", name="Head to Head", order=2)

DATA = load_data()
TEAMS = get_team_list(DATA["matches"])
SMIN, SMAX = get_season_range(DATA["matches"])

layout = html.Div([
    html.H2("⚔️ Head-to-Head Analysis", className="page-header"),
    html.Div([
        html.Div([
            html.Label("Team A", className="kpi-label mb-1"),
            dcc.Dropdown(id="h2h-team-a", options=[{"label": t, "value": t} for t in TEAMS],
                         placeholder="Choose Team A", className="mb-2"),
        ], style={"flex": "1", "minWidth": "200px"}),
        html.Div([
            html.Label("Team B", className="kpi-label mb-1"),
            dcc.Dropdown(id="h2h-team-b", options=[{"label": t, "value": t} for t in TEAMS],
                         placeholder="Choose Team B", className="mb-2"),
        ], style={"flex": "1", "minWidth": "200px"}),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "12px"}),
    html.Div([
        html.Label("Season Range", className="kpi-label mb-1"),
        dcc.RangeSlider(id="h2h-season", min=SMIN, max=SMAX, step=1,
                        value=[SMIN, SMAX],
                        marks={y: str(y) for y in range(SMIN, SMAX + 1, 2)},
                        tooltip={"placement": "bottom"}),
    ], className="mb-3"),
    html.Div(id="h2h-kpis"),
    html.Div(id="h2h-plots"),
])


@callback(
    Output("h2h-kpis", "children"),
    Output("h2h-plots", "children"),
    Input("h2h-team-a", "value"),
    Input("h2h-team-b", "value"),
    Input("h2h-season", "value"),
)
def update_h2h(ta, tb, season):
    if not season:
        return no_update, no_update

    m = DATA["matches"].copy()
    d = DATA["deliveries"].copy()
    s0, s1 = season

    # Filter
    if ta and tb:
        m = m[((m["Team1"]==ta)&(m["Team2"]==tb))|((m["Team1"]==tb)&(m["Team2"]==ta))]
    elif ta:
        m = m[(m["Team1"]==ta)|(m["Team2"]==ta)]
    elif tb:
        m = m[(m["Team1"]==tb)|(m["Team2"]==tb)]

    m = m[(m["Season"]>=s0)&(m["Season"]<=s1)]
    if m.empty:
        return html.Div("No matches found.", className="text-center text-muted py-4"), None

    d = d[d["Match_Id"].isin(m["Id"])]

    total = len(m)
    t1w = int((m["Winner"]==ta).sum()) if ta else 0
    t2w = int((m["Winner"]==tb).sum()) if tb else 0
    ties = int((m["Result"]=="Tie").sum()) if "Result" in m.columns else 0
    nr = int((m["Result"]=="No Result").sum()) if "Result" in m.columns else 0

    def kpi(label, val, clr):
        return html.Div([
            html.Div(label, className="kpi-label"),
            html.Div(str(val), className="kpi-value", style={"color": clr}),
        ], className="kpi-card")

    kpis = html.Div([
        kpi("Matches", total, THEME["text"]),
        kpi(f"{team_abbr(ta)} Wins" if ta else "Team A", t1w, team_color(ta)),
        kpi(f"{team_abbr(tb)} Wins" if tb else "Team B", t2w, team_color(tb)),
        kpi("Ties", ties, "#fdd835"),
        kpi("No Result", nr, "#94a3b8"),
    ], className="kpi-row")

    plots = []
    ca, cb = team_color(ta), team_color(tb)

    # Win Comparison
    fig_win = px.bar(x=[team_abbr(ta) or "A", team_abbr(tb) or "B"], y=[t1w, t2w],
                     color_discrete_sequence=[ca, cb], title="Win Comparison")
    fig_win.update_traces(marker_color=[ca, cb])
    apply_dark_theme(fig_win, height=280)

    # Toss gauge
    toss_pct = (m["Toss_Winner"]==m["Winner"]).mean()*100 if len(m) else 0
    fig_toss = go.Figure(go.Indicator(
        mode="gauge+number", value=toss_pct,
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": THEME["accent"]}},
        title={"text": "Toss → Match Win %"}))
    apply_dark_theme(fig_toss, height=280)

    plots.append(html.Div([
        html.Div(dcc.Graph(figure=fig_win, config={"displayModeBar": False}), className="glass-card"),
        html.Div(dcc.Graph(figure=fig_toss, config={"displayModeBar": False}), className="glass-card"),
    ], className="chart-row two-col"))

    # Season-wise wins
    st = m.groupby(["Season", "Winner"]).size().unstack(fill_value=0)
    fig_trend = go.Figure()
    for col in st.columns:
        fig_trend.add_trace(go.Scatter(x=st.index, y=st[col], mode="lines+markers",
                                       name=team_abbr(col), line=dict(color=team_color(col))))
    apply_dark_theme(fig_trend, title="Season-wise Wins", height=300,
                     xaxis=dict(dtick=1, showgrid=False))
    plots.append(html.Div(dcc.Graph(figure=fig_trend, config={"displayModeBar": False}), className="glass-card mb-3"))

    # Margin Distribution
    m2 = m.copy()
    m2["Result_Margin"] = pd.to_numeric(m2.get("Result_Margin", 0), errors="coerce").fillna(0)
    runs_df = m2[m2["Result"]=="Runs"] if "Result" in m2.columns else pd.DataFrame()
    wkts_df = m2[m2["Result"]=="Wickets"] if "Result" in m2.columns else pd.DataFrame()

    fig_margin = make_subplots(rows=1, cols=2, subplot_titles=("Defending (By Runs)", "Chasing (By Wickets)"))
    if not runs_df.empty:
        fig_margin.add_trace(go.Histogram(x=runs_df["Result_Margin"], nbinsx=15, marker_color="#ffb703"), 1, 1)
    if not wkts_df.empty:
        fig_margin.add_trace(go.Histogram(x=wkts_df["Result_Margin"], nbinsx=10, marker_color="#00b4d8"), 1, 2)
    apply_dark_theme(fig_margin, title="Match Margin Distribution", height=320, showlegend=False)
    plots.append(html.Div(dcc.Graph(figure=fig_margin, config={"displayModeBar": False}), className="glass-card mb-3"))

    # Top batters & bowlers in H2H
    top_bats = d.groupby(["Batter", "Batting_Team"])["Batsman_Runs"].sum().reset_index().nlargest(3, "Batsman_Runs").sort_values("Batsman_Runs", ascending=True)
    top_bats["display"] = top_bats.apply(lambda r: f"{r['Batter']} — {team_abbr(r['Batting_Team'])}", axis=1)
    top_bats["color"] = top_bats["Batting_Team"].map(team_color)

    fig_bat = go.Figure(go.Bar(x=top_bats["Batsman_Runs"], y=top_bats["display"], orientation="h",
                               marker_color=top_bats["color"], text=top_bats["Batsman_Runs"], textposition="outside"))
    apply_dark_theme(fig_bat, title="Top 3 Batters (Runs)", height=260)

    top_bowls = d[d["Is_Wicket"]==1].groupby(["Bowler", "Bowling_Team"]).size().reset_index(name="Wickets").nlargest(3, "Wickets").sort_values("Wickets", ascending=True)
    top_bowls["display"] = top_bowls.apply(lambda r: f"{r['Bowler']} — {team_abbr(r['Bowling_Team'])}", axis=1)
    top_bowls["color"] = top_bowls["Bowling_Team"].map(team_color)

    fig_bowl = go.Figure(go.Bar(x=top_bowls["Wickets"], y=top_bowls["display"], orientation="h",
                                marker_color=top_bowls["color"], text=top_bowls["Wickets"], textposition="outside"))
    apply_dark_theme(fig_bowl, title="Top 3 Bowlers (Wickets)", height=260)

    plots.append(html.Div([
        html.Div(dcc.Graph(figure=fig_bat, config={"displayModeBar": False}), className="glass-card"),
        html.Div(dcc.Graph(figure=fig_bowl, config={"displayModeBar": False}), className="glass-card"),
    ], className="chart-row two-col"))

    # Top venues
    venue_counts = m["Venue"].value_counts().head(3).reset_index()
    venue_counts.columns = ["Venue", "Matches"]
    fig_venues = px.bar(venue_counts, x="Venue", y="Matches", text="Matches", color="Matches", color_continuous_scale="Blues")
    fig_venues.update_traces(textposition="outside")
    apply_dark_theme(fig_venues, title="Top Venues", height=260)
    plots.append(html.Div(dcc.Graph(figure=fig_venues, config={"displayModeBar": False}), className="glass-card mb-3"))

    return kpis, html.Div(plots)

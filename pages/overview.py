"""Season Overview Page — ported from P06 notebook."""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme, REGION_COLORS

dash.register_page(__name__, path="/", name="Overview", order=0)

DATA = load_data()
M = DATA["matches"]
D = DATA["deliveries"]
V = DATA["venues"]


def build_kpi_card(label, value, color):
    return html.Div([
        html.Div(label, className="kpi-label"),
        html.Div(str(value), className="kpi-value", style={"color": color}),
    ], className="kpi-card")


# ─── Precompute static figures ────────────────────────────────────────────────
def compute_layout():
    m, d, v = M.copy(), D.copy(), V.copy()

    # KPIs
    total_matches = len(m)
    total_runs = int(d["Total_Runs"].sum())
    total_wickets = int(d["Is_Wicket"].sum())
    avg_runs = round(total_runs / total_matches, 1) if total_matches else 0
    avg_wickets = round(total_wickets / total_matches, 2) if total_matches else 0
    unique_venues = m["Venue"].nunique()

    # Most trophies
    if "Match_Type" in m.columns:
        finals = m[m["Match_Type"] == "Final"]
    else:
        finals = pd.DataFrame()
    titles = finals["Winner"].value_counts() if not finals.empty else pd.Series(dtype=int)
    if not titles.empty:
        max_t = titles.max()
        winners = titles[titles == max_t].index.tolist()
        trophies = " & ".join([team_abbr(t) for t in winners]) + f" ({max_t})"
    else:
        trophies = "N/A"

    # Most POTM
    potm_col = "Player_Of_Match" if "Player_Of_Match" in m.columns else None
    if potm_col:
        potm_counts = m[potm_col].value_counts()
        top_potm = f"{potm_counts.index[0]} ({potm_counts.iloc[0]})" if not potm_counts.empty else "N/A"
    else:
        top_potm = "N/A"

    # Best win%
    wins = m["Winner"].value_counts().rename_axis("Team").reset_index(name="Wins")
    played = pd.concat([m[["Team1"]].rename(columns={"Team1":"Team"}), m[["Team2"]].rename(columns={"Team2":"Team"})])
    played = played["Team"].value_counts().rename_axis("Team").reset_index(name="Played")
    tp = wins.merge(played, on="Team", how="right").fillna(0)
    tp["Win_pct"] = np.where(tp["Played"]>0, tp["Wins"]/tp["Played"]*100, 0)
    tp = tp.sort_values("Win_pct", ascending=False)
    best_team_display = f"{team_abbr(tp.iloc[0]['Team'])} ({tp.iloc[0]['Win_pct']:.1f}%)" if not tp.empty else "N/A"

    # Highest match total
    match_totals = d.groupby("Match_Id")["Total_Runs"].sum().reset_index()
    ht = match_totals.nlargest(1, "Total_Runs")
    if not ht.empty:
        hm_id = int(ht.iloc[0]["Match_Id"])
        hm_runs = int(ht.iloc[0]["Total_Runs"])
        row = m[m["Id"] == hm_id]
        hi_teams = f"{team_abbr(row.iloc[0]['Team1'])} v {team_abbr(row.iloc[0]['Team2'])}" if not row.empty else str(hm_id)
        highest_display = f"{hi_teams} ({hm_runs})"
    else:
        highest_display = "N/A"

    kpi_row = html.Div([
        build_kpi_card("Total Matches", f"{total_matches:,}", THEME["accent"]),
        build_kpi_card("Total Runs", f"{total_runs:,}", THEME["neon_green"]),
        build_kpi_card("Total Wickets", f"{total_wickets:,}", THEME["neon_red"]),
        build_kpi_card("Avg Runs/Match", avg_runs, THEME["neon_blue"]),
        build_kpi_card("Avg Wkts/Match", avg_wickets, "#e91e63"),
        build_kpi_card("Venues", unique_venues, THEME["neon_purple"]),
        build_kpi_card("Most Trophies", trophies, THEME["accent"]),
        build_kpi_card("Most POTM", top_potm, "#ffd166"),
        build_kpi_card("Best Win%", best_team_display, "#00e676"),
        build_kpi_card("Highest Total", highest_display, "#ffb703"),
    ], className="kpi-row")

    # ─── Chart 1: Avg Runs vs Avg Wickets per Season ──────────────────────────
    match_stats = d.groupby(["Match_Id", "Season"], dropna=False)[["Total_Runs", "Is_Wicket"]].sum().reset_index()
    season_stats = match_stats.groupby("Season")[["Total_Runs", "Is_Wicket"]].mean().reset_index().sort_values("Season")

    fig_rw = go.Figure()
    fig_rw.add_trace(go.Scatter(x=season_stats["Season"], y=season_stats["Total_Runs"],
                                name="Avg Runs/Match", mode="lines+markers",
                                line=dict(color="#00b4d8", width=3)))
    fig_rw.add_trace(go.Scatter(x=season_stats["Season"], y=season_stats["Is_Wicket"],
                                name="Avg Wkts/Match", mode="lines+markers",
                                line=dict(color="#f94144", width=3), yaxis="y2"))
    apply_dark_theme(fig_rw, title="Avg Runs vs Avg Wickets per Match (Season)", height=350,
                     yaxis=dict(title="Avg Runs", gridcolor="rgba(255,255,255,0.04)"),
                     yaxis2=dict(title="Avg Wickets", overlaying="y", side="right", showgrid=False),
                     xaxis=dict(tickmode="linear", showgrid=False))

    # ─── Chart 2/3: Heatmaps ─────────────────────────────────────────────────
    ball_counts = d.groupby(["Season", "Over"]).size().rename("Balls").reset_index()
    runs_sum = d.groupby(["Season", "Over"])["Batsman_Runs"].sum().rename("Runs").reset_index()
    wkts_sum = d.groupby(["Season", "Over"])["Is_Wicket"].sum().rename("Wickets").reset_index()

    heat = runs_sum.merge(ball_counts, on=["Season", "Over"], how="left")
    heat["RPO"] = heat["Runs"] / heat["Balls"] * 6
    heat2 = wkts_sum.merge(ball_counts, on=["Season", "Over"], how="left")
    heat2["WPO"] = heat2["Wickets"] / heat2["Balls"] * 6

    pivot_runs = heat.pivot(index="Season", columns="Over", values="RPO").sort_index().fillna(0)
    pivot_wk = heat2.pivot(index="Season", columns="Over", values="WPO").sort_index().fillna(0)

    fig_bat_heat = px.imshow(pivot_runs, color_continuous_scale="YlOrRd",
                             labels=dict(x="Over", y="Season", color="Avg Runs/Over"), aspect="auto",
                             title="Batting Intensity — Avg Runs per Over")
    apply_dark_theme(fig_bat_heat, height=360)

    fig_bowl_heat = px.imshow(pivot_wk, color_continuous_scale="PuBuGn",
                              labels=dict(x="Over", y="Season", color="Avg Wkts/Over"), aspect="auto",
                              title="Bowling Intensity — Avg Wickets per Over")
    apply_dark_theme(fig_bowl_heat, height=360)

    # ─── Chart 4/5: Top Batters & Bowlers ─────────────────────────────────────
    batter_team_map = d.groupby(["Batter", "Batting_Team"]).size().reset_index(name="c") \
        .sort_values(["Batter", "c"], ascending=[True, False]).drop_duplicates("Batter").set_index("Batter")["Batting_Team"].to_dict()
    bowler_team_map = d.groupby(["Bowler", "Bowling_Team"]).size().reset_index(name="c") \
        .sort_values(["Bowler", "c"], ascending=[True, False]).drop_duplicates("Bowler").set_index("Bowler")["Bowling_Team"].to_dict()

    top_bat = d.groupby("Batter")["Batsman_Runs"].sum().reset_index().nlargest(10, "Batsman_Runs")
    top_bat["Team"] = top_bat["Batter"].map(batter_team_map).fillna("N/A")
    top_bat["Color"] = top_bat["Team"].map(team_color).fillna("#888")

    fig_top_bat = go.Figure(go.Bar(
        x=top_bat["Batsman_Runs"][::-1], y=(top_bat["Batter"] + " — " + top_bat["Team"].map(team_abbr))[::-1],
        orientation="h", marker_color=top_bat["Color"][::-1],
        text=top_bat["Batsman_Runs"][::-1], textposition="outside"))
    apply_dark_theme(fig_top_bat, title="Top 10 Run Scorers", height=360, xaxis=dict(showgrid=False))

    top_bowl = d[d["Is_Wicket"]==1].groupby("Bowler").size().reset_index(name="Wickets").nlargest(10, "Wickets")
    top_bowl["Team"] = top_bowl["Bowler"].map(bowler_team_map).fillna("N/A")
    top_bowl["Color"] = top_bowl["Team"].map(team_color).fillna("#888")

    fig_top_bowl = go.Figure(go.Bar(
        x=top_bowl["Wickets"][::-1], y=(top_bowl["Bowler"] + " — " + top_bowl["Team"].map(team_abbr))[::-1],
        orientation="h", marker_color=top_bowl["Color"][::-1],
        text=top_bowl["Wickets"][::-1], textposition="outside"))
    apply_dark_theme(fig_top_bowl, title="Top 10 Wicket Takers", height=360, xaxis=dict(showgrid=False))

    # ─── Chart 6: POTM ───────────────────────────────────────────────────────
    if potm_col:
        potm_df = m[potm_col].value_counts().reset_index().head(10)
        potm_df.columns = ["Player", "Awards"]
        potm_df["Team"] = potm_df["Player"].map(batter_team_map).fillna("N/A")
        potm_df["Color"] = potm_df["Team"].map(team_color).fillna("#888")
        fig_potm = go.Figure(go.Bar(
            x=potm_df["Awards"][::-1], y=(potm_df["Player"] + " — " + potm_df["Team"].map(team_abbr))[::-1],
            orientation="h", marker_color=potm_df["Color"][::-1],
            text=potm_df["Awards"][::-1], textposition="outside"))
        apply_dark_theme(fig_potm, title="Most Player of the Match Awards", height=360, xaxis=dict(showgrid=False))
    else:
        fig_potm = go.Figure()

    # ─── Chart 7: Venue Map ──────────────────────────────────────────────────
    v_counts = m["Venue"].value_counts().reset_index()
    v_counts.columns = ["Venue", "Matches"]
    if not v.empty:
        vmap = v_counts.merge(v, on="Venue", how="left")
    else:
        vmap = v_counts
        vmap["lat"] = np.nan
        vmap["lon"] = np.nan
        vmap["Home"] = "N/A"

    fig_map = go.Figure()
    for _, row in vmap.dropna(subset=["lat", "lon"]).iterrows():
        home = row.get("Home", "N/A")
        clr = REGION_COLORS.get(home, team_color(home))
        fig_map.add_trace(go.Scattergeo(
            lon=[row["lon"]], lat=[row["lat"]],
            text=f"{row['Venue']}<br>{int(row['Matches'])} matches<br>Home: {home}",
            marker=dict(size=max(6, row["Matches"]**0.5 * 2.5), color=clr,
                        line=dict(width=0.6, color="white"), opacity=0.9),
            hoverinfo="text", showlegend=False))
    apply_dark_theme(fig_map, title="IPL Venues", height=480, showlegend=False,
                     geo=dict(scope="asia", projection_type="mercator",
                              center=dict(lat=22, lon=78),
                              lataxis=dict(range=[5, 35]), lonaxis=dict(range=[65, 90]),
                              showland=True, landcolor="rgb(15,25,40)",
                              showocean=True, oceancolor="rgb(10,15,25)",
                              showcountries=True, countrycolor="rgba(255,255,255,0.3)", showframe=False))

    # ─── Chart 8/9: Boundary% & Dot% ────────────────────────────────────────
    boundaries = d[d["Batsman_Runs"].isin([4, 6])].groupby("Season").size().reset_index(name="Boundaries")
    total_balls = d.groupby("Season").size().reset_index(name="TotalBalls")
    br = boundaries.merge(total_balls, on="Season", how="right").fillna(0)
    br["Boundary%"] = br["Boundaries"] / br["TotalBalls"] * 100
    br = br[(br["Season"] >= 2008) & (br["Season"] <= 2024)].sort_values("Season")

    fig_boundary = go.Figure(go.Scatter(
        x=br["Season"], y=br["Boundary%"], mode="lines+markers",
        line=dict(color="#ffd166", width=3, shape="spline"),
        marker=dict(size=9, color="#ffd166", line=dict(width=1.5, color="white")),
        fill="tozeroy", fillcolor="rgba(255,209,102,0.15)",
        hovertemplate="<b>Season %{x}</b><br>Boundary %: %{y:.2f}%<extra></extra>"))
    apply_dark_theme(fig_boundary, title="Season-wise Boundary %", height=360,
                     yaxis=dict(title="Boundary %", gridcolor="rgba(255,255,255,0.08)"),
                     xaxis=dict(title="Season", tickmode="linear", dtick=1, showgrid=False),
                     showlegend=False)

    dots = d[d["Batsman_Runs"] == 0].groupby("Season").size().reset_index(name="DotBalls")
    dr = dots.merge(total_balls, on="Season", how="right").fillna(0)
    dr["DotBall%"] = dr["DotBalls"] / dr["TotalBalls"] * 100
    dr = dr[(dr["Season"] >= 2008) & (dr["Season"] <= 2024)].sort_values("Season")

    fig_dot = go.Figure(go.Scatter(
        x=dr["Season"], y=dr["DotBall%"], mode="lines+markers",
        line=dict(color="#00b4d8", width=3, shape="spline"),
        marker=dict(size=9, color="#00b4d8", line=dict(width=1.5, color="white")),
        fill="tozeroy", fillcolor="rgba(0,180,216,0.15)",
        hovertemplate="<b>Season %{x}</b><br>Dot Ball %: %{y:.2f}%<extra></extra>"))
    apply_dark_theme(fig_dot, title="Season-wise Dot Ball %", height=360,
                     yaxis=dict(title="Dot Ball %", gridcolor="rgba(255,255,255,0.08)"),
                     xaxis=dict(title="Season", tickmode="linear", dtick=1, showgrid=False),
                     showlegend=False)

    return html.Div([
        html.H2("🏟️ IPL — Overall Overview (2008–2024)", className="page-header"),
        kpi_row,
        html.Div([dcc.Graph(figure=fig_rw, config={"displayModeBar": False})], className="glass-card mb-3"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_bat_heat, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_bowl_heat, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_top_bat, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_top_bowl, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
        html.Div([dcc.Graph(figure=fig_potm, config={"displayModeBar": False})], className="glass-card mb-3"),
        html.Div([dcc.Graph(figure=fig_map, config={"displayModeBar": False})], className="glass-card mb-3"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_boundary, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_dot, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
    ])


layout = compute_layout()

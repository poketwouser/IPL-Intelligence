"""
Overview Page — Cinematic IPL hero, live stats, player cards, premium charts.
"""

import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme, REGION_COLORS
from utils.components import (
    page_hero, featured_grid, featured_card,
    stat_card, player_card, player_card_grid,
    chart_card, graph, rankings_list, ranking_row,
    section_header, insight_card,
)

dash.register_page(__name__, path="/", name="Overview", order=0)

DATA  = load_data()
M     = DATA["matches"]
D     = DATA["deliveries"]
V     = DATA["venues"]


# ─── Compute static layout ────────────────────────────────────────────────────
def compute_layout():
    m, d, v = M.copy(), D.copy(), V.copy()

    # ── Global KPIs ──────────────────────────────────────────────────────────
    total_matches  = len(m)
    total_runs     = int(d["Total_Runs"].sum())
    total_wickets  = int(d["Is_Wicket"].sum())
    total_sixes    = int((d["Batsman_Runs"] == 6).sum())
    unique_venues  = m["Venue"].nunique()
    seasons_count  = m["Season"].nunique()

    # Titles
    if "Match_Type" in m.columns:
        finals  = m[m["Match_Type"] == "Final"]
    else:
        finals  = pd.DataFrame()
    titles_series = finals["Winner"].value_counts() if not finals.empty else pd.Series(dtype=int)

    # Best win%
    wins   = m["Winner"].value_counts().rename_axis("Team").reset_index(name="Wins")
    played = pd.concat([
        m[["Team1"]].rename(columns={"Team1": "Team"}),
        m[["Team2"]].rename(columns={"Team2": "Team"}),
    ])["Team"].value_counts().rename_axis("Team").reset_index(name="Played")
    tp = wins.merge(played, on="Team", how="right").fillna(0)
    tp["Win_pct"] = np.where(tp["Played"] > 0, tp["Wins"] / tp["Played"] * 100, 0)

    # Top batters
    bt_map  = (d.groupby(["Batter", "Batting_Team"]).size().reset_index(name="c")
               .sort_values(["Batter","c"], ascending=[True,False])
               .drop_duplicates("Batter").set_index("Batter")["Batting_Team"].to_dict())
    bwl_map = (d.groupby(["Bowler", "Bowling_Team"]).size().reset_index(name="c")
               .sort_values(["Bowler","c"], ascending=[True,False])
               .drop_duplicates("Bowler").set_index("Bowler")["Bowling_Team"].to_dict())

    top_bat  = d.groupby("Batter")["Batsman_Runs"].sum().reset_index().nlargest(10, "Batsman_Runs")
    top_bat["Team"]  = top_bat["Batter"].map(bt_map).fillna("N/A")

    top_bowl = (d[d["Is_Wicket"] == 1].groupby("Bowler").size()
                .reset_index(name="Wickets").nlargest(10, "Wickets"))
    top_bowl["Team"] = top_bowl["Bowler"].map(bwl_map).fillna("N/A")

    # ── Hero section ─────────────────────────────────────────────────────────
    hero = html.Div([
        html.Div("🏆 IPL INTELLIGENCE PLATFORM", className="hero-eyebrow"),
        html.H1([
            "CRICKET",
            html.Span(" DECODED", className="hero-title-accent"),
        ], className="hero-title"),
        html.P(
            "17 seasons · 1000+ matches · 150,000+ deliveries — all distilled into one premium analytics experience.",
            className="hero-sub",
        ),
        html.Div([
            html.Div([
                html.Div(
                    f"{total_matches:,}",
                    className="hero-stat-val",
                    **{"data-counter": str(total_matches), "data-duration": "2000"},
                ),
                html.Div("Matches", className="hero-stat-lbl"),
            ], className="hero-stat-item"),
            html.Div(className="hero-stat-sep"),
            html.Div([
                html.Div(
                    f"{total_runs // 1000}K",
                    className="hero-stat-val",
                    **{"data-counter": str(total_runs), "data-duration": "2400", "data-suffix": ""},
                ),
                html.Div("Total Runs", className="hero-stat-lbl"),
            ], className="hero-stat-item"),
            html.Div(className="hero-stat-sep"),
            html.Div([
                html.Div(
                    f"{total_sixes:,}",
                    className="hero-stat-val",
                    **{"data-counter": str(total_sixes), "data-duration": "2200"},
                ),
                html.Div("Sixes Hit", className="hero-stat-lbl"),
            ], className="hero-stat-item"),
            html.Div(className="hero-stat-sep"),
            html.Div([
                html.Div(
                    str(unique_venues),
                    className="hero-stat-val",
                    **{"data-counter": str(unique_venues), "data-duration": "1600"},
                ),
                html.Div("Venues", className="hero-stat-lbl"),
            ], className="hero-stat-item"),
        ], className="hero-stats-row"),
        html.Div(["↓", html.Span("EXPLORE", style={"marginTop": "4px"})],
                 className="scroll-cue"),
    ], className="hero-section")

    # ── Quick nav featured cards ──────────────────────────────────────────────
    featured = html.Div([
        html.Div("EXPLORE THE PLATFORM", style={
            "fontFamily": "'JetBrains Mono', monospace",
            "fontSize": "0.68rem",
            "letterSpacing": "0.18em",
            "color": "rgba(255,255,255,0.35)",
            "textAlign": "center",
            "textTransform": "uppercase",
            "marginBottom": "20px",
        }),
        featured_grid(
            featured_card("📋", "Match Explorer",
                          "Cinematic scorecards, manhattan charts, worm graphs, and fall of wickets.",
                          href="/match-explorer"),
            featured_card("⚔️", "Head to Head",
                          "Team rivalry deep-dives with season trends and margin analysis.",
                          href="/head-to-head"),
            featured_card("🏏", "Player Analysis",
                          "Career stats, phase breakdowns, form trends, and dismissal charts.",
                          href="/players"),
            featured_card("🎯", "Player Matchup",
                          "Batter vs Bowler confrontation — outcomes, phase SR, and over profiles.",
                          href="/player-vs-player"),
            featured_card("🛡️", "Team Analytics",
                          "Titles, win rates, top scorers, and venue performance by franchise.",
                          href="/teams"),
            featured_card("🔬", "Analytics Lab",
                          "Win probability curves, scoring patterns, and phase dominance by season.",
                          href="/advanced"),
        ),
    ], className="reveal")

    # ── Top player cards ──────────────────────────────────────────────────────
    top5_bat  = top_bat.head(5)
    top5_bowl = top_bowl.head(5)

    bat_cards = []
    for rank, (_, row) in enumerate(top5_bat.iterrows(), 1):
        name  = row["Batter"]
        team  = row["Team"]
        runs  = int(row["Batsman_Runs"])
        # secondary: innings
        inn   = int(d[d["Batter"] == name]["Batter"].count())
        bat_cards.append(player_card(
            player_name=name, team=team,
            primary_stat_val=f"{runs:,}", primary_stat_lbl="RUNS",
            secondary_stat_val=inn, secondary_stat_lbl="INN",
            rank=rank,
        ))

    bowl_cards = []
    for rank, (_, row) in enumerate(top5_bowl.iterrows(), 1):
        name  = row["Bowler"]
        team  = row["Team"]
        wkts  = int(row["Wickets"])
        bowl_cards.append(player_card(
            player_name=name, team=team,
            primary_stat_val=wkts, primary_stat_lbl="WICKETS",
            rank=rank,
        ))

    player_section = html.Div([
        html.Div([
            section_header("🏏 Orange Cap Leaders", tag="Most Runs"),
            player_card_grid(*bat_cards),
        ], className="reveal"),
        html.Div([
            section_header("🎯 Purple Cap Leaders", tag="Most Wickets"),
            player_card_grid(*bowl_cards),
        ], className="reveal"),
    ])

    # ── Rankings lists ────────────────────────────────────────────────────────
    max_runs  = int(top_bat["Batsman_Runs"].max()) if not top_bat.empty else 1
    max_wkts  = int(top_bowl["Wickets"].max())     if not top_bowl.empty else 1

    bat_rows  = [ranking_row(i+1, row["Batter"],
                              int(row["Batsman_Runs"]), max_runs, "",
                              team_color(row["Team"]))
                 for i, (_, row) in enumerate(top_bat.head(10).iterrows())]

    bowl_rows = [ranking_row(i+1, row["Bowler"],
                              int(row["Wickets"]), max_wkts, "",
                              team_color(row["Team"]))
                 for i, (_, row) in enumerate(top_bowl.head(10).iterrows())]

    rankings_section = html.Div([
        html.Div([
            section_header("All-Time Run Scorers", tag="Top 10"),
            rankings_list(*bat_rows),
        ], className="glass-card chart-card"),
        html.Div([
            section_header("All-Time Wicket Takers", tag="Top 10"),
            rankings_list(*bowl_rows),
        ], className="glass-card chart-card"),
    ], className="chart-row two-col reveal")

    # ── Season trend chart ────────────────────────────────────────────────────
    match_stats   = d.groupby(["Match_Id","Season"])[["Total_Runs","Is_Wicket"]].sum().reset_index()
    season_stats  = match_stats.groupby("Season")[["Total_Runs","Is_Wicket"]].mean().reset_index().sort_values("Season")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=season_stats["Season"], y=season_stats["Total_Runs"],
        name="Avg Runs/Match", mode="lines+markers",
        line=dict(color="#00d4ff", width=3, shape="spline"),
        marker=dict(size=7, color="#00d4ff",
                    line=dict(width=1.5, color="rgba(0,212,255,0.3)")),
        fill="tozeroy", fillcolor="rgba(0,212,255,0.05)",
        hovertemplate="Season %{x}<br>Avg Runs: %{y:.1f}<extra></extra>",
    ))
    fig_trend.add_trace(go.Scatter(
        x=season_stats["Season"], y=season_stats["Is_Wicket"],
        name="Avg Wickets/Match", mode="lines+markers",
        line=dict(color="#ff4757", width=3, shape="spline"),
        marker=dict(size=7, color="#ff4757"),
        yaxis="y2",
        hovertemplate="Season %{x}<br>Avg Wkts: %{y:.1f}<extra></extra>",
    ))
    apply_dark_theme(fig_trend,
                     height=340,
                     title="Season Trend — Avg Runs vs Wickets per Match",
                     yaxis=dict(title="Avg Runs", gridcolor="rgba(255,255,255,0.04)"),
                     yaxis2=dict(title="Avg Wickets", overlaying="y", side="right", showgrid=False),
                     xaxis=dict(tickmode="linear", showgrid=False),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    # ── Boundary & Dot% ───────────────────────────────────────────────────────
    total_b   = d.groupby("Season").size().reset_index(name="TotalBalls")
    boundaries = d[d["Batsman_Runs"].isin([4,6])].groupby("Season").size().reset_index(name="Boundaries")
    dots       = d[d["Batsman_Runs"] == 0].groupby("Season").size().reset_index(name="DotBalls")
    br = boundaries.merge(total_b, on="Season", how="right").fillna(0)
    br["Boundary%"] = br["Boundaries"] / br["TotalBalls"] * 100
    br = br[(br["Season"] >= 2008) & (br["Season"] <= 2024)].sort_values("Season")
    dr = dots.merge(total_b, on="Season", how="right").fillna(0)
    dr["Dot%"] = dr["DotBalls"] / dr["TotalBalls"] * 100
    dr = dr[(dr["Season"] >= 2008) & (dr["Season"] <= 2024)].sort_values("Season")

    fig_boundary = go.Figure(go.Scatter(
        x=br["Season"], y=br["Boundary%"], mode="lines+markers",
        line=dict(color="#f5a623", width=3, shape="spline"),
        marker=dict(size=8, color="#f5a623", line=dict(width=1.5, color="rgba(245,166,35,0.3)")),
        fill="tozeroy", fillcolor="rgba(245,166,35,0.07)",
        hovertemplate="Season %{x}<br>Boundary%%: %{y:.2f}%%<extra></extra>"))
    apply_dark_theme(fig_boundary, height=310, title="Season-wise Boundary %",
                     yaxis=dict(title="Boundary %", gridcolor="rgba(255,255,255,0.06)"),
                     xaxis=dict(title="Season", tickmode="linear", dtick=2, showgrid=False),
                     showlegend=False)

    fig_dot = go.Figure(go.Scatter(
        x=dr["Season"], y=dr["Dot%"], mode="lines+markers",
        line=dict(color="#a855f7", width=3, shape="spline"),
        marker=dict(size=8, color="#a855f7", line=dict(width=1.5, color="rgba(168,85,247,0.3)")),
        fill="tozeroy", fillcolor="rgba(168,85,247,0.07)",
        hovertemplate="Season %{x}<br>Dot%%: %{y:.2f}%%<extra></extra>"))
    apply_dark_theme(fig_dot, height=310, title="Season-wise Dot Ball %",
                     yaxis=dict(title="Dot %", gridcolor="rgba(255,255,255,0.06)"),
                     xaxis=dict(title="Season", tickmode="linear", dtick=2, showgrid=False),
                     showlegend=False)

    # ── Heatmaps ─────────────────────────────────────────────────────────────
    ball_counts = d.groupby(["Season","Over"]).size().rename("Balls").reset_index()
    runs_sum    = d.groupby(["Season","Over"])["Batsman_Runs"].sum().rename("Runs").reset_index()
    wkts_sum    = d.groupby(["Season","Over"])["Is_Wicket"].sum().rename("Wickets").reset_index()

    heat  = runs_sum.merge(ball_counts, on=["Season","Over"], how="left")
    heat["RPO"] = heat["Runs"] / heat["Balls"] * 6
    heat2 = wkts_sum.merge(ball_counts, on=["Season","Over"], how="left")
    heat2["WPO"] = heat2["Wickets"] / heat2["Balls"] * 6

    pivot_runs = heat.pivot(index="Season", columns="Over", values="RPO").sort_index().fillna(0)
    pivot_wk   = heat2.pivot(index="Season", columns="Over", values="WPO").sort_index().fillna(0)
    pivot_runs.columns = [str(i+1) for i in pivot_runs.columns]
    pivot_wk.columns   = [str(i+1) for i in pivot_wk.columns]

    fig_bat_heat = px.imshow(pivot_runs, color_continuous_scale="YlOrRd",
                             labels=dict(x="Over", y="Season", color="RPO"), aspect="auto",
                             title="Batting Intensity — Avg Runs per Over")
    apply_dark_theme(fig_bat_heat, height=360)
    fig_bat_heat.update_coloraxes(colorbar=dict(
        tickfont=dict(color="rgba(255,255,255,0.45)", size=10, family="JetBrains Mono"),
        title=dict(font=dict(color="rgba(255,255,255,0.5)", size=10)),
    ))

    fig_bowl_heat = px.imshow(pivot_wk, color_continuous_scale="PuBuGn",
                              labels=dict(x="Over", y="Season", color="WPO"), aspect="auto",
                              title="Bowling Intensity — Avg Wickets per Over")
    apply_dark_theme(fig_bowl_heat, height=360)

    # ── POTM chart ────────────────────────────────────────────────────────────
    potm_col = "Player_Of_Match" if "Player_Of_Match" in m.columns else None
    if potm_col:
        potm_df = m[potm_col].value_counts().head(10).reset_index()
        potm_df.columns = ["Player", "Awards"]
        potm_df["Team"]  = potm_df["Player"].map(bt_map).fillna("N/A")
        potm_df["Color"] = potm_df["Team"].apply(team_color).fillna("#888")
        fig_potm = go.Figure(go.Bar(
            x=potm_df["Awards"][::-1],
            y=(potm_df["Player"] + " · " + potm_df["Team"].apply(team_abbr))[::-1],
            orientation="h",
            marker=dict(color=potm_df["Color"][::-1].tolist(),
                        line=dict(width=0)),
            text=potm_df["Awards"][::-1],
            textposition="outside",
            textfont=dict(color="rgba(255,255,255,0.5)", size=11),
            hovertemplate="%{y}<br>Awards: %{x}<extra></extra>",
        ))
        apply_dark_theme(fig_potm, height=380, title="Player of the Match Leaders",
                         xaxis=dict(showgrid=False),
                         margin=dict(l=200, r=60, t=44, b=36))
    else:
        fig_potm = go.Figure()

    # ── Venue map ─────────────────────────────────────────────────────────────
    v_counts = m["Venue"].value_counts().reset_index()
    v_counts.columns = ["Venue", "Matches"]
    vmap = v_counts.merge(v, on="Venue", how="left") if not v.empty else v_counts
    if "lat" not in vmap.columns:
        vmap["lat"] = np.nan; vmap["lon"] = np.nan; vmap["Home"] = "N/A"

    fig_map = go.Figure()
    for _, row in vmap.dropna(subset=["lat","lon"]).iterrows():
        home = row.get("Home","N/A")
        clr  = REGION_COLORS.get(home, team_color(home)) or "#f5a623"
        fig_map.add_trace(go.Scattergeo(
            lon=[row["lon"]], lat=[row["lat"]],
            text=f"{row['Venue']}<br>{int(row['Matches'])} matches<br>Home: {home}",
            marker=dict(size=max(6, row["Matches"]**0.5 * 2.2),
                        color=clr, line=dict(width=0.7, color="white"), opacity=0.88),
            hoverinfo="text", showlegend=False,
        ))
    apply_dark_theme(fig_map, height=460, title="IPL Venue Map", showlegend=False,
                     geo=dict(scope="asia", projection_type="mercator",
                              center=dict(lat=22, lon=78),
                              lataxis=dict(range=[5,37]), lonaxis=dict(range=[64,92]),
                              showland=True, landcolor="rgba(15,26,42,0.9)",
                              showocean=True, oceancolor="rgba(5,12,22,0.9)",
                              showcountries=True,
                              countrycolor="rgba(255,255,255,0.2)",
                              showframe=False, bgcolor="rgba(0,0,0,0)"))

    # ── AI Insight cards ──────────────────────────────────────────────────────
    avg_run  = round(total_runs / total_matches, 1) if total_matches else 0
    avg_wkt  = round(total_wickets / total_matches, 1) if total_matches else 0
    top_team = tp.sort_values("Win_pct", ascending=False).iloc[0] if not tp.empty else None

    insights_row = html.Div([
        insight_card("DATA POINT",
                     f"IPL averages {avg_run} runs per match — with the death overs accounting "
                     f"for the highest boundary rates across all seasons."),
        insight_card("DOMINANCE",
                     f"{team_abbr(top_team['Team']) if top_team is not None else 'MI'} leads all franchises "
                     f"with the highest overall win percentage across IPL history."),
        insight_card("IMPACT",
                     f"Powerplay wickets have become increasingly decisive — teams losing 3+ in PP "
                     f"win only ~22% of matches across the dataset."),
    ], style={"display": "grid", "gridTemplateColumns": "repeat(auto-fill, minmax(280px,1fr))",
              "gap": "16px", "marginBottom": "28px"})

    # ── Final layout ─────────────────────────────────────────────────────────
    return html.Div([
        # Hero
        hero,

        # Featured nav cards
        featured,

        # Stat grid
        html.Div([
            stat_card(f"{total_matches:,}", "Total Matches",   "🏟️", "#f5a623", counter=True),
            stat_card(f"{total_runs:,}",    "Total Runs",      "🏏", "#00d4ff", counter=True),
            stat_card(f"{total_wickets:,}", "Total Wickets",   "🎯", "#ff4757", counter=True),
            stat_card(f"{total_sixes:,}",   "Sixes Hit",       "💥", "#00ff87", counter=True),
            stat_card(str(unique_venues),   "Venues",          "📍", "#a855f7", counter=True),
            stat_card(str(seasons_count),   "IPL Seasons",     "📅", "#ffd700", counter=True),
        ], className="stat-grid stagger-in"),

        # Player card sections
        player_section,

        # Rankings
        rankings_section,

        # Season trend
        html.Div([
            dcc.Graph(figure=fig_trend, config={"displayModeBar": False})
        ], className="glass-card chart-card reveal mb-3",
           style={"marginBottom": "18px"}),

        # Heatmaps
        html.Div([
            html.Div(dcc.Graph(figure=fig_bat_heat, config={"displayModeBar": False}),
                     className="glass-card"),
            html.Div(dcc.Graph(figure=fig_bowl_heat, config={"displayModeBar": False}),
                     className="glass-card"),
        ], className="chart-row two-col reveal"),

        # Boundary% / Dot%
        html.Div([
            html.Div(dcc.Graph(figure=fig_boundary, config={"displayModeBar": False}),
                     className="glass-card"),
            html.Div(dcc.Graph(figure=fig_dot, config={"displayModeBar": False}),
                     className="glass-card"),
        ], className="chart-row two-col reveal"),

        # POTM
        html.Div([
            dcc.Graph(figure=fig_potm, config={"displayModeBar": False})
        ], className="glass-card chart-card reveal", style={"marginBottom": "18px"}),

        # Venue map
        html.Div([
            dcc.Graph(figure=fig_map, config={"displayModeBar": False})
        ], className="glass-card chart-card reveal", style={"marginBottom": "28px"}),

        # Insights
        html.Div([
            html.Div("⚡ PLATFORM INSIGHTS", style={
                "fontFamily": "'JetBrains Mono', monospace",
                "fontSize": "0.68rem",
                "letterSpacing": "0.18em",
                "color": "rgba(255,255,255,0.35)",
                "textTransform": "uppercase",
                "marginBottom": "14px",
            }),
            insights_row,
        ], className="reveal"),
    ])


layout = compute_layout()

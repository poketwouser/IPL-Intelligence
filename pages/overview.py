"""
Overview — Cinematic homepage. Apple Sports × F1 aesthetic.
"""

import dash
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data_loader import load_data
from utils.constants import team_abbr, team_color, apply_dark_theme
from utils.components import (
    stat_card, player_card, player_card_grid,
    section_header, insight_card, featured_card,
    ranking_row, rankings_list,
)

dash.register_page(__name__, path="/", name="Overview", order=0)

DATA = load_data()
M    = DATA["matches"]
D    = DATA["deliveries"]
V    = DATA["venues"]


def build():
    m, d = M.copy(), D.copy()

    # ── Global KPIs ──────────────────────────────────────────────────
    total_matches = len(m)
    total_runs    = int(d["Total_Runs"].sum())
    total_sixes   = int((d["Batsman_Runs"] == 6).sum())
    seasons_count = m["Season"].nunique()
    total_players = d["Batter"].nunique()

    # ── Team/player maps ─────────────────────────────────────────────
    bat_team = (d.groupby(["Batter","Batting_Team"]).size().reset_index(name="c")
                .sort_values("c", ascending=False).drop_duplicates("Batter")
                .set_index("Batter")["Batting_Team"].to_dict())
    bowl_team = (d.groupby(["Bowler","Bowling_Team"]).size().reset_index(name="c")
                 .sort_values("c", ascending=False).drop_duplicates("Bowler")
                 .set_index("Bowler")["Bowling_Team"].to_dict())

    top_bat  = (d.groupby("Batter")["Batsman_Runs"].sum()
                .reset_index().nlargest(10, "Batsman_Runs"))
    top_bat["Team"] = top_bat["Batter"].map(bat_team).fillna("N/A")

    valid_wkt_mask = (
        (d["Is_Wicket"] == 1) &
        d["Player_Dismissed"].notna() &
        (~d["Dismissal_Kind"].isin(["Run Out","Retired Hurt","Retired Out","Obstructing The Field"]))
    )
    top_bowl = (d[valid_wkt_mask].groupby("Bowler").size()
                .reset_index(name="Wickets").nlargest(10, "Wickets"))
    top_bowl["Team"] = top_bowl["Bowler"].map(bowl_team).fillna("N/A")

    # ── Titles ───────────────────────────────────────────────────────
    finals = m[m["Match_Type"] == "Final"] if "Match_Type" in m.columns else pd.DataFrame()
    titles = finals["Winner"].value_counts() if not finals.empty else pd.Series(dtype=int)

    # ── Season champion ───────────────────────────────────────────────
    latest_season = int(m["Season"].max())
    champ_match   = finals[finals["Season"] == latest_season] if not finals.empty else pd.DataFrame()
    champion      = champ_match["Winner"].iloc[0] if not champ_match.empty else "N/A"
    orange_cap    = top_bat.iloc[0]["Batter"] if not top_bat.empty else "N/A"
    purple_cap    = top_bowl.iloc[0]["Bowler"] if not top_bowl.empty else "N/A"

    # ═══════════════════════════════════════════════════════════════════
    # CINEMATIC HERO
    # ═══════════════════════════════════════════════════════════════════
    hero = html.Section([
        html.Div(className="home-hero-bg", children=[
            html.Div(className="home-hero-grid"),
            html.Div(className="home-hero-orb home-hero-orb-1"),
            html.Div(className="home-hero-orb home-hero-orb-2"),
            html.Div(className="home-hero-orb home-hero-orb-3"),
        ]),

        html.Div([
            html.Div("IPL · 2008 – 2024 · CRICKET INTELLIGENCE", className="home-hero-eyebrow"),

            html.H1([
                html.Span("CRICKET", className="line-1"),
                html.Span("INTELLIGENCE", className="line-2"),
            ], className="home-hero-title"),

            html.P(
                f"{seasons_count} seasons. {total_matches:,} matches. {int(total_runs/1e6):.1f}M runs. "
                "Every delivery, every wicket, every moment — decoded.",
                className="home-hero-sub",
            ),

            html.Div([
                html.Div([
                    html.Div([
                        html.Span(className="stat-value",
                                  **{"data-counter": str(total_matches),
                                     "data-duration": "1600"}),
                        html.Span("+", style={"color": "var(--gold)"}),
                    ], className="hero-stat-val"),
                    html.Div("Matches", className="hero-stat-lbl"),
                ], className="hero-stat"),

                html.Div([
                    html.Div([
                        html.Span(className="stat-value",
                                  **{"data-counter": str(round(total_runs / 1e6, 1)),
                                     "data-suffix": "M", "data-decimals": "1",
                                     "data-duration": "1800"}),
                    ], className="hero-stat-val"),
                    html.Div("Runs Scored", className="hero-stat-lbl"),
                ], className="hero-stat"),

                html.Div([
                    html.Div([
                        html.Span(className="stat-value",
                                  **{"data-counter": str(total_sixes),
                                     "data-duration": "2000"}),
                        html.Span("+", style={"color": "var(--gold)"}),
                    ], className="hero-stat-val"),
                    html.Div("Sixes Hit", className="hero-stat-lbl"),
                ], className="hero-stat"),

                html.Div([
                    html.Div([
                        html.Span(className="stat-value",
                                  **{"data-counter": str(total_players),
                                     "data-duration": "1400"}),
                        html.Span("+", style={"color": "var(--gold)"}),
                    ], className="hero-stat-val"),
                    html.Div("Players", className="hero-stat-lbl"),
                ], className="hero-stat"),
            ], className="home-hero-stats"),

            html.Div([
                html.A("EXPLORE ANALYTICS →", href="/players",
                       className="btn btn-primary"),
                html.A("MATCH CENTER", href="/match-explorer",
                       className="btn btn-ghost"),
            ], className="home-hero-cta"),
        ], className="home-hero-content"),

        html.Div([
            html.Div(className="scroll-arrow"),
            html.Div("SCROLL", className="scroll-hint"),
        ], className="home-hero-scroll"),

    ], className="home-hero")

    # ═══════════════════════════════════════════════════════════════════
    # SEASON BANNER
    # ═══════════════════════════════════════════════════════════════════
    season_banner = html.Div([
        html.Div(str(latest_season), className="season-banner-year"),
        html.Div(className="season-banner-divider"),
        html.Div([
            html.Div(team_abbr(champion), className="season-banner-stat-val"),
            html.Div("IPL Champion", className="season-banner-stat-lbl"),
        ], className="season-banner-stat"),
        html.Div(className="season-banner-divider"),
        html.Div([
            html.Div(orange_cap.split()[-1], className="season-banner-stat-val"),
            html.Div("Orange Cap", className="season-banner-stat-lbl"),
        ], className="season-banner-stat"),
        html.Div(className="season-banner-divider"),
        html.Div([
            html.Div(purple_cap.split()[-1], className="season-banner-stat-val"),
            html.Div("Purple Cap", className="season-banner-stat-lbl"),
        ], className="season-banner-stat"),
        html.Div(className="season-banner-divider"),
        html.Div([
            html.Div(str(seasons_count), className="season-banner-stat-val"),
            html.Div("Seasons of Data", className="season-banner-stat-lbl"),
        ], className="season-banner-stat"),
    ], className="season-banner reveal")

    # ═══════════════════════════════════════════════════════════════════
    # FEATURED NAV CARDS
    # ═══════════════════════════════════════════════════════════════════
    nav_grid = html.Div([
        featured_card("/match-explorer",   "📋", "MATCH CENTER",
                      "Ball-by-Ball Cinema",
                      "Worm charts, Manhattan, Fall of Wickets — every match dissected.",
                      "#F5A623"),
        featured_card("/head-to-head",     "⚔️",  "RIVALRY",
                      "Head to Head",
                      "Season arcs, margin distributions, top performers in every rivalry.",
                      "#00D4FF"),
        featured_card("/players",          "🏏", "PLAYER INTEL",
                      "Player Analytics",
                      "Form curves, phase analysis, dismissal patterns, career arcs.",
                      "#00FF87"),
        featured_card("/player-vs-player", "🎯", "MATCHUP ARENA",
                      "Batter vs Bowler",
                      "Outcome distributions, phase strike rates, over-by-over profiling.",
                      "#7C3AED"),
        featured_card("/teams",            "🛡️", "TEAMS",
                      "Franchise Intelligence",
                      "Trophy cabinets, season performance, venue dominance.",
                      "#FF6B35"),
        featured_card("/advanced",         "🔬", "ANALYTICS LAB",
                      "Advanced Stats",
                      "Win probability curves, phase dominance, scoring evolution.",
                      "#FF1744"),
    ], className="featured-grid")

    # ═══════════════════════════════════════════════════════════════════
    # GLOBAL KPI STRIP
    # ═══════════════════════════════════════════════════════════════════
    kpi_strip = html.Div([
        stat_card(str(total_matches), "Matches",   "🏟", "#F5A623", counter=True, duration=1600),
        stat_card(f"{total_runs:,}",  "Total Runs","🏏", "#00D4FF", counter=True, duration=1800),
        stat_card(str(total_sixes),   "Sixes",     "💥", "#00FF87", counter=True, duration=2000),
        stat_card(str(seasons_count), "Seasons",   "📅", "#7C3AED"),
        stat_card(str(m["Venue"].nunique()), "Venues", "🗺", "#FF6B35"),
        stat_card(str(titles.max() if not titles.empty else 0),
                  "Most Titles",  "🏆", "#FFD700"),
    ], className="stat-grid stagger-in", style={"marginBottom": "var(--s8)"})

    # ═══════════════════════════════════════════════════════════════════
    # PLAYER CARDS — Top 5 Orange Cap
    # ═══════════════════════════════════════════════════════════════════
    bat_cards = player_card_grid([
        player_card(
            row["Batter"], row["Team"],
            f"{row['Batsman_Runs']:,}", "RUNS",
            rank=i + 1,
        )
        for i, (_, row) in enumerate(top_bat.head(5).iterrows())
    ])

    bowl_cards = player_card_grid([
        player_card(
            row["Bowler"], row["Team"],
            str(row["Wickets"]), "WKTs",
            rank=i + 1,
        )
        for i, (_, row) in enumerate(top_bowl.head(5).iterrows())
    ])

    # ═══════════════════════════════════════════════════════════════════
    # CHARTS
    # ═══════════════════════════════════════════════════════════════════

    # Season trend
    season_wins = (m.groupby(["Season","Winner"]).size().unstack(fill_value=0)
                   .sum(axis=1).reset_index(name="Matches"))
    season_wins["Season"] = season_wins["Season"].astype(int)

    sixes_season = (d[d["Batsman_Runs"] == 6].groupby("Season").size().reset_index(name="Sixes"))
    sixes_season["Season"] = sixes_season["Season"].astype(int)

    fig_season = go.Figure()
    fig_season.add_trace(go.Bar(
        x=season_wins["Season"], y=season_wins["Matches"],
        name="Matches",
        marker=dict(color="rgba(245,166,35,0.5)", line=dict(width=0)),
        hovertemplate="Season %{x}<br>Matches: %{y}<extra></extra>",
    ))
    fig_season.add_trace(go.Scatter(
        x=sixes_season["Season"], y=sixes_season["Sixes"],
        name="Sixes", yaxis="y2", mode="lines+markers",
        line=dict(color="#00FF87", width=2.5, shape="spline"),
        marker=dict(size=6),
        hovertemplate="Season %{x}<br>Sixes: %{y}<extra></extra>",
    ))
    apply_dark_theme(fig_season, title="Season Overview — Matches & Sixes", height=320,
                     yaxis=dict(title="Matches", gridcolor="rgba(255,255,255,0.04)"),
                     yaxis2=dict(title="Sixes", overlaying="y", side="right", showgrid=False),
                     xaxis=dict(dtick=1, showgrid=False),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"),
                     barmode="group")

    # Toss decision split
    toss_dec = m["Toss_Decision"].value_counts().reset_index()
    toss_dec.columns = ["Decision", "Count"]
    fig_toss = go.Figure(go.Pie(
        labels=toss_dec["Decision"],
        values=toss_dec["Count"],
        hole=0.6,
        marker=dict(colors=["#F5A623", "#00D4FF"], line=dict(color="rgba(0,0,0,0.5)", width=2)),
        textfont=dict(color="rgba(255,255,255,0.75)", size=12),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    apply_dark_theme(fig_toss, title="Toss Decision Split", height=280, showlegend=True,
                     legend=dict(x=0.5, y=-0.1, xanchor="center", orientation="h"))

    # Win by type
    result_counts = m["Result"].value_counts().head(4).reset_index()
    result_counts.columns = ["Result", "Count"]
    fig_result = go.Figure(go.Bar(
        x=result_counts["Count"], y=result_counts["Result"],
        orientation="h",
        marker=dict(color=["#F5A623","#00D4FF","#00FF87","#FF1744"][:len(result_counts)],
                    opacity=0.8, line=dict(width=0)),
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    apply_dark_theme(fig_result, title="Match Result Types", height=280, showlegend=False,
                     xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))

    # Boundary % by season
    d_copy = d.copy()
    d_copy["boundary"] = d_copy["Batsman_Runs"].isin([4, 6])
    bnd = d_copy.groupby("Season").agg(
        total=("Batsman_Runs", "count"),
        boundaries=("boundary", "sum"),
    ).reset_index()
    bnd["pct"] = round(bnd["boundaries"] / bnd["total"] * 100, 2)
    bnd["Season"] = bnd["Season"].astype(int)

    fig_bnd = go.Figure(go.Scatter(
        x=bnd["Season"], y=bnd["pct"],
        mode="lines+markers",
        line=dict(color="#F5A623", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(245,166,35,0.06)",
        marker=dict(size=7, color="#F5A623", line=dict(width=1.5, color="rgba(245,166,35,0.3)")),
        hovertemplate="Season %{x}<br>Boundary%%: %{y:.2f}%%<extra></extra>",
    ))
    apply_dark_theme(fig_bnd, title="Boundary % by Season", height=280,
                     xaxis=dict(dtick=1, showgrid=False),
                     yaxis=dict(title="%", gridcolor="rgba(255,255,255,0.04)"),
                     showlegend=False)

    # Titles bar
    if not titles.empty:
        tc = titles.reset_index()
        tc.columns = ["Team", "Titles"]
        tc = tc.sort_values("Titles", ascending=True)
        tc["color"] = tc["Team"].apply(lambda t: team_color(t) or "#F5A623")

        fig_titles = go.Figure(go.Bar(
            x=tc["Titles"], y=tc.apply(lambda r: team_abbr(r["Team"]), axis=1),
            orientation="h",
            marker=dict(color=tc["color"].tolist(), opacity=0.85, line=dict(width=0)),
            text=tc["Titles"], textposition="outside",
            textfont=dict(color="rgba(255,255,255,0.5)", size=11),
            hovertemplate="%{y}: %{x} titles<extra></extra>",
        ))
        apply_dark_theme(fig_titles, title="IPL Title Count", height=300,
                         xaxis=dict(showgrid=False, dtick=1),
                         margin=dict(l=72, r=60, t=44, b=36))
    else:
        fig_titles = go.Figure()
        apply_dark_theme(fig_titles, title="IPL Title Count", height=300)

    # Top batters ranking chart
    top10_bat = top_bat.head(10).sort_values("Batsman_Runs")
    top10_bat["color"] = top10_bat["Team"].apply(team_color)
    top10_bat["abbr"]  = top10_bat.apply(
        lambda r: f"{r['Batter'].split()[-1]} · {team_abbr(r['Team'])}", axis=1)

    fig_topbat = go.Figure(go.Bar(
        x=top10_bat["Batsman_Runs"], y=top10_bat["abbr"],
        orientation="h",
        marker=dict(color=top10_bat["color"].tolist(), opacity=0.82, line=dict(width=0)),
        text=top10_bat["Batsman_Runs"].apply(lambda v: f"{v:,}"),
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.45)", size=10),
        hovertemplate="%{y}: %{x:,} runs<extra></extra>",
    ))
    apply_dark_theme(fig_topbat, title="All-Time Top Run Scorers", height=360,
                     xaxis=dict(showgrid=False),
                     margin=dict(l=160, r=70, t=44, b=36))

    top10_bowl = top_bowl.head(10).sort_values("Wickets")
    top10_bowl["color"] = top10_bowl["Team"].apply(team_color)
    top10_bowl["abbr"]  = top10_bowl.apply(
        lambda r: f"{r['Bowler'].split()[-1]} · {team_abbr(r['Team'])}", axis=1)

    fig_topbowl = go.Figure(go.Bar(
        x=top10_bowl["Wickets"], y=top10_bowl["abbr"],
        orientation="h",
        marker=dict(color=top10_bowl["color"].tolist(), opacity=0.82, line=dict(width=0)),
        text=top10_bowl["Wickets"],
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.45)", size=10),
        hovertemplate="%{y}: %{x} wickets<extra></extra>",
    ))
    apply_dark_theme(fig_topbowl, title="All-Time Top Wicket Takers", height=360,
                     xaxis=dict(showgrid=False),
                     margin=dict(l=160, r=70, t=44, b=36))

    def _chart(fig):
        return html.Div(
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
            className="glass-card chart-card",
        )

    # ── Rankings lists ────────────────────────────────────────────────
    max_runs = int(top_bat.iloc[0]["Batsman_Runs"]) if not top_bat.empty else 1
    max_wkts = int(top_bowl.iloc[0]["Wickets"])     if not top_bowl.empty else 1

    bat_rankings = rankings_list(*[
        ranking_row(i+1, row["Batter"], int(row["Batsman_Runs"]),
                    max_runs, " runs", team_color(row["Team"]) or "#F5A623")
        for i, (_, row) in enumerate(top_bat.head(8).iterrows())
    ])

    bowl_rankings = rankings_list(*[
        ranking_row(i+1, row["Bowler"], int(row["Wickets"]),
                    max_wkts, " wkts", team_color(row["Team"]) or "#00D4FF")
        for i, (_, row) in enumerate(top_bowl.head(8).iterrows())
    ])

    # ═══════════════════════════════════════════════════════════════════
    # ASSEMBLE PAGE
    # ═══════════════════════════════════════════════════════════════════
    return html.Div([

        # 1 · Cinematic hero (full-width, breaks out of page-content padding)
        hero,

        # 2 · Season banner
        season_banner,

        # 3 · Featured nav grid
        section_header("EXPLORE", "ALL MODULES"),
        nav_grid,

        # 4 · Global KPIs
        section_header("PLATFORM STATS", f"{total_matches:,} MATCHES ANALYSED"),
        kpi_strip,

        # 5 · Top Player Cards
        section_header("ORANGE CAP — ALL TIME", "RUNS LEADERS"),
        bat_cards,
        html.Div(style={"height": "var(--s6)"}),

        section_header("PURPLE CAP — ALL TIME", "WICKETS LEADERS"),
        bowl_cards,
        html.Div(style={"height": "var(--s8)"}),

        # 6 · Charts
        section_header("SEASON OVERVIEW", "2008 – 2024"),
        html.Div([
            _chart(fig_season),
        ], className="reveal mb-lg"),

        html.Div([
            _chart(fig_toss),
            _chart(fig_result),
            _chart(fig_bnd),
        ], className="chart-row three-col reveal mb-lg"),

        # 7 · Titles
        section_header("TITLE RACE", "IPL CHAMPIONSHIPS"),
        html.Div(_chart(fig_titles), className="reveal mb-lg"),

        # 8 · Top 10 charts + rankings
        section_header("RECORDS", "ALL-TIME LEADERS"),
        html.Div([
            html.Div([
                section_header("TOP RUN SCORERS", "BATTING"),
                bat_rankings,
            ], className="glass-card reveal"),
            html.Div([
                section_header("TOP WICKET TAKERS", "BOWLING"),
                bowl_rankings,
            ], className="glass-card reveal"),
        ], className="chart-row two-col mb-lg"),

        html.Div([
            _chart(fig_topbat),
            _chart(fig_topbowl),
        ], className="chart-row two-col reveal mb-lg"),

        # 9 · Insights
        html.Div([
            insight_card("PLATFORM",
                         f"IPL Intelligence covers all {seasons_count} seasons from 2008 to 2024 — "
                         f"{total_matches:,} matches, {int(total_runs/1e6):.1f}M runs, "
                         f"and {total_sixes:,} sixes across {m['Venue'].nunique()} venues."),
            insight_card("DOMINANCE",
                         f"Mumbai Indians and Chennai Super Kings are the benchmark franchises — "
                         f"holding the most IPL titles and consistent top-3 finishes across eras."),
            insight_card("EVOLUTION",
                         "Death-over batting has fundamentally changed since 2016 — "
                         "run rates and six frequency in overs 16–20 have climbed every season."),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(280px, 1fr))",
            "gap": "var(--s5)",
            "marginBottom": "var(--s8)",
        }),

    ])


layout = build()

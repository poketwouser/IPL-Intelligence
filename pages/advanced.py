"""
Advanced Analytics Lab — Win probability, phase dominance, scoring patterns,
Impact Player analytics, and data-driven insights.
"""

import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_data
from utils.constants import apply_dark_theme, team_abbr, team_color
from utils.components import (
    page_hero, section_header, stat_card, insight_card, ranking_row, rankings_list,
)
from utils.analytics import impact_player_scores, team_impact_strategy

dash.register_page(__name__, path="/advanced", name="Analytics Lab", order=6)

DATA = load_data()
M    = DATA["matches"]
D    = DATA["deliveries"]


def build():
    m, d = M.copy(), D.copy()

    # ── Win probability by over (chasing) ─────────────────────────────────────
    match_winners = m.set_index("Id")["Winner"].to_dict()
    inn2          = d[d["Inning"] == 2]
    match_overs   = {}
    for _, row in inn2.iterrows():
        mid = row["Match_Id"]
        ov  = row["Over"]
        if mid not in match_overs:
            match_overs[mid] = {}
        if ov not in match_overs[mid]:
            match_overs[mid][ov] = {"team": row["Batting_Team"], "runs": 0}
        match_overs[mid][ov]["runs"] += row["Total_Runs"]

    over_data = {o: {"total": 0, "wins": 0} for o in range(1, 21)}
    for mid, overs in match_overs.items():
        winner        = match_winners.get(mid)
        first_entry   = list(overs.values())[0]
        chasing_team  = first_entry["team"]
        won           = winner == chasing_team
        for ov in overs:
            if 1 <= ov <= 20:
                over_data[ov]["total"] += 1
                if won:
                    over_data[ov]["wins"] += 1

    wp_overs = sorted(over_data.keys())
    wp_pct   = [
        round(over_data[o]["wins"] / over_data[o]["total"] * 100, 1)
        if over_data[o]["total"] else 50
        for o in wp_overs
    ]

    fig_wp = go.Figure()
    fig_wp.add_shape(type="line", x0=0, x1=20, y0=50, y1=50,
                     line=dict(color="rgba(255,255,255,0.15)", dash="dash", width=1))
    fig_wp.add_trace(go.Scatter(
        x=wp_overs, y=wp_pct,
        mode="lines+markers",
        fill="tozeroy", fillcolor="rgba(0,212,255,0.07)",
        line=dict(color="#00d4ff", width=3, shape="spline"),
        marker=dict(size=8, color="#00d4ff",
                    line=dict(width=1.5, color="rgba(0,212,255,0.3)")),
        hovertemplate="Over %{x}<br>Win Probability: %{y:.1f}%%<extra></extra>",
    ))
    apply_dark_theme(fig_wp,
                     title="Chasing Team Win Probability by Over",
                     height=360,
                     yaxis=dict(title="Win %", range=[0, 100],
                                gridcolor="rgba(255,255,255,0.04)"),
                     xaxis=dict(title="Over", tickmode="linear", dtick=1, showgrid=False),
                     showlegend=False)

    # ── Match total runs distribution ──────────────────────────────────────────
    match_totals = d.groupby("Match_Id")["Total_Runs"].sum().values
    fig_dist = go.Figure(go.Histogram(
        x=match_totals, nbinsx=32,
        marker=dict(color="rgba(245,166,35,0.55)",
                    line=dict(color="rgba(245,166,35,0.8)", width=1)),
        hovertemplate="Runs: %{x}<br>Matches: %{y}<extra></extra>",
    ))
    apply_dark_theme(fig_dist,
                     title="Match Total Runs Distribution",
                     height=340,
                     xaxis=dict(title="Total Runs (both innings)", showgrid=False),
                     yaxis=dict(title="Frequency", gridcolor="rgba(255,255,255,0.04)"),
                     showlegend=False)

    # ── Scoring patterns by over ────────────────────────────────────────────────
    over_stats = d.groupby("Over").agg(
        total=("Batsman_Runs", "count"),
        boundaries=("Batsman_Runs", lambda x: ((x == 4) | (x == 6)).sum()),
        sixes=("Batsman_Runs",     lambda x: (x == 6).sum()),
        dots=("Batsman_Runs",      lambda x: (x == 0).sum()),
    ).reset_index()
    over_stats = over_stats[(over_stats["Over"] >= 1) & (over_stats["Over"] <= 20)]
    over_stats["boundary_pct"] = round(over_stats["boundaries"] / over_stats["total"] * 100, 1)
    over_stats["six_pct"]      = round(over_stats["sixes"]      / over_stats["total"] * 100, 1)
    over_stats["dot_pct"]      = round(over_stats["dots"]       / over_stats["total"] * 100, 1)

    fig_scoring = go.Figure()
    fig_scoring.add_trace(go.Scatter(
        x=over_stats["Over"], y=over_stats["boundary_pct"],
        name="Boundary %", mode="lines+markers",
        line=dict(color="#f5a623", width=2.5, shape="spline"),
        marker=dict(size=7),
        hovertemplate="Over %{x}<br>Boundary%%: %{y:.1f}%%<extra></extra>",
    ))
    fig_scoring.add_trace(go.Scatter(
        x=over_stats["Over"], y=over_stats["dot_pct"],
        name="Dot Ball %", mode="lines+markers",
        line=dict(color="#a855f7", width=2.5, shape="spline"),
        marker=dict(size=7),
        hovertemplate="Over %{x}<br>Dot%%: %{y:.1f}%%<extra></extra>",
    ))
    fig_scoring.add_trace(go.Scatter(
        x=over_stats["Over"], y=over_stats["six_pct"],
        name="Six %", mode="lines+markers",
        line=dict(color="#00ff87", width=2, shape="spline", dash="dot"),
        marker=dict(size=6),
        hovertemplate="Over %{x}<br>Six%%: %{y:.1f}%%<extra></extra>",
    ))
    apply_dark_theme(fig_scoring,
                     title="Scoring Patterns Across 20 Overs",
                     height=340,
                     xaxis=dict(title="Over", tickmode="linear", dtick=1, showgrid=False),
                     yaxis=dict(title="Percentage (%)", gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    # ── Toss impact by season ──────────────────────────────────────────────────
    toss_data = m.copy()
    toss_data["toss_match"] = toss_data["Toss_Winner"] == toss_data["Winner"]
    toss_season = toss_data.groupby("Season")["toss_match"].mean().reset_index()
    toss_season["pct"] = round(toss_season["toss_match"] * 100, 1)

    fig_toss = go.Figure()
    fig_toss.add_shape(type="line",
                       x0=toss_season["Season"].min(),
                       x1=toss_season["Season"].max(),
                       y0=50, y1=50,
                       line=dict(color="rgba(255,255,255,0.15)", dash="dash", width=1))
    fig_toss.add_trace(go.Scatter(
        x=toss_season["Season"], y=toss_season["pct"],
        mode="lines+markers",
        line=dict(color="#f5a623", width=3, shape="spline"),
        marker=dict(size=9, color="#f5a623",
                    line=dict(width=1.5, color="rgba(245,166,35,0.3)")),
        fill="tonexty",
        fillcolor="rgba(245,166,35,0.06)",
        hovertemplate="Season %{x}<br>Toss → Win%%: %{y:.1f}%%<extra></extra>",
    ))
    apply_dark_theme(fig_toss,
                     title="Toss Winner → Match Winner % by Season",
                     height=320,
                     yaxis=dict(title="Win %", range=[30, 70],
                                gridcolor="rgba(255,255,255,0.04)"),
                     xaxis=dict(title="Season", dtick=1, showgrid=False),
                     showlegend=False)

    # ── Phase dominance across seasons ────────────────────────────────────────
    d_copy = d.copy()
    d_copy["phase"] = d_copy["Over"].apply(
        lambda o: "Powerplay" if o <= 6 else ("Middle" if o <= 15 else "Death")
    )
    phase_season = d_copy.groupby(["Season","phase"]).agg(
        runs=("Batsman_Runs", "sum"),
        balls=("Batsman_Runs", "count"),
    ).reset_index()
    phase_season["rpo"] = round(phase_season["runs"] / (phase_season["balls"] / 6), 2)

    PHASE_COLORS_MAP = {"Powerplay": "#ffd700", "Middle": "#1e90ff", "Death": "#dc143c"}
    fig_phase = go.Figure()
    for phase in ["Powerplay", "Middle", "Death"]:
        pdf = phase_season[phase_season["phase"] == phase]
        fig_phase.add_trace(go.Scatter(
            x=pdf["Season"], y=pdf["rpo"],
            name=phase, mode="lines+markers",
            line=dict(color=PHASE_COLORS_MAP[phase], width=2.5, shape="spline"),
            marker=dict(size=7),
            hovertemplate=f"{phase} — Season %{{x}}<br>RPO: %{{y:.2f}}<extra></extra>",
        ))
    apply_dark_theme(fig_phase,
                     title="Run Rate by Phase Across IPL Seasons",
                     height=320,
                     xaxis=dict(dtick=1, showgrid=False),
                     yaxis=dict(title="Runs per Over", gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    # ── Death-over evolution ────────────────────────────────────────────────────
    death = d_copy[d_copy["phase"] == "Death"].copy()
    death_season = death.groupby("Season").agg(
        runs=("Batsman_Runs","sum"),
        sixes=("Batsman_Runs", lambda x: (x==6).sum()),
        balls=("Batsman_Runs","count"),
    ).reset_index()
    death_season["rpo"]      = round(death_season["runs"] / (death_season["balls"]/6), 2)
    death_season["six_rate"] = round(death_season["sixes"] / death_season["balls"] * 100, 1)

    fig_death = go.Figure()
    fig_death.add_trace(go.Bar(
        x=death_season["Season"], y=death_season["rpo"],
        name="RPO (Death)",
        marker=dict(color="rgba(220,20,60,0.65)", line=dict(width=0)),
        hovertemplate="Season %{x}<br>Death RPO: %{y:.2f}<extra></extra>",
    ))
    fig_death.add_trace(go.Scatter(
        x=death_season["Season"], y=death_season["six_rate"],
        name="Six Rate %", yaxis="y2",
        mode="lines+markers",
        line=dict(color="#f5a623", width=2.5),
        marker=dict(size=7),
        hovertemplate="Season %{x}<br>Six Rate: %{y:.1f}%%<extra></extra>",
    ))
    apply_dark_theme(fig_death,
                     title="Death Overs Evolution — RPO & Six Rate",
                     height=320,
                     yaxis=dict(title="Runs per Over (Death)", gridcolor="rgba(255,255,255,0.04)"),
                     yaxis2=dict(title="Six Rate %", overlaying="y", side="right", showgrid=False),
                     xaxis=dict(dtick=1, showgrid=False),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"),
                     barmode="group")

    # ══════════════════════════════════════════════════════════════════════════
    # IMPACT PLAYER ANALYTICS — NEW SECTION
    # ══════════════════════════════════════════════════════════════════════════
    impact_df = impact_player_scores(d, m)
    team_strat = team_impact_strategy(d, m)

    # Impact Player leaderboard
    fig_impact = go.Figure()
    if not impact_df.empty:
        top_impact = impact_df.head(15).sort_values("impact_score")
        # Get team for each player
        bat_team_map = (d.groupby(["Batter","Batting_Team"]).size().reset_index(name="c")
                        .sort_values("c", ascending=False).drop_duplicates("Batter")
                        .set_index("Batter")["Batting_Team"].to_dict())

        top_impact["team"] = top_impact["Player"].map(bat_team_map).fillna("N/A")
        top_impact["color"] = top_impact["team"].apply(lambda t: team_color(t) or "#00ff87")
        top_impact["label"] = top_impact.apply(
            lambda r: f"{r['Player'].split()[-1]} · {team_abbr(r['team'])}", axis=1
        )

        fig_impact = go.Figure(go.Bar(
            x=top_impact["impact_score"], y=top_impact["label"],
            orientation="h",
            marker=dict(color=top_impact["color"].tolist(), opacity=0.85, line=dict(width=0)),
            text=top_impact["impact_score"].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            textfont=dict(color="rgba(255,255,255,0.5)", size=10),
            hovertemplate="%{y}<br>Impact Score: %{x:.1f}<extra></extra>",
        ))
    apply_dark_theme(fig_impact,
                     title="Impact Score Leaderboard — Top 15",
                     height=420,
                     xaxis=dict(title="Avg Impact Score per Match", showgrid=False),
                     margin=dict(l=160, r=70, t=44, b=36))

    # Team phase strategy heatmap
    fig_team_strat = go.Figure()
    if not team_strat.empty:
        # Pivot to create heatmap data
        for phase in ["Powerplay", "Middle", "Death"]:
            pdf = team_strat[team_strat["phase"] == phase].nlargest(10, "rpo")
            pdf["abbr"] = pdf["Batting_Team"].apply(team_abbr)
            fig_team_strat.add_trace(go.Bar(
                x=pdf["abbr"], y=pdf["rpo"],
                name=phase,
                marker=dict(color=PHASE_COLORS_MAP.get(phase, "#888"), opacity=0.8),
                hovertemplate=f"%{{x}} · {phase}<br>RPO: %{{y:.2f}}<extra></extra>",
            ))
    apply_dark_theme(fig_team_strat,
                     title="Team Run Rate by Phase — All-Time",
                     height=340,
                     barmode="group",
                     xaxis=dict(showgrid=False),
                     yaxis=dict(title="Runs per Over", gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    # Impact rankings list
    impact_rankings = []
    if not impact_df.empty:
        max_impact = impact_df.iloc[0]["impact_score"]
        impact_rankings = rankings_list(*[
            ranking_row(i+1, row["Player"], round(row["impact_score"], 1),
                        max_impact, " pts",
                        team_color(bat_team_map.get(row["Player"], "")) or "#00ff87")
            for i, (_, row) in enumerate(impact_df.head(10).iterrows())
        ])

    # ── Summary KPIs ──────────────────────────────────────────────────────────
    avg_wp_early = round(np.mean([wp_pct[i] for i in range(0, 6)]), 1)
    avg_wp_death = round(np.mean([wp_pct[i] for i in range(14, 20)]), 1)
    avg_toss_win = round(toss_season["pct"].mean(), 1)
    peak_rpo_over = over_stats.loc[over_stats["boundary_pct"].idxmax(), "Over"] if not over_stats.empty else "N/A"
    top_impactor = impact_df.iloc[0]["Player"].split()[-1] if not impact_df.empty else "N/A"
    top_impact_score = round(impact_df.iloc[0]["impact_score"], 1) if not impact_df.empty else 0

    kpis_row = html.Div([
        stat_card(f"{avg_wp_early}%",  "Chase Win% — PP",    "📊", "#00d4ff"),
        stat_card(f"{avg_wp_death}%",  "Chase Win% — Death", "📊", "#ff4757"),
        stat_card(f"{avg_toss_win}%",  "Avg Toss→Win %",     "🪙", "#f5a623"),
        stat_card(f"Over {peak_rpo_over}", "Peak Boundary Over", "💥", "#00ff87"),
        stat_card(f"{top_impact_score}", f"Top Impact ({top_impactor})", "⚡", "#7C3AED"),
    ], className="stat-grid stagger-in", style={"marginBottom": "28px"})

    # ── Layout ─────────────────────────────────────────────────────────────────
    def _card(fig):
        return html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}),
                        className="glass-card")

    return html.Div([
        page_hero(
            "🔬 ANALYTICS LAB",
            "Advanced ", "Intelligence",
            subtitle="Win probability curves, scoring patterns, toss impact, phase evolution, "
                     "and Impact Player analytics — all crunched from 150K+ deliveries.",
        ),

        kpis_row,

        # Win probability
        html.Div(_card(fig_wp), className="reveal", style={"marginBottom": "18px"}),

        # Match distribution + Scoring patterns
        html.Div([_card(fig_dist), _card(fig_scoring)],
                 className="chart-row two-col reveal"),

        # Toss + Phase dominance
        html.Div([_card(fig_toss), _card(fig_phase)],
                 className="chart-row two-col reveal", style={"marginTop": "18px"}),

        # Death overs
        html.Div(_card(fig_death), className="reveal",
                 style={"marginTop": "18px", "marginBottom": "28px"}),

        # ═══ IMPACT PLAYER SECTION ═══
        html.Div(className="section-divider"),
        section_header("⚡ IMPACT PLAYER ANALYTICS", "CONTRIBUTION SCORING"),

        html.Div([
            insight_card("METHODOLOGY",
                         "Impact Score = avg(runs + wickets × 25) per match. "
                         "Measures a player's total offensive contribution relative to appearances. "
                         "Players with 10+ matches included."),
        ], style={"marginBottom": "18px"}),

        html.Div([
            html.Div([
                section_header("IMPACT LEADERBOARD", "TOP 10"),
                impact_rankings if impact_rankings else html.P("No data", style={"color": "var(--t4)"}),
            ], className="glass-card reveal"),
            _card(fig_impact),
        ], className="chart-row two-col reveal", style={"marginBottom": "18px"}),

        html.Div(_card(fig_team_strat), className="reveal",
                 style={"marginBottom": "28px"}),

        # Insights
        html.Div([
            insight_card("WIN PROBABILITY",
                         f"Chasing teams have a {avg_wp_early}% win rate after the Powerplay "
                         f"and {avg_wp_death}% once they survive to the death overs."),
            insight_card("TOSS IMPACT",
                         f"On average, {avg_toss_win}% of toss winners also win the match — "
                         f"suggesting a modest but real advantage for toss winners."),
            insight_card("SCORING EVOLUTION",
                         "Death over RPO and six rates have climbed consistently since 2016 — "
                         "reflecting how T20 batting has evolved across IPL generations."),
        ], style={"display": "grid",
                  "gridTemplateColumns": "repeat(auto-fill, minmax(280px,1fr))",
                  "gap": "16px", "marginBottom": "28px"},
           className="reveal"),
    ])


layout = build()

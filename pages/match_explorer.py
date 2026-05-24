"""
Match Explorer — Cinematic scorecards, Manhattan chart, Worm, Fall of Wickets.
"""

import dash
from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_season_range
from utils.constants import team_abbr, team_color, apply_dark_theme
from utils.components import (
    page_hero, controls_bar, control_group,
    match_header_card, inning_header,
)

dash.register_page(__name__, path="/match-explorer", name="Match Explorer", order=1)

DATA  = load_data()
M     = DATA["matches"]
D     = DATA["deliveries"]
SMIN, SMAX = get_season_range(M)

layout = html.Div([
    page_hero(
        "📋 MATCH EXPLORER",
        "Scorecard ", "Cinema",
        subtitle="Ball-by-ball scorecards, worm charts, Manhattan charts, and fall of wickets — every match, every over.",
    ),

    controls_bar(
        control_group(
            "Season",
            dcc.Dropdown(
                id="me-season",
                options=[{"label": str(s), "value": s}
                         for s in sorted(M["Season"].dropna().unique())],
                value=int(M["Season"].max()),
                clearable=False,
                style={"color": "black"},
            ),
        ),
        control_group(
            "Select Match",
            dcc.Dropdown(id="me-match", placeholder="Choose a match…", style={"color": "black"}),
        ),
    ),

    html.Div(id="me-content"),
])


@callback(
    Output("me-match", "options"),
    Output("me-match", "value"),
    Input("me-season",  "value"),
)
def update_match_options(season):
    if not season:
        return [], None
    sm = M[M["Season"] == season].sort_values("Date")
    options = []
    for _, row in sm.iterrows():
        label = f"{team_abbr(row['Team1'])} vs {team_abbr(row['Team2'])}  ·  {str(row['Date'])[:10]}"
        if "Venue" in row and pd.notna(row["Venue"]):
            label += f"  @  {str(row['Venue'])[:28]}"
        options.append({"label": label, "value": int(row["Id"])})
    return options, options[0]["value"] if options else None


@callback(
    Output("me-content", "children"),
    Input("me-match",    "value"),
)
def render_scorecard(match_id):
    if not match_id:
        return html.P(
            "↑ Select a season and match above to view the scorecard.",
            style={"textAlign": "center", "color": "rgba(255,255,255,0.3)",
                   "fontFamily": "'JetBrains Mono', monospace", "fontSize": "0.82rem",
                   "padding": "48px 0"},
        )

    match = M[M["Id"] == match_id]
    if match.empty:
        return html.P("Match not found.", style={"color": "rgba(255,255,255,0.3)", "padding": "24px"})

    match = match.iloc[0]
    md    = D[D["Match_Id"] == match_id]

    team1  = match["Team1"]
    team2  = match["Team2"]
    winner = match.get("Winner", "N/A")
    result = match.get("Result", "")
    margin = match.get("Result_Margin", "")
    venue  = match.get("Venue", "")
    date   = str(match.get("Date", ""))[:10]
    potm   = match.get("Player_Of_Match", "N/A")

    result_text = f"{winner} won" if pd.notna(winner) and winner else "No Result"
    if pd.notna(result) and pd.notna(margin) and str(result).strip() and str(margin).strip():
        try:
            result_text += f" by {int(float(margin))} {result}".strip()
        except (ValueError, TypeError):
            pass

    header = match_header_card(team1, team2, date, str(venue), result_text, str(potm))

    # Determine batting order
    if match.get("Toss_Decision") == "Bat":
        first_bat  = match["Toss_Winner"]
        second_bat = team2 if team1 == match["Toss_Winner"] else team1
    else:
        second_bat = match["Toss_Winner"]
        first_bat  = team2 if team1 == match["Toss_Winner"] else team1

    sections = []

    for inn_num, bat_team in [(1, first_bat), (2, second_bat)]:
        inn_data = md[(md["Inning"] == inn_num) & (md["Batting_Team"] == bat_team)]
        if inn_data.empty:
            continue

        clr = team_color(bat_team) or "#f5a623"

        # Batting order
        batsmen_order, seen = [], set()
        for _, ball in inn_data.iterrows():
            for b in [ball["Batter"], ball.get("Non_Striker")]:
                if b and pd.notna(b) and b not in seen:
                    batsmen_order.append(b)
                    seen.add(b)

        dismissed_set = set(inn_data[inn_data["Is_Wicket"] == 1]["Player_Dismissed"].dropna())
        last_ball     = inn_data.iloc[-1]
        at_crease     = {last_ball["Batter"], last_ball.get("Non_Striker")}

        bat_rows = []
        for batsman in batsmen_order:
            b_balls = inn_data[
                (inn_data["Batter"] == batsman) &
                (~inn_data["Extras_Type"].isin(["Wides","Noballs"]))
            ]
            runs  = int(b_balls["Batsman_Runs"].sum())
            balls = len(b_balls)
            sr    = round(runs / balls * 100, 1) if balls else 0
            fours = int((b_balls["Batsman_Runs"] == 4).sum())
            sixes = int((b_balls["Batsman_Runs"] == 6).sum())

            dismissed  = batsman in dismissed_set
            at_crease_now = batsman in at_crease
            not_out    = not dismissed and at_crease_now
            runs_disp  = f"{runs}*" if not_out else str(runs)

            if dismissed:
                dis_row = inn_data[
                    (inn_data["Player_Dismissed"] == batsman) &
                    (inn_data["Is_Wicket"] == 1)
                ].iloc[0]
                dk      = dis_row.get("Dismissal_Kind", "")
                bowler  = dis_row.get("Bowler", "")
                fielder = dis_row.get("Fielder", "") if pd.notna(dis_row.get("Fielder", "")) else ""
                if dk == "Caught":
                    dis_text = f"c {fielder} b {bowler}"
                elif dk == "Bowled":
                    dis_text = f"b {bowler}"
                elif dk == "Lbw":
                    dis_text = f"lbw b {bowler}"
                elif dk == "Run Out":
                    dis_text = f"run out ({fielder})" if fielder else "run out"
                elif dk == "Stumped":
                    dis_text = f"st {fielder} b {bowler}"
                elif dk == "Caught And Bowled":
                    dis_text = f"c&b {bowler}"
                else:
                    dis_text = dk.lower() if dk else ""
            elif not_out:
                dis_text = "not out"
            else:
                dis_text = ""

            highlight_runs = runs >= 50
            bat_rows.append(html.Tr([
                html.Td(batsman, className="sc-player"),
                html.Td(dis_text, className="sc-dismissal"),
                html.Td(runs_disp,
                        className="sc-highlight" if highlight_runs else ""),
                html.Td(str(balls)),
                html.Td(str(fours)),
                html.Td(str(sixes)),
                html.Td(str(sr)),
            ]))

        bat_table = html.Table([
            html.Thead(html.Tr([
                html.Th(h) for h in ["Batter", "Dismissal", "R", "B", "4s", "6s", "SR"]
            ])),
            html.Tbody(bat_rows),
        ], className="scorecard-table")

        # Bowling table
        bowler_order, seen_b = [], set()
        for _, ball in inn_data.iterrows():
            b = ball["Bowler"]
            if b not in seen_b:
                bowler_order.append(b)
                seen_b.add(b)

        bowl_rows = []
        for bowler in bowler_order:
            b_data    = inn_data[inn_data["Bowler"] == bowler]
            valid_b   = b_data[~b_data["Extras_Type"].isin(["Wides","Noballs"])]
            balls_bld = len(valid_b)
            if balls_bld == 0:
                continue
            runs_c    = int(b_data["Batsman_Runs"].sum() + b_data["Extra_Runs"].sum())
            overs     = balls_bld // 6
            rem       = balls_bld % 6
            overs_d   = f"{overs}.{rem}" if rem else str(overs)
            eco       = round(runs_c / (overs + rem/6), 2) if (overs + rem/6) else 0
            wkts      = len(b_data[
                (b_data["Is_Wicket"] == 1) &
                b_data["Player_Dismissed"].notna() &
                (~b_data["Dismissal_Kind"].isin(["Run Out","Obstructing The Field","Retired Hurt","Retired Out"]))
            ])
            bowl_rows.append(html.Tr([
                html.Td(bowler, className="sc-player"),
                html.Td(overs_d),
                html.Td(str(runs_c)),
                html.Td(str(wkts), className="sc-wkt" if wkts >= 3 else ""),
                html.Td(str(eco)),
            ]))

        bowl_table = html.Table([
            html.Thead(html.Tr([html.Th(h) for h in ["Bowler", "O", "R", "W", "Eco"]])),
            html.Tbody(bowl_rows),
        ], className="scorecard-table")

        # Innings totals
        total_runs = int(inn_data["Total_Runs"].sum())
        total_wkts = int(inn_data["Is_Wicket"].sum())
        valid_total = inn_data[~inn_data["Extras_Type"].isin(["Wides","Noballs"])]
        total_balls = len(valid_total)
        t_overs     = total_balls // 6
        t_rem       = total_balls % 6
        overs_str   = f"{t_overs}.{t_rem}" if t_rem else str(t_overs)
        extras      = int(inn_data["Extra_Runs"].sum())

        sections.append(html.Div([
            inning_header(
                f"{'1st' if inn_num == 1 else '2nd'} Innings",
                bat_team, total_runs, total_wkts, overs_str, clr,
            ),
            bat_table,
            html.Div(f"Extras: {extras}", className="scorecard-extras"),
            html.Div("BOWLING", className="bowling-hdr"),
            bowl_table,
        ], className="glass-card chart-card reveal", style={"marginBottom": "16px"}))

    # Manhattan chart
    fig_man = go.Figure()
    fig_worm = go.Figure()
    fig_fow  = go.Figure()

    for inn_num, bat_team in [(1, first_bat), (2, second_bat)]:
        inn_data = md[(md["Inning"] == inn_num) & (md["Batting_Team"] == bat_team)]
        if inn_data.empty:
            continue
        clr = team_color(bat_team) or "#f5a623"
        over_runs = inn_data.groupby("Over")["Total_Runs"].sum().reset_index()

        fig_man.add_trace(go.Bar(
            x=over_runs["Over"], y=over_runs["Total_Runs"],
            name=team_abbr(bat_team),
            marker=dict(color=clr, opacity=0.78, line=dict(width=0)),
            hovertemplate="Over %{x}<br>Runs: %{y}<extra></extra>",
        ))

        cumulative = over_runs["Total_Runs"].cumsum()
        fig_worm.add_trace(go.Scatter(
            x=over_runs["Over"], y=cumulative,
            name=team_abbr(bat_team), mode="lines+markers",
            line=dict(color=clr, width=2.5, shape="spline"),
            marker=dict(size=6, color=clr),
            fill="tozeroy", fillcolor=f"rgba({int(clr[1:3],16)},{int(clr[3:5],16)},{int(clr[5:7],16)},0.09)" if clr.startswith("#") and len(clr)==7 else "rgba(245,166,35,0.09)",
            hovertemplate="Over %{x}<br>Cumulative: %{y}<extra></extra>",
        ))

        # Fall of wickets
        cum_r, wkt_n = 0, 0
        fow_x, fow_y, fow_text = [], [], []
        for _, ball in inn_data.iterrows():
            cum_r += ball["Total_Runs"]
            if ball["Is_Wicket"] == 1 and pd.notna(ball.get("Player_Dismissed")):
                wkt_n += 1
                over_b = f"{int(ball['Over'])}.{int(ball['Ball'])}"
                fow_x.append(wkt_n)
                fow_y.append(cum_r)
                fow_text.append(f"{ball['Player_Dismissed']}<br>{cum_r} ({over_b})")
        fig_fow.add_trace(go.Scatter(
            x=fow_x, y=fow_y, mode="lines+markers+text",
            name=team_abbr(bat_team),
            line=dict(color=clr, width=2, shape="spline"),
            marker=dict(size=10, color=clr, symbol="circle"),
            text=[str(y) for y in fow_y],
            textposition="top center",
            textfont=dict(size=10, color=clr),
            hovertext=fow_text, hoverinfo="text",
        ))

    apply_dark_theme(fig_man, title="Manhattan Chart — Runs per Over", height=320,
                     barmode="group",
                     xaxis=dict(title="Over", dtick=1, showgrid=False),
                     yaxis=dict(title="Runs", gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    apply_dark_theme(fig_worm, title="Worm Graph — Cumulative Runs", height=320,
                     xaxis=dict(title="Over", dtick=2, showgrid=False),
                     yaxis=dict(title="Cumulative Runs", gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    apply_dark_theme(fig_fow, title="Fall of Wickets", height=300,
                     xaxis=dict(title="Wicket Number", dtick=1, showgrid=False),
                     yaxis=dict(title="Score at Dismissal", gridcolor="rgba(255,255,255,0.04)"),
                     legend=dict(x=0.5, y=1.1, xanchor="center", orientation="h"))

    charts = html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig_man,  config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_worm, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col reveal"),
        html.Div([
            dcc.Graph(figure=fig_fow, config={"displayModeBar": False})
        ], className="glass-card chart-card reveal", style={"marginTop": "4px"}),
    ])

    return html.Div([header] + sections + [charts])

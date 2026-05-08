"""Match Explorer / Scorecard Page — ported from P05 notebook."""
import dash
from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data_loader import load_data, get_season_range
from utils.constants import THEME, team_abbr, team_color, apply_dark_theme

dash.register_page(__name__, path="/match-explorer", name="Match Explorer", order=1)

DATA = load_data()
M = DATA["matches"]
D = DATA["deliveries"]
SMIN, SMAX = get_season_range(M)

layout = html.Div([
    html.H2("📋 Match Explorer & Scorecard", className="page-header"),
    html.Div([
        html.Div([
            html.Label("Season", className="kpi-label mb-1"),
            dcc.Dropdown(id="me-season", options=[{"label": str(s), "value": s} for s in sorted(M["Season"].dropna().unique())],
                         value=int(M["Season"].max()), clearable=False),
        ], style={"width": "120px"}),
        html.Div([
            html.Label("Match", className="kpi-label mb-1"),
            dcc.Dropdown(id="me-match", placeholder="Select a match"),
        ], style={"flex": "1"}),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "16px", "alignItems": "flex-end"}),
    html.Div(id="me-content"),
])


@callback(
    Output("me-match", "options"),
    Output("me-match", "value"),
    Input("me-season", "value"),
)
def update_match_options(season):
    if not season:
        return [], None
    sm = M[M["Season"] == season].sort_values("Date")
    options = []
    for _, row in sm.iterrows():
        label = f"{team_abbr(row['Team1'])} vs {team_abbr(row['Team2'])} — {str(row['Date'])[:10]}"
        if "Venue" in row:
            label += f" @ {row['Venue'][:30]}"
        options.append({"label": label, "value": int(row["Id"])})
    return options, options[0]["value"] if options else None


@callback(
    Output("me-content", "children"),
    Input("me-match", "value"),
)
def render_scorecard(match_id):
    if not match_id:
        return html.P("Select a match to view scorecard", className="text-center text-muted py-4")

    match = M[M["Id"] == match_id]
    if match.empty:
        return html.P("Match not found", className="text-center text-muted py-4")
    match = match.iloc[0]
    md = D[D["Match_Id"] == match_id]

    team1, team2 = match["Team1"], match["Team2"]
    winner = match.get("Winner", "N/A")
    result = match.get("Result", "")
    margin = match.get("Result_Margin", "")
    venue = match.get("Venue", "")

    # Match header
    result_text = f"{winner} won" if pd.notna(winner) and winner else "No Result"
    if pd.notna(result) and pd.notna(margin):
        result_text += f" by {int(margin) if not pd.isna(margin) else ''} {result}".strip()

    header = html.Div([
        html.Div([
            html.H4(f"{team_abbr(team1)} vs {team_abbr(team2)}", style={"margin": "0", "fontWeight": "700"}),
            html.Small(f"{str(match.get('Date', ''))[:10]} • {venue}", className="text-muted"),
        ]),
        html.Div([
            html.Div(result_text, style={"color": THEME["accent"], "fontWeight": "600", "fontSize": "14px"}),
            html.Small(f"POTM: {match.get('Player_Of_Match', 'N/A')}", className="text-muted"),
        ], style={"textAlign": "right"}),
    ], className="glass-card mb-3", style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})

    # Generate innings scorecards
    sections = []

    # Determine batting order
    if match.get("Toss_Decision") == "Bat":
        first_bat = match["Toss_Winner"]
        second_bat = team2 if team1 == match["Toss_Winner"] else team1
    else:
        second_bat = match["Toss_Winner"]
        first_bat = team2 if team1 == match["Toss_Winner"] else team1

    for inn_num, bat_team in [(1, first_bat), (2, second_bat)]:
        inn_data = md[(md["Inning"] == inn_num) & (md["Batting_Team"] == bat_team)]
        if inn_data.empty:
            continue

        bowl_team = team2 if bat_team == team1 else team1

        # Batting table
        batsmen_order = []
        seen = set()
        for _, ball in inn_data.iterrows():
            for b in [ball["Batter"], ball.get("Non_Striker")]:
                if b and pd.notna(b) and b not in seen:
                    batsmen_order.append(b)
                    seen.add(b)

        dismissed_set = set(inn_data[inn_data["Is_Wicket"] == 1]["Player_Dismissed"].dropna())
        last_ball = inn_data.iloc[-1]
        at_crease = {last_ball["Batter"], last_ball.get("Non_Striker")}

        bat_rows = []
        for batsman in batsmen_order:
            b_balls = inn_data[(inn_data["Batter"] == batsman) & (~inn_data["Extras_Type"].isin(["Wides", "Noballs"]))]
            runs = int(b_balls["Batsman_Runs"].sum())
            balls = len(b_balls)
            sr = round(runs / balls * 100, 1) if balls else 0
            fours = int((b_balls["Batsman_Runs"] == 4).sum())
            sixes = int((b_balls["Batsman_Runs"] == 6).sum())

            was_dismissed = batsman in dismissed_set
            was_at_crease = batsman in at_crease
            not_out = not was_dismissed and was_at_crease
            runs_display = f"{runs}*" if not_out else str(runs)

            # Dismissal text
            if was_dismissed:
                dis_row = inn_data[(inn_data["Player_Dismissed"] == batsman) & (inn_data["Is_Wicket"] == 1)].iloc[0]
                dk = dis_row.get("Dismissal_Kind", "")
                bowler = dis_row.get("Bowler", "")
                fielder = dis_row.get("Fielder", "")
                fielder = fielder if pd.notna(fielder) else ""
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
                    dis_text = f"c & b {bowler}"
                else:
                    dis_text = dk.lower() if dk else ""
            elif not_out:
                dis_text = "not out"
            else:
                dis_text = ""

            bat_rows.append(html.Tr([
                html.Td(batsman, style={"fontWeight": "500"}),
                html.Td(dis_text, style={"color": "rgba(255,255,255,0.5)", "fontSize": "12px"}),
                html.Td(runs_display, style={"fontWeight": "700", "color": THEME["accent"] if runs >= 50 else "white"}),
                html.Td(str(balls)),
                html.Td(str(fours)),
                html.Td(str(sixes)),
                html.Td(str(sr)),
            ]))

        bat_table = html.Table([
            html.Thead(html.Tr([html.Th(h) for h in ["Batter", "Dismissal", "R", "B", "4s", "6s", "SR"]])),
            html.Tbody(bat_rows),
        ], className="scorecard-table")

        # Bowling table
        bowler_order = []
        seen_b = set()
        for _, ball in inn_data.iterrows():
            b = ball["Bowler"]
            if b not in seen_b:
                bowler_order.append(b)
                seen_b.add(b)

        bowl_rows = []
        for bowler in bowler_order:
            b_data = inn_data[inn_data["Bowler"] == bowler]
            valid_b = b_data[~b_data["Extras_Type"].isin(["Wides", "Noballs"])]
            balls_bowled = len(valid_b)
            if balls_bowled == 0:
                continue
            runs_c = int(b_data["Batsman_Runs"].sum() + b_data["Extra_Runs"].sum())
            overs = balls_bowled // 6
            rem = balls_bowled % 6
            overs_disp = f"{overs}.{rem}" if rem else str(overs)
            total_overs = overs + rem / 6
            eco = round(runs_c / total_overs, 2) if total_overs else 0
            wkts = len(b_data[(b_data["Is_Wicket"] == 1) & (b_data["Player_Dismissed"].notna()) &
                              (~b_data["Dismissal_Kind"].isin(["Run Out", "Obstructing The Field", "Retired Hurt", "Retired Out"]))])

            bowl_rows.append(html.Tr([
                html.Td(bowler, style={"fontWeight": "500"}),
                html.Td(overs_disp),
                html.Td(str(runs_c)),
                html.Td(str(wkts), style={"fontWeight": "700", "color": "#f44336" if wkts >= 3 else "white"}),
                html.Td(str(eco)),
            ]))

        bowl_table = html.Table([
            html.Thead(html.Tr([html.Th(h) for h in ["Bowler", "O", "R", "W", "Eco"]])),
            html.Tbody(bowl_rows),
        ], className="scorecard-table")

        # Innings total
        total_runs = int(inn_data["Total_Runs"].sum())
        total_wkts = int(inn_data["Is_Wicket"].sum())
        valid_total = inn_data[~inn_data["Extras_Type"].isin(["Wides", "Noballs"])]
        total_balls = len(valid_total)
        t_overs = total_balls // 6
        t_rem = total_balls % 6
        overs_str = f"{t_overs}.{t_rem}" if t_rem else str(t_overs)

        extras = int(inn_data["Extra_Runs"].sum())

        sections.append(html.Div([
            html.H5(f"{'1st' if inn_num == 1 else '2nd'} Innings — {team_abbr(bat_team)}: {total_runs}/{total_wkts} ({overs_str} ov)",
                     style={"color": team_color(bat_team), "fontWeight": "700", "marginBottom": "12px"}),
            bat_table,
            html.Div(f"Extras: {extras}", style={"color": "rgba(255,255,255,0.5)", "padding": "8px 12px", "fontSize": "13px"}),
            html.H6("Bowling", style={"color": "rgba(255,255,255,0.6)", "marginTop": "12px", "fontSize": "13px", "textTransform": "uppercase", "letterSpacing": "1px"}),
            bowl_table,
        ], className="glass-card mb-3"))

    # ─── Manhattan & Worm ────────────────────────────────────────────────────
    fig_manhattan = go.Figure()
    fig_worm = go.Figure()

    for inn_num, bat_team in [(1, first_bat), (2, second_bat)]:
        inn_data = md[(md["Inning"] == inn_num) & (md["Batting_Team"] == bat_team)]
        if inn_data.empty:
            continue
        over_runs = inn_data.groupby("Over")["Total_Runs"].sum().reset_index()
        clr = team_color(bat_team)
        fig_manhattan.add_trace(go.Bar(x=over_runs["Over"], y=over_runs["Total_Runs"],
                                        name=team_abbr(bat_team), marker_color=clr, opacity=0.8))

        cumulative = over_runs["Total_Runs"].cumsum()
        fig_worm.add_trace(go.Scatter(x=over_runs["Over"], y=cumulative, mode="lines+markers",
                                       name=team_abbr(bat_team), line=dict(color=clr, width=3)))

    apply_dark_theme(fig_manhattan, title="Manhattan Chart", height=340, barmode="group",
                     xaxis=dict(title="Over", dtick=1), yaxis=dict(title="Runs"))
    apply_dark_theme(fig_worm, title="Worm Graph", height=340,
                     xaxis=dict(title="Over", dtick=2), yaxis=dict(title="Cumulative Runs"))

    # Fall of wickets
    fig_fow = go.Figure()
    for inn_num, bat_team in [(1, first_bat), (2, second_bat)]:
        inn_data = md[(md["Inning"] == inn_num) & (md["Batting_Team"] == bat_team)]
        if inn_data.empty:
            continue
        cum_runs = 0
        wkt_num = 0
        fow_x, fow_y, fow_text = [], [], []
        for _, ball in inn_data.iterrows():
            cum_runs += ball["Total_Runs"]
            if ball["Is_Wicket"] == 1 and pd.notna(ball.get("Player_Dismissed")):
                wkt_num += 1
                over_ball = f"{int(ball['Over'])}.{int(ball['Ball'])}"
                fow_x.append(wkt_num)
                fow_y.append(cum_runs)
                fow_text.append(f"{ball['Player_Dismissed']}<br>{cum_runs} ({over_ball})")
        fig_fow.add_trace(go.Scatter(x=fow_x, y=fow_y, mode="lines+markers+text",
                                      name=team_abbr(bat_team), line=dict(color=team_color(bat_team), width=2),
                                      marker=dict(size=10), text=[str(y) for y in fow_y], textposition="top center",
                                      hovertext=fow_text, hoverinfo="text"))
    apply_dark_theme(fig_fow, title="Fall of Wickets", height=340,
                     xaxis=dict(title="Wicket Number", dtick=1), yaxis=dict(title="Score"))

    charts = html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig_manhattan, config={"displayModeBar": False}), className="glass-card"),
            html.Div(dcc.Graph(figure=fig_worm, config={"displayModeBar": False}), className="glass-card"),
        ], className="chart-row two-col"),
        html.Div(dcc.Graph(figure=fig_fow, config={"displayModeBar": False}), className="glass-card mb-3"),
    ])

    return html.Div([header] + sections + [charts])

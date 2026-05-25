"""
ALL-TIME — IPL Hall of Fame
Cinematic history of IPL records, legends, franchises, and milestones.
"""

import dash
from dash import html
import pandas as pd

from utils.data_loader import load_data
from utils.constants import NON_BOWLER_DISMISSALS, team_color, team_abbr

dash.register_page(__name__, path="/all-time", name="All-Time", order=1)

# ─── Data ────────────────────────────────────────────────────────────────────
_D  = load_data()
D   = _D["deliveries"]
M   = _D["matches"].drop_duplicates(subset=["Id"])

_WNB  = frozenset(["Wides", "Noballs"])
legal = D[~D["Extras_Type"].isin(_WNB)]

# ─── Batting ─────────────────────────────────────────────────────────────────
bat_runs = (D.groupby("Batter")["Batsman_Runs"].sum()
             .reset_index(name="Runs").sort_values("Runs", ascending=False))

sixes_df = (D[D["Batsman_Runs"] == 6].groupby("Batter").size()
             .reset_index(name="Sixes").sort_values("Sixes", ascending=False))

fours_df = (D[D["Batsman_Runs"] == 4].groupby("Batter").size()
             .reset_index(name="Fours").sort_values("Fours", ascending=False))

_bat_balls = legal.groupby("Batter").size().reset_index(name="Balls")
bat_sr = (bat_runs.merge(_bat_balls, on="Batter")
          .query("Balls >= 1000")
          .assign(SR=lambda df: (df["Runs"] / df["Balls"] * 100).round(2))
          .sort_values("SR", ascending=False))

_inn = D.groupby(["Match_Id", "Inning", "Batter"])["Batsman_Runs"].sum().reset_index(name="IR")
hundreds_df = (_inn[_inn["IR"] >= 100].groupby("Batter").size()
               .reset_index(name="Hundreds").sort_values("Hundreds", ascending=False))
fifties_df  = (_inn[(_inn["IR"] >= 50) & (_inn["IR"] < 100)].groupby("Batter").size()
               .reset_index(name="Fifties").sort_values("Fifties", ascending=False))

# ─── Bowling ─────────────────────────────────────────────────────────────────
_vwkt = D[(D["Is_Wicket"] == 1) & D["Player_Dismissed"].notna() &
          (~D["Dismissal_Kind"].isin(NON_BOWLER_DISMISSALS))]
bowl_wkts = (_vwkt.groupby("Bowler").size()
              .reset_index(name="Wickets").sort_values("Wickets", ascending=False))

_br = D.groupby("Bowler")["Total_Runs"].sum().reset_index(name="Runs")
_bb = legal.groupby("Bowler").size().reset_index(name="Balls")
bowl_eco = (bowl_wkts.merge(_br, on="Bowler").merge(_bb, on="Bowler")
            .query("Balls >= 1200")
            .assign(Economy=lambda df: (df["Runs"] / (df["Balls"] / 6)).round(2))
            .sort_values("Economy"))

bowl_dots = (D[(D["Total_Runs"] == 0) & (~D["Extras_Type"].isin(_WNB))]
             .groupby("Bowler").size()
             .reset_index(name="Dots").sort_values("Dots", ascending=False))

_bwi = _vwkt.groupby(["Match_Id", "Inning", "Bowler"]).size().reset_index(name="W")
_bri = D.groupby(["Match_Id", "Inning", "Bowler"])["Total_Runs"].sum().reset_index(name="R")
figures_df = (_bwi.merge(_bri, on=["Match_Id", "Inning", "Bowler"])
              .sort_values(["W", "R"], ascending=[False, True])
              .drop_duplicates("Bowler").head(10))

# ─── Fielding ────────────────────────────────────────────────────────────────
catches_df   = (D[(D["Dismissal_Kind"] == "Caught") & D["Fielder"].notna()]
                .groupby("Fielder").size().reset_index(name="Catches")
                .sort_values("Catches", ascending=False))
stumpings_df = (D[(D["Dismissal_Kind"] == "Stumped") & D["Fielder"].notna()]
                .groupby("Fielder").size().reset_index(name="Stumpings")
                .sort_values("Stumpings", ascending=False))

# ─── Individual records ───────────────────────────────────────────────────────
_ls = legal.sort_values(["Match_Id", "Inning", "Over", "Ball"]).copy()
_ls["_bn"] = _ls.groupby(["Match_Id", "Inning", "Batter"]).cumcount() + 1
_ls["_cr"] = _ls.groupby(["Match_Id", "Inning", "Batter"])["Batsman_Runs"].cumsum()

fastest50s  = (_ls[_ls["_cr"] >= 50]
               .groupby(["Match_Id", "Inning", "Batter"])["_bn"].min()
               .reset_index(name="Balls").sort_values("Balls")
               .drop_duplicates("Batter").head(10))
fastest100s = (_ls[_ls["_cr"] >= 100]
               .groupby(["Match_Id", "Inning", "Batter"])["_bn"].min()
               .reset_index(name="Balls").sort_values("Balls")
               .drop_duplicates("Batter").head(10))

potm_df = (M[M["Player_Of_Match"].notna()]
           .groupby("Player_Of_Match").size()
           .reset_index(name="Awards")
           .rename(columns={"Player_Of_Match": "Player"})
           .sort_values("Awards", ascending=False))

# ─── Team records ─────────────────────────────────────────────────────────────
team_totals = (D.groupby(["Match_Id", "Inning", "Batting_Team"])["Total_Runs"]
               .sum().reset_index(name="Total").sort_values("Total", ascending=False))

team_wins = (M[M["Winner"].notna()].groupby("Winner").size()
             .reset_index(name="Wins").sort_values("Wins", ascending=False))

_finals = M[M["Match_Type"].str.lower().str.strip() == "final"][["Season", "Winner"]].dropna()
if _finals.empty:
    _finals = M.sort_values("Date").groupby("Season").last()[["Winner"]].reset_index()
_finals = _finals.sort_values("Season")

# ─── Phase specialists ────────────────────────────────────────────────────────
def _phase_sr(overs, min_balls=100):
    ph_r = D[D["Over"].isin(overs)].groupby("Batter")["Batsman_Runs"].sum().reset_index(name="R")
    ph_b = legal[legal["Over"].isin(overs)].groupby("Batter").size().reset_index(name="B")
    ph   = ph_r.merge(ph_b, on="Batter").query(f"B >= {min_balls}")
    ph["SR"] = (ph["R"] / ph["B"] * 100).round(1)
    return ph.sort_values("SR", ascending=False).head(5)

pp_spec  = _phase_sr(range(1, 7))
mid_spec = _phase_sr(range(7, 16))
dth_spec = _phase_sr(range(16, 21))

# ─── Hero numbers ─────────────────────────────────────────────────────────────
TOTAL_RUNS    = int(D["Batsman_Runs"].sum())
TOTAL_MATCHES = int(M["Id"].nunique())
TOTAL_SIXES   = int((D["Batsman_Runs"] == 6).sum())
TOTAL_SEASONS = int(M["Season"].nunique())
_LAKH         = round(TOTAL_RUNS / 100_000, 1)
RUNS_LABEL    = f"{_LAKH}L+" if TOTAL_RUNS >= 100_000 else f"{TOTAL_RUNS:,}"


# ─── UI helpers ───────────────────────────────────────────────────────────────

def _fmt(v, decimals=0):
    try:
        if decimals > 0:
            return f"{float(v):.{decimals}f}"
        return f"{int(float(v)):,}"
    except Exception:
        return str(v)


def _podium_card(rank, name, val_str, tier, unit=""):
    tier_label = {1: "GOLD", 2: "SILVER", 3: "BRONZE"}.get(rank, "")
    return html.Div([
        html.Div(tier_label, className=f"podium-rank-badge {tier}"),
        html.Div([
            html.Div(val_str, className="podium-val"),
            html.Span(f" {unit}", className="podium-unit") if unit else None,
        ], className="podium-stat"),
        html.Div(name, className="podium-name"),
    ], className=f"podium-card {tier} reveal-scale")


def _legend_row(rank, name, value, ref_val, unit="", color="#f5a623",
                decimals=0, lower_better=False):
    try:
        fval = float(value)
        fref = float(ref_val) if ref_val else 1
        if lower_better and fval > 0:
            pct = round(min(fref, fval) / fval * 100, 1)
        else:
            pct = round(fval / fref * 100, 1) if fref else 0
    except Exception:
        pct = 0
    val_str = _fmt(value, decimals)
    if unit:
        val_str += f" {unit}"
    badge_cls = "legend-rank-badge top" if rank <= 3 else "legend-rank-badge"
    return html.Div([
        html.Div(str(rank), className=badge_cls),
        html.Div(str(name), className="legend-name"),
        html.Div(
            html.Div(className="legend-bar-fill",
                     **{"data-width": f"{pct}%"},
                     style={"background": f"linear-gradient(90deg, {color}, {color}99)"}),
            className="legend-bar-wrap",
        ),
        html.Div(val_str, className="legend-val"),
    ], className="legend-row")


def _category(title, tag, rows_df, name_col, val_col,
              unit="", color="#f5a623", top=10, ascending=False, decimals=0):
    rows = rows_df.head(top).reset_index(drop=True)
    if rows.empty:
        return html.Div()

    ref_val = (rows[val_col].min() if ascending else rows[val_col].max()) if not rows.empty else 1

    # Visual podium: silver left | gold center | bronze right
    render_order = ([(1, "silver"), (0, "gold"), (2, "bronze")] if len(rows) >= 3
                    else [(0, "gold"), (1, "silver")] if len(rows) == 2
                    else [(0, "gold")])

    podium_cards = []
    for idx, tier in render_order:
        if idx < len(rows):
            r   = rows.iloc[idx]
            podium_cards.append(
                _podium_card(idx + 1, r[name_col], _fmt(r[val_col], decimals), tier, unit))

    legend_rows = [
        _legend_row(i + 1, rows.iloc[i][name_col], rows.iloc[i][val_col],
                    ref_val, unit, color, decimals, lower_better=ascending)
        for i in range(len(rows))
    ]

    return html.Div([
        html.Div([
            html.Div(tag, className="at-cat-tag"),
            html.H3(title, className="at-cat-title"),
        ], className="at-cat-header reveal"),
        html.Div(podium_cards, className="podium-wrap"),
        html.Div(legend_rows, className="legend-list"),
    ], className="at-category")


# ─── Layout ───────────────────────────────────────────────────────────────────

def layout():

    # Champions timeline tiles
    champ_tiles = []
    for _, row in _finals.iterrows():
        yr   = int(row["Season"])
        team = str(row.get("Winner", "?"))
        clr  = team_color(team, "#888")
        abbr = team_abbr(team)
        champ_tiles.append(html.Div([
            html.Div(str(yr),     className="champ-tile-year"),
            html.Div(abbr,        className="champ-tile-abbr", style={"color": clr}),
            html.Div(team[:22],   className="champ-tile-team"),
        ], className="champ-tile reveal-scale"))

    # Dynasty cards
    dynasty_cards = []
    max_wins = int(team_wins["Wins"].max()) if not team_wins.empty else 1
    for _, row in team_wins.head(9).iterrows():
        team  = str(row["Winner"])
        wins  = int(row["Wins"])
        clr   = team_color(team, "#888")
        abbr  = team_abbr(team)
        yrs   = sorted(_finals[_finals["Winner"] == team]["Season"].astype(int).tolist())
        bar_p = round(wins / max_wins * 100)
        dynasty_cards.append(html.Div([
            html.Div(abbr, className="dynasty-abbr", style={"color": clr}),
            html.Div(team, className="dynasty-team-name"),
            html.Div([
                html.Div([
                    html.Div(str(wins), className="dynasty-wins-val"),
                    html.Div("WINS", className="dynasty-wins-lbl"),
                ], className="dynasty-stat"),
                html.Div([
                    html.Div(str(len(yrs)), className="dynasty-wins-val",
                             style={"color": "var(--gold)"}),
                    html.Div("TITLES", className="dynasty-wins-lbl"),
                ], className="dynasty-stat"),
            ], className="dynasty-stats-row"),
            html.Div([html.Div(str(y), className="dynasty-year-chip") for y in yrs],
                     className="dynasty-years") if yrs else None,
            html.Div(className="dynasty-bar",
                     **{"data-width": f"{bar_p}%"},
                     style={"background": clr}),
        ], className="dynasty-card reveal", style={"--team-color": clr}))

    # Phase blocks
    def _phase_block(df, label, color):
        max_sr = float(df["SR"].max()) if not df.empty else 1
        rows = []
        for i, (_, r) in enumerate(df.iterrows()):
            pct = round(r["SR"] / max_sr * 100, 1)
            badge_cls = "legend-rank-badge top" if i < 3 else "legend-rank-badge"
            rows.append(html.Div([
                html.Div(str(i + 1), className=badge_cls),
                html.Div(r["Batter"], className="legend-name"),
                html.Div(
                    html.Div(className="legend-bar-fill",
                             **{"data-width": f"{pct}%"},
                             style={"background": color}),
                    className="legend-bar-wrap",
                ),
                html.Div(f"{r['SR']} SR", className="legend-val"),
            ], className="legend-row"))
        return html.Div([
            html.Div(label, className="phase-label", style={"color": color}),
            html.Div(rows, className="legend-list"),
        ], className="phase-block reveal")

    # Best figures rows
    figure_rows = []
    for i, (_, row) in enumerate(figures_df.iterrows()):
        badge_cls = "legend-rank-badge top" if i < 3 else "legend-rank-badge"
        figure_rows.append(html.Div([
            html.Div(str(i + 1), className=badge_cls),
            html.Div(str(row["Bowler"]), className="legend-name"),
            html.Div(className="legend-bar-wrap"),
            html.Div(f"{int(row['W'])}/{int(row['R'])}", className="legend-val",
                     style={"color": "var(--red)", "fontWeight": "700",
                            "fontFamily": "var(--font-mono)", "fontSize": "0.9rem"}),
        ], className="legend-row"))

    # Fastest n-balls rows
    def _speed_rows(df, color):
        rows = []
        for i, (_, row) in enumerate(df.iterrows()):
            badge_cls = "legend-rank-badge top" if i < 3 else "legend-rank-badge"
            rows.append(html.Div([
                html.Div(str(i + 1), className=badge_cls),
                html.Div(str(row["Batter"]), className="legend-name"),
                html.Div(className="legend-bar-wrap"),
                html.Div(f"{int(row['Balls'])} balls", className="legend-val",
                         style={"color": color, "fontFamily": "var(--font-mono)"}),
            ], className="legend-row"))
        return rows

    # Highest team totals rows
    total_rows = []
    max_tot = int(team_totals["Total"].max()) if not team_totals.empty else 1
    for i, (_, row) in enumerate(team_totals.head(10).iterrows()):
        pct = round(row["Total"] / max_tot * 100, 1)
        clr = team_color(row["Batting_Team"], "#888")
        badge_cls = "legend-rank-badge top" if i < 3 else "legend-rank-badge"
        total_rows.append(html.Div([
            html.Div(str(i + 1), className=badge_cls),
            html.Div([
                html.Span(team_abbr(row["Batting_Team"]),
                          style={"color": clr, "fontFamily": "var(--font-mono)",
                                 "fontWeight": "700", "fontSize": "0.72rem"}),
            ], className="legend-name"),
            html.Div(
                html.Div(className="legend-bar-fill",
                         **{"data-width": f"{pct}%"},
                         style={"background": clr}),
                className="legend-bar-wrap",
            ),
            html.Div(str(int(row["Total"])), className="legend-val"),
        ], className="legend-row"))

    # ─── Page ────────────────────────────────────────────────────────────────
    return html.Div([

        # ── CINEMATIC HERO ────────────────────────────────────────────────────
        html.Section([
            html.Div(className="at-hero-orb at-orb-1"),
            html.Div(className="at-hero-orb at-orb-2"),
            html.Div(className="at-hero-orb at-orb-3"),
            html.Div(className="at-hero-grid"),

            html.Div([
                html.Div("IPL ALL-TIME RECORDS", className="at-hero-eyebrow"),
                html.H1([
                    html.Span(
                        f"{TOTAL_SEASONS} Seasons. {TOTAL_MATCHES:,}+ Matches.",
                        className="at-title-block"),
                    html.Span([
                        html.Span(f"{RUNS_LABEL} Runs. ", className="at-title-gold"),
                        "One League.",
                    ], className="at-title-block"),
                    html.Span("Infinite Legacy.", className="at-title-accent"),
                ], className="at-hero-title"),
                html.P(
                    "Every run. Every wicket. Every boundary. Every championship. "
                    "The living record of IPL history.",
                    className="at-hero-sub",
                ),
                html.Div([
                    html.Div([
                        html.Div("0", className="at-counter-val",
                                 **{"data-counter": str(TOTAL_RUNS), "data-duration": "2000"}),
                        html.Div("TOTAL RUNS", className="at-counter-lbl"),
                    ], className="at-counter"),
                    html.Div(className="at-counter-divider"),
                    html.Div([
                        html.Div("0", className="at-counter-val",
                                 **{"data-counter": str(TOTAL_MATCHES), "data-duration": "1500"}),
                        html.Div("MATCHES", className="at-counter-lbl"),
                    ], className="at-counter"),
                    html.Div(className="at-counter-divider"),
                    html.Div([
                        html.Div("0", className="at-counter-val",
                                 **{"data-counter": str(TOTAL_SIXES), "data-duration": "1800"}),
                        html.Div("SIXES HIT", className="at-counter-lbl"),
                    ], className="at-counter"),
                    html.Div(className="at-counter-divider"),
                    html.Div([
                        html.Div(str(TOTAL_SEASONS), className="at-counter-val"),
                        html.Div("SEASONS", className="at-counter-lbl"),
                    ], className="at-counter"),
                ], className="at-hero-counters"),
            ], className="at-hero-content"),
        ], className="at-hero"),

        # ── BATTING LEGENDS ───────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("BATTING", className="at-section-eyebrow"),
                html.H2("Run Machines", className="at-section-title"),
            ], className="at-section-header reveal"),

            _category("Most Runs All-Time", "ALL-TIME RUNS",
                       bat_runs, "Batter", "Runs", "runs", "#f5a623"),

            html.Div([
                _category("Most Sixes", "POWER HITTING",
                           sixes_df, "Batter", "Sixes", "6s", "#ff6b35"),
                _category("Most Fours", "TIMING & PLACEMENT",
                           fours_df, "Batter", "Fours", "4s", "#00d4ff"),
            ], className="at-col-2"),

            html.Div([
                _category("Best Strike Rate", "AGGRESSION",
                           bat_sr, "Batter", "SR", "", "#00ff87", decimals=2),
                _category("Most Centuries", "HUNDREDS",
                           hundreds_df, "Batter", "Hundreds", "100s", "#a855f7"),
                _category("Most Half-Centuries", "FIFTIES",
                           fifties_df, "Batter", "Fifties", "50s", "#ffd700"),
            ], className="at-col-3"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── BOWLING LEGENDS ───────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("BOWLING", className="at-section-eyebrow"),
                html.H2("Wicket Warriors", className="at-section-title"),
            ], className="at-section-header reveal"),

            _category("Most Wickets All-Time", "ALL-TIME WICKETS",
                       bowl_wkts, "Bowler", "Wickets", "wkts", "#ff1744"),

            html.Div([
                _category("Best Economy Rate", "MISERS",
                           bowl_eco, "Bowler", "Economy", "eco", "#00e5ff",
                           ascending=True, decimals=2),
                _category("Most Dot Balls Bowled", "PRESSURE MERCHANTS",
                           bowl_dots, "Bowler", "Dots", "dots", "#7c3aed"),
            ], className="at-col-2"),

            html.Div([
                html.Div([
                    html.Div("BEST BOWLING PERFORMANCES", className="at-cat-tag"),
                    html.H3("Greatest Single-Innings Spells", className="at-cat-title"),
                ], className="at-cat-header reveal"),
                html.Div(figure_rows, className="legend-list"),
            ], className="at-category"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── FIELDING ──────────────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("FIELDING", className="at-section-eyebrow"),
                html.H2("Safe Hands", className="at-section-title"),
            ], className="at-section-header reveal"),
            html.Div([
                _category("Most Catches", "CATCHING EXCELLENCE",
                           catches_df, "Fielder", "Catches", "catches", "#00d4ff"),
                _category("Most Stumpings", "GLOVES OF STEEL",
                           stumpings_df, "Fielder", "Stumpings", "stumpings", "#f5a623"),
            ], className="at-col-2"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── INDIVIDUAL RECORDS ────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("INDIVIDUAL RECORDS", className="at-section-eyebrow"),
                html.H2("Historic Moments", className="at-section-title"),
            ], className="at-section-header reveal"),

            _category("Player of the Match Awards", "MATCH IMPACT",
                       potm_df, "Player", "Awards", "awards", "#ffd700"),

            html.Div([
                html.Div([
                    html.Div([
                        html.Div("FASTEST FIFTIES", className="at-cat-tag"),
                        html.H3("Blazing Half-Centuries", className="at-cat-title"),
                    ], className="at-cat-header reveal"),
                    html.Div(_speed_rows(fastest50s, "var(--green)"), className="legend-list"),
                ], className="at-category"),
                html.Div([
                    html.Div([
                        html.Div("FASTEST CENTURIES", className="at-cat-tag"),
                        html.H3("Hundred in a Flash", className="at-cat-title"),
                    ], className="at-cat-header reveal"),
                    html.Div(_speed_rows(fastest100s, "var(--gold)"), className="legend-list"),
                ], className="at-category"),
            ], className="at-col-2"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── HIGHEST TEAM TOTALS ───────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("TEAM RECORDS", className="at-section-eyebrow"),
                html.H2("Highest Team Totals", className="at-section-title"),
            ], className="at-section-header reveal"),
            html.Div(total_rows, className="legend-list reveal"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── TEAM DYNASTIES ────────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("FRANCHISE", className="at-section-eyebrow"),
                html.H2("Team Dynasties", className="at-section-title"),
            ], className="at-section-header reveal"),
            html.Div(dynasty_cards, className="dynasty-grid stagger-in"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── CHAMPIONS TIMELINE ────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("HISTORY", className="at-section-eyebrow"),
                html.H2("Champions Timeline", className="at-section-title"),
                html.P("Every IPL champion across all seasons",
                       className="at-section-sub"),
            ], className="at-section-header reveal"),
            html.Div(champ_tiles, className="champions-grid stagger-in"),
        ], className="at-section"),

        html.Div(className="section-divider"),

        # ── PHASE SPECIALISTS ─────────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div("ANALYTICS", className="at-section-eyebrow"),
                html.H2("Phase Specialists", className="at-section-title"),
                html.P("Best strike rates by game phase — minimum 100 balls faced",
                       className="at-section-sub"),
            ], className="at-section-header reveal"),
            html.Div([
                _phase_block(pp_spec,  "POWERPLAY  (Ov 1–6)",    "#ffd700"),
                _phase_block(mid_spec, "MIDDLE OVERS (Ov 7–15)", "#00d4ff"),
                _phase_block(dth_spec, "DEATH OVERS (Ov 16–20)", "#ff1744"),
            ], className="phase-grid"),
        ], className="at-section"),

    ], className="page-wrap at-page")

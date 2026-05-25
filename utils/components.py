"""
IPL Intelligence — Component Library v4.0
Premium UI building blocks. Matches design system v4 CSS classes exactly.
"""

from dash import html, dcc
from utils.constants import team_abbr, team_color, TEAM_INFO


# ── Colour helpers ────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgba(hex_color, alpha):
    try:
        r, g, b = _hex_to_rgb(hex_color)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(245,166,35,{alpha})"


def get_initials(name):
    parts = str(name).split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


# ── Layout scaffolding ────────────────────────────────────────────────────────

def page_hero(tag, title, title_accent=None, subtitle=None):
    """Cinematic page-level hero with eyebrow, title, optional accent + subtitle."""
    parts = [html.Div(tag, className="hero-eyebrow")]

    title_parts = [title]
    if title_accent:
        title_parts.append(html.Span(title_accent, className="accent"))
    parts.append(html.H1(title_parts, className="page-title"))
    parts.append(html.Div(className="page-divider"))

    if subtitle:
        parts.append(html.P(subtitle, className="page-subtitle"))

    return html.Div(parts, className="page-hero reveal")


def section_header(title, tag=None):
    right = html.Span(tag, className="section-tag") if tag else None
    return html.Div(
        [html.Span(title, className="section-hdr-title"), right],
        className="section-hdr",
    )


def controls_bar(*groups):
    return html.Div(list(groups), className="controls-bar")


def control_group(label, *children):
    return html.Div([
        html.Label(label, className="control-label"),
        *children,
    ], className="control-group")


# ── KPI / Stat card ───────────────────────────────────────────────────────────

def stat_card(value, label, icon="", color="#f5a623",
              counter=False, duration=1800, suffix="", decimals=0, prefix=""):
    """Animated KPI card. counter=True enables JS count-up animation."""
    val_node_kwargs = {}
    display_val = value

    if counter:
        try:
            numeric = float(str(value).replace(",", "").replace("%", "").strip())
            val_node_kwargs["data-counter"]  = str(numeric)
            val_node_kwargs["data-duration"] = str(duration)
            val_node_kwargs["data-decimals"] = str(decimals)
            val_node_kwargs["data-suffix"]   = suffix
            val_node_kwargs["data-prefix"]   = prefix
            display_val = "0"
        except ValueError:
            pass

    return html.Div([
        html.Span(icon, className="stat-icon") if icon else None,
        html.Div(display_val, className="stat-value", **val_node_kwargs),
        html.Div(label, className="stat-label"),
    ], className="stat-card",
       style={"--card-color": color})


# ── Player card (FIFA-style) ──────────────────────────────────────────────────

def player_card(player_name, team,
                primary_stat_val, primary_stat_lbl,
                secondary_stat_val="", secondary_stat_lbl="",
                tertiary_stat_val="", tertiary_stat_lbl="",
                rank=None, image_url=None):
    """
    FIFA Ultimate Team style player card.
    Supports up to 3 stats. Uses image_url if provided, otherwise initials avatar.
    """
    clr = team_color(team) or "#F5A623"
    clr_dim = _rgba(clr, 0.15)

    # Avatar
    if image_url:
        avatar = html.Div([
            html.Img(src=image_url, className="player-card-avatar-img"),
            html.Div(className="player-card-avatar-ring"),
        ], className="player-card-avatar")
    else:
        initials = get_initials(player_name)
        avatar = html.Div([
            html.Div(initials, className="player-card-avatar-initials",
                     style={"--team-color": clr, "--team-color-dim": clr_dim}),
            html.Div(className="player-card-avatar-ring"),
        ], className="player-card-avatar")

    # Stats
    stats = []
    for val, lbl in [(primary_stat_val, primary_stat_lbl),
                     (secondary_stat_val, secondary_stat_lbl),
                     (tertiary_stat_val, tertiary_stat_lbl)]:
        if val and lbl:
            stats.append(html.Div([
                html.Div(str(val), className="player-card-stat-val"),
                html.Div(lbl, className="player-card-stat-lbl"),
            ], className="player-card-stat"))

    name_parts = str(player_name).split()
    display_name = (name_parts[-1] if len(name_parts) > 1 else player_name)

    card_inner = html.Div([
        html.Div(f"#{rank}" if rank else team_abbr(team), className="player-card-rank"),
        avatar,
        html.Div(display_name, className="player-card-name"),
        html.Div(team_abbr(team), className="player-card-team"),
        html.Div(className="player-card-divider"),
        html.Div(stats, className="player-card-stats") if stats else None,
    ], className="player-card-inner")

    return html.Div([
        html.Div(className="player-card-foil"),
        html.Div(className="player-card-border-ring"),
        card_inner,
    ], className="player-card",
       style={"--team-color": clr, "--team-color-dim": clr_dim})


def player_card_grid(cards, style=None):
    return html.Div(cards, className="player-card-grid", style=style or {})


# ── Profile card (full player page) ──────────────────────────────────────────

def player_profile_card(player_name, team, role,
                        bat_stats=None, bowl_stats=None, image_url=None):
    """Full-width player profile card for the players page."""
    clr     = team_color(team) or "#F5A623"
    clr_dim = _rgba(clr, 0.12)
    abbr    = team_abbr(team)
    initials = get_initials(player_name)

    if image_url:
        avatar_el = html.Img(src=image_url, className="player-card-avatar-img",
                             style={"width": "100px", "height": "100px",
                                    "borderRadius": "50%", "objectFit": "cover", "objectPosition": "top"})
    else:
        avatar_el = html.Div(initials, className="player-card-avatar-initials",
                             style={"width": "100px", "height": "100px", "fontSize": "2rem",
                                    "--team-color": clr, "--team-color-dim": clr_dim})

    stat_sections = []
    if bat_stats:
        stat_sections.append(html.Div([
            html.Div("BATTING", className="section-tag",
                     style={"marginBottom": "10px", "display": "block"}),
            html.Div([
                html.Div([
                    html.Div(str(v), className="stat-value",
                             style={"--card-color": clr, "fontSize": "1.3rem"}),
                    html.Div(k, className="stat-label"),
                ], className="stat-card", style={"--card-color": clr, "padding": "12px 14px"})
                for k, v in bat_stats.items()
            ], className="stat-grid",
               style={"gridTemplateColumns": "repeat(auto-fill, minmax(120px, 1fr))"}),
        ]))

    if bowl_stats:
        stat_sections.append(html.Div([
            html.Div("BOWLING", className="section-tag",
                     style={"marginBottom": "10px", "marginTop": "16px", "display": "block"}),
            html.Div([
                html.Div([
                    html.Div(str(v), className="stat-value",
                             style={"--card-color": "#00D4FF", "fontSize": "1.3rem"}),
                    html.Div(k, className="stat-label"),
                ], className="stat-card", style={"--card-color": "#00D4FF", "padding": "12px 14px"})
                for k, v in bowl_stats.items()
            ], className="stat-grid",
               style={"gridTemplateColumns": "repeat(auto-fill, minmax(120px, 1fr))"}),
        ]))

    return html.Div([
        html.Div([
            html.Div([
                avatar_el,
                html.Div(className="player-card-avatar-ring",
                         style={"position": "absolute", "inset": "-4px", "top": "-4px"}),
            ], style={"position": "relative", "flexShrink": "0"}),

            html.Div([
                html.Div(player_name, style={
                    "fontFamily": "var(--font-display)", "fontSize": "clamp(1.4rem,3vw,2rem)",
                    "fontWeight": "900", "color": "var(--t1)", "lineHeight": "1.1",
                    "letterSpacing": "-0.01em",
                }),
                html.Div([
                    html.Span(abbr, className="badge badge-gold"),
                    html.Span(role, className="badge badge-cyan",
                              style={"marginLeft": "8px"}),
                ], style={"marginTop": "8px"}),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "24px",
                  "marginBottom": "24px"}),
        *stat_sections,
    ], className="glass-card reveal",
       style={"borderColor": _rgba(clr, 0.25), "marginBottom": "24px"})


# ── Rivalry / H2H header ──────────────────────────────────────────────────────

def rivalry_header(team_a, team_b, wins_a, wins_b, total_matches):
    clr_a = team_color(team_a) or "#F5A623"
    clr_b = team_color(team_b) or "#00D4FF"

    return html.Div([
        html.Div([
            html.Div(team_abbr(team_a), className="rivalry-team-abbr",
                     style={"color": clr_a, "textShadow": f"0 0 24px {_rgba(clr_a, 0.4)}"}),
            html.Div(team_a, className="rivalry-team-name"),
            html.Div(str(wins_a), className="rivalry-wins",
                     style={"color": clr_a}),
        ], className="rivalry-side left"),

        html.Div([
            html.Div("VS", className="rivalry-vs"),
            html.Div(f"{total_matches} matches", className="rivalry-total"),
            html.Div(className="page-divider",
                     style={"background": f"linear-gradient(90deg, {clr_a}, {clr_b})",
                            "margin": "4px auto", "width": "40px"}),
        ], className="rivalry-center"),

        html.Div([
            html.Div(team_abbr(team_b), className="rivalry-team-abbr",
                     style={"color": clr_b, "textShadow": f"0 0 24px {_rgba(clr_b, 0.4)}",
                            "textAlign": "right"}),
            html.Div(team_b, className="rivalry-team-name"),
            html.Div(str(wins_b), className="rivalry-wins",
                     style={"color": clr_b, "textAlign": "right"}),
        ], className="rivalry-side right"),
    ], className="rivalry-header reveal")


# ── Player vs Player matchup arena ────────────────────────────────────────────

def matchup_arena(batter, batter_team, bowler, bowler_team,
                  balls, runs, sr, dismissals):
    bat_clr  = team_color(batter_team) or "#F5A623"
    bowl_clr = team_color(bowler_team) or "#00D4FF"

    return html.Div([
        html.Div([
            html.Div("BATTER", className="arena-role-tag"),
            html.Div(batter, className="arena-player-name"),
            html.Span(team_abbr(batter_team), className="arena-team-badge badge",
                      style={"background": _rgba(bat_clr, 0.12),
                             "border": f"1px solid {_rgba(bat_clr, 0.3)}",
                             "color": bat_clr}),
        ], className="arena-player batter"),

        html.Div([
            html.Div("VS", className="arena-vs-text"),
            html.Div(f"{balls} balls · {runs} runs · {sr} SR · {dismissals}W",
                     className="arena-sr-badge"),
        ], className="arena-vs-wrap"),

        html.Div([
            html.Div("BOWLER", className="arena-role-tag"),
            html.Div(bowler, className="arena-player-name",
                     style={"textAlign": "right"}),
            html.Span(team_abbr(bowler_team), className="arena-team-badge badge",
                      style={"background": _rgba(bowl_clr, 0.12),
                             "border": f"1px solid {_rgba(bowl_clr, 0.3)}",
                             "color": bowl_clr}),
        ], className="arena-player bowler"),
    ], className="matchup-arena reveal")


# ── Match header ──────────────────────────────────────────────────────────────

def match_header_card(team1, team2, date_str, venue, result_text, potm):
    clr1 = team_color(team1) or "#F5A623"
    clr2 = team_color(team2) or "#00D4FF"

    return html.Div([
        html.Div([
            html.Div(team_abbr(team1), className="match-team-abbr",
                     style={"color": clr1}),
            html.Div(team1, className="match-team-name"),
        ], className="match-team-block left"),

        html.Div([
            html.Div("VS", className="match-vs-dot"),
            html.Div(result_text, className="match-result-text"),
            html.Div(f"🏅 {potm}", className="match-potm-badge") if potm and potm != "N/A" else None,
            html.Div(f"{date_str}  ·  {venue[:36]}" if venue else date_str,
                     className="match-date-venue"),
        ], className="match-center-meta"),

        html.Div([
            html.Div(team_abbr(team2), className="match-team-abbr",
                     style={"color": clr2, "textAlign": "right"}),
            html.Div(team2, className="match-team-name"),
        ], className="match-team-block right"),

        # decorative colour bars
        html.Div(style={
            "position": "absolute", "top": "0", "left": "0", "bottom": "0", "width": "3px",
            "background": f"linear-gradient(180deg, {clr1}, transparent)",
        }),
        html.Div(style={
            "position": "absolute", "top": "0", "right": "0", "bottom": "0", "width": "3px",
            "background": f"linear-gradient(180deg, {clr2}, transparent)",
        }),
    ], className="match-header-card reveal")


# ── Innings header ────────────────────────────────────────────────────────────

def inning_header(num_label, team, score, wickets, overs_str, team_clr):
    clr = team_clr or "#F5A623"
    return html.Div([
        html.Span(num_label, className="inning-number"),
        html.Span(team, className="inning-team", style={"color": clr}),
        html.Div([
            html.Span(f"{score}/{wickets}", className="inning-score"),
            html.Span(f"({overs_str} ov)", className="inning-overs"),
        ], style={"display": "flex", "alignItems": "baseline", "gap": "8px"}),
    ], className="inning-header",
       style={"borderLeft": f"3px solid {clr}"})


# ── Insight card ──────────────────────────────────────────────────────────────

def insight_card(tag, text):
    return html.Div([
        html.Div(tag, className="insight-tag"),
        html.Div(text, className="insight-text"),
    ], className="insight-card reveal")


# ── Trophy cabinet ────────────────────────────────────────────────────────────

def trophy_cabinet(years):
    if not years:
        return html.Div("—", style={"color": "var(--t4)", "fontFamily": "var(--font-mono)", "fontSize": "0.75rem"})
    items = [
        html.Div([
            html.Div("🏆", className="trophy-icon"),
            html.Div(str(y), className="trophy-year"),
        ], className="trophy-item")
        for y in years
    ]
    return html.Div(items, className="trophy-cabinet")


# ── Rankings list ─────────────────────────────────────────────────────────────

def rankings_list(*rows):
    return html.Div(list(rows), className="rankings-list")


def ranking_row(rank, name, value, max_value, unit="", color="#f5a623"):
    pct = round(value / max_value * 100, 1) if max_value else 0
    return html.Div([
        html.Div(str(rank), className=f"ranking-rank {'top' if rank <= 3 else ''}"),
        html.Div(name, className="ranking-name"),
        html.Div(
            html.Div(className="ranking-bar-fill",
                     style={"width": f"{pct}%",
                            "background": f"linear-gradient(90deg, {color}, {color}cc)"}),
            className="ranking-bar-wrap",
        ),
        html.Div(f"{value:,}{unit}", className="ranking-val"),
    ], className="ranking-row")


# ── Featured navigation card ──────────────────────────────────────────────────

def featured_card(href, icon, label, title, description, glow_color="#f5a623"):
    return html.A([
        html.Div(className="featured-card-glow",
                 style={"background": glow_color}),
        html.Div(icon, className="featured-card-icon"),
        html.Div(label, className="featured-card-label"),
        html.Div(title, className="featured-card-title"),
        html.Div(description, className="featured-card-desc"),
        html.Div(["EXPLORE", html.Span("→")], className="featured-card-arrow"),
    ], href=href, className="featured-card reveal")


# ── Backward-compat shim ──────────────────────────────────────────────────────

def kpi_card(value, label, color="#f5a623"):
    """Legacy shim — maps to stat_card."""
    return stat_card(value, label, color=color)

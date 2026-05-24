"""
Premium UI Component Library for IPL Intelligence Platform.
All building blocks for the redesigned frontend.
"""

from dash import html, dcc
from utils.constants import team_abbr, team_color, TEAM_INFO


# ─── Colour helpers ───────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color):
    """Convert #RRGGBB to (r,g,b) tuple."""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _darken(hex_color, factor=0.55):
    """Return a darker version of a hex colour."""
    try:
        r, g, b = _hex_to_rgb(hex_color)
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"
    except Exception:
        return "#0a1520"


def get_initials(name):
    """Return up to 2 initials from a player name."""
    parts = str(name).split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


# ─── Page skeleton ────────────────────────────────────────────────────────────

def page_wrap(*children, extra_class=""):
    """Standard page container with scroll-reveal wrapper."""
    return html.Div(
        html.Div(list(children), className=f"page-wrap {extra_class}"),
        className="main-wrap",
    )


def page_hero(tag, title, title_accent=None, subtitle=None, divider=True):
    """Cinematic page hero with eyebrow tag, large title, optional subtitle."""
    parts = [
        html.Div([html.Span(tag)], className="hero-eyebrow"),
    ]
    title_content = [title]
    if title_accent:
        title_content.append(html.Span(title_accent, className="accent-text"))
    parts.append(html.H1(title_content, className="page-title"))
    if divider:
        parts.append(html.Div(className="page-divider"))
    if subtitle:
        parts.append(html.P(subtitle, className="page-subtitle"))
    return html.Div(parts, className="page-hero reveal")


def section_header(title, tag=None):
    """Small section header with optional mono tag on the right."""
    right = html.Span(tag, className="section-tag") if tag else None
    return html.Div(
        [html.Span(title, className="section-hdr-title"), right],
        className="section-hdr",
    )


# ─── Stat / KPI cards ─────────────────────────────────────────────────────────

def stat_card(value, label, icon="", color="#f5a623", counter=False,
              duration=2000, suffix="", decimals=0):
    """
    Premium animated KPI card.
    Pass counter=True to enable JS scroll-triggered count-up animation.
    """
    val_attrs = {
        "className": "stat-card-val",
        "style": {"--stat-color": color},
    }
    if counter:
        # Strip formatting characters so the counter JS gets a plain number
        raw = str(value).replace(",", "").replace("%", "").replace("K", "000").replace("M", "000000")
        try:
            num = float(raw)
        except ValueError:
            num = 0
        val_attrs["data-counter"] = str(num)
        val_attrs["data-duration"] = str(duration)
        val_attrs["data-suffix"] = suffix
        val_attrs["data-decimals"] = str(decimals)

    return html.Div([
        html.Span(icon, className="stat-card-icon"),
        html.Div(str(value), **val_attrs),
        html.Div(label, className="stat-card-label"),
        html.Div(className="stat-card-glow"),
    ], className="stat-card", style={"--stat-color": color})


def kpi_card(label, value, color="#f5a623"):
    """Legacy-compatible KPI card used by existing callback returns."""
    return html.Div([
        html.Div(label, className="kpi-label"),
        html.Div(str(value), className="kpi-value", style={"color": color}),
    ], className="kpi-card")


def kpi_row(*cards):
    """Wrap KPI cards in a centred flex row."""
    return html.Div(list(cards), className="kpi-row")


# ─── Chart wrappers ───────────────────────────────────────────────────────────

def chart_card(graph_or_children, title=None, subtitle=None, extra_class=""):
    """Glass card wrapping a dcc.Graph or any children."""
    parts = []
    if title:
        parts.append(html.Div(title, className="chart-card-title"))
    if subtitle:
        parts.append(html.Div(subtitle, className="chart-card-sub"))
    if isinstance(graph_or_children, list):
        parts.extend(graph_or_children)
    else:
        parts.append(graph_or_children)
    return html.Div(parts, className=f"chart-card {extra_class}")


def graph(fig, config=None):
    """Standard dcc.Graph with display bar hidden."""
    if config is None:
        config = {"displayModeBar": False, "responsive": True}
    return dcc.Graph(figure=fig, config=config, style={"height": "100%"})


def chart_row(*items, cols="two-col"):
    """CSS grid row for charts."""
    return html.Div(
        [html.Div(item, className="glass-card") for item in items],
        className=f"chart-row {cols}",
    )


# ─── Player cards ─────────────────────────────────────────────────────────────

def player_card(player_name, team, primary_stat_val, primary_stat_lbl,
                secondary_stat_val="", secondary_stat_lbl="", rank=None):
    """
    FIFA / NBA 2K style player card with holographic sheen.
    Uses initials-based avatar since we don't have actual photos.
    """
    tc  = team_color(team) or "#1a3060"
    tc2 = _darken(tc, 0.38)
    abbr = team_abbr(team) or "IPL"
    initials = get_initials(player_name)

    try:
        r, g, b = _hex_to_rgb(tc)
        glow_rgba = f"rgba({r},{g},{b},0.35)"
        border_rgba = f"rgba({r},{g},{b},0.45)"
    except Exception:
        glow_rgba = "rgba(245,166,35,0.35)"
        border_rgba = "rgba(245,166,35,0.45)"

    rank_el = html.Div(f"#{rank}", className="player-rank-badge") if rank else None

    stats = [
        html.Div([
            html.Span(str(primary_stat_val), className="pc-stat-val"),
            html.Span(primary_stat_lbl, className="pc-stat-lbl"),
        ], className="pc-stat"),
    ]
    if secondary_stat_val:
        stats.append(html.Div([
            html.Span(str(secondary_stat_val), className="pc-stat-val"),
            html.Span(secondary_stat_lbl, className="pc-stat-lbl"),
        ], className="pc-stat"))

    return html.Div([
        html.Div(className="player-card-bg", style={
            "background": f"linear-gradient(145deg, {tc2} 0%, #060c16 100%)"
        }),
        html.Div(className="player-card-sheen"),
        html.Div(className="player-card-border", style={
            "--pc-border": border_rgba,
            "boxShadow": f"inset 0 0 20px {glow_rgba}, 0 0 20px {glow_rgba}",
        }),
        rank_el,
        html.Div([
            html.Div([
                html.Div([
                    html.Div(initials, className="player-avatar"),
                ], className="player-avatar-ring", style={
                    "background": f"conic-gradient(from 0deg, {tc} 0%, #f5a623 50%, {tc} 100%)"
                }),
            ], className="player-avatar-wrap"),
            html.Div([
                html.Div(abbr, className="pc-team", style={"color": tc}),
                html.Div(player_name, className="pc-name"),
                html.Div(stats, className="pc-stats"),
            ], className="player-card-info"),
        ], className="player-card-inner"),
    ], className="player-card", style={"--pc-color": tc, "--tc1": tc2})


def player_card_grid(*cards):
    """Responsive grid of player cards."""
    return html.Div(list(cards), className="player-card-grid stagger-in")


# ─── Controls bar ─────────────────────────────────────────────────────────────

def controls_bar(*groups):
    """Styled filter/control bar."""
    return html.Div(list(groups), className="controls-bar reveal")


def control_group(label, *children):
    """Labelled control group (dropdown, slider, etc.)."""
    return html.Div([
        html.Div(label, className="control-label"),
        *children,
    ], className="control-group")


# ─── Ranking list ─────────────────────────────────────────────────────────────

def ranking_row(pos, name, value, max_value, unit="", color="#f5a623"):
    """One row in a rankings / top-N list with an animated bar."""
    pct = min(int((value / max_value) * 100), 100) if max_value else 0
    top_class = "rank-pos top" if pos <= 3 else "rank-pos"
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    pos_display = medals.get(pos, str(pos))
    return html.Div([
        html.Span(pos_display, className=top_class),
        html.Span(name, className="rank-name"),
        html.Div(html.Div(className="rank-bar-fill", style={
            "width": f"{pct}%",
            "background": f"linear-gradient(90deg, {color}, {_darken(color, 1.5)})",
        }), className="rank-bar-wrap"),
        html.Span(f"{value:,}{unit}", className="rank-val", style={"color": color}),
    ], className="ranking-row")


def rankings_list(*rows):
    return html.Div(list(rows), className="rankings-list")


# ─── Match components ─────────────────────────────────────────────────────────

def match_header_card(team1, team2, date_str, venue, result_text, potm):
    """Cinematic match header with team badges, result, and POTM."""
    c1 = team_color(team1)
    c2 = team_color(team2)
    return html.Div([
        html.Div([
            html.Div([
                html.Div(team_abbr(team1), className="match-team-badge", style={"color": c1}),
                html.Div(team1, className="match-team-name"),
            ], className="match-team-block"),
            html.Div([
                html.Div("VS", className="match-vs"),
            ], className="matchup-vs-block"),
            html.Div([
                html.Div(team_abbr(team2), className="match-team-badge", style={"color": c2}),
                html.Div(team2, className="match-team-name"),
            ], className="match-team-block"),
        ], className="match-teams-row"),
        html.Div([
            html.Div(result_text, className="match-result-text"),
            html.Div(f"{date_str}  ·  {venue[:40] if venue else ''}", className="match-meta"),
            html.Div(f"⭐ POTM: {potm}", className="match-potm") if potm else None,
        ], className="match-result-row"),
    ], className="match-header-card reveal")


def inning_header(num_label, team, score, wickets, overs_str, team_clr):
    """Styled inning header showing team name and score."""
    return html.Div([
        html.Div([
            html.Span(num_label, className="inning-overs"),
            html.Span(f"  {team}", className="inning-team-name", style={"color": team_clr}),
        ]),
        html.Div([
            html.Span(f"{score}/{wickets}", className="inning-score"),
            html.Span(f"  ({overs_str} ov)", className="inning-overs"),
        ]),
    ], className="inning-hdr", style={
        "background": f"rgba({','.join(str(c) for c in _hex_to_rgb(team_clr))},0.06)",
        "borderColor": f"rgba({','.join(str(c) for c in _hex_to_rgb(team_clr))},0.18)",
    })


# ─── Insight / advanced cards ─────────────────────────────────────────────────

def insight_card(tag, text):
    """Purple-accented AI-insight card."""
    return html.Div([
        html.Div(f"◆ {tag}", className="insight-tag"),
        html.Div(text, className="insight-text"),
    ], className="insight-card reveal")


# ─── Featured nav cards ────────────────────────────────────────────────────────

def featured_card(icon, title, description, href="#"):
    """Large clickable navigation card for the homepage."""
    return html.A([
        html.Span(icon, className="featured-card-icon"),
        html.Div(title, className="featured-card-title"),
        html.Div(description, className="featured-card-desc"),
        html.Span("→", className="featured-card-arrow"),
        html.Div(className="featured-glow"),
    ], href=href, className="featured-card")


def featured_grid(*cards):
    return html.Div(list(cards), className="featured-grid stagger-in")


# ─── Team trophy cabinet ──────────────────────────────────────────────────────

def trophy_cabinet(years):
    """Render a trophy-cabinet grid for a given list of years."""
    if not years:
        return html.Div("No titles yet", style={"color": "rgba(255,255,255,0.3)", "fontSize": "0.85rem"})
    items = [
        html.Div([
            html.Span("🏆", className="trophy-icon"),
            html.Div(str(y), className="trophy-yr"),
        ], className="trophy-item")
        for y in sorted(years)
    ]
    return html.Div(items, className="trophy-grid")


# ─── Player profile section ───────────────────────────────────────────────────

def player_profile_card(player_name, team, role, bat_stats=None, bowl_stats=None):
    """
    Full-width player profile card at the top of the player analysis page.
    bat_stats / bowl_stats: dicts with keys like runs, sr, average, wickets, economy…
    """
    tc       = team_color(team) or "#f5a623"
    abbr_txt = team_abbr(team) or "IPL"
    initials = get_initials(player_name)

    stat_blocks = []

    if bat_stats:
        stat_blocks.append(html.Div("🏏 Batting", className="profile-section-hdr"))
        bat_items = []
        mapping = [
            ("Runs",     bat_stats.get("runs", 0)),
            ("Innings",  bat_stats.get("innings", 0)),
            ("SR",       bat_stats.get("sr", 0)),
            ("Avg",      bat_stats.get("average", 0)),
            ("4s / 6s",  f"{bat_stats.get('fours',0)} / {bat_stats.get('sixes',0)}"),
            ("50s/100s", f"{bat_stats.get('fifties',0)} / {bat_stats.get('hundreds',0)}"),
        ]
        for lbl, val in mapping:
            bat_items.append(html.Div([
                html.Span(str(val), className="profile-stat-val"),
                html.Span(lbl, className="profile-stat-lbl"),
            ], className="profile-stat"))
        stat_blocks.append(html.Div(bat_items, className="profile-stats-grid"))

    if bowl_stats:
        stat_blocks.append(html.Div("🎯 Bowling", className="profile-section-hdr"))
        bowl_items = []
        mapping = [
            ("Wickets",  bowl_stats.get("wickets", 0)),
            ("Innings",  bowl_stats.get("innings", 0)),
            ("Economy",  bowl_stats.get("economy", 0)),
            ("Bowl SR",  bowl_stats.get("sr", 0)),
            ("Dot %",    f"{bowl_stats.get('dot_pct', 0)}%"),
        ]
        for lbl, val in mapping:
            bowl_items.append(html.Div([
                html.Span(str(val), className="profile-stat-val"),
                html.Span(lbl, className="profile-stat-lbl"),
            ], className="profile-stat"))
        stat_blocks.append(html.Div(bowl_items, className="profile-stats-grid"))

    return html.Div([
        html.Div([
            html.Div(initials, className="profile-avatar",
                     style={"--pf-color": tc,
                            "background": f"linear-gradient(135deg, {_darken(tc,0.4)} 0%, #0a1520 100%)"}),
            html.Div([
                html.Div(player_name, className="profile-name"),
                html.Div([
                    html.Span(abbr_txt, className="profile-team-badge", style={"--pf-color": tc}),
                    html.Span(role, className="profile-role"),
                ], className="profile-meta"),
            ]),
        ], className="player-profile-top"),
        html.Div(stat_blocks),
    ], className="player-profile reveal", style={"--pf-color": tc})


# ─── Rivalry / H2H header ─────────────────────────────────────────────────────

def rivalry_header(team_a, team_b, wins_a, wins_b, total_matches):
    """Visual header for head-to-head rivalry pages."""
    ca = team_color(team_a) or "#f5a623"
    cb = team_color(team_b) or "#00d4ff"
    return html.Div([
        html.Div([
            html.Div(team_abbr(team_a) or "?", className="rivalry-abbr", style={"color": ca}),
            html.Div(str(wins_a), className="rivalry-wins"),
            html.Div(team_a, style={"fontSize": "0.75rem", "color": "rgba(255,255,255,0.45)"}),
        ], className="rivalry-team"),
        html.Div([
            html.Div("VS", className="rivalry-vs-text"),
            html.Div(f"{total_matches} matches", className="rivalry-matches-count"),
        ], className="rivalry-vs"),
        html.Div([
            html.Div(team_abbr(team_b) or "?", className="rivalry-abbr", style={"color": cb}),
            html.Div(str(wins_b), className="rivalry-wins"),
            html.Div(team_b, style={"fontSize": "0.75rem", "color": "rgba(255,255,255,0.45)"}),
        ], className="rivalry-team"),
    ], className="rivalry-header reveal")


# ─── Matchup arena (Player vs Player) ─────────────────────────────────────────

def matchup_arena(batter, batter_team, bowler, bowler_team,
                  balls, runs, sr, dismissals):
    """Visual VS arena for player vs player page."""
    bat_c  = team_color(batter_team) or "#00d4ff"
    bowl_c = team_color(bowler_team) or "#ff4757"
    return html.Div([
        html.Div([
            html.Div(get_initials(batter), className="matchup-avatar",
                     style={"background": f"linear-gradient(135deg,{_darken(bat_c,0.4)},#0a1520)",
                            "borderColor": bat_c, "color": "white"}),
            html.Div(batter, className="matchup-name"),
            html.Div(team_abbr(batter_team), className="matchup-team-lbl", style={"color": bat_c}),
            html.Span("🏏 BATTER", className="badge badge-cyan",
                      style={"marginTop": "4px", "fontSize": "0.6rem"}),
        ], className="matchup-player"),
        html.Div([
            html.Div("VS", className="matchup-vs-text"),
            html.Div([
                html.Span(f"{balls} balls", className="badge badge-gold"),
                html.Span(f"{runs} runs", className="badge badge-green"),
                html.Span(f"SR {sr}", className="badge badge-cyan"),
                html.Span(f"{dismissals} 🎯", className="badge badge-red"),
            ], style={"display": "flex", "flexWrap": "wrap", "gap": "5px",
                      "justifyContent": "center", "marginTop": "8px"}),
        ], className="matchup-vs-block"),
        html.Div([
            html.Div(get_initials(bowler), className="matchup-avatar",
                     style={"background": f"linear-gradient(135deg,{_darken(bowl_c,0.4)},#0a1520)",
                            "borderColor": bowl_c, "color": "white"}),
            html.Div(bowler, className="matchup-name"),
            html.Div(team_abbr(bowler_team), className="matchup-team-lbl", style={"color": bowl_c}),
            html.Span("🎯 BOWLER", className="badge badge-red",
                      style={"marginTop": "4px", "fontSize": "0.6rem"}),
        ], className="matchup-player"),
    ], className="matchup-arena")

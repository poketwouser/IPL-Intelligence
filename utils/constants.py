"""Theme constants, team mappings, and chart templates for the IPL Dashboard."""

# ─── Theme ────────────────────────────────────────────────────────────────────
THEME = {
    "bg_dark": "#0b1020",
    "card_bg": "#111827",
    "accent": "#ffb703",
    "text": "white",
    "neon_blue": "#00b4d8",
    "neon_green": "#00e676",
    "neon_red": "#f44336",
    "neon_purple": "#ce93d8",
}

# ─── Team Info ────────────────────────────────────────────────────────────────
TEAM_INFO = {
    "Chennai Super Kings":          {"abbr": "CSK",  "color": "#F9CD05"},
    "Mumbai Indians":               {"abbr": "MI",   "color": "#004BA0"},
    "Royal Challengers Bangalore":  {"abbr": "RCB",  "color": "#DA1818"},
    "Royal Challengers Bengaluru":  {"abbr": "RCB",  "color": "#DA1818"},
    "Kolkata Knight Riders":        {"abbr": "KKR",  "color": "#3A225D"},
    "Delhi Capitals":               {"abbr": "DC",   "color": "#17449B"},
    "Delhi Daredevils":             {"abbr": "DD",   "color": "#17449B"},
    "Sunrisers Hyderabad":          {"abbr": "SRH",  "color": "#FF822A"},
    "Rajasthan Royals":             {"abbr": "RR",   "color": "#E73895"},
    "Punjab Kings":                 {"abbr": "PBKS", "color": "#C91C1C"},
    "Kings XI Punjab":              {"abbr": "KXIP", "color": "#C91C1C"},
    "Lucknow Super Giants":        {"abbr": "LSG",  "color": "#009FDB"},
    "Gujarat Titans":               {"abbr": "GT",   "color": "#1C2833"},
    "Rising Pune Supergiant":       {"abbr": "RPS",  "color": "#652D91"},
    "Rising Pune Supergiants":      {"abbr": "RPS",  "color": "#652D91"},
    "Pune Warriors India":          {"abbr": "PWI",  "color": "#3C8DBC"},
    "Pune Warriors":                {"abbr": "PWI",  "color": "#3C8DBC"},
    "Kochi Tuskers Kerala":         {"abbr": "KTK",  "color": "#EE7B30"},
    "Gujarat Lions":                {"abbr": "GL",   "color": "#F26522"},
    "Deccan Chargers":              {"abbr": "DCG",  "color": "#2E8B57"},
}

REGION_COLORS = {"UAE": "#F59E0B", "SA": "#10B981"}

PHASE_COLORS = {"PP": "#FFD700", "Powerplay": "#FFD700", "Middle": "#1E90FF", "Death": "#DC143C"}

# Non-bowler dismissals (not credited to the bowler)
NON_BOWLER_DISMISSALS = frozenset([
    "Run Out", "Obstructing The Field", "Retired Hurt", "Retired Out",
    "Handled The Ball", "Timed Out",
])

# Extras that don't count as valid balls
INVALID_BALL_EXTRAS = frozenset(["Wides", "Noballs", "Wide", "No ball"])


def team_abbr(name):
    """Get team abbreviation from full name."""
    if not name or str(name) == "nan":
        return "N/A"
    info = TEAM_INFO.get(name)
    if info:
        return info["abbr"]
    return str(name)[:3].upper()


def team_color(name, fallback="#888888"):
    """Get team color from full name."""
    if not name or str(name) == "nan":
        return fallback
    info = TEAM_INFO.get(name)
    if info:
        return info["color"]
    if name in REGION_COLORS:
        return REGION_COLORS[name]
    return fallback


# ─── Plotly Layout Template ───────────────────────────────────────────────────
PLOTLY_TEMPLATE = dict(
    plot_bgcolor=THEME["bg_dark"],
    paper_bgcolor=THEME["bg_dark"],
    font=dict(color="white", family="Inter, sans-serif"),
    margin=dict(l=50, r=30, t=50, b=40),
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
)


def apply_dark_theme(fig, **kwargs):
    """Apply the standard dark theme to any Plotly figure."""
    layout_args = {**PLOTLY_TEMPLATE, **kwargs}
    fig.update_layout(**layout_args)
    return fig


# ─── Card Helper ──────────────────────────────────────────────────────────────
def kpi_style():
    return {
        "background": THEME["card_bg"],
        "borderRadius": "12px",
        "padding": "14px 16px",
        "textAlign": "center",
        "border": "1px solid rgba(255,255,255,0.06)",
        "minWidth": "140px",
    }

"""
IPL Intelligence Platform — Production Application
====================================================
Cinematic sports analytics experience. Dash multi-page with floating navbar,
particle canvas, custom cursor, and premium dark design system.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_caching import Cache

from utils.data_loader import load_data
from utils.constants import THEME

# ─── Pre-load Data ─────────────────────────────────────────────────────────────
DATA = load_data()

# ─── App Init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Orbitron:wght@400;600;700;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="IPL Intel — Cricket Intelligence Platform",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "theme-color", "content": "#020509"},
        {"name": "description", "content": "Premium IPL Analytics Dashboard — 2008 to 2024"},
    ],
)

server = app.server
cache  = Cache(server, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 600})

# ─── Navigation Config ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    {"href": "/",                 "icon": "🏟️", "label": "Overview"},
    {"href": "/match-explorer",   "icon": "📋", "label": "Matches"},
    {"href": "/head-to-head",     "icon": "⚔️", "label": "Head to Head"},
    {"href": "/players",          "icon": "🏏", "label": "Players"},
    {"href": "/player-vs-player", "icon": "🎯", "label": "Matchup"},
    {"href": "/teams",            "icon": "🛡️", "label": "Teams"},
    {"href": "/advanced",         "icon": "🔬", "label": "Analytics Lab"},
]


def _nav_link(item, mobile=False):
    cls = "drawer-nav-link" if mobile else "nav-link"
    return html.A(
        [html.Span(item["icon"], className="nav-link-icon"), item["label"]],
        href=item["href"],
        className=cls,
    )


def make_navbar():
    return html.Nav([
        # Logo
        html.A([
            html.Div("🏏", className="nav-logo-ball"),
            html.Span("IPL INTEL", className="nav-logo-text"),
        ], href="/", className="nav-logo"),

        # Center links (desktop)
        html.Div(
            [_nav_link(item) for item in NAV_ITEMS],
            className="nav-links",
        ),

        # Right side
        html.Div([
            html.Span("2008 – 2024", className="nav-badge"),
            html.Button([html.Span(), html.Span(), html.Span()],
                        className="hamburger", id="hamburger-btn",
                        **{"aria-label": "Menu"}),
        ], className="nav-right"),
    ], className="floating-navbar", id="floating-navbar")


def make_mobile_drawer():
    links = [_nav_link(item, mobile=True) for item in NAV_ITEMS]
    return html.Div([
        html.Div([
            html.Div("🏏", className="nav-logo-ball", style={"marginBottom": "4px"}),
            html.Div("IPL INTEL", style={
                "fontFamily": "'Orbitron', sans-serif",
                "fontSize": "0.9rem",
                "fontWeight": "700",
                "letterSpacing": "0.14em",
                "color": "#f5a623",
                "marginBottom": "20px",
            }),
        ], style={"textAlign": "center"}),
        *links,
        html.Div(style={"flex": "1"}),
        html.Div("Built with Dash · Plotly", style={
            "fontFamily": "'JetBrains Mono', monospace",
            "fontSize": "0.65rem",
            "color": "rgba(255,255,255,0.2)",
            "letterSpacing": "0.08em",
            "textAlign": "center",
            "paddingTop": "20px",
            "borderTop": "1px solid rgba(255,255,255,0.06)",
        }),
    ], className="mobile-drawer", id="mobile-drawer")


# ─── Root Layout ───────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id="data-loaded", data=True),
    dcc.Location(id="url", refresh=False),

    # ── Animated background layers ──────────────────────────────
    html.Div(className="ipl-bg"),
    html.Canvas(id="particle-canvas"),

    # ── Custom cursor ───────────────────────────────────────────
    html.Div(id="cursor", className="cursor"),
    html.Div(id="cursor-ring", className="cursor-ring"),

    # ── Page loader ─────────────────────────────────────────────
    html.Div([
        html.Div("IPL INTEL", className="loader-brand"),
        html.Div("Cricket Intelligence Platform", className="loader-sub"),
        html.Div(html.Div(className="loader-fill"), className="loader-track"),
    ], id="page-loader", className="page-loader"),

    # ── Scroll progress ─────────────────────────────────────────
    html.Div(className="scroll-progress", id="scroll-progress"),

    # ── Floating navbar ─────────────────────────────────────────
    make_navbar(),

    # ── Mobile drawer + overlay ─────────────────────────────────
    make_mobile_drawer(),
    html.Div(className="drawer-overlay", id="drawer-overlay"),

    # ── Page content ────────────────────────────────────────────
    html.Main(
        html.Div(dash.page_container, className="page-wrap"),
        className="main-content",
    ),

    # ── Footer ──────────────────────────────────────────────────
    html.Footer(
        "IPL Intel  ·  2008–2024  ·  Built with Dash & Plotly  ·  Data: Cricsheet",
        className="page-footer",
    ),

], className="app-root")


# ─── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)

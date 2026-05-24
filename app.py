"""
IPL Intelligence Platform — v4.0
Cinema-grade cricket analytics. GSAP + Lenis smooth scroll. Apple Sports aesthetic.
"""

import dash
from dash import html, dcc
from flask_caching import Cache

from utils.data_loader import load_data
from utils.constants import THEME

DATA = load_data()

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap",
    ],
    external_scripts=[
        {"src": "https://cdn.jsdelivr.net/npm/lenis@1.1.14/dist/lenis.min.js"},
        {"src": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"},
        {"src": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"},
    ],
    suppress_callback_exceptions=True,
    title="IPL Intel — Cricket Intelligence Platform",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "theme-color", "content": "#010205"},
        {"name": "description", "content": "Premium IPL Analytics Dashboard — 2008 to 2024"},
    ],
)

server = app.server
cache = Cache(server, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 600})

NAV_ITEMS = [
    {"href": "/",                 "label": "Overview",      "icon": "HOME"},
    {"href": "/match-explorer",   "label": "Matches",       "icon": "MATCH"},
    {"href": "/head-to-head",     "label": "H2H",           "icon": "RIVAL"},
    {"href": "/players",          "label": "Players",       "icon": "PLAYER"},
    {"href": "/player-vs-player", "label": "Matchup",       "icon": "VS"},
    {"href": "/teams",            "label": "Teams",         "icon": "TEAM"},
    {"href": "/advanced",         "label": "Lab",           "icon": "LAB"},
]


def _nav_link(item, mobile=False):
    cls = "drawer-link" if mobile else "nav-link"
    return html.A(
        [
            html.Span(item["icon"], className="nav-link-tag"),
            html.Span(item["label"], className="nav-link-label"),
        ],
        href=item["href"],
        className=cls,
    )


def make_navbar():
    return html.Nav([
        html.A([
            html.Div(className="logo-orb"),
            html.Div([
                html.Span("IPL", className="logo-ipl"),
                html.Span("INTEL", className="logo-intel"),
            ], className="logo-text-wrap"),
        ], href="/", className="nav-logo"),

        html.Div([_nav_link(item) for item in NAV_ITEMS], className="nav-links"),

        html.Div([
            html.Span("2024", className="nav-season-badge"),
            html.Button(
                [html.Span(className="bar"), html.Span(className="bar"), html.Span(className="bar")],
                className="hamburger",
                id="hamburger-btn",
                **{"aria-label": "Open menu"},
            ),
        ], className="nav-right"),
    ], className="navbar", id="navbar")


def make_drawer():
    return html.Div([
        html.Div([
            html.Div(className="drawer-logo-orb"),
            html.Div("IPL INTEL", className="drawer-logo-text"),
            html.Button("✕", className="drawer-close", id="drawer-close"),
        ], className="drawer-header"),
        html.Nav([_nav_link(item, mobile=True) for item in NAV_ITEMS], className="drawer-nav"),
        html.Div([
            html.Div("2008 – 2024 · Cricsheet Data", className="drawer-footer-text"),
        ], className="drawer-footer"),
    ], className="drawer", id="drawer")


app.layout = html.Div([
    dcc.Store(id="data-loaded", data=True),
    dcc.Location(id="url", refresh=False),

    html.Div(id="cursor"),
    html.Div(id="cursor-trail"),

    html.Div([
        html.Div(className="loader-orb"),
        html.Div([
            html.Div("IPL", className="loader-title-ipl"),
            html.Div("INTELLIGENCE", className="loader-title-sub"),
        ], className="loader-title"),
        html.Div(className="loader-bar-wrap", children=[
            html.Div(className="loader-bar-fill", id="loader-bar"),
        ]),
        html.Div("Loading cricket data…", className="loader-hint"),
    ], id="page-loader", className="page-loader"),

    html.Div(className="scroll-line", id="scroll-line"),

    html.Div(className="ambient-layer"),
    html.Canvas(id="particle-canvas"),

    make_navbar(),
    make_drawer(),
    html.Div(className="drawer-backdrop", id="drawer-backdrop"),

    html.Main(
        html.Div(dash.page_container, className="page-content"),
        className="main",
    ),

    html.Footer([
        html.Div([
            html.Span("IPL INTEL", className="footer-brand"),
            html.Span("·", className="footer-dot"),
            html.Span("2008 – 2024", className="footer-meta"),
            html.Span("·", className="footer-dot"),
            html.Span("Data: Cricsheet", className="footer-meta"),
            html.Span("·", className="footer-dot"),
            html.Span("Built with Dash & Plotly", className="footer-meta"),
        ], className="footer-inner"),
    ], className="footer"),

], id="app-root")


if __name__ == "__main__":
    app.run(debug=True, port=8050)

"""
IPL Analytics Dashboard — Production Dash Application
=====================================================
Multi-page Dash app with 7 analytics modules covering all IPL data from 2008–2024.
"""
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_caching import Cache

from utils.data_loader import load_data
from utils.constants import THEME

# ─── Pre-load Data ────────────────────────────────────────────────────────────
DATA = load_data()

# ─── App Init ─────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="IPL Analytics — Cricket Intelligence Platform",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server
cache = Cache(server, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 600})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    {"href": "/",               "icon": "🏟️", "label": "Overview"},
    {"href": "/match-explorer", "icon": "📋", "label": "Match Explorer"},
    {"href": "/head-to-head",   "icon": "⚔️", "label": "Head to Head"},
    {"href": "/players",        "icon": "🏏", "label": "Player Analysis"},
    {"href": "/player-vs-player","icon": "🎯", "label": "Player v Player"},
    {"href": "/teams",          "icon": "🛡️", "label": "Teams"},
    {"href": "/advanced",       "icon": "🔬", "label": "Analytics Lab"},
]

def make_sidebar():
    nav_links = []
    for item in NAV_ITEMS:
        nav_links.append(
            dbc.NavLink(
                [html.Span(item["icon"], className="me-2"), item["label"]],
                href=item["href"],
                active="exact",
                className="sidebar-link",
            )
        )
    return html.Div(
        [
            html.Div(
                [
                    html.Div("⚡", className="sidebar-logo-icon"),
                    html.Div([
                        html.H5("IPL Analytics", className="mb-0 fw-bold text-white"),
                        html.Small("2008 — 2024", className="text-muted", style={"fontSize": "10px", "letterSpacing": "2px"}),
                    ]),
                ],
                className="d-flex align-items-center gap-2 px-3 py-3 border-bottom border-secondary",
            ),
            dbc.Nav(nav_links, vertical=True, pills=True, className="py-2 px-2 flex-grow-1"),
            html.Div(
                html.Small("Built with Dash • Plotly", className="text-muted"),
                className="text-center py-3 border-top border-secondary",
                style={"fontSize": "10px"},
            ),
        ],
        className="sidebar d-flex flex-column",
    )


# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = html.Div(
    [
        dcc.Store(id="data-loaded", data=True),
        make_sidebar(),
        html.Div(
            dash.page_container,
            className="main-content",
        ),
    ],
    className="app-container",
)


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)

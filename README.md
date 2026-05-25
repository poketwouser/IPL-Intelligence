<p align="center">
  <img src="https://img.shields.io/badge/IPL-Intelligence-f5a623?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgZmlsbD0iI2Y1YTYyMyIvPjwvc3ZnPg==&logoColor=white" alt="IPL Intelligence" />
  <br/>
  <img src="https://img.shields.io/badge/Dash-2.14+-00ADD8?style=flat-square&logo=plotly" />
  <img src="https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=flat-square&logo=plotly" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/GSAP-3.12-88CE02?style=flat-square" />
  <img src="https://img.shields.io/badge/Deploy-Vercel-000000?style=flat-square&logo=vercel" />
  <a href="https://ipl-intel.vercel.app/" target="_blank"><img src="https://img.shields.io/badge/Live_Demo-🔴_Online-FF0000?style=flat-square" /></a>
</p>

<h1 align="center">🏏 IPL Intelligence Platform</h1>

<p align="center">
  <strong><a href="https://ipl-intel.vercel.app/">🌐 VIEW LIVE DEMO: ipl-intel.vercel.app</a></strong>
</p>

<p align="center">
  <strong>Cinema-grade cricket analytics. Apple Sports × F1 aesthetics.</strong>
  <br/>
  <em>19 seasons (2008–2026 Live) · 1,200+ matches · 260K+ deliveries — decoded.</em>
</p>

---

## ✨ What Is This?

IPL Intelligence is a **production-grade cricket analytics platform** built with Python, Dash, and Plotly. It transforms raw Cricsheet ball-by-ball data (2008–2026) into an immersive, cinematic sports intelligence experience.

This is not a dashboard. It's a **sports cinematography engine** — with GSAP-powered animations, glassmorphic UI, holographic player cards, scroll-triggered storytelling, and 3D tilt effects.

---

## 🎯 Features

### 📊 Analytics Modules
| Module | Description |
|--------|-------------|
| **Overview** | Cinematic homepage with hero, season rewind timeline, KPI counters |
| **Match Explorer** | Ball-by-ball scorecards, Manhattan, Worm, Fall of Wickets |
| **Head to Head** | Team rivalry analysis with margin distributions, season arcs |
| **Player Analysis** | FIFA-style profile cards, radar charts, performance meters |
| **Batter vs Bowler** | Matchup arena with outcome distributions, over-by-over profiling |
| **Team Intelligence** | Trophy cabinets, venue dominance, season performance trends |
| **Analytics Lab** | Win probability curves, Impact Player scores, phase evolution |

### 🎨 Design System
- **Dark Cinema Theme** — void-to-surface gradient palette
- **Glassmorphism** — frosted-glass cards with 24px blur + saturation
- **Holographic Foil** — CSS `@property` animated gradient on player cards
- **GSAP Scroll Reveals** — directional, staggered, scale-up animations
- **Lenis Smooth Scroll** — butter-smooth inertia scrolling
- **3D Tilt** — perspective-based card interactions
- **Magnetic Buttons** — cursor-attracted micro-animations
- **Custom Cursor** — dot + trail system with hover states
- **Stadium Glow** — pulsing radial ambient light effects
- **Page Transitions** — blur + slide animation between routes

### ⚡ Impact Player Analytics (NEW)
- **Impact Score** — `avg(runs + wickets × 25)` per match appearance
- **Leaderboard** — Top 15 all-time impact players
- **Phase Strategy** — Team RPO comparison across Powerplay/Middle/Death
- **Win Probability** — Over-by-over chase success curves

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Dash 2.14+ (multi-page architecture) |
| **Charting** | Plotly 5.18+ (dark-themed, interactive) |
| **Data** | Pandas + Parquet (compressed, fast I/O) |
| **Animations** | GSAP 3.12 + ScrollTrigger |
| **Scrolling** | Lenis smooth scroll |
| **Styling** | Custom CSS (2,500+ lines, design system v5) |
| **Server** | Flask + Vercel Serverless |
| **Caching** | Flask-Caching (SimpleCache) |
| **Deployment** | Vercel (vercel.json + api/index.py included) |
| **Data Source** | [Cricsheet](https://cricsheet.org/) (2008–2026) |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/ipl-data-curation-and-visualization.git
cd ipl-data-curation-and-visualization

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open **http://localhost:8050** in your browser.

---

## 📂 Project Structure

```
├── app.py                  # Main Dash application + layout
├── pages/
│   ├── overview.py         # Cinematic homepage + season rewind
│   ├── match_explorer.py   # Ball-by-ball match center
│   ├── head_to_head.py     # Team rivalry analytics
│   ├── players.py          # Player profiles + radar charts
│   ├── player_vs_player.py # Batter vs Bowler matchup arena
│   ├── teams.py            # Franchise intelligence
│   └── advanced.py         # Analytics lab + Impact Player
├── utils/
│   ├── analytics.py        # Statistical computation engine
│   ├── components.py       # UI component library (50+ components)
│   ├── constants.py        # Design tokens + team mappings
│   ├── data_loader.py      # Parquet data pipeline
│   └── player_images.py    # ESPNcricinfo image pipeline
├── assets/
│   ├── style.css           # Design system v5 (2,500+ lines)
│   ├── animations.js       # GSAP animation engine v5
│   └── particles.js        # Canvas particle system
├── data/processed/         # Parquet datasets (matches, deliveries, venues)
├── Procfile                # Render deployment
├── render.yaml             # Render service config
└── requirements.txt        # Python dependencies
```

---

## 🌍 Deployment

### Vercel (Recommended)

1. Push your code to GitHub.
2. Go to [Vercel](https://vercel.com) and click **Add New Project**.
3. Import your GitHub repository.
4. Leave all settings as default (Vercel will auto-detect `vercel.json`).
5. Click **Deploy**. The app will be available on a `.vercel.app` domain. 🚀

### Hugging Face Spaces (Free Alternative)

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and create a new Space.
2. Choose **Docker** as the SDK and select **Blank**.
3. Push your repository to the Hugging Face git remote.
4. The space will automatically build using the provided `Dockerfile` and host it for free.

### Manual

```bash
gunicorn app:server --bind 0.0.0.0:8050 --workers 2 --timeout 120
```

---

## 📊 Data Pipeline

The platform uses pre-processed Parquet files for fast startup:

1. **Raw Data** — CSV from Cricsheet (`data/raw/`)
2. **Processing** — Jupyter notebooks (`notebooks/P01-P05`)
3. **Output** — Optimized Parquet files (`data/processed/`)
4. **Loading** — `utils/data_loader.py` reads Parquet at startup

---

## 🎨 Design Philosophy

> *"Every pixel should feel like it belongs in a broadcast."*

The design draws from:
- **Apple Sports** — Clean typography, spacious layouts
- **Formula 1 App** — Dark cinema aesthetics, data-rich displays
- **FIFA Ultimate Team** — Holographic player cards with team colors
- **SofaScore** — Performance meters, form curves
- **Netflix** — Scroll-triggered content reveals

---

## 📜 License

MIT License. Data sourced from [Cricsheet](https://cricsheet.org/) under their terms.

---

<p align="center">
  <sub>Built with ❤️ and way too much cricket data.</sub>
</p>

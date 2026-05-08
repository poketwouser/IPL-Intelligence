# 🏏 IPL Analytics Dashboard

A production-grade IPL cricket analytics platform with 17 seasons of data (2008–2024), interactive visualizations, and advanced metrics.

## ✨ Features

### 📊 Dashboard Modules
- **Overview** — KPI cards, season trends, top performers, venue map, boundary/dot trends
- **Head to Head** — Team matchup analytics with win comparison, toss impact, margin distributions
- **Player Analysis** — Career stats, season runs/wickets, form curves, dismissal breakdowns, phase analysis
- **Player vs Player** — Batter vs bowler matchup with outcomes, phase strike rates, over profiles
- **Team Analytics** — Win percentages, toss impact gauges, champions timeline
- **Advanced Lab** — Win probability curves, scoring patterns, run distributions

### 🎨 Design
- Dark futuristic theme with glassmorphism
- Animated KPI counters with Framer Motion
- Interactive Plotly.js charts with dark theme
- Responsive sidebar navigation
- Particle-effect backgrounds
- Premium typography (Inter)

## 🛠️ Tech Stack
- **Next.js 15+** with App Router
- **TypeScript** for type safety
- **TailwindCSS** for styling
- **Plotly.js** for interactive charts
- **Framer Motion** for animations
- **Zustand** for state management

## 🚀 Getting Started

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## 📦 Data
The dashboard uses pre-processed IPL data:
- `matches.json` — 1,106 matches with full metadata
- `deliveries.json` — 260,920 ball-by-ball records
- `venue_coords.json` — 37 venue locations

## 🌐 Deployment

### Vercel
```bash
npx vercel
```

### GitHub Pages
```bash
npm run build
```

## 📁 Architecture
```
dashboard/
├── app/                    # Next.js pages
│   ├── page.tsx           # Overview
│   ├── head-to-head/      # Team matchups
│   ├── players/           # Player analysis
│   ├── player-vs-player/  # PvP matchups
│   ├── teams/             # Team analytics
│   └── advanced/          # Advanced lab
├── components/            # React components
│   ├── charts/            # PlotlyChart, KPICard
│   └── layout/            # Sidebar
├── lib/                   # Core logic
│   ├── analytics.ts       # Cricket computation engine
│   ├── constants.ts       # Teams, colors, theme
│   └── data.ts            # Data loading
├── hooks/                 # Zustand store
├── types/                 # TypeScript definitions
└── public/data/           # JSON data files
```

## 📊 Preserved Notebook Logic
All original notebook analytics are preserved and enhanced:
- P01/P03: Data preprocessing & imputation
- P06: Season overview with 10+ KPIs
- P07: Head-to-head with KDE distributions
- P08: Player analysis with form curves
- P09: Player vs Player matchup engine

## License
MIT

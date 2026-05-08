'use client';
import { useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useDataStore } from '@/hooks/useData';
import KPICard from '@/components/charts/KPICard';
import PlotlyChart from '@/components/charts/PlotlyChart';
import {
  computeOverviewKPIs, computeSeasonTrends, computeTopBatters,
  computeTopBowlers, computeBoundaryDotTrends, buildSeasonMap,
} from '@/lib/analytics';
import { getTeamColor, THEME } from '@/lib/constants';

export default function OverviewPage() {
  const { matches, deliveries, venues, loading, loaded, loadData } = useDataStore();
  useEffect(() => { loadData(); }, [loadData]);

  const seasonMap = useMemo(() => loaded ? buildSeasonMap(matches) : {}, [matches, loaded]);
  const kpis = useMemo(() => loaded ? computeOverviewKPIs(matches, deliveries) : null, [matches, deliveries, loaded]);
  const trends = useMemo(() => loaded ? computeSeasonTrends(matches, deliveries) : [], [matches, deliveries, loaded]);
  const topBat = useMemo(() => loaded ? computeTopBatters(deliveries) : [], [deliveries, loaded]);
  const topBowl = useMemo(() => loaded ? computeTopBowlers(deliveries) : [], [deliveries, loaded]);
  const bdTrends = useMemo(() => loaded ? computeBoundaryDotTrends(deliveries, seasonMap) : [], [deliveries, seasonMap, loaded]);

  // Venue map data
  const venueData = useMemo(() => {
    if (!loaded) return [];
    const counts: Record<string, number> = {};
    matches.forEach(m => { counts[m.Venue] = (counts[m.Venue] || 0) + 1; });
    return venues.map(v => ({ ...v, matches: counts[v.Venue] || 0 })).filter(v => v.matches > 0);
  }, [matches, venues, loaded]);

  // POTM data
  const potmData = useMemo(() => {
    if (!loaded) return [];
    const counts: Record<string, number> = {};
    matches.forEach(m => { if (m.Player_Of_Match && m.Player_Of_Match !== 'No Result') counts[m.Player_Of_Match] = (counts[m.Player_Of_Match] || 0) + 1; });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([name, awards]) => ({ name, awards }));
  }, [matches, loaded]);

  if (loading || !loaded) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-72 skeleton" />
        <div className="flex gap-3 flex-wrap">{Array.from({length: 8}).map((_, i) => <div key={i} className="h-20 flex-1 min-w-[150px] skeleton" />)}</div>
        <div className="h-[350px] skeleton" />
        <div className="grid grid-cols-2 gap-4"><div className="h-[350px] skeleton" /><div className="h-[350px] skeleton" /></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400 bg-clip-text text-transparent">
          🏟️ IPL — Overall Overview (2008–2024)
        </h1>
        <p className="text-sm text-white/40 mt-1">17 Seasons • {kpis?.totalMatches} Matches • {kpis?.totalRuns?.toLocaleString()} Runs</p>
      </motion.div>

      {/* KPI Row */}
      <div className="flex gap-3 flex-wrap justify-center">
        <KPICard label="Total Matches" value={kpis!.totalMatches} color={THEME.accent} icon="🏏" delay={0} />
        <KPICard label="Total Runs" value={kpis!.totalRuns} color={THEME.neonGreen} icon="🏃" delay={1} />
        <KPICard label="Total Wickets" value={kpis!.totalWickets} color={THEME.neonRed} icon="🎯" delay={2} />
        <KPICard label="Avg Runs/Match" value={kpis!.avgRuns} color={THEME.neonBlue} delay={3} />
        <KPICard label="Venues" value={kpis!.uniqueVenues} color={THEME.neonPurple} icon="📍" delay={4} />
        <KPICard label="Most Trophies" value={kpis!.mostTrophies} color={THEME.accent} icon="🏆" delay={5} />
        <KPICard label="Most POTM" value={kpis!.mostPotm} color={THEME.neonYellow} icon="⭐" delay={6} />
        <KPICard label="Best Win %" value={`${kpis!.bestPct}%`} color={getTeamColor(kpis!.bestTeam)} delay={7} />
      </div>

      {/* Season Trends */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[
            { x: trends.map(t => t.season), y: trends.map(t => t.avgRuns), name: 'Avg Runs/Match', mode: 'lines+markers' as const, line: { color: '#00b4d8', width: 3 }, marker: { size: 7 } },
            { x: trends.map(t => t.season), y: trends.map(t => t.avgWickets), name: 'Avg Wickets/Match', mode: 'lines+markers' as const, line: { color: '#f94144', width: 3 }, yaxis: 'y2', marker: { size: 7 } },
          ]}
          layout={{
            title: { text: 'Avg Runs vs Avg Wickets per Match (Season)', font: { size: 16 } },
            height: 350,
            yaxis: { title: { text: 'Avg Runs' }, showgrid: true, gridcolor: 'rgba(255,255,255,0.04)' },
            yaxis2: { title: { text: 'Avg Wickets' }, overlaying: 'y', side: 'right', showgrid: false },
            xaxis: { showgrid: false, tickmode: 'linear' as const, dtick: 1 },
            legend: { x: 0.5, y: 1.15, xanchor: 'center', orientation: 'h' as const },
          }}
        />
      </div>

      {/* Top Batters + Bowlers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <PlotlyChart
            data={[{
              type: 'bar' as const, orientation: 'h' as const,
              x: topBat.map(b => b.runs).reverse(),
              y: topBat.map(b => `${b.name} — ${b.abbr}`).reverse(),
              marker: { color: topBat.map(b => b.color).reverse() },
              text: topBat.map(b => b.runs.toLocaleString()).reverse(),
              textposition: 'outside' as const,
            }]}
            layout={{ title: { text: 'Top 10 Run Scorers' }, height: 400, xaxis: { showgrid: false } }}
          />
        </div>
        <div className="glass-card p-4">
          <PlotlyChart
            data={[{
              type: 'bar' as const, orientation: 'h' as const,
              x: topBowl.map(b => b.wickets).reverse(),
              y: topBowl.map(b => `${b.name} — ${b.abbr}`).reverse(),
              marker: { color: topBowl.map(b => b.color).reverse() },
              text: topBowl.map(b => String(b.wickets)).reverse(),
              textposition: 'outside' as const,
            }]}
            layout={{ title: { text: 'Top 10 Wicket Takers' }, height: 400, xaxis: { showgrid: false } }}
          />
        </div>
      </div>

      {/* POTM */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[{
            type: 'bar' as const, orientation: 'h' as const,
            x: potmData.map(p => p.awards).reverse(),
            y: potmData.map(p => p.name).reverse(),
            marker: { color: '#ffd166' },
            text: potmData.map(p => String(p.awards)).reverse(),
            textposition: 'outside' as const,
          }]}
          layout={{ title: { text: 'Most Player of the Match Awards' }, height: 400, xaxis: { showgrid: false } }}
        />
      </div>

      {/* Venue Map */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[{
            type: 'scattergeo' as const,
            lon: venueData.map(v => v.lon),
            lat: venueData.map(v => v.lat),
            text: venueData.map(v => `${v.Venue}<br>${v.matches} matches<br>Home: ${v.Home}`),
            marker: {
              size: venueData.map(v => Math.max(6, Math.sqrt(v.matches) * 2.5)),
              color: venueData.map(v => getTeamColor(v.Home) || '#9e9e9e'),
              line: { width: 0.6, color: 'white' },
              opacity: 0.9,
            },
            hoverinfo: 'text' as const,
          }]}
          layout={{
            title: { text: 'IPL Venues' },
            height: 500, showlegend: false,
            geo: {
              scope: 'asia' as const, projection: { type: 'mercator' as const },
              center: { lat: 22, lon: 78 },
              lataxis: { range: [5, 35] }, lonaxis: { range: [65, 90] },
              showland: true, landcolor: 'rgb(15,25,40)',
              showocean: true, oceancolor: 'rgb(10,15,25)',
              showcountries: true, countrycolor: 'rgba(255,255,255,0.3)',
              showframe: false,
            },
          }}
        />
      </div>

      {/* Boundary + Dot Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <PlotlyChart
            data={[{
              x: bdTrends.map(d => d.season), y: bdTrends.map(d => d.boundaryPct),
              mode: 'lines+markers' as const, name: 'Boundary %',
              line: { color: '#ffd166', width: 3, shape: 'spline' as const },
              marker: { size: 9, color: '#ffd166', line: { width: 1.5, color: 'white' } },
              fill: 'tozeroy' as const, fillcolor: 'rgba(255,209,102,0.15)',
            }]}
            layout={{
              title: { text: 'Season-wise Boundary %' }, height: 350,
              yaxis: { title: { text: 'Boundary %' }, gridcolor: 'rgba(255,255,255,0.08)' },
              xaxis: { title: { text: 'Season' }, tickmode: 'linear' as const, dtick: 1, showgrid: false },
              showlegend: false, hovermode: 'x unified' as const,
            }}
          />
        </div>
        <div className="glass-card p-4">
          <PlotlyChart
            data={[{
              x: bdTrends.map(d => d.season), y: bdTrends.map(d => d.dotPct),
              mode: 'lines+markers' as const, name: 'Dot Ball %',
              line: { color: '#00b4d8', width: 3, shape: 'spline' as const },
              marker: { size: 9, color: '#00b4d8', line: { width: 1.5, color: 'white' } },
              fill: 'tozeroy' as const, fillcolor: 'rgba(0,180,216,0.15)',
            }]}
            layout={{
              title: { text: 'Season-wise Dot Ball %' }, height: 350,
              yaxis: { title: { text: 'Dot Ball %' }, gridcolor: 'rgba(255,255,255,0.08)' },
              xaxis: { title: { text: 'Season' }, tickmode: 'linear' as const, dtick: 1, showgrid: false },
              showlegend: false, hovermode: 'x unified' as const,
            }}
          />
        </div>
      </div>
    </div>
  );
}

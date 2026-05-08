'use client';
import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useDataStore } from '@/hooks/useData';
import KPICard from '@/components/charts/KPICard';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { headToHeadStats, getTeamList, getSeasonRange } from '@/lib/analytics';
import { getTeamAbbr, getTeamColor, THEME } from '@/lib/constants';

export default function HeadToHeadPage() {
  const { matches, deliveries, loading, loaded, loadData } = useDataStore();
  useEffect(() => { loadData(); }, [loadData]);

  const teams = useMemo(() => loaded ? getTeamList(matches) : [], [matches, loaded]);
  const [seasonMin, seasonMax] = useMemo(() => loaded ? getSeasonRange(matches) : [2008, 2024], [matches, loaded]);

  const [teamA, setTeamA] = useState('');
  const [teamB, setTeamB] = useState('');
  const [range, setRange] = useState<[number, number]>([2008, 2024]);

  useEffect(() => { if (loaded) setRange([seasonMin, seasonMax]); }, [loaded, seasonMin, seasonMax]);

  const stats = useMemo(() => {
    if (!loaded || !teamA || !teamB) return null;
    return headToHeadStats(teamA, teamB, matches, deliveries, range);
  }, [teamA, teamB, matches, deliveries, range, loaded]);

  if (loading || !loaded) return <div className="h-[400px] skeleton" />;

  return (
    <div className="space-y-6">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-2xl font-bold text-center bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
        ⚔️ Head to Head Analysis
      </motion.h1>

      {/* Team selectors */}
      <div className="flex flex-wrap gap-4 justify-center items-end">
        <div className="flex-1 min-w-[200px] max-w-[300px]">
          <label className="text-xs text-white/50 mb-1 block">Team A</label>
          <select value={teamA} onChange={e => setTeamA(e.target.value)} className="w-full">
            <option value="">Select Team A</option>
            {teams.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="text-2xl text-white/30 font-bold">VS</div>
        <div className="flex-1 min-w-[200px] max-w-[300px]">
          <label className="text-xs text-white/50 mb-1 block">Team B</label>
          <select value={teamB} onChange={e => setTeamB(e.target.value)} className="w-full">
            <option value="">Select Team B</option>
            {teams.filter(t => t !== teamA).map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {/* Season range */}
      <div className="flex justify-center items-center gap-4">
        <label className="text-xs text-white/50">From</label>
        <select value={range[0]} onChange={e => setRange([Number(e.target.value), range[1]])}>
          {Array.from({ length: seasonMax - seasonMin + 1 }, (_, i) => seasonMin + i).map(s => <option key={s}>{s}</option>)}
        </select>
        <label className="text-xs text-white/50">To</label>
        <select value={range[1]} onChange={e => setRange([range[0], Number(e.target.value)])}>
          {Array.from({ length: seasonMax - seasonMin + 1 }, (_, i) => seasonMin + i).map(s => <option key={s}>{s}</option>)}
        </select>
      </div>

      {!stats && <p className="text-center text-white/40 py-12">Select both teams to view head-to-head analytics</p>}

      {stats && (
        <>
          {/* KPIs */}
          <div className="flex gap-3 flex-wrap justify-center">
            <KPICard label="Matches" value={stats.total} color={THEME.text} delay={0} />
            <KPICard label={`${getTeamAbbr(teamA)} Wins`} value={stats.t1Wins} color={getTeamColor(teamA)} delay={1} />
            <KPICard label={`${getTeamAbbr(teamB)} Wins`} value={stats.t2Wins} color={getTeamColor(teamB)} delay={2} />
            <KPICard label="Ties" value={stats.ties} color="#fdd835" delay={3} />
            <KPICard label="No Result" value={stats.noResult} color="#94a3b8" delay={4} />
          </div>

          {/* Win Comparison + Toss Gauge */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const,
                  x: [getTeamAbbr(teamA), getTeamAbbr(teamB)],
                  y: [stats.t1Wins, stats.t2Wins],
                  marker: { color: [getTeamColor(teamA), getTeamColor(teamB)] },
                  text: [String(stats.t1Wins), String(stats.t2Wins)],
                  textposition: 'outside' as const,
                }]}
                layout={{ title: { text: 'Win Comparison' }, height: 300, xaxis: { showgrid: false } }}
              />
            </div>
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'indicator' as const, mode: 'gauge+number' as const,
                  value: stats.tossWinPct,
                  gauge: { axis: { range: [0, 100] }, bar: { color: THEME.accent } },
                  title: { text: 'Toss → Match Win %' },
                }]}
                layout={{ height: 300 }}
              />
            </div>
          </div>

          {/* Season Wins Trend */}
          <div className="glass-card p-4">
            <PlotlyChart
              data={(() => {
                const seasons = Object.keys(stats.seasonWins).map(Number).sort();
                const allTeams = new Set<string>();
                Object.values(stats.seasonWins).forEach(sw => Object.keys(sw).forEach(t => allTeams.add(t)));
                return Array.from(allTeams).map(team => ({
                  x: seasons, y: seasons.map(s => stats.seasonWins[s]?.[team] || 0),
                  mode: 'lines+markers' as const, name: getTeamAbbr(team),
                  line: { color: getTeamColor(team) },
                }));
              })()}
              layout={{
                title: { text: 'Season-wise Wins' }, height: 300,
                xaxis: { dtick: 1, showgrid: false },
                yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
              }}
            />
          </div>

          {/* Margin Distribution */}
          <div className="glass-card p-4">
            <PlotlyChart
              data={[
                { x: stats.runMargins, type: 'histogram' as const, name: 'By Runs', marker: { color: '#ffb703' }, nbinsx: 15, xaxis: 'x', yaxis: 'y' },
                { x: stats.wktMargins, type: 'histogram' as const, name: 'By Wickets', marker: { color: '#00b4d8' }, nbinsx: 10, xaxis: 'x2', yaxis: 'y2' },
              ]}
              layout={{
                title: { text: 'Match Margin Distribution' }, height: 350, showlegend: false,
                grid: { rows: 1, columns: 2, pattern: 'independent' as const },
                xaxis: { title: { text: 'Runs' } }, yaxis: { title: { text: 'Count' } },
                xaxis2: { title: { text: 'Wickets' } }, yaxis2: { title: { text: 'Count' } },
                annotations: [
                  { text: 'Defending Wins (By Runs)', xref: 'x domain' as const, yref: 'y domain' as const, x: 0.5, y: 1.1, showarrow: false, font: { color: 'white', size: 13 } },
                  { text: 'Chasing Wins (By Wickets)', xref: 'x2 domain' as const, yref: 'y2 domain' as const, x: 0.5, y: 1.1, showarrow: false, font: { color: 'white', size: 13 } },
                ],
              }}
            />
          </div>

          {/* Top 3 Batters + Bowlers */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const, orientation: 'h' as const,
                  x: stats.topBat.map(b => b.runs).reverse(),
                  y: stats.topBat.map(b => `${b.name} — ${b.abbr}`).reverse(),
                  marker: { color: stats.topBat.map(b => b.color).reverse() },
                  text: stats.topBat.map(b => String(b.runs)).reverse(),
                  textposition: 'outside' as const,
                }]}
                layout={{ title: { text: 'Top 3 Batters by Runs' }, height: 260, xaxis: { showgrid: false } }}
              />
            </div>
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const, orientation: 'h' as const,
                  x: stats.topBowl.map(b => b.wickets).reverse(),
                  y: stats.topBowl.map(b => `${b.name} — ${b.abbr}`).reverse(),
                  marker: { color: stats.topBowl.map(b => b.color).reverse() },
                  text: stats.topBowl.map(b => String(b.wickets)).reverse(),
                  textposition: 'outside' as const,
                }]}
                layout={{ title: { text: 'Top 3 Bowlers by Wickets' }, height: 260, xaxis: { showgrid: false } }}
              />
            </div>
          </div>

          {/* Top Venues */}
          <div className="glass-card p-4">
            <PlotlyChart
              data={[{
                type: 'bar' as const,
                x: stats.topVenues.map(v => v.venue),
                y: stats.topVenues.map(v => v.matches),
                marker: { color: ['#1e88e5', '#42a5f5', '#90caf9'] },
                text: stats.topVenues.map(v => String(v.matches)),
                textposition: 'outside' as const,
              }]}
              layout={{ title: { text: 'Top 3 Venues' }, height: 260 }}
            />
          </div>
        </>
      )}
    </div>
  );
}

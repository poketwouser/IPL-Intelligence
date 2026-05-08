'use client';
import { useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useDataStore } from '@/hooks/useData';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { getTeamAbbr, getTeamColor, TEAM_MAP } from '@/lib/constants';

export default function TeamsPage() {
  const { matches, deliveries, loading, loaded, loadData } = useDataStore();
  useEffect(() => { loadData(); }, [loadData]);

  // Team win percentages
  const teamStats = useMemo(() => {
    if (!loaded) return [];
    const wins: Record<string, number> = {};
    const played: Record<string, number> = {};
    matches.forEach(m => {
      if (m.Team1) played[m.Team1] = (played[m.Team1] || 0) + 1;
      if (m.Team2) played[m.Team2] = (played[m.Team2] || 0) + 1;
      if (m.Winner && m.Winner !== 'No Result') wins[m.Winner] = (wins[m.Winner] || 0) + 1;
    });
    return Object.keys(played)
      .filter(t => t in TEAM_MAP)
      .map(t => ({ team: t, abbr: getTeamAbbr(t), played: played[t], wins: wins[t] || 0, pct: Math.round((wins[t] || 0) / played[t] * 1000) / 10, color: getTeamColor(t) }))
      .sort((a, b) => b.pct - a.pct);
  }, [matches, loaded]);

  // Toss impact
  const tossImpact = useMemo(() => {
    if (!loaded) return { batFirst: 0, fieldFirst: 0 };
    const batFirst = matches.filter(m => m.Toss_Decision === 'Bat' && m.Toss_Winner === m.Winner).length;
    const batTotal = matches.filter(m => m.Toss_Decision === 'Bat').length;
    const fieldFirst = matches.filter(m => m.Toss_Decision === 'Field' && m.Toss_Winner === m.Winner).length;
    const fieldTotal = matches.filter(m => m.Toss_Decision === 'Field').length;
    return { batFirst: batTotal ? Math.round(batFirst / batTotal * 1000) / 10 : 0, fieldFirst: fieldTotal ? Math.round(fieldFirst / fieldTotal * 1000) / 10 : 0 };
  }, [matches, loaded]);

  // Season titles
  const titles = useMemo(() => {
    if (!loaded) return [];
    const finals = matches.filter(m => m.Match_Type?.toLowerCase().includes('final'));
    return finals.map(m => ({ season: m.Season, winner: m.Winner, abbr: getTeamAbbr(m.Winner), color: getTeamColor(m.Winner) })).sort((a, b) => a.season - b.season);
  }, [matches, loaded]);

  if (loading || !loaded) return <div className="h-[400px] skeleton" />;

  return (
    <div className="space-y-6">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-2xl font-bold text-center bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
        🛡️ Team Analytics
      </motion.h1>

      {/* Win % leaderboard */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[{
            type: 'bar' as const, orientation: 'h' as const,
            x: teamStats.map(t => t.pct).reverse(),
            y: teamStats.map(t => `${t.abbr} (${t.played} matches)`).reverse(),
            marker: { color: teamStats.map(t => t.color).reverse() },
            text: teamStats.map(t => `${t.pct}%`).reverse(),
            textposition: 'outside' as const,
          }]}
          layout={{ title: { text: 'All-Time Win Percentage' }, height: 500, xaxis: { showgrid: false, title: { text: 'Win %' } } }}
        />
      </div>

      {/* Toss Impact */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <PlotlyChart
            data={[{
              type: 'indicator' as const, mode: 'gauge+number' as const,
              value: tossImpact.batFirst,
              gauge: { axis: { range: [0, 100] }, bar: { color: '#ffb703' } },
              title: { text: 'Bat First → Win %' },
            }]}
            layout={{ height: 280 }}
          />
        </div>
        <div className="glass-card p-4">
          <PlotlyChart
            data={[{
              type: 'indicator' as const, mode: 'gauge+number' as const,
              value: tossImpact.fieldFirst,
              gauge: { axis: { range: [0, 100] }, bar: { color: '#00b4d8' } },
              title: { text: 'Field First → Win %' },
            }]}
            layout={{ height: 280 }}
          />
        </div>
      </div>

      {/* Title Timeline */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[{
            type: 'bar' as const,
            x: titles.map(t => t.season),
            y: titles.map(() => 1),
            marker: { color: titles.map(t => t.color) },
            text: titles.map(t => t.abbr),
            textposition: 'inside' as const,
            hovertext: titles.map(t => `${t.season}: ${t.winner}`),
          }]}
          layout={{
            title: { text: 'IPL Champions Timeline' }, height: 250,
            yaxis: { showticklabels: false, showgrid: false },
            xaxis: { tickmode: 'linear' as const, dtick: 1, showgrid: false },
          }}
        />
      </div>
    </div>
  );
}

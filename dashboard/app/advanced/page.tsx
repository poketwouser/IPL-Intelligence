'use client';
import { useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useDataStore } from '@/hooks/useData';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { buildSeasonMap, getTeamColor, getTeamAbbr } from '@/lib/constants';

export default function AdvancedPage() {
  const { matches, deliveries, loading, loaded, loadData } = useDataStore();
  useEffect(() => { loadData(); }, [loadData]);

  // Win probability by over (chasing team)
  const winProbByOver = useMemo(() => {
    if (!loaded) return [];
    const overData: Record<number, { total: number; wins: number }> = {};
    const matchWinners: Record<number, string> = {};
    matches.forEach(m => { matchWinners[m.Id] = m.Winner; });

    // For each match, track runs scored by over for innings 2
    const inn2 = deliveries.filter(d => d.inn === 2);
    const matchOvers: Record<number, Record<number, { chasingTeam: string; runsScored: number }>> = {};
    inn2.forEach(d => {
      if (!matchOvers[d.mid]) matchOvers[d.mid] = {};
      if (!matchOvers[d.mid][d.o]) matchOvers[d.mid][d.o] = { chasingTeam: d.bt, runsScored: 0 };
      matchOvers[d.mid][d.o].runsScored += d.tr;
    });

    // Simplified win probability: track if chasing team eventually won
    for (let over = 1; over <= 20; over++) {
      overData[over] = { total: 0, wins: 0 };
    }
    Object.entries(matchOvers).forEach(([matchId, overs]) => {
      const mId = Number(matchId);
      const winner = matchWinners[mId];
      const firstOverEntry = Object.values(overs)[0];
      if (!firstOverEntry) return;
      const chasingTeam = firstOverEntry.chasingTeam;
      const won = winner === chasingTeam;
      Object.keys(overs).forEach(o => {
        const ov = Number(o);
        if (ov >= 1 && ov <= 20) {
          overData[ov].total += 1;
          if (won) overData[ov].wins += 1;
        }
      });
    });

    return Object.entries(overData).map(([o, { total, wins }]) => ({
      over: Number(o),
      pct: total ? Math.round(wins / total * 1000) / 10 : 50,
    })).sort((a, b) => a.over - b.over);
  }, [matches, deliveries, loaded]);

  // Run distribution histogram
  const runDist = useMemo(() => {
    if (!loaded) return [];
    const matchTotals: Record<number, number> = {};
    deliveries.forEach(d => { matchTotals[d.mid] = (matchTotals[d.mid] || 0) + d.tr; });
    return Object.values(matchTotals);
  }, [deliveries, loaded]);

  // Scoring patterns by over
  const scoringByOver = useMemo(() => {
    if (!loaded) return [];
    const data: Record<number, { boundaries: number; dots: number; total: number }> = {};
    deliveries.forEach(d => {
      if (!data[d.o]) data[d.o] = { boundaries: 0, dots: 0, total: 0 };
      data[d.o].total += 1;
      if (d.r === 4 || d.r === 6) data[d.o].boundaries += 1;
      if (d.r === 0) data[d.o].dots += 1;
    });
    return Object.entries(data).map(([o, v]) => ({
      over: Number(o),
      boundaryPct: Math.round(v.boundaries / v.total * 1000) / 10,
      dotPct: Math.round(v.dots / v.total * 1000) / 10,
    })).filter(d => d.over >= 1 && d.over <= 20).sort((a, b) => a.over - b.over);
  }, [deliveries, loaded]);

  if (loading || !loaded) return <div className="h-[400px] skeleton" />;

  return (
    <div className="space-y-6">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-2xl font-bold text-center bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
        🔬 Advanced Analytics Lab
      </motion.h1>
      <p className="text-center text-white/40 text-sm">Experimental metrics, simulations, and deep-dive analytics</p>

      {/* Win Probability Curve */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[{
            x: winProbByOver.map(d => d.over),
            y: winProbByOver.map(d => d.pct),
            mode: 'lines+markers' as const,
            fill: 'tozeroy' as const,
            fillcolor: 'rgba(0,180,216,0.1)',
            line: { color: '#00b4d8', width: 3, shape: 'spline' as const },
            marker: { size: 8, color: '#00b4d8' },
          }]}
          layout={{
            title: { text: 'Chasing Team Win Probability by Over' }, height: 350,
            yaxis: { title: { text: 'Win %' }, range: [0, 100] },
            xaxis: { title: { text: 'Over' }, tickmode: 'linear' as const, dtick: 1 },
            shapes: [{ type: 'line' as const, x0: 0, x1: 20, y0: 50, y1: 50, line: { color: 'rgba(255,255,255,0.2)', dash: 'dash' as const } }],
          }}
        />
      </div>

      {/* Match Total Distribution */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[{
            x: runDist, type: 'histogram' as const, nbinsx: 30,
            marker: { color: 'rgba(255,183,3,0.6)', line: { color: '#ffb703', width: 1 } },
          }]}
          layout={{
            title: { text: 'Match Total Runs Distribution' }, height: 350,
            xaxis: { title: { text: 'Total Runs in Match' } },
            yaxis: { title: { text: 'Frequency' } },
          }}
        />
      </div>

      {/* Scoring Patterns by Over */}
      <div className="glass-card p-4">
        <PlotlyChart
          data={[
            {
              x: scoringByOver.map(d => d.over), y: scoringByOver.map(d => d.boundaryPct),
              name: 'Boundary %', mode: 'lines+markers' as const,
              line: { color: '#ffd166', width: 2 }, marker: { size: 6 },
            },
            {
              x: scoringByOver.map(d => d.over), y: scoringByOver.map(d => d.dotPct),
              name: 'Dot Ball %', mode: 'lines+markers' as const,
              line: { color: '#00b4d8', width: 2 }, marker: { size: 6 },
            },
          ]}
          layout={{
            title: { text: 'Scoring Patterns by Over' }, height: 350,
            xaxis: { title: { text: 'Over' }, tickmode: 'linear' as const, dtick: 1 },
            yaxis: { title: { text: 'Percentage' } },
            legend: { x: 0.5, y: 1.15, xanchor: 'center', orientation: 'h' as const },
          }}
        />
      </div>

      {/* Pressure Index - Wicket probability by phase */}
      <div className="glass-card p-6 text-center">
        <h3 className="text-lg font-semibold text-white/70 mb-2">🧪 More Coming Soon</h3>
        <p className="text-sm text-white/40">Monte Carlo simulations • Player similarity embeddings • Clustering projections • Network graphs • Chord diagrams • Bayesian performance intervals • Predictive analytics</p>
      </div>
    </div>
  );
}

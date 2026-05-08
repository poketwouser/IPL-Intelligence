'use client';
import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useDataStore } from '@/hooks/useData';
import KPICard from '@/components/charts/KPICard';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { playerVsPlayerStats, getPlayerList, getSeasonRange, buildSeasonMap, getPlayerTeam } from '@/lib/analytics';
import { getTeamAbbr, getTeamColor, PHASE_COLORS, THEME, INVALID_BALL_EXTRAS, NON_BOWLER_DISMISSALS } from '@/lib/constants';

export default function PvPPage() {
  const { matches, deliveries, loading, loaded, loadData } = useDataStore();
  useEffect(() => { loadData(); }, [loadData]);

  const players = useMemo(() => loaded ? getPlayerList(deliveries) : [], [deliveries, loaded]);
  const seasonMap = useMemo(() => loaded ? buildSeasonMap(matches) : {}, [matches, loaded]);
  const [seasonMin, seasonMax] = useMemo(() => loaded ? getSeasonRange(matches) : [2008, 2024], [matches, loaded]);

  const [pA, setPa] = useState('');
  const [pB, setPb] = useState('');
  const [direction, setDirection] = useState('A_bat_B_bowl');
  const [range, setRange] = useState<[number, number]>([2008, 2024]);

  useEffect(() => { if (loaded) setRange([seasonMin, seasonMax]); }, [loaded, seasonMin, seasonMax]);

  const stats = useMemo(() => {
    if (!loaded || !pA || !pB || pA === pB) return null;
    return playerVsPlayerStats(pA, pB, direction, deliveries, range, seasonMap);
  }, [pA, pB, direction, deliveries, range, seasonMap, loaded]);

  // Derived charts data
  const outcomeData = useMemo(() => {
    if (!stats) return [];
    const valid = stats.matchup.filter(d => !d.et || !INVALID_BALL_EXTRAS.has(d.et));
    const counts: Record<string, number> = { '0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '6': 0, 'W': 0 };
    valid.forEach(d => {
      if (d.w === 1 && d.pd && !NON_BOWLER_DISMISSALS.has(d.dk || '')) {
        counts['W']++;
      } else {
        counts[String(d.r)] = (counts[String(d.r)] || 0) + 1;
      }
    });
    return Object.entries(counts).map(([k, v]) => ({ outcome: k, count: v }));
  }, [stats]);

  const phaseData = useMemo(() => {
    if (!stats) return [];
    const valid = stats.matchup.filter(d => !d.et || !INVALID_BALL_EXTRAS.has(d.et));
    const phases: Record<string, { runs: number; balls: number }> = { Powerplay: { runs: 0, balls: 0 }, Middle: { runs: 0, balls: 0 }, Death: { runs: 0, balls: 0 } };
    valid.forEach(d => {
      const p = d.o <= 6 ? 'Powerplay' : d.o <= 15 ? 'Middle' : 'Death';
      phases[p].runs += d.r;
      phases[p].balls += 1;
    });
    return Object.entries(phases).map(([phase, { runs, balls }]) => ({ phase, sr: balls ? Math.round(runs / balls * 1000) / 10 : 0 }));
  }, [stats]);

  const overProfile = useMemo(() => {
    if (!stats) return [];
    const valid = stats.matchup.filter(d => !d.et || !INVALID_BALL_EXTRAS.has(d.et));
    const data: Record<number, { runs: number; balls: number }> = {};
    valid.forEach(d => {
      if (!data[d.o]) data[d.o] = { runs: 0, balls: 0 };
      data[d.o].runs += d.r;
      data[d.o].balls += 1;
    });
    return Object.entries(data).map(([o, { runs, balls }]) => ({ over: Number(o), avgRuns: balls ? Math.round(runs / balls * 100) / 100 : 0 })).sort((a, b) => a.over - b.over);
  }, [stats]);

  const teamA = useMemo(() => pA && loaded ? getPlayerTeam(pA, deliveries) : '', [pA, deliveries, loaded]);
  const teamB = useMemo(() => pB && loaded ? getPlayerTeam(pB, deliveries) : '', [pB, deliveries, loaded]);

  if (loading || !loaded) return <div className="h-[400px] skeleton" />;

  const outcomeColors: Record<string, string> = { '0': '#7f8c8d', '1': '#3498db', '2': '#2980b9', '3': '#2ecc71', '4': '#f39c12', '6': '#e74c3c', 'W': '#c0392b' };

  return (
    <div className="space-y-6">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-2xl font-bold text-center bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
        🎯 Player vs Player Matchup
      </motion.h1>

      <div className="flex flex-wrap gap-4 justify-center items-end">
        <div className="min-w-[200px]">
          <label className="text-xs text-white/50 mb-1 block">Player A</label>
          <select value={pA} onChange={e => setPa(e.target.value)} className="w-full">
            <option value="">Select Player A</option>
            {players.map(p => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div className="min-w-[200px]">
          <label className="text-xs text-white/50 mb-1 block">Player B</label>
          <select value={pB} onChange={e => setPb(e.target.value)} className="w-full">
            <option value="">Select Player B</option>
            {players.filter(p => p !== pA).map(p => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-white/50 mb-1 block">Direction</label>
          <select value={direction} onChange={e => setDirection(e.target.value)}>
            <option value="A_bat_B_bowl">A batting vs B bowling</option>
            <option value="B_bat_A_bowl">B batting vs A bowling</option>
          </select>
        </div>
      </div>

      {(!pA || !pB || pA === pB) && <p className="text-center text-white/40 py-12">Select two different players</p>}

      {stats && (
        <>
          <div className="flex gap-3 flex-wrap justify-center">
            <KPICard label="Player A" value={`${pA.split(' ').pop()} (${getTeamAbbr(teamA)})`} color={getTeamColor(teamA)} delay={0} />
            <KPICard label="Player B" value={`${pB.split(' ').pop()} (${getTeamAbbr(teamB)})`} color={getTeamColor(teamB)} delay={1} />
            <KPICard label="Balls" value={stats.balls} color={THEME.text} delay={2} />
            <KPICard label="Runs" value={stats.runs} color={THEME.neonGreen} delay={3} />
            <KPICard label="SR" value={stats.sr} color={THEME.neonBlue} delay={4} />
            <KPICard label="4s/6s • Dot%" value={`${stats.fours}/${stats.sixes} • ${stats.dotPct}%`} color={THEME.accent} delay={5} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const, x: outcomeData.map(o => o.outcome), y: outcomeData.map(o => o.count),
                  marker: { color: outcomeData.map(o => outcomeColors[o.outcome] || '#888') },
                  text: outcomeData.map(o => String(o.count)), textposition: 'outside' as const,
                }]}
                layout={{ title: { text: 'Ball Outcomes' }, height: 300, showlegend: false }}
              />
            </div>
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const, x: phaseData.map(p => p.phase), y: phaseData.map(p => p.sr),
                  marker: { color: phaseData.map(p => PHASE_COLORS[p.phase] || '#888') },
                }]}
                layout={{ title: { text: 'Phase Strike Rate' }, height: 300, showlegend: false }}
              />
            </div>
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  x: overProfile.map(o => o.over), y: overProfile.map(o => o.avgRuns),
                  mode: 'lines+markers' as const, line: { color: '#00FFFF', shape: 'spline' as const },
                  marker: { size: 8 },
                }]}
                layout={{ title: { text: 'Avg Runs by Over' }, height: 300 }}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

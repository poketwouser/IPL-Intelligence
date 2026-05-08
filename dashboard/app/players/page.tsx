'use client';
import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useDataStore } from '@/hooks/useData';
import KPICard from '@/components/charts/KPICard';
import PlotlyChart from '@/components/charts/PlotlyChart';
import {
  battingSummary, bowlingSummary, playerSeasonRuns, playerSeasonWickets,
  playerFormCurve, playerPhaseBreakdown, dismissalBreakdown,
  getPlayerList, getSeasonRange, buildSeasonMap, getPlayerTeam,
} from '@/lib/analytics';
import { getTeamAbbr, getTeamColor, PHASE_COLORS, THEME } from '@/lib/constants';

export default function PlayersPage() {
  const { matches, deliveries, loading, loaded, loadData } = useDataStore();
  useEffect(() => { loadData(); }, [loadData]);

  const players = useMemo(() => loaded ? getPlayerList(deliveries) : [], [deliveries, loaded]);
  const seasonMap = useMemo(() => loaded ? buildSeasonMap(matches) : {}, [matches, loaded]);
  const [seasonMin, seasonMax] = useMemo(() => loaded ? getSeasonRange(matches) : [2008, 2024], [matches, loaded]);

  const [player, setPlayer] = useState('');
  const [range, setRange] = useState<[number, number]>([2008, 2024]);

  useEffect(() => { if (loaded) { setRange([seasonMin, seasonMax]); if (players.length) setPlayer(players[0]); } }, [loaded, seasonMin, seasonMax, players]);

  const bat = useMemo(() => player && loaded ? battingSummary(player, deliveries) : null, [player, deliveries, loaded]);
  const bowl = useMemo(() => player && loaded ? bowlingSummary(player, deliveries) : null, [player, deliveries, loaded]);
  const sRuns = useMemo(() => player && loaded ? playerSeasonRuns(player, deliveries, seasonMap).filter(d => d.season >= range[0] && d.season <= range[1]) : [], [player, deliveries, seasonMap, range, loaded]);
  const sWkts = useMemo(() => player && loaded ? playerSeasonWickets(player, deliveries, seasonMap).filter(d => d.season >= range[0] && d.season <= range[1]) : [], [player, deliveries, seasonMap, range, loaded]);
  const form = useMemo(() => player && loaded ? playerFormCurve(player, deliveries, matches) : [], [player, deliveries, matches, loaded]);
  const dismiss = useMemo(() => player && loaded ? dismissalBreakdown(player, deliveries) : [], [player, deliveries, loaded]);
  const batPhase = useMemo(() => player && loaded ? playerPhaseBreakdown(player, deliveries, 'bat') : [], [player, deliveries, loaded]);
  const bowlPhase = useMemo(() => player && loaded ? playerPhaseBreakdown(player, deliveries, 'bowl') : [], [player, deliveries, loaded]);
  const team = useMemo(() => player && loaded ? getPlayerTeam(player, deliveries) : '', [player, deliveries, loaded]);
  const teamColor = getTeamColor(team);

  if (loading || !loaded) return <div className="h-[400px] skeleton" />;

  return (
    <div className="space-y-6">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-2xl font-bold text-center bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
        🏏 Player Analysis
      </motion.h1>

      {/* Player selector + season range */}
      <div className="flex flex-wrap gap-4 justify-center items-end">
        <div className="min-w-[250px]">
          <label className="text-xs text-white/50 mb-1 block">Player</label>
          <select value={player} onChange={e => setPlayer(e.target.value)} className="w-full">
            {players.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-white/50 mb-1 block">From</label>
          <select value={range[0]} onChange={e => setRange([Number(e.target.value), range[1]])}>
            {Array.from({ length: seasonMax - seasonMin + 1 }, (_, i) => seasonMin + i).map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-white/50 mb-1 block">To</label>
          <select value={range[1]} onChange={e => setRange([range[0], Number(e.target.value)])}>
            {Array.from({ length: seasonMax - seasonMin + 1 }, (_, i) => seasonMin + i).map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {player && bat && bowl && (
        <>
          {/* Player card */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6 border-l-4" style={{ borderLeftColor: teamColor }}>
            <h2 className="text-xl font-bold mb-1" style={{ color: teamColor }}>{player} • {getTeamAbbr(team)}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
              <div>
                <h3 className="text-sm font-semibold text-cyan-400 mb-2">Batting Performance</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-white/50">Runs:</span> <span className="font-bold">{bat.runs.toLocaleString()}</span></div>
                  <div><span className="text-white/50">SR:</span> <span className="font-bold">{bat.strikeRate}</span></div>
                  <div><span className="text-white/50">4s / 6s:</span> <span className="font-bold">{bat.fours} / {bat.sixes}</span></div>
                  <div><span className="text-white/50">Boundary %:</span> <span className="font-bold">{bat.boundaryPct}%</span></div>
                  <div><span className="text-white/50">Average:</span> <span className="font-bold">{bat.average}</span></div>
                  <div><span className="text-white/50">High Score:</span> <span className="font-bold">{bat.highScore}</span></div>
                  <div><span className="text-white/50">50s / 100s:</span> <span className="font-bold">{bat.fifties} / {bat.hundreds}</span></div>
                  <div><span className="text-white/50">Innings:</span> <span className="font-bold">{bat.innings}</span></div>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-rose-400 mb-2">Bowling Performance</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-white/50">Wickets:</span> <span className="font-bold">{bowl.wickets}</span></div>
                  <div><span className="text-white/50">Economy:</span> <span className="font-bold">{bowl.economy}</span></div>
                  <div><span className="text-white/50">Bowl SR:</span> <span className="font-bold">{bowl.strikeRate}</span></div>
                  <div><span className="text-white/50">Dot %:</span> <span className="font-bold">{bowl.dotPct}%</span></div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Season Runs + Wickets */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const, x: sRuns.map(d => d.season), y: sRuns.map(d => d.runs),
                  marker: { color: sRuns.map((_, i) => `hsl(${200 + i * 10}, 70%, 55%)`) },
                }]}
                layout={{ title: { text: 'Season Runs' }, height: 300 }}
              />
            </div>
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  x: sWkts.map(d => d.season), y: sWkts.map(d => d.wickets),
                  mode: 'lines+markers' as const, marker: { size: 8, color: '#e74c3c' },
                  line: { color: '#e74c3c', width: 2 },
                }]}
                layout={{ title: { text: 'Season Wickets' }, height: 300 }}
              />
            </div>
          </div>

          {/* Form Curve */}
          <div className="glass-card p-4">
            <PlotlyChart
              data={[
                { x: form.map(f => f.date), y: form.map(f => f.runs), mode: 'lines' as const, name: 'Runs', line: { color: 'rgba(0,180,216,0.3)', width: 1 } },
                { x: form.map(f => f.date), y: form.map(f => f.rolling), mode: 'lines' as const, name: 'Rolling Avg (5)', line: { color: '#00b4d8', width: 3 } },
              ]}
              layout={{ title: { text: 'Form Curve' }, height: 300, xaxis: { showgrid: false }, legend: { x: 0, y: 1 } }}
            />
          </div>

          {/* Dismissals + Phase */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'pie' as const, labels: dismiss.map(d => d.kind), values: dismiss.map(d => d.count),
                  hole: 0.4, textinfo: 'label+percent' as const,
                  marker: { colors: ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#9b59b6', '#1abc9c', '#e91e63'] },
                }]}
                layout={{ title: { text: 'Dismissal Breakdown' }, height: 350, showlegend: false }}
              />
            </div>
            <div className="glass-card p-4">
              <PlotlyChart
                data={[{
                  type: 'bar' as const, x: batPhase.map(p => p.phase), y: batPhase.map(p => p.runs),
                  marker: { color: batPhase.map(p => PHASE_COLORS[p.phase] || '#888') },
                  text: batPhase.map(p => `${p.runs} (SR: ${p.sr})`), textposition: 'outside' as const,
                }]}
                layout={{ title: { text: 'Batting by Phase' }, height: 350 }}
              />
            </div>
          </div>

          {/* Bowling Phase */}
          <div className="glass-card p-4">
            <PlotlyChart
              data={[{
                type: 'bar' as const, x: bowlPhase.map(p => p.phase),
                y: bowlPhase.map(p => p.balls ? Math.round(p.runs / p.balls * 60) / 10 : 0),
                marker: { color: bowlPhase.map(p => PHASE_COLORS[p.phase] || '#888') },
              }]}
              layout={{ title: { text: 'Avg Runs Conceded per Phase' }, height: 300 }}
            />
          </div>
        </>
      )}
    </div>
  );
}

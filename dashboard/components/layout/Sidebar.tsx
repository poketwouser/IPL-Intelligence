'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

const NAV_ITEMS = [
  { href: '/', label: 'Overview', icon: '🏟️', desc: 'IPL at a glance' },
  { href: '/head-to-head', label: 'Head to Head', icon: '⚔️', desc: 'Team matchups' },
  { href: '/players', label: 'Players', icon: '🏏', desc: 'Player analysis' },
  { href: '/player-vs-player', label: 'Player v Player', icon: '🎯', desc: 'Batting vs bowling' },
  { href: '/teams', label: 'Teams', icon: '🛡️', desc: 'Team analytics' },
  { href: '/advanced', label: 'Analytics Lab', icon: '🔬', desc: 'Advanced stats' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="fixed top-4 left-4 z-50 lg:hidden w-10 h-10 rounded-lg bg-white/10 backdrop-blur-xl flex items-center justify-center text-white border border-white/10"
      >
        {collapsed ? '✕' : '☰'}
      </button>

      {/* Sidebar */}
      <AnimatePresence>
        <motion.aside
          initial={{ x: -280 }}
          animate={{ x: 0 }}
          className={`fixed top-0 left-0 h-full z-40 w-[240px] bg-[#080c18]/95 backdrop-blur-2xl border-r border-white/[0.06] flex flex-col transition-transform duration-300 ${
            collapsed ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          {/* Logo */}
          <div className="px-5 py-6 border-b border-white/[0.06]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-lg font-bold text-black">
                ⚡
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-tight">IPL Analytics</h1>
                <p className="text-[10px] text-white/40 uppercase tracking-widest">2008 — 2024</p>
              </div>
            </div>
          </div>

          {/* Nav items */}
          <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href} onClick={() => setCollapsed(false)}>
                  <motion.div
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                      isActive
                        ? 'bg-amber-400/10 text-amber-400'
                        : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'
                    }`}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full bg-amber-400"
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                      />
                    )}
                    <span className="text-lg">{item.icon}</span>
                    <div>
                      <div className="text-sm font-medium">{item.label}</div>
                      <div className="text-[10px] opacity-50">{item.desc}</div>
                    </div>
                  </motion.div>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-5 py-4 border-t border-white/[0.06]">
            <div className="text-[10px] text-white/30 text-center">
              Built with Next.js • Plotly
            </div>
          </div>
        </motion.aside>
      </AnimatePresence>
    </>
  );
}

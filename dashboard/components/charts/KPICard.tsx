'use client';
import { motion } from 'framer-motion';
import { useEffect, useState, useRef } from 'react';

interface KPICardProps {
  label: string;
  value: string | number;
  color: string;
  icon?: string;
  delay?: number;
}

function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<number>(0);
  useEffect(() => {
    const duration = 1200;
    const start = ref.current;
    const diff = value - start;
    const startTime = Date.now();
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) requestAnimationFrame(animate);
      else ref.current = value;
    };
    animate();
  }, [value]);
  return <>{display.toLocaleString()}</>;
}

export default function KPICard({ label, value, color, icon, delay = 0 }: KPICardProps) {
  const isNumeric = typeof value === 'number';
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, delay: delay * 0.08, ease: [0.25, 0.46, 0.45, 0.94] }}
      whileHover={{ scale: 1.04, y: -2 }}
      className="relative group min-w-[150px] flex-1"
    >
      <div className="relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.04] backdrop-blur-xl p-4 text-center transition-all duration-300 group-hover:border-white/[0.12] group-hover:bg-white/[0.06]">
        {/* Glow effect */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" style={{
          background: `radial-gradient(circle at 50% 0%, ${color}15 0%, transparent 70%)`
        }} />
        {icon && <div className="text-xl mb-1">{icon}</div>}
        <div className="text-xs font-medium uppercase tracking-wider mb-1" style={{ color }}>{label}</div>
        <div className="text-xl font-bold text-white/90 tracking-tight">
          {isNumeric ? <AnimatedNumber value={value as number} /> : String(value)}
        </div>
      </div>
    </motion.div>
  );
}

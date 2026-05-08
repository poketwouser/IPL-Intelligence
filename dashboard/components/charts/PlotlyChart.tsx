'use client';
import dynamic from 'next/dynamic';
import { PLOTLY_DARK_LAYOUT } from '@/lib/constants';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false, loading: () => (
  <div className="w-full h-[350px] rounded-xl bg-white/[0.03] animate-pulse flex items-center justify-center">
    <div className="w-8 h-8 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
  </div>
)});

interface PlotlyChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  className?: string;
  style?: React.CSSProperties;
}

export default function PlotlyChart({ data, layout = {}, config, className = '', style }: PlotlyChartProps) {
  const mergedLayout: Partial<Plotly.Layout> = {
    ...PLOTLY_DARK_LAYOUT,
    autosize: true,
    ...layout,
    font: { ...PLOTLY_DARK_LAYOUT.font, ...(layout.font || {}) },
    margin: { ...PLOTLY_DARK_LAYOUT.margin, ...(layout.margin || {}) },
  };

  const mergedConfig: Partial<Plotly.Config> = {
    displayModeBar: false,
    responsive: true,
    ...config,
  };

  return (
    <div className={`w-full rounded-xl overflow-hidden ${className}`} style={style}>
      <Plot
        data={data}
        layout={mergedLayout}
        config={mergedConfig}
        useResizeHandler
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

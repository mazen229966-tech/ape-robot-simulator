import { useEffect, useMemo, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

export interface ChartSeries {
  x: number[];
  y: number[];
  name: string;
  color?: string;
}

interface Props {
  series: ChartSeries[];
  xTitle: string;
  yTitle: string;
  height?: number;
}

const PALETTE = ['#38bdf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#f472b6'];

const BASE_LAYOUT = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(16,22,30,0.6)',
  font: { color: '#9fb0c3', family: 'Inter, sans-serif', size: 11 },
  margin: { l: 56, r: 16, t: 10, b: 44 },
  xaxis: { gridcolor: '#1d2936', zerolinecolor: '#33455c' },
  yaxis: { gridcolor: '#1d2936', zerolinecolor: '#33455c' },
  legend: { orientation: 'h' as const, bgcolor: 'rgba(0,0,0,0)', font: { size: 11 } },
  showlegend: true,
};

/** Plotly line chart styled for the dark engineering theme. */
export default function LineChart({ series, xTitle, yTitle, height = 300 }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  const layout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      height,
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: xTitle } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: yTitle } },
    }),
    [xTitle, yTitle, height],
  );

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const traces = series.map((s, i) => ({
      x: s.x,
      y: s.y,
      name: s.name,
      mode: 'lines',
      line: { color: s.color ?? PALETTE[i % PALETTE.length], width: 1.8 },
    }));
    void Plotly.react(el, traces, layout, {
      responsive: true,
      displaylogo: false,
      displayModeBar: false,
    });
    return () => {
      Plotly.purge(el);
    };
  }, [series, layout]);

  return <div ref={ref} style={{ width: '100%', height }} />;
}

import type { ReactNode } from 'react';

interface Props {
  value: ReactNode;
  label: string;
  unit?: string;
  accent?: boolean;
}

/** Compact value/label card used for KPI style displays. */
export default function ParameterCard({ value, label, unit, accent = true }: Props) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={accent ? undefined : { color: 'var(--text-0)' }}>
        {value}
        {unit && <span style={{ fontSize: 13, color: 'var(--text-1)', marginLeft: 6 }}>{unit}</span>}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

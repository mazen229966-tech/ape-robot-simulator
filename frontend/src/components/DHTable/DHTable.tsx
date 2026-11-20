import type { DHTable as DHTableType } from '../../types/robot';

interface Props {
  table: DHTableType;
}

/** Read-only DH parameter display (UI units: mm / deg). */
export default function DHTableView({ table }: Props) {
  return (
    <div>
      <table className="table">
        <thead>
          <tr>
            <th>i</th>
            <th>θᵢ (deg)</th>
            <th>dᵢ (mm)</th>
            <th>aᵢ (mm)</th>
            <th>αᵢ (deg)</th>
          </tr>
        </thead>
        <tbody>
          {table.links.map((l) => (
            <tr key={l.i}>
              <td>{l.i}</td>
              <td className="accent">{l.theta}</td>
              <td>{l.d_mm.toFixed(2)}</td>
              <td>{l.a_mm.toFixed(2)}</td>
              <td>{l.alpha_deg.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="muted mt" style={{ fontSize: 12 }}>
        {table.convention} · {table.transform_formula}
      </div>
    </div>
  );
}

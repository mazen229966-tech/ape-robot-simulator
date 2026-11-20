import { useEffect, useState } from 'react';

import DHTableView from '../../components/DHTable/DHTable';
import RobotViewer from '../../components/RobotViewer/RobotViewer';
import * as api from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { exportDHUrl } from '../../services/api';

interface EditRow {
  d: number; // mm
  a: number; // mm
  alpha: number; // deg
}

export default function DHModel() {
  const dhTable = useRobotStore((s) => s.dhTable);
  const fetchDH = useRobotStore((s) => s.fetchDH);
  const fetchRobot = useRobotStore((s) => s.fetchRobot);
  const info = useRobotStore((s) => s.info);

  const [rows, setRows] = useState<EditRow[]>([]);
  const [msg, setMsg] = useState<{ kind: 'ok' | 'error' | 'working'; text: string } | null>(null);

  useEffect(() => {
    if (!dhTable) void fetchDH();
  }, [dhTable, fetchDH]);

  useEffect(() => {
    if (dhTable) {
      setRows(dhTable.links.map((l) => ({ d: l.d_mm, a: l.a_mm, alpha: l.alpha_deg })));
    }
  }, [dhTable]);

  const apply = async () => {
    setMsg({ kind: 'working', text: 'Applying parameters…' });
    try {
      const res = await api.applyDH(
        rows.map((r) => ({ d: r.d / 1000, a: r.a / 1000, alpha: r.alpha })),
      );
      useRobotStore.setState({ dhTable: res });
      await fetchRobot();
      setMsg({ kind: 'ok', text: '✓ Parameters applied — model rebuilt.' });
    } catch (err) {
      setMsg({ kind: 'error', text: err instanceof Error ? err.message : 'Apply failed' });
    }
  };

  const reset = async () => {
    setMsg({ kind: 'working', text: 'Resetting…' });
    try {
      const res = await api.resetDH();
      useRobotStore.setState({ dhTable: res });
      await fetchRobot();
      setMsg({ kind: 'ok', text: '✓ Default educational parameters restored.' });
    } catch (err) {
      setMsg({ kind: 'error', text: err instanceof Error ? err.message : 'Reset failed' });
    }
  };

  const edit = (i: number, key: keyof EditRow, value: number) => {
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [key]: value } : r)));
  };

  return (
    <div className="page">
      <div className="page-title">DH Model</div>
      <div className="page-subtitle">
        Denavit–Hartenberg definition of the kinematic chain (standard convention:
        A_i = Rz(θᵢ)·Tz(dᵢ)·Tx(aᵢ)·Rx(αᵢ)). Joint type: Revolute · θ in degrees ·
        d, a in mm · α in degrees.
      </div>

      <div className="note mb">
        Parameter Source: <strong>{dhTable?.parameter_source ?? '…'}</strong>
        {info && info.kinematic_parameter_source.includes('Educational') && (
          <span> — APE does not publish a DH table for the SV2-6045; these values are
          dimensioned to match the official 454&nbsp;mm reach and official joint limits.
          They can be replaced with official CAD/URDF data without touching the rest
          of the system.</span>
        )}
      </div>

      <div className="grid cols-2" style={{ gridTemplateColumns: 'minmax(0,3fr) minmax(0,2fr)' }}>
        <div className="card">
          <div className="card-title">DH Parameters (editable)</div>
          <table className="table">
            <thead>
              <tr>
                <th>i</th>
                <th>θ</th>
                <th>d (mm)</th>
                <th>a (mm)</th>
                <th>α (deg)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td className="accent">q{i + 1}</td>
                  {(['d', 'a', 'alpha'] as const).map((k) => (
                    <td key={k}>
                      <input
                        className="input"
                        type="number"
                        step={0.5}
                        value={r[k]}
                        onChange={(e) => edit(i, k, Number(e.target.value))}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          <div className="btn-row mt">
            <button className="btn primary" onClick={apply}>Apply Parameters</button>
            <button className="btn" onClick={reset}>Reset Parameters</button>
            <a className="btn ghost" href={exportDHUrl('csv')} download>Export CSV</a>
            <a className="btn ghost" href={exportDHUrl('json')} download>Export JSON</a>
          </div>

          {msg && <div className={`msg ${msg.kind} mt`}>{msg.text}</div>}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">Active Table</div>
            {dhTable ? <DHTableView table={dhTable} /> : <div className="muted">Loading…</div>}
          </div>
          <div className="card">
            <div className="card-title">Model Preview</div>
            <RobotViewer height={280} />
          </div>
        </div>
      </div>
    </div>
  );
}

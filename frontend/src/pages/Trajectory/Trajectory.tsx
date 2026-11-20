import { useMemo, useState } from 'react';

import LineChart from '../../components/Charts/LineChart';
import { JOINT_COLORS } from '../../components/Charts/JointSeriesSelector';
import SimulationControls from '../../components/SimulationControls/SimulationControls';
import * as api from '../../services/api';
import { exportTrajectoryUrl } from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

const RAD2DEG = 180 / Math.PI;

interface CartPoint { x: number; y: number; z: number; t: number }

export default function Trajectory() {
  const qDeg = useRobotStore((s) => s.qDeg);
  const trajectory = useSimulationStore((s) => s.trajectory);
  const trajectoryLabel = useSimulationStore((s) => s.trajectoryLabel);
  const setTrajectory = useSimulationStore((s) => s.setTrajectory);

  const [tab, setTab] = useState<'joint' | 'cartesian'>('joint');

  // joint-space inputs
  const [q0, setQ0] = useState<number[]>([0, -35, 55, 0, -20, 0]);
  const [qf, setQf] = useState<number[]>([40, 15, 85, -30, 45, 60]);
  const [duration, setDuration] = useState(4);
  const [samples, setSamples] = useState(200);
  const [method, setMethod] = useState<'cubic' | 'quintic'>('quintic');

  // cartesian inputs
  const [points, setPoints] = useState<CartPoint[]>([
    { x: 260, y: 0, z: 280, t: 0 },
    { x: 300, y: 60, z: 280, t: 2 },
    { x: 340, y: 0, z: 280, t: 4 },
  ]);
  const [rpy, setRpy] = useState({ roll: 180, pitch: 0, yaw: 0 });
  const [useDefaultOri, setUseDefaultOri] = useState(true);

  const [state, setState] = useState<'idle' | 'working' | 'ok' | 'error'>('idle');
  const [error, setError] = useState('');

  const generateJoint = async () => {
    setState('working');
    setError('');
    try {
      const res = await api.planJointTrajectory({ q0, qf, duration, samples, method });
      setTrajectory(res, `Joint-space ${method}`);
      setState('ok');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Trajectory generation failed');
    }
  };

  const generateCartesian = async () => {
    setState('working');
    setError('');
    try {
      const res = await api.planCartesianTrajectory({
        points: points.map((p) => ({ x: p.x / 1000, y: p.y / 1000, z: p.z / 1000, t: p.t })),
        orientation: useDefaultOri ? null : rpy,
      });
      setTrajectory(res, 'Cartesian (via IK)');
      setState('ok');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Trajectory generation failed');
    }
  };

  const previewSeries = useMemo(() => {
    if (!trajectory) return [];
    return trajectory.q[0].map((_, j) => ({
      x: trajectory.t,
      y: trajectory.q.map((row) => row[j] * RAD2DEG),
      name: `J${j + 1}`,
      color: JOINT_COLORS[j],
    }));
  }, [trajectory]);

  const editJoint = (setter: React.Dispatch<React.SetStateAction<number[]>>, i: number, v: number) =>
    setter((prev) => prev.map((x, j) => (j === i ? v : x)));

  return (
    <div className="page">
      <div className="page-title">Trajectory Planning</div>
      <div className="page-subtitle">
        Joint-space polynomials (cubic / quintic) or Cartesian waypoints converted
        to joint motion through the real IK solver.
      </div>

      <div className="btn-row mb">
        <button className={`btn${tab === 'joint' ? ' primary' : ''}`} onClick={() => setTab('joint')}>
          Joint Space
        </button>
        <button className={`btn${tab === 'cartesian' ? ' primary' : ''}`} onClick={() => setTab('cartesian')}>
          Cartesian Space
        </button>
      </div>

      {tab === 'joint' && (
        <div className="card">
          <div className="grid cols-2">
            <div>
              <div className="spread">
                <div className="card-title" style={{ marginBottom: 0 }}>Start Configuration q₀ (deg)</div>
                <button className="btn sm ghost" onClick={() => setQ0(qDeg.map((v) => Number(v.toFixed(2))))}>
                  Current
                </button>
              </div>
              <div className="grid cols-3 mt">
                {q0.map((v, i) => (
                  <div key={i}>
                    <label className="field-label">J{i + 1}</label>
                    <input className="input" type="number" step={1} value={v}
                      onChange={(e) => editJoint(setQ0, i, Number(e.target.value))} />
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="spread">
                <div className="card-title" style={{ marginBottom: 0 }}>Final Configuration q<sub>f</sub> (deg)</div>
                <button className="btn sm ghost" onClick={() => setQf(qDeg.map((v) => Number(v.toFixed(2))))}>
                  Current
                </button>
              </div>
              <div className="grid cols-3 mt">
                {qf.map((v, i) => (
                  <div key={i}>
                    <label className="field-label">J{i + 1}</label>
                    <input className="input" type="number" step={1} value={v}
                      onChange={(e) => editJoint(setQf, i, Number(e.target.value))} />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid cols-3 mt">
            <div>
              <label className="field-label">Duration (s)</label>
              <input className="input" type="number" min={0.1} step={0.5} value={duration}
                onChange={(e) => setDuration(Number(e.target.value))} />
            </div>
            <div>
              <label className="field-label">Samples</label>
              <input className="input" type="number" min={2} max={5000} step={10} value={samples}
                onChange={(e) => setSamples(Number(e.target.value))} />
            </div>
            <div>
              <label className="field-label">Interpolation</label>
              <select className="input" value={method} onChange={(e) => setMethod(e.target.value as 'cubic' | 'quintic')}>
                <option value="quintic">Quintic Polynomial</option>
                <option value="cubic">Cubic Polynomial</option>
              </select>
            </div>
          </div>

          <div className="btn-row mt">
            <button className="btn primary" onClick={generateJoint} disabled={state === 'working'}>
              {state === 'working' ? 'Generating…' : 'Generate Trajectory'}
            </button>
          </div>
        </div>
      )}

      {tab === 'cartesian' && (
        <div className="card">
          <div className="card-title">Cartesian Waypoints (mm, seconds)</div>
          <table className="table">
            <thead>
              <tr><th>Point</th><th>X (mm)</th><th>Y (mm)</th><th>Z (mm)</th><th>Time (s)</th><th /></tr>
            </thead>
            <tbody>
              {points.map((p, i) => (
                <tr key={i}>
                  <td>P{i + 1}</td>
                  {(['x', 'y', 'z', 't'] as const).map((k) => (
                    <td key={k}>
                      <input className="input" type="number" step={k === 't' ? 0.5 : 5} value={p[k]}
                        onChange={(e) =>
                          setPoints((prev) => prev.map((q, j) => (j === i ? { ...q, [k]: Number(e.target.value) } : q)))
                        } />
                    </td>
                  ))}
                  <td>
                    <button
                      className="btn sm danger"
                      onClick={() => setPoints((prev) => prev.filter((_, j) => j !== i))}
                      disabled={points.length <= 2}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="btn-row mt">
            <button
              className="btn sm"
              onClick={() => {
                const last = points[points.length - 1];
                setPoints([...points, { x: last.x, y: last.y, z: last.z, t: last.t + 2 }]);
              }}
            >
              + Add Point
            </button>
            <label style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: 13, color: 'var(--text-1)' }}>
              <input type="checkbox" checked={useDefaultOri} onChange={(e) => setUseDefaultOri(e.target.checked)} />
              Tool pointing down (default)
            </label>
          </div>
          {!useDefaultOri && (
            <div className="grid cols-3 mt">
              {(['roll', 'pitch', 'yaw'] as const).map((k) => (
                <div key={k}>
                  <label className="field-label">{k} (°)</label>
                  <input className="input" type="number" value={rpy[k]}
                    onChange={(e) => setRpy({ ...rpy, [k]: Number(e.target.value) })} />
                </div>
              ))}
            </div>
          )}
          <div className="btn-row mt">
            <button className="btn primary" onClick={generateCartesian} disabled={state === 'working'}>
              {state === 'working' ? 'Generating (IK along path)…' : 'Generate Trajectory'}
            </button>
          </div>
          <div className="muted mt" style={{ fontSize: 12 }}>
            Cartesian trajectories are converted to joint space with the real IK
            solver sample-by-sample (warm started), then FK-validated.
          </div>
        </div>
      )}

      {state === 'error' && <div className="msg error mt">⚠ {error}</div>}

      {trajectory && (
        <>
          <div className="mt">
            <SimulationControls />
          </div>
          <div className="card mt">
            <div className="spread">
              <div className="card-title" style={{ marginBottom: 0 }}>
                Active Trajectory — {trajectoryLabel} · {trajectory.samples} samples ·{' '}
                {trajectory.duration.toFixed(2)} s
              </div>
              <div className="btn-row">
                <a className="btn sm ghost" href={exportTrajectoryUrl(trajectory.trajectory_id, 'csv')} download>
                  Export CSV
                </a>
                <a className="btn sm ghost" href={exportTrajectoryUrl(trajectory.trajectory_id, 'json')} download>
                  Export JSON
                </a>
              </div>
            </div>
            <LineChart
              series={previewSeries}
              xTitle="Time (s)"
              yTitle="Joint position (deg)"
              height={280}
            />
          </div>
        </>
      )}
    </div>
  );
}

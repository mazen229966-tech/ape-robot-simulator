import { useState } from 'react';

import RobotViewer from '../../components/RobotViewer/RobotViewer';
import * as api from '../../services/api';
import { useRobotStore } from '../../store/robotStore';

const PRESETS = [10_000, 50_000, 100_000];

export default function Workspace() {
  const workspace = useRobotStore((s) => s.workspace);
  const setWorkspace = useRobotStore((s) => s.setWorkspace);
  const [samples, setSamples] = useState(10_000);
  const [state, setState] = useState<'idle' | 'working' | 'ok' | 'error'>('idle');
  const [error, setError] = useState('');

  const generate = async () => {
    setState('working');
    setError('');
    try {
      const res = await api.generateWorkspace(samples);
      setWorkspace(res);
      setState('ok');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Workspace generation failed');
    }
  };

  return (
    <div className="page">
      <div className="page-title">Workspace Analysis</div>
      <div className="page-subtitle">
        Monte-Carlo sampling of the joint space inside the official limits, FK
        evaluation on the backend, point cloud streamed to the 3D viewer.
      </div>

      <div className="grid cols-2" style={{ gridTemplateColumns: 'minmax(0,2fr) minmax(0,3fr)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">Sampling</div>
            <label className="field-label">Number of Samples</label>
            <input
              className="input"
              type="number"
              min={1000}
              max={200000}
              step={1000}
              value={samples}
              onChange={(e) => setSamples(Number(e.target.value))}
            />
            <div className="btn-row mt">
              {PRESETS.map((n) => (
                <button
                  key={n}
                  className={`btn sm${samples === n ? ' primary' : ''}`}
                  onClick={() => setSamples(n)}
                >
                  {n.toLocaleString()}
                </button>
              ))}
            </div>
            <div className="btn-row mt">
              <button className="btn primary" onClick={generate} disabled={state === 'working'}>
                {state === 'working' ? 'Computing on backend…' : 'Generate Workspace'}
              </button>
            </div>
            {state === 'working' && (
              <div className="msg working mt">Computing FK for {samples.toLocaleString()} configurations…</div>
            )}
            {state === 'ok' && workspace && (
              <div className="msg ok mt">
                ✓ Complete — {workspace.valid_samples.toLocaleString()} samples,{' '}
                {workspace.displayed_points.toLocaleString()} points displayed.
              </div>
            )}
            {state === 'error' && <div className="msg error mt">⚠ {error}</div>}
          </div>

          {workspace && (
            <div className="card">
              <div className="card-title">Workspace Bounds</div>
              <table className="table">
                <thead>
                  <tr><th>Axis</th><th>Min (mm)</th><th>Max (mm)</th></tr>
                </thead>
                <tbody>
                  {(['x', 'y', 'z'] as const).map((axis) => (
                    <tr key={axis}>
                      <td>{axis.toUpperCase()}</td>
                      <td className="mono">{workspace.bounds_mm[`${axis}_min`].toFixed(1)}</td>
                      <td className="mono">{workspace.bounds_mm[`${axis}_max`].toFixed(1)}</td>
                    </tr>
                  ))}
                  <tr>
                    <td>Reach (√(x²+y²))</td>
                    <td className="mono" colSpan={2}>{workspace.reach_mm.toFixed(1)} mm</td>
                  </tr>
                </tbody>
              </table>
              <div className="muted mt" style={{ fontSize: 12 }}>
                The official maximum radius of the SV2-6045 is 454 mm. The
                educational DH model is dimensioned so that this sampled envelope
                reaches the same radius (regression-tested on the backend).
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">
            Workspace Point Cloud — use TOP / SIDE / FRONT for orthographic inspections
          </div>
          <RobotViewer height={560} />
        </div>
      </div>
    </div>
  );
}

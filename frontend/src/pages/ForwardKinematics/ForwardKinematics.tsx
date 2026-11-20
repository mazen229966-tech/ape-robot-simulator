import { useState } from 'react';

import RobotViewer from '../../components/RobotViewer/RobotViewer';
import * as api from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import type { FKResult } from '../../types/robot';

export default function ForwardKinematics() {
  const qDeg = useRobotStore((s) => s.qDeg);
  const applyFK = useRobotStore((s) => s.applyFK);
  const info = useRobotStore((s) => s.info);

  const [angles, setAngles] = useState<number[]>([30, -20, 40, 10, 30, 0]);
  const [result, setResult] = useState<FKResult | null>(null);
  const [state, setState] = useState<'idle' | 'working' | 'ok' | 'error'>('idle');
  const [error, setError] = useState('');

  const limits = info?.joint_limits_deg;

  const calculate = async () => {
    setState('working');
    setError('');
    try {
      const res = await api.computeFK(angles);
      setResult(res);
      applyFK(res);
      setState('ok');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'FK computation failed');
    }
  };

  const copyMatrix = async () => {
    if (!result) return;
    const text = result.transform
      .map((row) => `[ ${row.map((v) => v.toFixed(6)).join('  ')} ]`)
      .join('\n');
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* clipboard may be unavailable; selection still possible */
    }
  };

  return (
    <div className="page">
      <div className="page-title">Forward Kinematics</div>
      <div className="page-subtitle">
        Enter six joint angles — the backend computes T₀₆ = A₁A₂A₃A₄A₅A₆, position,
        orientation (ZYX roll/pitch/yaw) and updates the 3D robot.
      </div>

      <div className="grid cols-2" style={{ gridTemplateColumns: 'minmax(0,2fr) minmax(0,3fr)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">Joint Angles</div>
            <div className="grid cols-2">
              {angles.map((v, i) => (
                <div key={i}>
                  <label className="field-label">
                    J{i + 1} {limits ? `(${limits[i][0]}°…+${limits[i][1]}°)` : ''}
                  </label>
                  <input
                    className="input"
                    type="number"
                    step={1}
                    value={v}
                    onChange={(e) =>
                      setAngles((prev) => prev.map((x, j) => (j === i ? Number(e.target.value) : x)))
                    }
                  />
                </div>
              ))}
            </div>
            <div className="btn-row mt">
              <button className="btn primary" onClick={calculate} disabled={state === 'working'}>
                {state === 'working' ? 'Calculating…' : 'Calculate FK'}
              </button>
              <button className="btn ghost" onClick={() => setAngles(qDeg.map((v) => Number(v.toFixed(2))))}>
                Use Current Pose
              </button>
            </div>
            {state === 'ok' && <div className="msg ok mt">✓ Complete — robot state updated.</div>}
            {state === 'error' && <div className="msg error mt">⚠ {error}</div>}
          </div>

          {result && (
            <>
              <div className="card">
                <div className="card-title">Position</div>
                <div className="grid cols-3">
                  <div><div className="field-label">X</div><div className="mono accent">{result.position_mm.x.toFixed(2)} mm</div></div>
                  <div><div className="field-label">Y</div><div className="mono accent">{result.position_mm.y.toFixed(2)} mm</div></div>
                  <div><div className="field-label">Z</div><div className="mono accent">{result.position_mm.z.toFixed(2)} mm</div></div>
                </div>
              </div>
              <div className="card">
                <div className="card-title">Orientation (ZYX)</div>
                <div className="grid cols-3">
                  <div><div className="field-label">Roll</div><div className="mono">{result.orientation.roll.toFixed(2)} °</div></div>
                  <div><div className="field-label">Pitch</div><div className="mono">{result.orientation.pitch.toFixed(2)} °</div></div>
                  <div><div className="field-label">Yaw</div><div className="mono">{result.orientation.yaw.toFixed(2)} °</div></div>
                </div>
              </div>
              <div className="card">
                <div className="spread">
                  <div className="card-title" style={{ marginBottom: 0 }}>Transformation Matrix T₀₆</div>
                  <button className="btn sm" onClick={copyMatrix}>Copy Matrix</button>
                </div>
                <pre className="formula mt">
                  {result.transform.map((row) => `[ ${row.map((v) => v.toFixed(4).padStart(9)).join(' ')} ]`).join('\n')}
                </pre>
              </div>
            </>
          )}
        </div>

        <div className="card">
          <div className="card-title">3D Result</div>
          <RobotViewer height={560} />
        </div>
      </div>
    </div>
  );
}

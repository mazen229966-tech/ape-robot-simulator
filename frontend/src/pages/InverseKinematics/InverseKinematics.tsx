import { useState } from 'react';

import CartesianInput, { type CartesianValue } from '../../components/CartesianInput/CartesianInput';
import RobotViewer from '../../components/RobotViewer/RobotViewer';
import * as api from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import type { IKResult } from '../../types/robot';

export default function InverseKinematics() {
  const ee = useRobotStore((s) => s.ee);
  const qDeg = useRobotStore((s) => s.qDeg);
  const applyFK = useRobotStore((s) => s.applyFK);

  const [posMm, setPosMm] = useState<CartesianValue>({ x: 300, y: 0, z: 280 });
  const [rpy, setRpy] = useState({ roll: 180, pitch: 0, yaw: 0 });
  const [useGuess, setUseGuess] = useState(true);
  const [result, setResult] = useState<IKResult | null>(null);
  const [state, setState] = useState<'idle' | 'working' | 'ok' | 'error'>('idle');
  const [error, setError] = useState('');

  const solve = async () => {
    setState('working');
    setError('');
    setResult(null);
    try {
      const res = await api.computeIK(
        { x: posMm.x / 1000, y: posMm.y / 1000, z: posMm.z / 1000 },
        rpy,
        useGuess ? qDeg : undefined,
      );
      setResult(res);
      setState('ok');
      // apply the solution to the shared robot state + 3D viewer
      applyFK({
        q_deg: res.q_deg,
        position: res.fk_validation.position,
        position_mm: {
          x: res.fk_validation.position.x * 1000,
          y: res.fk_validation.position.y * 1000,
          z: res.fk_validation.position.z * 1000,
        },
        orientation: res.fk_validation.orientation,
        transform: [],
      });
    } catch (err) {
      setState('error');
      const msg = err instanceof Error ? err.message : 'IK failed';
      setError(
        msg.includes('outside')
          ? 'Target is outside reachable workspace.'
          : msg.includes('No valid')
            ? 'No valid IK solution found within joint limits.'
            : msg,
      );
    }
  };

  const useCurrentEE = () => {
    if (!ee) return;
    setPosMm({
      x: Number((ee.position.x * 1000).toFixed(1)),
      y: Number((ee.position.y * 1000).toFixed(1)),
      z: Number((ee.position.z * 1000).toFixed(1)),
    });
    setRpy({
      roll: Number(ee.orientation.roll.toFixed(2)),
      pitch: Number(ee.orientation.pitch.toFixed(2)),
      yaw: Number(ee.orientation.yaw.toFixed(2)),
    });
  };

  return (
    <div className="page">
      <div className="page-title">Inverse Kinematics</div>
      <div className="page-subtitle">
        Desired pose → IK solver (numerical, multi-start, joint-limited) → q₁…q₆ →
        FK validation. Targets outside the workspace or without a valid solution are rejected.
      </div>

      <div className="grid cols-2" style={{ gridTemplateColumns: 'minmax(0,2fr) minmax(0,3fr)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="spread">
              <div className="card-title" style={{ marginBottom: 0 }}>Desired Pose</div>
              <button className="btn sm ghost" onClick={useCurrentEE}>Use Current EE</button>
            </div>
            <div className="mt">
              <CartesianInput value={posMm} onChange={setPosMm} unit="mm" />
            </div>
            <div className="grid cols-3 mt">
              {(['roll', 'pitch', 'yaw'] as const).map((k) => (
                <div key={k}>
                  <label className="field-label">{k[0].toUpperCase() + k.slice(1)} (°)</label>
                  <input
                    className="input"
                    type="number"
                    step={1}
                    value={rpy[k]}
                    onChange={(e) => setRpy({ ...rpy, [k]: Number(e.target.value) })}
                  />
                </div>
              ))}
            </div>
            <label className="mt" style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13, color: 'var(--text-1)' }}>
              <input type="checkbox" checked={useGuess} onChange={(e) => setUseGuess(e.target.checked)} />
              Warm-start from current robot configuration
            </label>
            <div className="btn-row mt">
              <button className="btn primary" onClick={solve} disabled={state === 'working'}>
                {state === 'working' ? 'Solving…' : 'Solve IK'}
              </button>
            </div>
            {state === 'error' && <div className="msg error mt">⚠ {error}</div>}
          </div>

          {result && (
            <>
              <div className="card">
                <div className="card-title">Solution (joint angles)</div>
                <div className="grid cols-3">
                  {result.q_deg.map((v, i) => (
                    <div key={i}>
                      <div className="field-label">J{i + 1}</div>
                      <div className="mono accent">{v.toFixed(2)} °</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <div className="card-title">FK Validation</div>
                <table className="table">
                  <tbody>
                    <tr>
                      <td>Position Error</td>
                      <td className="mono accent">{result.position_error_mm.toFixed(4)} mm</td>
                    </tr>
                    <tr>
                      <td>Orientation Error</td>
                      <td className="mono accent">{result.orientation_error_deg.toFixed(4)} °</td>
                    </tr>
                    <tr>
                      <td>Status</td>
                      <td>
                        {result.valid ? (
                          <span className="badge ready"><span className="dot" />VALID</span>
                        ) : (
                          <span className="badge error"><span className="dot" />REJECTED</span>
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div className="muted mt" style={{ fontSize: 12 }}>
                  FK(q_IK) = ({(result.fk_validation.position.x * 1000).toFixed(2)},{' '}
                  {(result.fk_validation.position.y * 1000).toFixed(2)},{' '}
                  {(result.fk_validation.position.z * 1000).toFixed(2)}) mm
                </div>
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

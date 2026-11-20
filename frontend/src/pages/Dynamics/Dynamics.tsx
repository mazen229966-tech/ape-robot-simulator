import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import LineChart from '../../components/Charts/LineChart';
import JointSeriesSelector, { JOINT_COLORS } from '../../components/Charts/JointSeriesSelector';
import ParameterCard from '../../components/ParameterCard/ParameterCard';
import SimulationControls from '../../components/SimulationControls/SimulationControls';
import * as api from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';
import type { DynamicsResult, TorqueComponent } from '../../types/dynamics';

const COMPONENTS: { key: TorqueComponent; label: string }[] = [
  { key: 'inertia', label: 'Inertia Torque M(q)·q̈' },
  { key: 'coriolis', label: 'Coriolis/Centrifugal C(q,q̇)·q̇' },
  { key: 'gravity', label: 'Gravity g(q)' },
  { key: 'friction', label: 'Friction F(q̇)' },
];

export default function Dynamics() {
  const trajectory = useSimulationStore((s) => s.trajectory);
  const info = useRobotStore((s) => s.info);
  const [result, setResult] = useState<DynamicsResult | null>(null);
  const [state, setState] = useState<'idle' | 'working' | 'ok' | 'error'>('idle');
  const [error, setError] = useState('');
  const [selection, setSelection] = useState<number | 'all'>('all');
  const [component, setComponent] = useState<TorqueComponent>('total');

  const compute = async () => {
    if (!trajectory) return;
    setState('working');
    setError('');
    try {
      const res = await api.computeDynamics(trajectory.trajectory_id);
      setResult(res);
      setState('ok');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Dynamics computation failed');
    }
  };

  const series = useMemo(() => {
    if (!result) return [];
    const data = result.components[component];
    const joints = selection === 'all' ? [0, 1, 2, 3, 4, 5] : [selection];
    return joints.map((j) => ({
      x: result.t,
      y: result.t.map((_, i) => data[i][j]),
      name: `J${j + 1}`,
      color: JOINT_COLORS[j],
    }));
  }, [result, selection, component]);

  if (!trajectory) {
    return (
      <div className="page">
        <div className="page-title">Dynamic Analysis</div>
        <div className="msg info">
          Generate a trajectory first (<Link to="/trajectory">Trajectory</Link> or{' '}
          <Link to="/draw-h">Draw H</Link>) — torques are computed along it.
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-title">Dynamic Analysis</div>
      <div className="page-subtitle">
        Inverse dynamics via the recursive Newton–Euler algorithm (Robotics Toolbox).
      </div>

      <div className="formula mb">
        τ = M(q)·q̈ + C(q,q̇)·q̇ + g(q) + F(q̇)
      </div>

      <div className="note mb">
        Dynamic Model: <strong>{info?.dynamic_parameter_source ?? 'Educational / Assumed'}</strong> —
        APE does not publish mass/inertia data for the SV2-6045. Link masses sum to the
        official 23 kg body weight; torques are therefore representative values, not
        factory data.
      </div>

      <div className="spread mb">
        <button className="btn primary" onClick={compute} disabled={state === 'working'}>
          {state === 'working' ? 'Computing torques…' : 'Compute Torques'}
        </button>
        {result && (
          <span className="muted mono" style={{ fontSize: 12 }}>
            RNE cross-check discrepancy: {result.rne_discrepancy_nm.toExponential(2)} N·m
          </span>
        )}
      </div>
      {state === 'error' && <div className="msg error mb">⚠ {error}</div>}

      {result && (
        <>
          <div className="grid cols-3 mb">
            {result.stats.per_joint.map((s) => (
              <ParameterCard
                key={s.joint}
                value={`J${s.joint}: ${s.max_abs_torque_nm.toFixed(1)}`}
                unit="N·m"
                label={`Max |τ${s.joint}|`}
              />
            ))}
          </div>

          <div className="card mb">
            <div className="card-title">Torque Summary</div>
            <table className="table">
              <thead>
                <tr><th>Joint</th><th>Max Torque (N·m)</th><th>RMS Torque (N·m)</th><th>Peak (N·m)</th></tr>
              </thead>
              <tbody>
                {result.stats.per_joint.map((s) => (
                  <tr key={s.joint}>
                    <td>J{s.joint}</td>
                    <td className="mono">{s.max_abs_torque_nm.toFixed(2)}</td>
                    <td className="mono">{s.rms_torque_nm.toFixed(2)}</td>
                    <td className="mono">{s.peak_torque_nm.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card mb">
            <div className="spread">
              <div className="card-title" style={{ marginBottom: 0 }}>Torque vs Time</div>
              <select className="input" style={{ width: 280 }} value={component}
                onChange={(e) => setComponent(e.target.value as TorqueComponent)}>
                <option value="total">Total Torque τ</option>
                {COMPONENTS.map((c) => (
                  <option key={c.key} value={c.key}>{c.label}</option>
                ))}
              </select>
            </div>
            <div className="mt">
              <JointSeriesSelector selection={selection} onChange={setSelection} />
            </div>
            <LineChart series={series} xTitle="Time (s)" yTitle="Torque (N·m)" height={340} />
          </div>

          <SimulationControls />
        </>
      )}
    </div>
  );
}

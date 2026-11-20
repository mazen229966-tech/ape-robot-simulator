import ParameterCard from '../../components/ParameterCard/ParameterCard';
import RobotViewer from '../../components/RobotViewer/RobotViewer';
import SimulationControls from '../../components/SimulationControls/SimulationControls';
import { simStop } from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

export default function Dashboard() {
  const info = useRobotStore((s) => s.info);
  const qDeg = useRobotStore((s) => s.qDeg);
  const ee = useRobotStore((s) => s.ee);
  const preset = useRobotStore((s) => s.preset);
  const setStatus = useRobotStore((s) => s.setStatus);
  const setSimStatus = useSimulationStore((s) => s.setSimStatus);
  const trajectory = useSimulationStore((s) => s.trajectory);

  const stopAll = async () => {
    try {
      await simStop();
    } finally {
      setSimStatus('stopped');
      setStatus('STOPPED');
    }
  };

  const specs = info?.official_specs;
  const p = ee?.position;
  const o = ee?.orientation;

  return (
    <div className="page">
      <div className="page-title">Dashboard</div>
      <div className="page-subtitle">
        System overview — robot state, end-effector pose and live simulation.
      </div>

      <div className="grid cols-4">
        <ParameterCard value={specs?.dof ?? 6} label="Robot Axes" />
        <ParameterCard value={Math.round((specs?.max_radius_m ?? 0.454) * 1000)} unit="mm" label="Reach" />
        <ParameterCard value={specs?.payload_rated_kg ?? 1} unit="kg" label="Payload" />
        <ParameterCard value={specs?.repeatability_mm ?? 0.02} unit="mm" label="Repeatability" />
      </div>

      <div className="grid cols-3 mt" style={{ gridTemplateColumns: 'minmax(0,2fr) minmax(0,1fr)' }}>
        <div className="card">
          <div className="card-title">3D Robot Viewer</div>
          <RobotViewer height={430} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">End Effector</div>
            <table className="table">
              <tbody>
                <tr><td>X</td><td className="mono accent">{p ? (p.x * 1000).toFixed(2) : '--'} mm</td></tr>
                <tr><td>Y</td><td className="mono accent">{p ? (p.y * 1000).toFixed(2) : '--'} mm</td></tr>
                <tr><td>Z</td><td className="mono accent">{p ? (p.z * 1000).toFixed(2) : '--'} mm</td></tr>
                <tr><td>Roll</td><td className="mono">{o ? o.roll.toFixed(2) : '--'} °</td></tr>
                <tr><td>Pitch</td><td className="mono">{o ? o.pitch.toFixed(2) : '--'} °</td></tr>
                <tr><td>Yaw</td><td className="mono">{o ? o.yaw.toFixed(2) : '--'} °</td></tr>
              </tbody>
            </table>
          </div>

          <div className="card">
            <div className="card-title">Joint State</div>
            <table className="table">
              <tbody>
                {qDeg.map((v, i) => (
                  <tr key={i}>
                    <td>J{i + 1}</td>
                    <td className="mono">{v.toFixed(2)} °</td>
                    <td className="muted mono" style={{ fontSize: 11 }}>
                      {info ? `[${info.joint_limits_deg[i][0]}°, ${info.joint_limits_deg[i][1]}°]` : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <div className="btn-row">
              <button className="btn" onClick={() => preset('home')} title="Move to the home pose">
                Home
              </button>
              <button className="btn" onClick={() => preset('zero')} title="All joints to zero">
                Reset
              </button>
              <button
                className="btn danger"
                onClick={() => void stopAll()}
                title="Stop any running simulation and freeze the robot state"
              >
                Stop
              </button>
            </div>
          </div>
        </div>
      </div>

      {trajectory && (
        <div className="mt">
          <SimulationControls />
        </div>
      )}
    </div>
  );
}

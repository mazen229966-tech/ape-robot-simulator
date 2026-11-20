import JointControls from '../../components/JointControls/JointControls';
import RobotViewer from '../../components/RobotViewer/RobotViewer';
import { simStop } from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

export default function RobotControl() {
  const ee = useRobotStore((s) => s.ee);
  const preset = useRobotStore((s) => s.preset);
  const info = useRobotStore((s) => s.info);
  const setStatus = useRobotStore((s) => s.setStatus);
  const setSimStatus = useSimulationStore((s) => s.setSimStatus);

  const stopMotion = async () => {
    try {
      await simStop();
    } finally {
      setSimStatus('stopped');
      setStatus('STOPPED');
    }
  };

  const p = ee?.position;
  const o = ee?.orientation;

  return (
    <div className="page">
      <div className="page-title">Robot Control</div>
      <div className="page-subtitle">
        Direct joint control — every slider movement is validated against the
        official joint limits, recomputed by the backend FK and mirrored in the
        3D viewer and all state displays.
      </div>

      <div className="grid cols-2" style={{ gridTemplateColumns: 'minmax(0,5fr) minmax(0,6fr)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">Joint Sliders</div>
            <JointControls />
            <div className="btn-row mt">
              <button className="btn" onClick={() => preset('home')}>Home</button>
              <button className="btn" onClick={() => preset('zero')}>Zero Position</button>
              <button
                className="btn"
                onClick={() => preset('zero')}
                title="Reset is equivalent to Zero for this robot"
              >
                Reset
              </button>
              <button
                className="btn danger"
                onClick={() => void stopMotion()}
                title="Stop any running motion and hold the current pose"
              >
                Stop Motion
              </button>
            </div>
          </div>

          <div className="card">
            <div className="card-title">End Effector (live FK)</div>
            <div className="grid cols-3">
              <div>
                <div className="field-label">X</div>
                <div className="mono accent">{p ? (p.x * 1000).toFixed(2) : '--'} mm</div>
              </div>
              <div>
                <div className="field-label">Y</div>
                <div className="mono accent">{p ? (p.y * 1000).toFixed(2) : '--'} mm</div>
              </div>
              <div>
                <div className="field-label">Z</div>
                <div className="mono accent">{p ? (p.z * 1000).toFixed(2) : '--'} mm</div>
              </div>
              <div>
                <div className="field-label">Roll</div>
                <div className="mono">{o ? o.roll.toFixed(2) : '--'} °</div>
              </div>
              <div>
                <div className="field-label">Pitch</div>
                <div className="mono">{o ? o.pitch.toFixed(2) : '--'} °</div>
              </div>
              <div>
                <div className="field-label">Yaw</div>
                <div className="mono">{o ? o.yaw.toFixed(2) : '--'} °</div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-title">Official Joint Ranges</div>
            <table className="table">
              <thead>
                <tr><th>Joint</th><th>Range</th><th>Max Speed</th></tr>
              </thead>
              <tbody>
                {(info?.joint_limits_deg ?? []).map((lim, i) => (
                  <tr key={i}>
                    <td>J{i + 1}</td>
                    <td className="mono">{lim[0]}° … +{lim[1]}°</td>
                    <td className="mono">{info?.joint_speeds_deg_s[i] ?? '—'} °/s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-title">3D View</div>
          <RobotViewer height={620} />
        </div>
      </div>
    </div>
  );
}

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import LineChart from '../../components/Charts/LineChart';
import JointSeriesSelector, { JOINT_COLORS } from '../../components/Charts/JointSeriesSelector';
import RobotViewer from '../../components/RobotViewer/RobotViewer';
import SimulationControls from '../../components/SimulationControls/SimulationControls';
import { useSimulationStore } from '../../store/simulationStore';

const RAD2DEG = 180 / Math.PI;

export default function MotionAnalysis() {
  const trajectory = useSimulationStore((s) => s.trajectory);
  const [selection, setSelection] = useState<number | 'all'>('all');

  const charts = useMemo(() => {
    if (!trajectory) return null;
    const joints = selection === 'all' ? [0, 1, 2, 3, 4, 5] : [selection];
    const build = (data: number[][], scale: number) =>
      joints.map((j) => ({
        x: trajectory.t,
        y: trajectory.t.map((_, i) => data[i][j] * scale),
        name: `J${j + 1}`,
        color: JOINT_COLORS[j],
      }));
    return {
      position: build(trajectory.q, RAD2DEG),
      velocity: build(trajectory.qd, RAD2DEG),
      acceleration: build(trajectory.qdd, RAD2DEG),
    };
  }, [trajectory, selection]);

  if (!trajectory) {
    return (
      <div className="page">
        <div className="page-title">Motion Analysis</div>
        <div className="msg info">
          No trajectory loaded. Generate one on the{' '}
          <Link to="/trajectory">Trajectory</Link> page or via{' '}
          <Link to="/draw-h">Draw H</Link>, then return here for
          position / velocity / acceleration analysis.
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-title">Motion Analysis</div>
      <div className="page-subtitle">
        q(t), q̇(t) and q̈(t) of the active trajectory ({trajectory.method},{' '}
        {trajectory.samples} samples). Position is analytic for joint-space
        polynomials and finite-difference based for Cartesian trajectories.
      </div>

      <div className="spread mb">
        <JointSeriesSelector selection={selection} onChange={setSelection} />
        <div className="muted mono" style={{ fontSize: 12 }}>
          q in deg · q̇ in deg/s · q̈ in deg/s²
        </div>
      </div>

      {charts && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">Joint Position vs Time</div>
            <LineChart series={charts.position} xTitle="Time (s)" yTitle="Position (deg)" />
          </div>
          <div className="card">
            <div className="card-title">Joint Velocity vs Time</div>
            <LineChart series={charts.velocity} xTitle="Time (s)" yTitle="Velocity (deg/s)" />
          </div>
          <div className="card">
            <div className="card-title">Joint Acceleration vs Time</div>
            <LineChart series={charts.acceleration} xTitle="Time (s)" yTitle="Acceleration (deg/s²)" />
          </div>
        </div>
      )}

      <div className="grid cols-2 mt">
        <div className="card">
          <div className="card-title">Animation</div>
          <SimulationControls />
          <div className="mt">
            <RobotViewer height={380} />
          </div>
        </div>
        <div className="card">
          <div className="card-title">End-Effector Path</div>
          <LineChart
            series={[
              { x: trajectory.t, y: trajectory.ee_path.map((p) => p[0] * 1000), name: 'X', color: '#f87171' },
              { x: trajectory.t, y: trajectory.ee_path.map((p) => p[1] * 1000), name: 'Y', color: '#34d399' },
              { x: trajectory.t, y: trajectory.ee_path.map((p) => p[2] * 1000), name: 'Z', color: '#60a5fa' },
            ]}
            xTitle="Time (s)"
            yTitle="Position (mm)"
            height={280}
          />
          <div className="muted mt" style={{ fontSize: 12 }}>
            Path length: {(trajectory.ee_path_length * 1000).toFixed(1)} mm — computed by FK
            along the joint trajectory.
          </div>
        </div>
      </div>
    </div>
  );
}

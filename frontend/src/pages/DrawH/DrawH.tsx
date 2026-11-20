import { useState } from 'react';

import RobotViewer from '../../components/RobotViewer/RobotViewer';
import { getSimulationSocket } from '../../hooks/useSimulationSocket';
import * as api from '../../services/api';
import { simStart } from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

const RAD2DEG = 180 / Math.PI;

export default function DrawH() {
  const setRobotState = useRobotStore((s) => s.setJoints);
  const setStatus = useRobotStore((s) => s.setStatus);
  const trajectory = useSimulationStore((s) => s.trajectory);
  const setTrajectory = useSimulationStore((s) => s.setTrajectory);
  const simStatus = useSimulationStore((s) => s.simStatus);
  const progress = useSimulationStore((s) => s.progress);
  const setSimStatus = useSimulationStore((s) => s.setSimStatus);

  type Plane = 'XY' | 'XZ' | 'YZ';
  // Validated default geometry per plane (matches the backend envelope).
  const PLANE_DEFAULTS: Record<
    Plane,
    { width: number; height: number; z: number; cx: number; cy: number }
  > = {
    XY: { width: 150, height: 200, z: 280, cx: 290, cy: 0 },
    XZ: { width: 100, height: 140, z: 250, cx: 300, cy: 120 },
    YZ: { width: 100, height: 140, z: 250, cx: 300, cy: 120 },
  };

  const [plane, setPlane] = useState<Plane>('XY');
  const [widthMm, setWidthMm] = useState(150);
  const [heightMm, setHeightMm] = useState(200);
  const [planeZMm, setPlaneZMm] = useState(280);
  const [speedMmS, setSpeedMmS] = useState(50);
  const [centerX, setCenterX] = useState(290);
  const [centerY, setCenterY] = useState(0);

  const selectPlane = (p: Plane) => {
    setPlane(p);
    const d = PLANE_DEFAULTS[p];
    setWidthMm(d.width);
    setHeightMm(d.height);
    setPlaneZMm(d.z);
    setCenterX(d.cx);
    setCenterY(d.cy);
  };

  const [state, setState] = useState<'idle' | 'working' | 'ok' | 'error'>('idle');
  const [error, setError] = useState('');

  const isH = trajectory?.method === 'draw-h';
  const done = isH && simStatus === 'done';
  const drawingProgress = isH ? Math.round(progress * 100) : 0;

  const generate = async () => {
    setState('working');
    setError('');
    try {
      const res = await api.generateDrawH({
        plane,
        width: widthMm / 1000,
        height: heightMm / 1000,
        drawing_height: planeZMm / 1000,
        speed: speedMmS / 1000,
        center: { x: centerX / 1000, y: centerY / 1000, z: 0 },
      });
      setTrajectory(res, 'Draw H');
      setState('ok');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'H trajectory generation failed');
    }
  };

  const draw = async () => {
    if (!trajectory || trajectory.method !== 'draw-h') return;
    setStatus('RUNNING');
    setSimStatus('running');
    // Move to start (§33): pose the robot at the trajectory start first.
    const q0deg = trajectory.q[0].map((v) => v * RAD2DEG);
    await setRobotState(q0deg);
    const sock = getSimulationSocket();
    if (sock) sock.start(trajectory.trajectory_id, 1);
    else await simStart(trajectory.trajectory_id, 1);
  };

  const stop = async () => {
    await api.simStop();
    setSimStatus('stopped');
    setStatus('STOPPED');
  };

  return (
    <div className="page">
      <div className="page-title">Draw Letter H</div>
      <div className="page-subtitle">
        Final demo — the H is a real Cartesian trajectory: corner points → linear
        path → IK → joint trajectory → FK validation → 3D animation. Pen up/down
        moves are planned; a mid-stroke configuration change (if required) is done
        pen-up at a dedicated reconfiguration point.
      </div>

      <div className="grid cols-2" style={{ gridTemplateColumns: 'minmax(0,2fr) minmax(0,3fr)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">H Parameters</div>
            <div className="grid cols-2">
              <div>
                <label className="field-label">Plane</label>
                <select
                  className="input"
                  value={plane}
                  onChange={(e) => selectPlane(e.target.value as Plane)}
                >
                  <option value="XY">XY (horizontal surface)</option>
                  <option value="XZ">XZ (vertical wall, tool tilted 45°)</option>
                  <option value="YZ">YZ (vertical wall, tool tilted 45°)</option>
                </select>
                {plane === 'YZ' && (
                  <div className="muted mt" style={{ fontSize: 11 }}>
                    Note: on this educational model the YZ wall is only
                    marginally reachable — generation may report that no
                    continuous IK solution exists. XY and XZ are fully
                    validated.
                  </div>
                )}
              </div>
              <div>
                <label className="field-label">
                  {plane === 'XY' ? 'Drawing Height (mm)' : 'H Centre Height z (mm)'}
                </label>
                <input className="input" type="number" min={100} max={450} step={10} value={planeZMm}
                  onChange={(e) => setPlaneZMm(Number(e.target.value))} />
              </div>
              <div>
                <label className="field-label">H Width (mm)</label>
                <input className="input" type="number" min={40} max={300} step={10} value={widthMm}
                  onChange={(e) => setWidthMm(Number(e.target.value))} />
              </div>
              <div>
                <label className="field-label">H Height (mm)</label>
                <input className="input" type="number" min={40} max={300} step={10} value={heightMm}
                  onChange={(e) => setHeightMm(Number(e.target.value))} />
              </div>
              <div>
                <label className="field-label">Speed (mm/s)</label>
                <input className="input" type="number" min={5} max={200} step={5} value={speedMmS}
                  onChange={(e) => setSpeedMmS(Number(e.target.value))} />
              </div>
              <div>
                <label className="field-label">
                  {plane === 'XY' && 'Center X / Y (mm)'}
                  {plane === 'XZ' && 'Center X / Wall Y (mm)'}
                  {plane === 'YZ' && 'Wall X / Center Y (mm)'}
                </label>
                <div style={{ display: 'flex', gap: 6 }}>
                  <input className="input" type="number" step={10} value={centerX}
                    onChange={(e) => setCenterX(Number(e.target.value))} />
                  <input className="input" type="number" step={10} value={centerY}
                    onChange={(e) => setCenterY(Number(e.target.value))} />
                </div>
              </div>
            </div>

            <div className="btn-row mt">
              <button className="btn primary" onClick={generate} disabled={state === 'working'}>
                {state === 'working' ? 'Generating (IK along H path)…' : 'Generate H Trajectory'}
              </button>
            </div>
            {state === 'error' && <div className="msg error mt">⚠ {error}</div>}
            {state === 'ok' && trajectory && (
              <div className="msg ok mt">
                ✓ Trajectory ready — {trajectory.samples} samples,{' '}
                {trajectory.duration.toFixed(1)} s, drawn length{' '}
                {((trajectory.draw_distance ?? 0) * 1000).toFixed(0)} mm.
              </div>
            )}
          </div>

          {isH && trajectory && (
            <div className="card">
              <div className="card-title">Drawing Control</div>
              <div className="btn-row">
                <button className="btn primary" onClick={draw} disabled={simStatus === 'running'}>
                  ▶ DRAW H
                </button>
                <button className="btn danger" onClick={stop} disabled={simStatus !== 'running' && simStatus !== 'paused'}>
                  ⏹ Stop
                </button>
              </div>
              <div className="mt spread">
                <span className="muted" style={{ fontSize: 13 }}>Drawing Progress</span>
                <span className="mono accent">{drawingProgress}%</span>
              </div>
              <div className="progress-track mt">
                <div className="progress-fill" style={{ width: `${drawingProgress}%` }} />
              </div>
              {done && <div className="msg ok mt">✓ H Drawing Completed</div>}
              {simStatus === 'running' && (
                <div className="msg working mt">Drawing in progress…</div>
              )}

              <div className="mt">
                <div className="card-title">Phases</div>
                <table className="table">
                  <thead>
                    <tr><th>Phase</th><th>Pen</th><th>Time</th></tr>
                  </thead>
                  <tbody>
                    {(trajectory.phases ?? []).map((p, i) => (
                      <tr key={i}>
                        <td>{p.phase}</td>
                        <td>{p.pen_down ? '✎ down' : 'up'}</td>
                        <td className="mono">{p.t_start.toFixed(1)}–{p.t_end.toFixed(1)} s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-title">H Geometry</div>
            <svg viewBox="0 0 200 200" width="100%" style={{ maxWidth: 220, display: 'block', margin: '0 auto' }}>
              <g stroke="#38bdf8" strokeWidth="5" strokeLinecap="round">
                <line x1="50" y1="30" x2="50" y2="170" />
                <line x1="150" y1="30" x2="150" y2="170" />
                <line x1="50" y1="100" x2="150" y2="100" />
              </g>
              <g fill="#fbbf24" fontSize="11" fontFamily="monospace">
                <text x="28" y="26">P1</text>
                <text x="28" y="184">P2</text>
                <text x="58" y="96">P3</text>
                <text x="118" y="96">P4</text>
                <text x="156" y="26">P5</text>
                <text x="156" y="184">P6</text>
              </g>
            </svg>
            <div className="muted" style={{ fontSize: 12 }}>
              P1→P2 left vertical · P3→P4 middle bar · P5→P6 right vertical.
              The pen lifts between strokes. On the XY plane the tool axis
              points straight down; on vertical walls the pen is tilted 45°
              towards the surface (a horizontal tool is not continuously
              reachable within the official joint limits of this model).
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">3D Drawing View</div>
          <RobotViewer height={640} />
        </div>
      </div>
    </div>
  );
}

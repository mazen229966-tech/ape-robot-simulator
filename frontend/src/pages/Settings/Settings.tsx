import { useRobotStore } from '../../store/robotStore';

export default function Settings() {
  const info = useRobotStore((s) => s.info);
  const showGrid = useRobotStore((s) => s.showGrid);
  const showFrames = useRobotStore((s) => s.showFrames);
  const showWorkspace = useRobotStore((s) => s.showWorkspace);
  const showTrajectory = useRobotStore((s) => s.showTrajectory);
  const showAxes = useRobotStore((s) => s.showAxes);
  const toggle = useRobotStore((s) => s.toggle);

  const toggles: { key: 'showGrid' | 'showFrames' | 'showWorkspace' | 'showTrajectory' | 'showAxes'; label: string; hint: string; value: boolean }[] = [
    { key: 'showGrid', label: 'Show Grid', hint: 'Ground grid in the 3D viewer', value: showGrid },
    { key: 'showFrames', label: 'Show Coordinate Frames', hint: 'DH frames {0}…{6} with axes', value: showFrames },
    { key: 'showWorkspace', label: 'Show Workspace', hint: 'Workspace point cloud overlay', value: showWorkspace },
    { key: 'showTrajectory', label: 'Show Trajectory', hint: 'End-effector path of the active trajectory', value: showTrajectory },
    { key: 'showAxes', label: 'Show Base Axes', hint: 'Labelled X/Y/Z base coordinate axes', value: showAxes },
  ];

  return (
    <div className="page">
      <div className="page-title">Settings</div>
      <div className="page-subtitle">Display preferences and parameter provenance.</div>

      <div className="grid cols-2">
        <div className="card">
          <div className="card-title">Display</div>
          <div className="grid cols-2 mb">
            <div>
              <label className="field-label">Units</label>
              <select className="input" value="metric" onChange={() => undefined}>
                <option value="metric">Metric</option>
              </select>
            </div>
            <div>
              <label className="field-label">Angle</label>
              <select className="input" value="deg" onChange={() => undefined}>
                <option value="deg">Degrees</option>
              </select>
            </div>
            <div>
              <label className="field-label">Theme</label>
              <select className="input" value="dark" onChange={() => undefined}>
                <option value="dark">Dark Engineering</option>
              </select>
            </div>
          </div>

          {toggles.map((t) => (
            <label
              key={t.key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 0',
                borderBottom: '1px solid var(--border)',
                cursor: 'pointer',
              }}
            >
              <input type="checkbox" checked={t.value} onChange={() => toggle(t.key)} />
              <span>{t.label}</span>
              <span className="muted" style={{ marginLeft: 'auto', fontSize: 12 }}>{t.hint}</span>
            </label>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <div className="card-title">Robot Parameters</div>
            <table className="table">
              <tbody>
                <tr>
                  <td>Kinematic (DH) source</td>
                  <td className="mono accent">{info?.kinematic_parameter_source ?? '—'}</td>
                </tr>
                <tr>
                  <td>Dynamic model source</td>
                  <td className="mono accent">{info?.dynamic_parameter_source ?? '—'}</td>
                </tr>
                <tr>
                  <td>Official specs source</td>
                  <td className="mono">{info?.official_specs.source ?? '—'}</td>
                </tr>
                <tr>
                  <td>Gravity</td>
                  <td className="mono">{info?.gravity_m_s2 ?? 9.81} m/s²</td>
                </tr>
              </tbody>
            </table>
            <div className="note mt">
              Educational / Assumed parameters are clearly separated from official
              APE data and can be replaced in <code>backend/app/models/ape_sv45.py</code>{' '}
              without touching the rest of the system.
            </div>
          </div>

          <div className="card">
            <div className="card-title">Simulation Notice</div>
            <p style={{ color: 'var(--text-1)', lineHeight: 1.7, margin: 0 }}>
              This platform is a <strong>simulation only</strong>. It never sends
              commands to real hardware. The STOP control freezes the animation and
              the simulation loop — it is a simulation stop, not an industrial
              emergency stop.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

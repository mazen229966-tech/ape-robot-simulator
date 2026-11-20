import { Link } from 'react-router-dom';

const SECTIONS = [
  {
    id: 'robot',
    title: 'Robot — APE SV2-6045',
    body: `Six-axis vertical articulated robot by APE Technology. Official data:
rated payload 1 kg (max 2.5 kg), maximum radius 454 mm, repeatability ±0.02 mm,
body weight 23 kg. Joint ranges: J1 ±165°, J2 ±100°, J3 −70°/+90°, J4 ±160°,
J5 ±130°, J6 ±360°. The kinematic (DH) and dynamic parameters used by this
simulator are educational estimates dimensioned to these official values —
APE does not publish them.`,
  },
  {
    id: 'dh',
    title: 'DH Modelling',
    body: `Standard (classic) Denavit–Hartenberg convention. Each link transform:`,
    formula: `A_i = Rz(θ_i) · Tz(d_i) · Tx(a_i) · Rx(α_i)

     [ cosθ   -sinθ·cosα    sinθ·sinα    a·cosθ ]
A_i = [ sinθ    cosθ·cosα   -cosθ·sinα    a·sinθ ]
     [  0        sinα         cosα          d    ]
     [  0         0            0            1    ]`,
  },
  {
    id: 'fk',
    title: 'Forward Kinematics',
    body: `The full chain multiplies the six link transforms:`,
    formula: `T_06 = A1 · A2 · A3 · A4 · A5 · A6

position:  X = T_06[0,3]   Y = T_06[1,3]   Z = T_06[2,3]
orientation:  R = T_06[0:3,0:3]  →  roll/pitch/yaw (ZYX)`,
  },
  {
    id: 'ik',
    title: 'Inverse Kinematics',
    body: `Numerical IK (Levenberg–Marquardt, multi-start) with joint-limit
enforcement. Every accepted solution is re-validated by forward kinematics:
FK(q_IK) is compared against the target pose and the position error (mm) and
orientation error (deg) are reported. Unreachable targets are rejected with
clear messages.`,
  },
  {
    id: 'workspace',
    title: 'Workspace',
    body: `Monte-Carlo method: N joint configurations are sampled uniformly inside
the official joint limits, FK is evaluated (vectorised, on the backend) and the
resulting point cloud bounds are reported. Displayed points are downsampled
server-side to keep the UI responsive.`,
  },
  {
    id: 'trajectory',
    title: 'Trajectory Planning',
    body: `Joint space — cubic and quintic polynomials with rest boundary conditions:`,
    formula: `cubic:    q(t) = q0 + a2·t² + a3·t³            (v=0 at both ends)
quintic:  q(t) = q0 + a3·t³ + a4·t⁴ + a5·t⁵    (v=0, a=0 at both ends)

Cartesian: timed waypoints → linear path interpolation → IK per sample
(warm started) → joint trajectory → FK validation.`,
  },
  {
    id: 'dynamics',
    title: 'Dynamics',
    body: `Inverse dynamics via the recursive Newton–Euler algorithm; the torque is
decomposed into its physical components:`,
    formula: `τ = M(q)·q̈ + C(q,q̇)·q̇ + g(q) + F(q̇)

M(q)   inertia matrix          → inertia torque
C(q,q̇) Coriolis/centrifugal   → velocity torque
g(q)   gravity loading         → gravity torque
F(q̇)  viscous + Coulomb       → friction torque`,
  },
  {
    id: 'drawh',
    title: 'Draw H',
    body: `The letter H is defined as a real Cartesian trajectory: six corner points
(P1 top-left → P2 bottom-left, P3→P4 middle bar, P5→P6 right vertical),
converted through IK into a joint trajectory, FK-validated and animated.
Pen up/down moves are planned, and a mid-stroke configuration change — if the
kinematics requires it — is performed pen-up at a dedicated reconfiguration
point. Drawing progress, phases and completion are reported live.

The drawing plane is selectable (spec §32). On the XY plane the tool axis
points straight down; on the vertical XZ / YZ walls the pen is tilted 45°
towards the surface because a purely horizontal tool is not continuously
reachable within the official joint limits of the educational model. Each
plane uses validated default geometry; the YZ wall is only marginally
reachable and generation may be rejected with a clear message.`,
  },
];

const DEMO_STEPS = [
  ['Overview', 'This is the APE 6-DOF robot used as the reference model.'],
  ['DH Model', 'Explain the six links and the standard-DH convention.'],
  ['Robot Control', 'Move J1…J6 with the sliders — the 3D robot and FK follow live.'],
  ['Forward Kinematics', 'Enter joint angles, read X Y Z and orientation.'],
  ['Inverse Kinematics', 'Feed the same X Y Z back, get the joints, check the FK validation error.'],
  ['Workspace', 'Generate the point cloud and inspect 3D / Top / Side / Front views.'],
  ['Trajectory', 'Plan a joint-space or Cartesian trajectory between points.'],
  ['Motion Analysis', 'Show position, velocity and acceleration of every joint.'],
  ['Dynamics', 'Compute and display torque J1…J6 with the component decomposition.'],
  ['Draw H', 'Run DRAW H — the robot draws the letter H as a real Cartesian trajectory.'],
];

export default function Documentation() {
  return (
    <div className="page">
      <div className="page-title">About / Documentation</div>
      <div className="page-subtitle">
        Theory reference for the project report — every formula shown here is
        implemented exactly this way in the Python engine.
      </div>

      <div className="grid cols-2">
        {SECTIONS.map((s) => (
          <div className="card" key={s.id}>
            <div className="card-title">{s.title}</div>
            <p style={{ color: 'var(--text-1)', lineHeight: 1.7, margin: '0 0 10px', whiteSpace: 'pre-line' }}>
              {s.body}
            </p>
            {s.formula && <pre className="formula">{s.formula}</pre>}
          </div>
        ))}
      </div>

      <div className="card mt">
        <div className="card-title">Suggested Demo Flow</div>
        <table className="table">
          <thead>
            <tr><th>Step</th><th>Page</th><th>What to explain</th></tr>
          </thead>
          <tbody>
            {DEMO_STEPS.map(([page, text], i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td className="accent">{page}</td>
                <td>{text}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="muted mt" style={{ fontSize: 12 }}>
          More detail (architecture, parameter sources, API reference) lives in the
          repository: <code>docs/</code>, <code>README.md</code> and the live{' '}
          <a href="/docs" target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
            API documentation (/docs)
          </a>. Navigation: <Link to="/" style={{ color: 'var(--accent)' }}>Overview</Link>.
        </div>
      </div>
    </div>
  );
}

# APE SV2-6045 Robot Simulator

A complete end-to-end **web-based robotics simulation platform** for the APE
SV2-6045 6-DOF industrial robot — forward/inverse kinematics, workspace
analysis, trajectory planning, dynamics with torque decomposition, and a
"Draw the letter H" demo built on a real Cartesian path.

> **Simulation only.** This project never controls real hardware and never
> presents assumed values as factory data.

---

## The robot

The [APE SV2-6045](https://www.ape.cn) is a vertical articulated 6-axis robot.
Official published data (used as ground truth throughout):

| Spec | Value |
|---|---|
| Rated / max payload | 1 kg / 2.5 kg |
| Maximum radius | 454 mm |
| Repeatability | ±0.02 mm |
| Body weight | 23 kg |
| Joint ranges | J1 ±165°, J2 ±100°, J3 −70/+90°, J4 ±160°, J5 ±130°, J6 ±360° |
| Max joint speeds | 360 / 300 / 300 / 540 / 540 / 600 deg/s |

APE does **not** publish DH or mass/inertia data. The simulator therefore uses
a clearly-labelled **Educational / Assumed** parameter set, dimensioned to the
official 454 mm reach and joint limits, stored in a single swappable file. It
is never presented as factory data.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · NumPy / SciPy · **Robotics Toolbox for Python** |
| Frontend | React 19 · TypeScript · Vite · **Three.js / R3F / drei** · Plotly |
| Realtime | WebSocket (`/ws/simulation`) streaming ~30 Hz frames |
| Units | All internal math in SI (m, rad, s, N·m); UI shows mm / deg |

**No math in React.** Components never compute kinematics or call the network
directly — `services/api.ts` and `services/websocket.ts` are the only network
entry points, and every number displayed comes from the backend engine.

---

## Pages (13)

Overview · Dashboard · DH Model · Robot Control · Forward Kinematics ·
Inverse Kinematics · Workspace · Trajectory · Motion Analysis · Dynamics ·
Draw H · Documentation · Settings

---

## Quick start

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Interactive API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev        # Vite dev server, proxies /api and /ws to :8000
```

### Tests
```bash
cd backend
pytest             # 60 tests: FK, FK→IK→FK, limits, workspace, trajectory, dynamics, API, Draw H (XY/XZ/YZ), URDF
```

---

## Repository layout

```
ape-robot-simulator/
├── backend/
│   ├── app/
│   │   ├── models/        # ape_sv45.py (DH, limits, dynamics) + schemas
│   │   ├── robotics/      # dh, robot, kinematics, ik, workspace,
│   │   │                  # trajectory, dynamics, validation, draw_h
│   │   ├── simulation/    # state + playback engine
│   │   ├── api/           # FastAPI routers
│   │   └── main.py        # app + /ws/simulation
│   ├── tests/             # pytest suite
│   └── tools/generate_urdf.py
├── frontend/src/
│   ├── components/        # RobotViewer, charts, controls, …
│   ├── pages/             # 13 pages
│   ├── services/          # api.ts, websocket.ts (only network access)
│   ├── store/             # zustand stores
│   └── hooks/             # useSimulationSocket
├── robot/
│   ├── urdf/sv2_6045.urdf # kinematically identical to the DH model
│   └── meshes/            # primitive shapes, no external meshes
└── docs/
    ├── architecture/      # system_architecture.md
    └── formulas/          # dh, ik, trajectory, dynamics, draw_h
```

---

## Key design points

- **Draw H is real computation** — corner points → linear Cartesian path →
  IK per sample → joint trajectory → FK validation → 3D animation. No fakes,
  no hard-coded results.
- **IK is FK-validated** — every returned solution carries its achieved
  position/orientation error.
- **Torque decomposition is exact** — the component sum equals the direct RNE
  evaluation to ~1e-14 N·m (asserted in tests).
- **URDF matches the DH model** — verified identical over 500 random
  configurations (error < 1e-9 m).
- **Clean error handling** — unreachable targets and limit violations return
  typed JSON errors surfaced verbatim in the UI.

See `docs/architecture/system_architecture.md` for the full architecture and
`docs/formulas/` for the mathematical reference.

---

## Honesty & provenance

- Official APE specs are cited with source and treated as ground truth.
- All DH / mass / inertia values are labelled **"Educational / Assumed"** in
  the API, the DH page, the Settings page, the Overview, and the docs.
- Swapping in real parameters requires editing one file:
  `backend/app/models/ape_sv45.py`.

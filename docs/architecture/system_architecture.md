# APE SV2-6045 Robot Simulator — System Architecture

## 1. Overview

```
┌───────────────────────────────  Browser  ───────────────────────────────┐
│  React 19 + TypeScript + Vite                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Pages (13)  │  │ RobotViewer  │  │ Plotly charts│  │ Zustand store│  │
│  │             │  │ (R3F/drei)   │  │              │  │              │  │
│  └──────┬──────┘  └──────▲───────┘  └──────▲───────┘  └──────▲───────┘  │
│         │ services/api.ts (REST)    30 Hz frame stream          │        │
└─────────┼────────────────────────────┼──────────────────────────┼───────┘
          │ HTTP (proxied /api/*)      │ WebSocket /ws/simulation │
┌─────────▼────────────────────────────┼──────────────────────────┼───────┐
│  FastAPI  (uvicorn, port 8000)       │                          │        │
│  ┌──────────────┐   ┌───────────────────────────────┐   ┌────────────┐  │
│  │ REST routers │   │ simulation.engine  (~30 Hz)   │   │ state      │  │
│  │ /api/robot   │   │ time-stepping, pause/resume   │   │ (global)   │  │
│  │ /api/fk …    │   └───────────────┬───────────────┘   └────────────┘  │
│  └──────┬───────┘                   │                                    │
│         ▼                           ▼                                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ robotics core (pure NumPy + Robotics Toolbox for Python)           │  │
│  │ dh · robot · kinematics · inverse_kinematics · workspace           │  │
│  │ trajectory · dynamics · validation · draw_h                        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  models/ape_sv45.py  ← single source of parameters (SI units)            │
└──────────────────────────────────────────────────────────────────────────┘
```

## 2. Backend (Python)

| Module | Responsibility |
|---|---|
| `models/ape_sv45.py` | DH table (educational), official joint limits/speeds, educational dynamic model, official specs. **Only file that contains robot numbers.** |
| `models/parameters.py` | Runtime parameter store — allows DH editing/validation/reset. |
| `robotics/dh.py` | Standard-DH transforms, frame chains (NumPy). |
| `robotics/robot.py` | Robotics Toolbox `DHRobot` construction (dynamics, rne). |
| `robotics/kinematics.py` | Forward kinematics, Jacobian, orientations. |
| `robotics/inverse_kinematics.py` | Numeric IK (multi-start Levenberg–Marquardt), warm start, alternative-configuration search, FK validation of solutions. |
| `robotics/workspace.py` | Monte-Carlo workspace sampling + bounds. |
| `robotics/trajectory.py` | Cubic/quintic joint polynomials, timed Cartesian path planning with IK per sample. |
| `robotics/dynamics.py` | Inverse dynamics (RNE) + torque decomposition (inertia / Coriolis / gravity / friction). |
| `robotics/validation.py` | Joint-limit, velocity and continuity checks. |
| `robotics/draw_h.py` | H-letter Cartesian path generation with pen up/down, family transitions and retrace blending. |
| `simulation/engine.py` | Time-stepping playback engine driving the WebSocket stream. |
| `api/*.py` | FastAPI routers; unit conversion at the API edge (mm/deg ↔ m/rad). |

### Unit convention
All internal computation is **SI** (metres, radians, seconds, N·m). The API
converts at its edge and the frontend always displays **mm and degrees**.

### Error handling
Domain errors (unreachable target, limit violation, workspace miss…) are raised
as typed exceptions and mapped to clean JSON `{"error_code", "message"}`
responses by global handlers — the frontend surfaces them verbatim.

## 3. Frontend (React)

- **Routing**: React Router — 13 pages (Overview, Dashboard, DH Model, Robot
  Control, FK, IK, Workspace, Trajectory, Motion Analysis, Dynamics, Draw H,
  Documentation, Settings).
- **State**: three Zustand stores — `robotStore` (robot info, DH, joints,
  workspace), `simulationStore` (active trajectory, sim status), and
  `livePose` (mutable per-frame pose channel read inside `useFrame` — the
  30 Hz stream never triggers React re-renders).
- **3D**: React-Three-Fiber + drei. The arm is rendered from the DH parameters
  (cylinders sized by link lengths, joint groups rotated by the live pose) —
  the browser never computes kinematics; it only visualizes backend results.
- **Charts**: Plotly (line charts for q/q̇/q̈/τ with per-joint selection).
- **Services**: `services/api.ts` and `services/websocket.ts` are the only
  places that touch the network. Components never call `fetch` directly.

### Real-time path
`SimulationControls` sends `{type: start|pause|resume|stop}` over
`/ws/simulation`. The engine steps the active trajectory at ~30 Hz and pushes
`frame` messages `{time, progress, q_deg, position, ee}`. The viewer reads the
shared `livePose` object inside `useFrame`, so animation stays smooth
independently of React's render cycle.

## 4. Draw H pipeline (real computation, no fakes)

```
H corners (XY plane)
  → linear Cartesian path with pen up/down segments
  → IK per sample (warm-started; family transition by pen-up retrace + blend)
  → joint trajectory q(t)
  → FK validation of every sample (position error ≤ 0.5 mm)
  → playback engine → 3D animation of the arm drawing the H
```

## 5. Deployment / development

```
backend:  uvicorn app.main:app --port 8000
frontend: npm run dev  (Vite proxies /api/* and /ws/* to :8000)
tests:    cd backend && pytest            # 58 tests
```

Production: `npm run build` produces a static bundle; serve it behind any
reverse proxy that forwards `/api` and `/ws` to the FastAPI service.

## 6. Design constraints honored

- Simulation only — no hardware control anywhere in the code base.
- Educational DH/dynamics parameters are labelled *"Educational / Assumed"*
  everywhere they surface (API responses, DH page, Settings, Overview).
- Official APE specs (reach, limits, speeds, repeatability) are the only
  "factory" data and are cited with their source.
- No hard-coded results: every displayed number is computed by the engine at
  request time.

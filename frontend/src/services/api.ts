import type { DHTable, FKResult, IKResult, RobotInfo } from '../types/robot';
import type {
  SimulationStatus,
  TrajectoryResult,
  WorkspaceResult,
} from '../types/trajectory';
import type { DynamicsResult } from '../types/dynamics';

/**
 * Central API service.  Components never call fetch directly (spec §47);
 * all backend traffic goes through these typed wrappers using relative URLs
 * (the Vite dev server proxies /api and /ws to the FastAPI backend).
 */

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === 'string') detail = body.detail;
    } catch {
      /* keep default message */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) });

/* ----------------------------- robot / state ---------------------------- */

export const getRobot = () => request<RobotInfo>('/api/robot');

export const setRobotState = (qDeg: number[]) =>
  post<{ q_deg: number[]; q_rad: number[]; end_effector: FKResult }>(
    '/api/robot/state',
    { q: qDeg, unit: 'deg' },
  );

export const robotPreset = (preset: 'home' | 'zero') =>
  post<{ q_deg: number[]; end_effector: FKResult }>('/api/robot/preset', {
    preset,
  });

/* --------------------------------- DH ----------------------------------- */

export const getDH = () => request<DHTable>('/api/dh');

export const applyDH = (links: { d: number; a: number; alpha: number }[]) =>
  post<DHTable>('/api/dh/apply', { links });

export const resetDH = () => post<DHTable>('/api/dh/reset');

export const exportDHUrl = (format: 'csv' | 'json') =>
  `/api/dh/export?format=${format}`;

/* ------------------------------ kinematics ------------------------------ */

export const computeFK = (qDeg: number[]) =>
  post<FKResult>('/api/fk', { q: qDeg, unit: 'deg' });

export const computeIK = (
  position: { x: number; y: number; z: number },
  orientation: { roll: number; pitch: number; yaw: number },
  qGuessDeg?: number[],
) =>
  post<IKResult>('/api/ik', {
    position,
    orientation,
    q_guess: qGuessDeg ? { q: qGuessDeg, unit: 'deg' } : null,
  });

/* ------------------------------- workspace ------------------------------ */

export const generateWorkspace = (samples: number, seed = 42) =>
  post<WorkspaceResult>('/api/workspace', { samples, seed });

/* ------------------------------- trajectory ----------------------------- */

export const planJointTrajectory = (body: {
  q0: number[];
  qf: number[];
  duration: number;
  samples: number;
  method: 'cubic' | 'quintic';
}) => post<TrajectoryResult>('/api/trajectory/joint', body);

export const planCartesianTrajectory = (body: {
  points: { x: number; y: number; z: number; t: number }[];
  orientation?: { roll: number; pitch: number; yaw: number } | null;
  dt?: number;
}) => post<TrajectoryResult>('/api/trajectory/cartesian', body);

/* -------------------------------- dynamics ------------------------------ */

export const computeDynamics = (trajectoryId?: string) =>
  post<DynamicsResult>('/api/dynamics', {
    trajectory_id: trajectoryId ?? null,
  });

/* --------------------------------- Draw H ------------------------------- */

export const generateDrawH = (body: {
  plane?: 'XY' | 'XZ' | 'YZ';
  width: number;
  height: number;
  drawing_height: number;
  speed: number;
  center?: { x: number; y: number; z: number };
  lift?: number;
}) => post<TrajectoryResult>('/api/draw/h', { plane: 'XY', ...body });

/* ------------------------------- simulation ----------------------------- */

export const simStart = (trajectoryId?: string, speed = 1) =>
  post<SimulationStatus>('/api/simulation/start', {
    trajectory_id: trajectoryId ?? null,
    speed,
  });

export const simStop = () => post<SimulationStatus>('/api/simulation/stop');
export const simPause = () => post<SimulationStatus>('/api/simulation/pause');
export const simResume = () => post<SimulationStatus>('/api/simulation/resume');
export const getSimulation = () =>
  request<SimulationStatus>('/api/simulation');

/* --------------------------------- export ------------------------------- */

export const exportTrajectoryUrl = (trajectoryId: string, format: 'csv' | 'json') =>
  `/api/export/trajectory?trajectory_id=${trajectoryId}&format=${format}`;

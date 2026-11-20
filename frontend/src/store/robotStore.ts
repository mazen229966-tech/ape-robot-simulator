import { create } from 'zustand';

import * as api from '../services/api';
import type { DHTable, FKResult, RobotInfo, RobotStatus } from '../types/robot';
import type { WorkspaceResult } from '../types/trajectory';
import { livePose, setLivePose } from './livePose';

export type ViewPresetName = '3d' | 'top' | 'side' | 'front';

interface RobotStore {
  info: RobotInfo | null;
  qDeg: number[];
  ee: FKResult | null;
  status: RobotStatus;
  errorMsg: string | null;
  loaded: boolean;
  busy: boolean;

  // viewer options
  showFrames: boolean;
  showGrid: boolean;
  showWorkspace: boolean;
  showTrajectory: boolean;
  showAxes: boolean;

  workspace: WorkspaceResult | null;
  dhTable: DHTable | null;
  viewPreset: { name: ViewPresetName; nonce: number };

  fetchRobot: () => Promise<void>;
  fetchDH: () => Promise<void>;
  setJoints: (qDeg: number[]) => Promise<void>;
  preset: (name: 'home' | 'zero') => Promise<void>;
  applyFK: (res: FKResult) => void;
  setStatus: (s: RobotStatus, error?: string | null) => void;
  setBusy: (b: boolean) => void;
  toggle: (key: 'showFrames' | 'showGrid' | 'showWorkspace' | 'showTrajectory' | 'showAxes') => void;
  setViewPreset: (name: ViewPresetName) => void;
  setWorkspace: (ws: WorkspaceResult | null) => void;
}

function degToRad(deg: number[]): number[] {
  return deg.map((d) => (d * Math.PI) / 180);
}

export const useRobotStore = create<RobotStore>((set, get) => ({
  info: null,
  qDeg: [0, 0, 0, 0, 0, 0],
  ee: null,
  status: 'READY',
  errorMsg: null,
  loaded: false,
  busy: false,

  showFrames: false,
  showGrid: true,
  showWorkspace: false,
  showTrajectory: true,
  showAxes: true,

  workspace: null,
  dhTable: null,
  viewPreset: { name: '3d', nonce: 0 },

  fetchRobot: async () => {
    try {
      const info = await api.getRobot();
      setLivePose(degToRad(info.state.q_deg), info.state.end_effector.position);
      set({
        info,
        qDeg: info.state.q_deg,
        ee: info.state.end_effector,
        loaded: true,
        status: 'READY',
        errorMsg: null,
      });
    } catch (err) {
      set({
        loaded: true,
        status: 'ERROR',
        errorMsg: err instanceof Error ? err.message : 'Backend unreachable',
      });
    }
  },

  fetchDH: async () => {
    const dh = await api.getDH();
    set({ dhTable: dh });
  },

  setJoints: async (qDeg: number[]) => {
    const { info } = get();
    const limits = info?.joint_limits_deg;
    const clamped = limits
      ? qDeg.map((v, i) => Math.min(Math.max(v, limits[i][0]), limits[i][1]))
      : qDeg;
    // immediate visual feedback, confirmed by the backend response
    setLivePose(degToRad(clamped));
    set({ qDeg: clamped });
    try {
      const res = await api.setRobotState(clamped);
      set({
        qDeg: res.q_deg,
        ee: res.end_effector,
        status: 'READY',
        errorMsg: null,
      });
      setLivePose(degToRad(res.q_deg), res.end_effector.position);
    } catch (err) {
      set({
        status: 'ERROR',
        errorMsg: err instanceof Error ? err.message : 'State update failed',
      });
    }
  },

  preset: async (name) => {
    try {
      const res = await api.robotPreset(name);
      setLivePose(degToRad(res.q_deg), res.end_effector.position);
      set({ qDeg: res.q_deg, ee: res.end_effector, status: 'READY', errorMsg: null });
    } catch (err) {
      set({
        status: 'ERROR',
        errorMsg: err instanceof Error ? err.message : 'Preset failed',
      });
    }
  },

  applyFK: (res: FKResult) => {
    setLivePose(degToRad(res.q_deg), res.position);
    set({ qDeg: res.q_deg, ee: res, status: 'READY', errorMsg: null });
  },

  setStatus: (status, error = null) => set({ status, errorMsg: error }),
  setBusy: (busy) => set({ busy }),

  toggle: (key) => set((s) => ({ [key]: !s[key] }) as Partial<RobotStore>),

  setViewPreset: (name) =>
    set((s) => ({ viewPreset: { name, nonce: s.viewPreset.nonce + 1 } })),

  setWorkspace: (workspace) => set({ workspace, showWorkspace: workspace !== null }),
}));

/** Current end-effector helper for displays. */
export function formatEE(ee: FKResult | null): string {
  if (!ee) return '--';
  const p = ee.position_mm ?? {
    x: ee.position.x * 1000,
    y: ee.position.y * 1000,
    z: ee.position.z * 1000,
  };
  return `X ${p.x.toFixed(1)}  Y ${p.y.toFixed(1)}  Z ${p.z.toFixed(1)} mm`;
}

export { livePose };

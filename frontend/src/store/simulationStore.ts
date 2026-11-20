import { create } from 'zustand';

import type { SimulationStatus, TrajectoryResult } from '../types/trajectory';
import { setLivePose } from './livePose';

interface SimulationStore {
  trajectory: TrajectoryResult | null;
  trajectoryLabel: string;
  simStatus: SimulationStatus['status'];
  simTime: number;
  progress: number;
  wsConnected: boolean;
  penDownNow: boolean;

  setTrajectory: (traj: TrajectoryResult | null, label?: string) => void;
  setSimStatus: (s: SimulationStatus['status']) => void;
  setConnected: (c: boolean) => void;
  applyFrame: (f: {
    time: number;
    duration: number;
    progress: number;
    q_rad: number[];
    q_deg: number[];
    position: { x: number; y: number; z: number };
    status: string;
  }) => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  trajectory: null,
  trajectoryLabel: '',
  simStatus: 'idle',
  simTime: 0,
  progress: 0,
  wsConnected: false,
  penDownNow: false,

  setTrajectory: (trajectory, label = '') =>
    set({
      trajectory,
      trajectoryLabel: label,
      simTime: 0,
      progress: 0,
      penDownNow: false,
    }),

  setSimStatus: (status) => set({ simStatus: status }),
  setConnected: (wsConnected) => set({ wsConnected }),

  applyFrame: (f) => {
    setLivePose(f.q_rad, f.position);
    const { trajectory } = get();
    let penDownNow = false;
    if (trajectory?.pen_down && trajectory.t.length > 0) {
      const idx = Math.min(
        trajectory.t.length - 1,
        Math.max(0, Math.round(f.progress * (trajectory.t.length - 1))),
      );
      penDownNow = trajectory.pen_down[idx];
    }
    set({
      simTime: f.time,
      progress: f.progress,
      penDownNow,
      simStatus:
        f.status === 'running'
          ? 'running'
          : f.status === 'paused'
            ? 'paused'
            : (f.status as SimulationStatus['status']),
    });
  },
}));

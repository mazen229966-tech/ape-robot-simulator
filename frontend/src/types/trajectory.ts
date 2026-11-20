export interface TrajectoryPhase {
  phase: string;
  pen_down: boolean;
  t_start: number;
  t_end: number;
  index_start: number;
  index_end: number;
}

export interface TransitionSpan {
  index_start: number;
  index_end: number;
}

export interface TrajectoryResult {
  trajectory_id: string;
  method: string;
  space: string;
  samples: number;
  duration: number;
  dt: number;
  t: number[];
  /** joint positions [samples][6] in radians */
  q: number[][];
  /** joint velocities [samples][6] in rad/s */
  qd: number[][];
  /** joint accelerations [samples][6] in rad/s^2 */
  qdd: number[][];
  /** end-effector path [samples][3] in metres */
  ee_path: number[][];
  ee_path_length: number;
  /* Draw-H extras */
  pen_down?: boolean[];
  phases?: TrajectoryPhase[];
  transitions?: TransitionSpan[];
  draw_distance?: number;
  corners?: Record<string, number[]>;
  plane?: 'XY' | 'XZ' | 'YZ';
  plane_offset?: number;
  drawing_plane_z?: number;
}

export interface WorkspaceResult {
  samples: number;
  valid_samples: number;
  displayed_points: number;
  /** flat x,y,z,... point cloud in millimetres */
  points_mm: number[];
  bounds_mm: Record<string, number>;
  reach_mm: number;
}

export interface SimulationStatus {
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'done';
  trajectory_id: string | null;
  speed: number;
  time: number;
  duration: number;
}

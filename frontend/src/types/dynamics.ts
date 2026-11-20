export interface JointTorqueStat {
  joint: number;
  max_abs_torque_nm: number;
  rms_torque_nm: number;
  peak_torque_nm: number;
}

export type TorqueComponent =
  | 'inertia'
  | 'coriolis'
  | 'gravity'
  | 'friction'
  | 'total';

export interface DynamicsResult {
  t: number[];
  components: Record<TorqueComponent, number[][]>;
  stats: { per_joint: JointTorqueStat[] };
  rne_discrepancy_nm: number;
  parameter_source: string;
}

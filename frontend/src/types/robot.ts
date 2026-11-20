export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export interface Orientation {
  roll: number;
  pitch: number;
  yaw: number;
}

export interface FKResult {
  q_deg: number[];
  position: Vec3;
  position_mm: Vec3;
  orientation: Orientation;
  transform: number[][];
}

export interface RobotStateResponse {
  q_deg: number[];
  q_rad: number[];
  end_effector: FKResult;
}

export interface OfficialSpecs {
  manufacturer: string;
  model: string;
  type: string;
  dof: number;
  payload_rated_kg: number;
  payload_max_kg: number;
  max_radius_m: number;
  repeatability_mm: number;
  body_weight_kg: number;
  max_tcp_speed_m_s: number;
  installation: string;
  drive: string;
  encoder: string;
  protection: string;
  noise_db: number;
  joint_speeds_deg_s: number[];
  source: string;
}

export interface RobotInfo {
  name: string;
  manufacturer: string;
  dof: number;
  official_specs: OfficialSpecs;
  joint_limits_deg: [number, number][];
  joint_speeds_deg_s: number[];
  home_position_deg: number[];
  kinematic_parameter_source: string;
  dynamic_parameter_source: string;
  gravity_m_s2: number;
  state: RobotStateResponse;
}

export interface IKResult {
  q_deg: number[];
  q_rad: number[];
  position_error_mm: number;
  orientation_error_deg: number;
  valid: boolean;
  fk_validation: {
    position: Vec3;
    orientation: Orientation;
  };
}

export interface DHRow {
  i: number;
  theta: string;
  joint_type: string;
  d_m: number;
  a_m: number;
  alpha_rad: number;
  d_mm: number;
  a_mm: number;
  alpha_deg: number;
}

export interface DHTable {
  convention: string;
  transform_formula: string;
  units: Record<string, string>;
  parameter_source: string;
  links: DHRow[];
}

export type RobotStatus = 'READY' | 'RUNNING' | 'STOPPED' | 'ERROR';

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line, Text } from '@react-three/drei';
import * as THREE from 'three';

import { livePose } from '../../store/livePose';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

/** Grid + labelled base axes (X, Y, Z written per spec §35). */
export function SceneEnvironment() {
  const showGrid = useRobotStore((s) => s.showGrid);
  const showAxes = useRobotStore((s) => s.showAxes);
  return (
    <group>
      {showGrid && (
        <gridHelper
          args={[2.4, 24, '#2b3c50', '#1a2634']}
          position={[0, 0, -0.001]}
        />
      )}
      {/* ground disc */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -0.003]}>
        <circleGeometry args={[1.2, 64]} />
        <meshStandardMaterial color="#0d1319" metalness={0.1} roughness={0.95} />
      </mesh>
      {showAxes && (
        <group>
          <Line points={[[0, 0, 0], [0.55, 0, 0]]} color="#f87171" lineWidth={1.6} />
          <Line points={[[0, 0, 0], [0, 0.55, 0]]} color="#34d399" lineWidth={1.6} />
          <Line points={[[0, 0, 0], [0, 0, 0.55]]} color="#60a5fa" lineWidth={1.6} />
          <Text position={[0.6, 0, 0]} fontSize={0.045} color="#f87171">X</Text>
          <Text position={[0, 0.6, 0]} fontSize={0.045} color="#34d399">Y</Text>
          <Text position={[0, 0, 0.6]} fontSize={0.045} color="#60a5fa">Z</Text>
        </group>
      )}
    </group>
  );
}

/** Workspace point cloud computed on the backend (mm -> m). */
export function WorkspaceCloud() {
  const workspace = useRobotStore((s) => s.workspace);
  const show = useRobotStore((s) => s.showWorkspace);

  const geometry = useMemo(() => {
    if (!workspace) return null;
    const n = workspace.points_mm.length / 3;
    const positions = new Float32Array(n * 3);
    const colors = new Float32Array(n * 3);
    const c = new THREE.Color();
    let zMin = Infinity;
    let zMax = -Infinity;
    for (let i = 0; i < n; i += 1) zMin = Math.min(zMin, workspace.points_mm[i * 3 + 2]);
    for (let i = 0; i < n; i += 1) zMax = Math.max(zMax, workspace.points_mm[i * 3 + 2]);
    for (let i = 0; i < n; i += 1) {
      positions[i * 3] = workspace.points_mm[i * 3] / 1000;
      positions[i * 3 + 1] = workspace.points_mm[i * 3 + 1] / 1000;
      positions[i * 3 + 2] = workspace.points_mm[i * 3 + 2] / 1000;
      const h = (workspace.points_mm[i * 3 + 2] - zMin) / Math.max(1e-9, zMax - zMin);
      c.setHSL(0.55 - 0.35 * h, 0.75, 0.55);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    return g;
  }, [workspace]);

  if (!show || !geometry) return null;
  return (
    <points geometry={geometry}>
      <pointsMaterial size={0.0045} vertexColors transparent opacity={0.55} sizeAttenuation />
    </points>
  );
}

/** End-effector path of the active trajectory + live tracer. */
export function EEPath() {
  const trajectory = useSimulationStore((s) => s.trajectory);
  const show = useRobotStore((s) => s.showTrajectory);
  const tracer = useRef<THREE.Mesh>(null);

  const points = useMemo(() => {
    if (!trajectory) return null;
    // decimate for rendering performance
    const step = Math.max(1, Math.floor(trajectory.ee_path.length / 600));
    const pts: [number, number, number][] = [];
    for (let i = 0; i < trajectory.ee_path.length; i += step) {
      const p = trajectory.ee_path[i];
      pts.push([p[0], p[1], p[2]]);
    }
    return pts.length >= 2 ? pts : null;
  }, [trajectory]);

  useFrame(() => {
    if (!tracer.current) return;
    const simStatus = useSimulationStore.getState().simStatus;
    const active = simStatus === 'running' || simStatus === 'paused' || simStatus === 'done';
    tracer.current.visible = active;
    if (active) {
      // tracer follows the live pose (set by the WebSocket frame handler)
      tracer.current.position.set(livePose.ee.x, livePose.ee.y, livePose.ee.z);
    }
  });

  if (!show) return null;
  return (
    <group>
      {points && (
        <Line points={points} color="#38bdf8" lineWidth={1.5} transparent opacity={0.8} />
      )}
      <mesh ref={tracer} visible={false}>
        <sphereGeometry args={[0.009, 16, 16]} />
        <meshBasicMaterial color="#fbbf24" />
      </mesh>
    </group>
  );
}

/** Drawing plane hint shown for Draw-H trajectories (XY / XZ / YZ). */
export function DrawingPlane() {
  const trajectory = useSimulationStore((s) => s.trajectory);
  if (!trajectory?.drawing_plane_z || trajectory.method !== 'draw-h') return null;
  const plane = trajectory.plane ?? 'XY';
  const corners = Object.values(trajectory.corners ?? {});
  if (corners.length !== 6) return null;

  const xs = corners.map((c) => c[0]);
  const ys = corners.map((c) => c[1]);
  const zs = corners.map((c) => c[2]);
  const mid = (v: number[]) => (Math.min(...v) + Math.max(...v)) / 2;
  const span = (v: number[]) => Math.max(...v) - Math.min(...v) + 0.1;

  const PAD = 0.002; // pull the hint slightly off the surface
  if (plane === 'XY') {
    const z = trajectory.plane_offset ?? trajectory.drawing_plane_z;
    return (
      <mesh position={[mid(xs), mid(ys), z - PAD]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[span(xs), span(ys)]} />
        <meshBasicMaterial color="#173a52" transparent opacity={0.4} side={THREE.DoubleSide} />
      </mesh>
    );
  }
  if (plane === 'XZ') {
    const y = trajectory.plane_offset ?? mid(ys);
    const off = y >= 0 ? -PAD : PAD;
    return (
      <mesh position={[mid(xs), y + off, mid(zs)]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[span(zs), span(xs)]} />
        <meshBasicMaterial color="#173a52" transparent opacity={0.4} side={THREE.DoubleSide} />
      </mesh>
    );
  }
  // YZ
  const x = trajectory.plane_offset ?? mid(xs);
  const off = x >= 0 ? -PAD : PAD;
  return (
    <mesh position={[x + off, mid(ys), mid(zs)]} rotation={[0, 0, 0]}>
      <planeGeometry args={[span(ys), span(zs)]} />
      <meshBasicMaterial color="#173a52" transparent opacity={0.4} side={THREE.DoubleSide} />
    </mesh>
  );
}

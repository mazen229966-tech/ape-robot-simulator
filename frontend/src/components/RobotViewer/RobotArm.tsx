import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';

import type { DHRow } from '../../types/robot';
import { livePose } from '../../store/livePose';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

const METAL = '#8fa8bd';
const DARK = '#33455c';
const ACCENT = '#38bdf8';
const JOINT = '#1f2d3d';

interface FrameProps {
  index: number;
  show: boolean;
}

/** Coordinate frame widget with {i} label (DH frame visualisation). */
function FrameMarker({ index, show }: FrameProps) {
  if (!show) return null;
  return (
    <group>
      <axesHelper args={[0.085]} />
      <Text
        position={[0.02, 0.02, 0.05]}
        fontSize={0.03}
        color={ACCENT}
        anchorX="left"
      >
        {`{${index}}`}
      </Text>
    </group>
  );
}

/**
 * DH-driven parametric robot arm.
 *
 * The visual geometry is an approximation built from the SAME link
 * parameters as the mathematical model (a_i, d_i, alpha_i) -- joints rotate
 * about the DH z-axes exactly as the backend computes them.  It is clearly
 * not official APE CAD geometry.
 */
export default function RobotArm() {
  const dh = useRobotStore((s) => s.dhTable);
  const showFrames = useRobotStore((s) => s.showFrames);

  // joint group refs, one per DOF
  const joints = useRef<(THREE.Group | null)[]>([]);
  const penGlow = useRef<THREE.Mesh>(null);
  const lastVersion = useRef(-1);

  useFrame(() => {
    if (livePose.version === lastVersion.current) return;
    lastVersion.current = livePose.version;
    for (let i = 0; i < 6; i += 1) {
      const g = joints.current[i];
      if (g) g.rotation.z = livePose.qRad[i];
    }
  });

  // pen contact glow follows the pen-down state during drawing
  useFrame(() => {
    if (!penGlow.current) return;
    const penDown = useSimulationStore.getState().penDownNow;
    const running = useSimulationStore.getState().simStatus === 'running';
    penGlow.current.visible = penDown && running;
  });

  const rows: DHRow[] | null = dh?.links ?? null;

  const dims = useMemo(() => {
    if (!rows) return null;
    return {
      d1: rows[0].d_m,
      a1: rows[0].a_m,
      alpha1: rows[0].alpha_rad,
      a2: rows[1].a_m,
      alpha2: rows[1].alpha_rad,
      a3: rows[2].a_m,
      alpha3: rows[2].alpha_rad,
      d4: rows[3].d_m,
      alpha4: rows[3].alpha_rad,
      d5: rows[4].d_m,
      alpha5: rows[4].alpha_rad,
      d6: rows[5].d_m,
    };
  }, [rows]);

  if (!dims) return null;

  return (
    <group>
      {/* base plate */}
      <mesh position={[0, 0, 0.012]}>
        <cylinderGeometry args={[0.11, 0.13, 0.024, 40]} />
        <meshStandardMaterial color={DARK} metalness={0.55} roughness={0.5} />
      </mesh>
      <FrameMarker index={0} show={showFrames} />

      {/* J1 */}
      <group ref={(g) => { joints.current[0] = g; }}>
        <mesh position={[0, 0, dims.d1 / 2 + 0.02]}>
          <cylinderGeometry args={[0.056, 0.068, dims.d1 + 0.02, 32]} />
          <meshStandardMaterial color={METAL} metalness={0.6} roughness={0.35} />
        </mesh>
        <group
          position={[dims.a1, 0, dims.d1]}
          rotation={[dims.alpha1, 0, 0]}
        >
          <FrameMarker index={1} show={showFrames} />

          {/* J2 */}
          <group ref={(g) => { joints.current[1] = g; }}>
            <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[0.052, 0.052, 0.11, 32]} />
              <meshStandardMaterial color={JOINT} metalness={0.5} roughness={0.45} />
            </mesh>
            {/* upper arm */}
            <mesh position={[dims.a2 / 2, 0, 0.01]}>
              <boxGeometry args={[dims.a2, 0.052, 0.062]} />
              <meshStandardMaterial color={METAL} metalness={0.6} roughness={0.35} />
            </mesh>
            <group
              position={[dims.a2, 0, 0]}
              rotation={[dims.alpha2, 0, 0]}
            >
              <FrameMarker index={2} show={showFrames} />

              {/* J3 */}
              <group ref={(g) => { joints.current[2] = g; }}>
                <mesh rotation={[Math.PI / 2, 0, 0]}>
                  <cylinderGeometry args={[0.044, 0.044, 0.095, 32]} />
                  <meshStandardMaterial color={JOINT} metalness={0.5} roughness={0.45} />
                </mesh>
                {/* forearm */}
                <mesh position={[dims.a3 / 2, 0, 0]}>
                  <boxGeometry args={[dims.a3, 0.042, 0.05]} />
                  <meshStandardMaterial color={METAL} metalness={0.6} roughness={0.35} />
                </mesh>
                <group
                  position={[dims.a3, 0, 0]}
                  rotation={[dims.alpha3, 0, 0]}
                >
                  <FrameMarker index={3} show={showFrames} />

                  {/* J4 */}
                  <group ref={(g) => { joints.current[3] = g; }}>
                    <mesh position={[0, 0, dims.d4 / 2]}>
                      <cylinderGeometry args={[0.033, 0.038, dims.d4, 28]} />
                      <meshStandardMaterial color={METAL} metalness={0.6} roughness={0.35} />
                    </mesh>
                    <group
                      position={[0, 0, dims.d4]}
                      rotation={[dims.alpha4, 0, 0]}
                    >
                      <FrameMarker index={4} show={showFrames} />

                      {/* J5 */}
                      <group ref={(g) => { joints.current[4] = g; }}>
                        <mesh>
                          <sphereGeometry args={[0.032, 28, 28]} />
                          <meshStandardMaterial color={JOINT} metalness={0.5} roughness={0.45} />
                        </mesh>
                        <group
                          position={[0, 0, dims.d5]}
                          rotation={[dims.alpha5, 0, 0]}
                        >
                          <FrameMarker index={5} show={showFrames} />

                          {/* J6 + tool */}
                          <group ref={(g) => { joints.current[5] = g; }}>
                            <mesh position={[0, 0, dims.d6 / 2]}>
                              <cylinderGeometry args={[0.021, 0.026, dims.d6, 24]} />
                              <meshStandardMaterial color={METAL} metalness={0.6} roughness={0.35} />
                            </mesh>
                            <group position={[0, 0, dims.d6]}>
                              <FrameMarker index={6} show={showFrames} />
                              {/* pen tool: tip at the TCP, body along -z6 */}
                              <mesh position={[0, 0, -0.028]}>
                                <cylinderGeometry args={[0.006, 0.006, 0.045, 16]} />
                                <meshStandardMaterial color="#d9e2ec" metalness={0.3} roughness={0.4} />
                              </mesh>
                              <mesh position={[0, 0, -0.055]} rotation={[Math.PI, 0, 0]}>
                                <coneGeometry args={[0.006, 0.012, 16]} />
                                <meshStandardMaterial color={ACCENT} metalness={0.2} roughness={0.35} />
                              </mesh>
                              {/* contact glow */}
                              <mesh ref={penGlow} visible={false}>
                                <sphereGeometry args={[0.011, 16, 16]} />
                                <meshBasicMaterial color="#fbbf24" transparent opacity={0.85} />
                              </mesh>
                              {/* EE marker */}
                              <mesh>
                                <sphereGeometry args={[0.007, 16, 16]} />
                                <meshBasicMaterial color={ACCENT} />
                              </mesh>
                            </group>
                          </group>
                        </group>
                      </group>
                    </group>
                  </group>
                </group>
              </group>
            </group>
          </group>
        </group>
      </group>
    </group>
  );
}

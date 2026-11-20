import { Suspense, useEffect, useRef, type ComponentRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

import { useRobotStore, type ViewPresetName } from '../../store/robotStore';
import RobotArm from './RobotArm';
import { DrawingPlane, EEPath, SceneEnvironment, WorkspaceCloud } from './SceneExtras';
import './RobotViewer.css';

type OrbitControlsImpl = ComponentRef<typeof OrbitControls>;

const PRESETS: Record<ViewPresetName, { pos: [number, number, number]; target: [number, number, number] }> = {
  // world coordinates: three.js Y-up.  Robot z = world y, robot y = world -z.
  '3d': { pos: [0.95, 0.72, 0.95], target: [0.18, 0.22, 0] },
  top: { pos: [0.18, 1.7, 0.0001], target: [0.18, 0, 0] },
  front: { pos: [1.9, 0.36, 0.0001], target: [0.1, 0.28, 0] },
  side: { pos: [0.18, 0.36, 1.9], target: [0.18, 0.28, 0] },
};

function CameraRig({ controls }: { controls: React.RefObject<OrbitControlsImpl | null> }) {
  const viewPreset = useRobotStore((s) => s.viewPreset);
  const applied = useRef(-1);

  useEffect(() => {
    if (viewPreset.nonce === applied.current) return;
    applied.current = viewPreset.nonce;
    const ctl = controls.current;
    if (!ctl) return;
    const { pos, target } = PRESETS[viewPreset.name];
    ctl.object.position.set(pos[0], pos[1], pos[2]);
    ctl.target.set(target[0], target[1], target[2]);
    ctl.update();
  }, [viewPreset, controls]);

  return null;
}

interface Props {
  height?: number | string;
}

/**
 * The shared 3D robot scene (spec §17).  Every page that needs the robot
 * renders this viewer; all pages see the SAME robot state because the pose
 * comes from the shared live-pose channel fed by the backend.
 */
export default function RobotViewer({ height = 420 }: Props) {
  const controls = useRef<OrbitControlsImpl | null>(null);
  const setViewPreset = useRobotStore((s) => s.setViewPreset);
  const viewPreset = useRobotStore((s) => s.viewPreset);
  const showFrames = useRobotStore((s) => s.showFrames);
  const showWorkspace = useRobotStore((s) => s.showWorkspace);
  const showTrajectory = useRobotStore((s) => s.showTrajectory);
  const workspace = useRobotStore((s) => s.workspace);
  const toggle = useRobotStore((s) => s.toggle);

  return (
    <div className="viewer-wrap" style={{ height }}>
      <Canvas
        camera={{ fov: 42, position: PRESETS['3d'].pos, near: 0.01, far: 50 }}
        dpr={[1, 2]}
      >
        <color attach="background" args={['#0b0f14']} />
        <ambientLight intensity={0.55} />
        <hemisphereLight args={['#b8d4ea', '#0b0f14', 0.5]} />
        <directionalLight position={[2, 3, 1.5]} intensity={1.15} />
        <directionalLight position={[-1.5, 1, -1]} intensity={0.35} />
        <Suspense fallback={null}>
          {/* robot lives in a z-up frame */}
          <group rotation={[-Math.PI / 2, 0, 0]}>
            <SceneEnvironment />
            <RobotArm />
            <WorkspaceCloud />
            <EEPath />
            <DrawingPlane />
          </group>
        </Suspense>
        <OrbitControls
          ref={controls}
          makeDefault
          enableDamping
          dampingFactor={0.12}
          minDistance={0.25}
          maxDistance={5}
        />
        <CameraRig controls={controls} />
      </Canvas>

      <div className="viewer-toolbar">
        <div className="btn-row">
          {(['3d', 'top', 'side', 'front'] as ViewPresetName[]).map((name) => (
            <button
              key={name}
              className={`btn sm${viewPreset.name === name ? ' primary' : ''}`}
              onClick={() => setViewPreset(name)}
              title={`Switch to ${name.toUpperCase()} view`}
            >
              {name.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="viewer-options">
          <label title="Show DH coordinate frames {0}..{6}">
            <input
              type="checkbox"
              checked={showFrames}
              onChange={() => toggle('showFrames')}
            />
            Frames
          </label>
          <label title="Show/hide the generated workspace point cloud">
            <input
              type="checkbox"
              checked={showWorkspace && workspace !== null}
              disabled={workspace === null}
              onChange={() => toggle('showWorkspace')}
            />
            Workspace
          </label>
          <label title="Show/hide the end-effector path of the active trajectory">
            <input
              type="checkbox"
              checked={showTrajectory}
              onChange={() => toggle('showTrajectory')}
            />
            EE Path
          </label>
        </div>
      </div>
    </div>
  );
}

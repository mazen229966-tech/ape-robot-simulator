/**
 * Mutable, allocation-free channel for the live robot pose.
 *
 * WebSocket frames arrive at ~30 Hz.  Writing them into a React/zustand
 * state would re-render the 3D scene on every frame (spec §48 forbids
 * that).  Instead the animation loop inside the Canvas reads this object
 * directly in useFrame, while a small amount of low-frequency state
 * (time, progress) goes through the stores for the UI panels.
 */
export const livePose = {
  qRad: new Float64Array(6),
  ee: { x: 0, y: 0, z: 0 },
  /** bumped on every update so the renderer knows data is fresh */
  version: 0,
};

export function setLivePose(qRad: ArrayLike<number>, ee?: { x: number; y: number; z: number }): void {
  for (let i = 0; i < 6; i += 1) livePose.qRad[i] = qRad[i];
  if (ee) {
    livePose.ee.x = ee.x;
    livePose.ee.y = ee.y;
    livePose.ee.z = ee.z;
  }
  livePose.version += 1;
}

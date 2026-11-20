"""Draw the letter H with the end-effector (final demo, spec §31-34, §57).

The H is defined as a *real Cartesian trajectory*:

    H corner points -> Cartesian path (timed segments) -> IK -> joint
    trajectory -> FK validation -> 3D animation

Pen behaviour
-------------
The tool starts above the drawing plane, lowers onto it ("pen contact"),
draws a stroke, lifts, travels to the next stroke and repeats.  A per-sample
``pen_down`` mask is returned so the UI can show a contact effect while the
pen touches the drawing plane.

Corner numbering (spec §32)::

    P1 ------- (top)        P5 ------- (top)
    |                       |
    P3 ==================== P4          <- middle bar
    |                       |
    P2 ------- (bottom)     P6 ------- (bottom)

Drawing order: left vertical (P1->P2), middle bar (P3->P4), right vertical
(P5->P6), with lift/travel moves in between.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np

from ..utils.errors import TrajectoryError
from ..utils.units import rpy_to_matrix
from ..models.ape_sv45 import HOME_POSITION_DEG
from .trajectory import (
    TOOL_Z_DOWN_RPY,
    _finalize_trajectory,
    _ik_along_path,
)

PHASE_APPROACH = "approach"
PHASE_LOWER = "lower pen"
PHASE_DRAW = "draw"
PHASE_LIFT = "lift pen"
PHASE_TRAVEL = "travel"
PHASE_FINISH = "finish"

SUPPORTED_PLANES = ("XY", "XZ", "YZ")

# Default H placement per plane (inside the validated feasible envelope).
# For XY the H lies on a horizontal plane at z = drawing_height; for the
# vertical planes (XZ / YZ) drawing_height is the z of the H centre and the
# plane offset comes from the center parameter (y for XZ, x for YZ).
DEFAULT_CENTER = {"XY": (0.29, 0.0), "XZ": (0.30, 0.12), "YZ": (0.30, 0.12)}
DEFAULT_DRAWING_HEIGHT = {"XY": 0.28, "XZ": 0.25, "YZ": 0.25}
# Default letter size per plane.  The vertical-plane defaults are smaller
# because the reachable wall region of the educational model is smaller.
DEFAULT_SIZE = {"XY": (0.15, 0.20), "XZ": (0.10, 0.14), "YZ": (0.10, 0.14)}
# Default start pose per plane.  The IK path solver keeps the trajectory in
# the configuration family of its seed; these poses were searched so that the
# default H of each plane needs at most one pen-up reconfiguration.
DEFAULT_START_POSE_DEG = {
    "XY": list(HOME_POSITION_DEG),
    "XZ": [79.3, -44.9, 36.6, -108.9, -102.5, -184.6],
    "YZ": list(HOME_POSITION_DEG),
}


def _segment_samples(p0, p1, t0, speed, dt):
    """Timed samples of a constant-speed linear segment (excluding start)."""
    length = float(np.linalg.norm(np.asarray(p1) - np.asarray(p0)))
    if length <= 1e-12:
        return [], t0
    duration = length / speed
    n = max(1, int(round(duration / dt)))
    s = np.linspace(0.0, 1.0, n + 1)[1:]
    t = t0 + s * duration
    pts = [np.asarray(p0) + (np.asarray(p1) - np.asarray(p0)) * k for k in s]
    return list(zip(pts, t)), t0 + duration


def generate_h_trajectory(
    plane: str = "XY",
    width: Optional[float] = None,
    height: Optional[float] = None,
    drawing_height: Optional[float] = None,
    speed: float = 0.05,
    center_xy: Optional[tuple] = None,
    lift: float = 0.02,
    dt: float = 0.02,
    q_start_deg: Optional[List[float]] = None,
) -> Dict:
    """Build the complete H-drawing Cartesian trajectory.

    All lengths in metres, speed in m/s, dt in seconds.

    The letter H is defined in a local 2D frame (u = letter width axis,
    v = letter height axis) and mapped onto one of three drawing planes:

    * ``XY`` -- horizontal plane ``z = drawing_height``; tool points down.
    * ``XZ`` -- vertical wall ``y = center_y``; the H spans x (width) and
      z (height, centred at ``drawing_height``); tool axis is horizontal,
      pointing at the wall.
    * ``YZ`` -- vertical wall ``x = center_x``; the H spans y (width) and
      z (height); tool axis horizontal, pointing at the wall.

    Pen lift / reconfiguration manoeuvres always happen along the plane
    normal (away from the drawing surface), never "through" it.

    Defaults are chosen inside the validated feasible envelope of the
    educational model (verified sample-by-sample with the IK solver).
    """
    plane = plane.upper()
    if plane not in SUPPORTED_PLANES:
        raise TrajectoryError(
            f"Unsupported drawing plane '{plane}'. Use XY, XZ or YZ."
        )

    if width is None:
        width = DEFAULT_SIZE[plane][0]
    if height is None:
        height = DEFAULT_SIZE[plane][1]
    if drawing_height is None:
        drawing_height = DEFAULT_DRAWING_HEIGHT[plane]
    if center_xy is None:
        center_xy = DEFAULT_CENTER[plane]

    if width <= 0 or height <= 0:
        raise TrajectoryError("H width and height must be positive.")
    if speed <= 0:
        raise TrajectoryError("Drawing speed must be positive.")
    c0, c1 = (float(v) for v in center_xy)
    z = float(drawing_height)
    w2, h2 = float(width) / 2.0, float(height) / 2.0

    # Plane mapping ------------------------------------------------------- #
    # local (u, v) -> world point; tool orientation; pen lift direction.
    # On the vertical planes the pen is tilted 45 degrees towards the wall
    # (and downwards); a purely horizontal tool is not continuously
    # reachable inside the official joint limits of this model.
    if plane == "XY":
        def to_world(u: float, v: float) -> np.ndarray:
            return np.array([c0 + u, c1 + v, z])

        tool_rpy = (math.pi, 0.0, 0.0)          # tool axis -> -z (down)
        lift_dir = np.array([0.0, 0.0, 1.0])
        plane_offset = z
    elif plane == "XZ":
        y_plane = c1
        # +1 if wall is on the +y side, -1 otherwise.
        wall_dir = 1.0 if y_plane >= 0.0 else -1.0

        def to_world(u: float, v: float) -> np.ndarray:
            return np.array([c0 + u, y_plane, z + v])

        # Tool axis -> wall_dir*y and down (45 deg tilt).
        # roll = -wall_dir * 135 deg gives axis [0, wall_dir*SQ2, -SQ2].
        tool_rpy = (-wall_dir * 3.0 * math.pi / 4.0, 0.0, 0.0)
        # Pen lift retracts along the outward plane normal (toward robot).
        lift_dir = np.array([0.0, -wall_dir, 0.0])
        plane_offset = y_plane
    else:  # YZ
        x_plane = c0
        wall_dir = 1.0 if x_plane >= 0.0 else -1.0

        def to_world(u: float, v: float) -> np.ndarray:
            return np.array([x_plane, c1 + u, z + v])

        # Tool axis -> wall_dir*x and down (45 deg tilt).
        # pitch = wall_dir * 135 deg gives axis [wall_dir*SQ2, 0, -SQ2].
        tool_rpy = (0.0, wall_dir * 3.0 * math.pi / 4.0, 0.0)
        lift_dir = np.array([-wall_dir, 0.0, 0.0])
        plane_offset = x_plane

    # Corner points (spec §32) ------------------------------------------- #
    P1 = to_world(-w2, +h2)  # top-left
    P2 = to_world(-w2, -h2)  # bottom-left
    P3 = to_world(-w2, 0.0)  # center-left
    P4 = to_world(+w2, 0.0)  # center-right
    P5 = to_world(+w2, +h2)  # top-right
    P6 = to_world(+w2, -h2)  # bottom-right

    above = lambda P: P + lift_dir * float(lift)

    # Ordered list of (from, to, phase, pen_down) segments -------------- #
    segments = [
        (above(P1), above(P1), PHASE_APPROACH, False),   # start hold point
        (above(P1), P1, PHASE_LOWER, False),             # lower pen
        (P1, P2, PHASE_DRAW, True),                      # left vertical
        (P2, above(P2), PHASE_LIFT, False),
        (above(P2), above(P3), PHASE_TRAVEL, False),
        (above(P3), P3, PHASE_LOWER, False),
        (P3, P4, PHASE_DRAW, True),                      # middle bar
        (P4, above(P4), PHASE_LIFT, False),
        (above(P4), above(P5), PHASE_TRAVEL, False),
        (above(P5), P5, PHASE_LOWER, False),
        (P5, P6, PHASE_DRAW, True),                      # right vertical
        (P6, above(P6), PHASE_FINISH, False),            # lift & finish
    ]

    # Sample all segments at constant speed ------------------------------ #
    path: List[np.ndarray] = [segments[0][0]]
    times: List[float] = [0.0]
    pen_down: List[bool] = [False]
    phases: List[str] = [segments[0][2]]

    t = 0.0
    draw_distance = 0.0
    for (p0, p1, phase, down) in segments[1:]:
        samples, t = _segment_samples(p0, p1, t, speed, dt)
        for p, tt in samples:
            path.append(p)
            times.append(tt)
            pen_down.append(down)
            phases.append(phase)
        if down:
            draw_distance += float(np.linalg.norm(p1 - p0))

    path_arr = np.array(path)
    t_arr = np.array(times)

    # Cartesian path -> IK -> joint trajectory --------------------------- #
    # Configuration-family flips (if any) are smoothed by automatically
    # inserting a pen-lift transition, so every drawn stroke stays smooth.
    # Seeding from the plane-specific start pose keeps the path inside the
    # smoothest configuration family (searched; deterministic).
    R = rpy_to_matrix(*tool_rpy)
    q_seed = np.deg2rad(
        np.asarray(
            q_start_deg
            if q_start_deg is not None
            else DEFAULT_START_POSE_DEG[plane],
            dtype=np.float64,
        )
    )
    q_traj, path_arr, t_arr, phases, pen_down, transition_spans = _ik_along_path(
        path_arr,
        t_arr,
        R,
        q_seed,
        transition_lift=float(lift),
        speed=float(speed),
        labels=phases,
        pen_mask=pen_down,
        lift_dir=lift_dir,
    )

    pen_mask = np.array(pen_down, dtype=bool)
    duration = float(t_arr[-1])

    qd = np.gradient(q_traj, t_arr, axis=0, edge_order=2)
    qdd = np.gradient(qd, t_arr, axis=0, edge_order=2)

    traj = {"t": t_arr, "q": q_traj, "qd": qd, "qdd": qdd}
    result = _finalize_trajectory(traj, method="draw-h", space="cartesian")

    # Rebuild the phase map from the (possibly transition-augmented) labels.
    phase_map: List[Dict] = []
    for i, (label, down) in enumerate(zip(phases, pen_down)):
        if phase_map and phase_map[-1]["phase"] == label:
            phase_map[-1]["t_end"] = float(t_arr[i])
            phase_map[-1]["index_end"] = i
        else:
            phase_map.append(
                {
                    "phase": label,
                    "pen_down": bool(down),
                    "t_start": float(t_arr[i]),
                    "t_end": float(t_arr[i]),
                    "index_start": i,
                    "index_end": i,
                }
            )

    result.update(
        {
            "pen_down": pen_mask.tolist(),
            "phases": phase_map,
            "transitions": [
                {"index_start": int(a), "index_end": int(b)}
                for a, b in transition_spans
            ],
            "draw_distance": draw_distance,
            "corners": {
                "P1": P1.tolist(),
                "P2": P2.tolist(),
                "P3": P3.tolist(),
                "P4": P4.tolist(),
                "P5": P5.tolist(),
                "P6": P6.tolist(),
            },
            "plane": plane,
            "plane_offset": plane_offset,
            "drawing_plane_z": z,
            "tool_orientation_rpy_deg": [math.degrees(a) for a in tool_rpy],
        }
    )
    return result

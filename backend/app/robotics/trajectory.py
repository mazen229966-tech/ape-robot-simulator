"""Trajectory planning.

Joint space
-----------
* **Cubic polynomial** -- zero velocity at both ends.
* **Quintic polynomial** -- zero velocity *and* acceleration at both ends.

Both produce ``q(t)``, ``qd(t)``, ``qdd(t)`` in closed form (no numeric
differentiation for joint-space trajectories).

Cartesian space
---------------
A sequence of timed waypoints (X,Y,Z + optional RPY) is interpolated
linearly per segment, every sample is converted to joint space through the
real IK solver with warm starting, and joint velocity/acceleration are
obtained by central finite differences.  This is the honest pipeline
required by spec §21 and §57:

    Cartesian points -> path -> IK -> joint trajectory -> FK validation.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

from ..models.parameters import parameter_store
from ..utils.errors import TrajectoryError
from ..utils.units import rpy_to_matrix
from .kinematics import forward_kinematics
from .inverse_kinematics import inverse_kinematics

JOINT_DT_DEFAULT = 0.02  # 50 Hz sampling for generated trajectories


# --------------------------------------------------------------------------- #
# Joint-space polynomial trajectories                                          #
# --------------------------------------------------------------------------- #


def cubic_trajectory(
    q0: Sequence[float], qf: Sequence[float], duration: float, samples: int
) -> Dict[str, np.ndarray]:
    """Cubic polynomial with rest boundary conditions at both ends."""
    q0 = np.asarray(q0, dtype=np.float64)
    qf = np.asarray(qf, dtype=np.float64)
    dq = qf - q0
    T = float(duration)
    t = np.linspace(0.0, T, int(samples))
    a2 = 3.0 * dq / T**2
    a3 = -2.0 * dq / T**3
    s = t[:, None]
    q = q0 + a2 * s**2 + a3 * s**3
    qd = 2.0 * a2 * s + 3.0 * a3 * s**2
    qdd = 2.0 * a2 + 6.0 * a3 * s
    return {"t": t, "q": q, "qd": qd, "qdd": qdd}


def quintic_trajectory(
    q0: Sequence[float], qf: Sequence[float], duration: float, samples: int
) -> Dict[str, np.ndarray]:
    """Quintic polynomial with rest (v=0, a=0) boundary conditions."""
    q0 = np.asarray(q0, dtype=np.float64)
    qf = np.asarray(qf, dtype=np.float64)
    dq = qf - q0
    T = float(duration)
    t = np.linspace(0.0, T, int(samples))
    a3 = 10.0 * dq / T**3
    a4 = -15.0 * dq / T**4
    a5 = 6.0 * dq / T**5
    s = t[:, None]
    q = q0 + a3 * s**3 + a4 * s**4 + a5 * s**5
    qd = 3.0 * a3 * s**2 + 4.0 * a4 * s**3 + 5.0 * a5 * s**4
    qdd = 6.0 * a3 * s + 12.0 * a4 * s**2 + 20.0 * a5 * s**3
    return {"t": t, "q": q, "qd": qd, "qdd": qdd}


def plan_joint_trajectory(
    q0_deg: Sequence[float],
    qf_deg: Sequence[float],
    duration: float,
    samples: int,
    method: str = "quintic",
) -> Dict:
    """Generate a joint-space trajectory (angles in degrees at the API edge)."""
    from .kinematics import check_joint_limits

    if duration <= 0:
        raise TrajectoryError("Trajectory duration must be positive.")
    if not (2 <= int(samples) <= 5000):
        raise TrajectoryError("Number of samples must be between 2 and 5000.")

    q0 = np.deg2rad(np.asarray(q0_deg, dtype=np.float64))
    qf = np.deg2rad(np.asarray(qf_deg, dtype=np.float64))
    check_joint_limits(q0)
    check_joint_limits(qf)

    method = method.lower()
    if method == "cubic":
        traj = cubic_trajectory(q0, qf, duration, samples)
    elif method == "quintic":
        traj = quintic_trajectory(q0, qf, duration, samples)
    else:
        raise TrajectoryError(f"Unknown interpolation method '{method}'.")

    return _finalize_trajectory(traj, method=method, space="joint")


# --------------------------------------------------------------------------- #
# Cartesian trajectories                                                       #
# --------------------------------------------------------------------------- #

TOOL_Z_DOWN_RPY = (math.pi, 0.0, 0.0)  # roll=180deg -> tool axis points down


JUMP_THRESHOLD_DEG = 25.0  # per-sample joint jump indicating a family flip


def _quintic_blend(q_from: np.ndarray, q_to: np.ndarray, n: int) -> np.ndarray:
    """Rest-to-rest quintic joint-space blend between two configurations."""
    s = np.linspace(0.0, 1.0, n)[:, None]
    poly = 10 * s**3 - 15 * s**4 + 6 * s**5
    return q_from + (q_to - q_from) * poly


def _ik_along_path(
    path: np.ndarray,
    t: np.ndarray,
    R: np.ndarray,
    q_seed=None,
    transition_lift: Optional[float] = None,
    speed: Optional[float] = None,
    max_transitions: int = 2,
    labels: Optional[List[str]] = None,
    pen_mask: Optional[List[bool]] = None,
    hold_samples: int = 45,
    hold_dt: float = 0.02,
    anchor_search: int = 30,
    lift_dir: Optional[np.ndarray] = None,
):
    """Solve IK sample-by-sample along a Cartesian path (streaming).

    Every sample uses the continuity-preferred solver so the joint
    trajectory stays inside one configuration family.  If the path forces a
    configuration-family change (elbow/wrist flip) -- detectable as a joint
    jump between consecutive solutions -- and ``transition_lift`` and
    ``speed`` are provided, an honest pen-up reconfiguration manoeuvre is
    inserted:

    1. Search backwards along the path for an anchor point where BOTH
       configuration families exist (lifted by ``transition_lift``).
    2. Lift the pen, backtrack pen-up to the anchor if needed.
    3. Blend the joints (quintic, rest-to-rest) between the two IK
       solutions of the lifted anchor point.
    4. Air-bridge pen-up to a point above the original path, lower back
       onto the path in the new family and continue.

    During the manoeuvre the end-effector follows FK(q) of the real joint
    motion -- always pen-up, never faked.

    Returns ``(q_traj, path, t, labels, pen_mask, transition_spans)``.
    """
    from .inverse_kinematics import (
        find_alternative_configuration,
        inverse_kinematics,
        inverse_kinematics_path_sample,
    )

    src_path = [np.asarray(p, dtype=np.float64) for p in path]
    src_t = [float(v) for v in t]
    out_path: List[np.ndarray] = []
    out_t: List[float] = []
    out_q: List[np.ndarray] = []
    out_labels: List[str] = []
    out_pen: List[bool] = []
    transition_spans: List[tuple] = []
    transitions_used = 0

    has_labels = labels is not None
    has_pen = pen_mask is not None
    src_to_out: List[int] = []

    def emit(p, time, q, label=None, pen=False):
        out_path.append(np.asarray(p, dtype=np.float64))
        out_t.append(float(time))
        out_q.append(np.asarray(q, dtype=np.float64))
        out_labels.append(label if has_labels else None)
        out_pen.append(bool(pen) if has_pen else None)

    q_prev: Optional[np.ndarray] = None
    if q_seed is not None:
        q_seed = np.asarray(q_seed, dtype=np.float64).ravel()
    time_shift = 0.0  # delay accumulated by inserted manoeuvres
    if lift_dir is None:
        lift_dir = np.array([0.0, 0.0, 1.0])
    lift_dir = np.asarray(lift_dir, dtype=np.float64).ravel()

    def jump_between(q_a: np.ndarray, q_b: np.ndarray) -> bool:
        return bool(np.max(np.abs(np.rad2deg(q_b - q_a))) > JUMP_THRESHOLD_DEG)

    def solve_at(point, seed):
        return inverse_kinematics_path_sample(point, R, seed)

    for i, p in enumerate(src_path):
        try:
            if q_prev is None:
                q_i = (
                    solve_at(p, q_seed)
                    if q_seed is not None
                    else inverse_kinematics(p, R)["q"]
                )
            else:
                q_i = solve_at(p, q_prev)
        except Exception as exc:
            raise TrajectoryError(
                f"Cartesian trajectory failed at t = {src_t[i]:.2f} s "
                f"(point x={p[0]:.3f}, y={p[1]:.3f}, z={p[2]:.3f} m): {exc}"
            ) from None

        needs_transition = (
            q_prev is not None
            and jump_between(q_prev, q_i)
            and transition_lift is not None
            and speed is not None
        )
        if not needs_transition:
            q_prev = q_i
            emit(
                p,
                src_t[i] + time_shift,
                q_i,
                labels[i] if has_labels else None,
                pen_mask[i] if has_pen else False,
            )
            src_to_out.append(len(out_path) - 1)
            continue

        # ---------------- reconfiguration manoeuvre --------------------- #
        if transitions_used >= max_transitions:
            raise TrajectoryError(
                "Cartesian trajectory requires a robot configuration "
                "change that cannot be smoothed along this path."
            )

        anchor = None
        lo = max(0, i - anchor_search)
        for j in range(i - 1, lo - 1, -1):
            u_j = src_path[j] + lift_dir * float(transition_lift)
            try:
                q_up_j = solve_at(u_j, out_q[src_to_out[j]])
                q_alt_j = find_alternative_configuration(u_j, R, q_up_j)
            except Exception:
                continue
            if q_alt_j is not None:
                anchor = (j, u_j, q_up_j, q_alt_j)
                break
        if anchor is None:
            raise TrajectoryError(
                "No reconfiguration point with two robot configurations "
                "exists near this path segment; try different geometry."
            )

        j, u_j, _q_up_j, q_alt_j = anchor
        transition_start = len(out_path)
        t_cursor = out_t[-1]
        cur = out_path[-1]
        q_walk = out_q[-1]

        # 1) retrace pen-up at drawing height back to the anchor xy (the
        #    current configuration family stays valid there).
        anchor_low = src_path[j]
        if np.linalg.norm(anchor_low - cur) > 1e-9:
            n_steps = max(
                2, int(np.ceil(np.linalg.norm(anchor_low - cur) / (speed * hold_dt)))
            )
            prev_b = cur
            for s in np.linspace(0.0, 1.0, n_steps)[1:]:
                b = cur + (anchor_low - cur) * s
                q_walk = solve_at(b, q_walk)
                t_cursor += float(np.linalg.norm(b - prev_b) / speed)
                prev_b = b
                emit(b, t_cursor, q_walk, "transition", False)

        # 2) lift straight up at the anchor.
        t_cursor += float(np.linalg.norm(u_j - anchor_low) / speed)
        q_walk = solve_at(u_j, q_walk)
        emit(u_j.copy(), t_cursor, q_walk, "transition", False)

        # 3) joint-space blend between the reached configuration at the
        #    anchor (old family) and the alternative one (new family).
        t_cursor += float(hold_dt) / 2.0
        for q_h in _quintic_blend(q_walk, q_alt_j, int(hold_samples)):
            emit(u_j.copy(), t_cursor, q_h, "transition", False)
            t_cursor += float(hold_dt)

        # 4) air-bridge to a point above the current path sample, then lower.
        u_i = p + lift_dir * float(transition_lift)
        q_walk = q_alt_j
        if np.linalg.norm(u_i - u_j) > 1e-6:
            n_bridge = max(
                2, int(np.ceil(np.linalg.norm(u_i - u_j) / (speed * hold_dt)))
            )
            prev_b = u_j
            for s in np.linspace(0.0, 1.0, n_bridge)[1:]:
                b = u_j + (u_i - u_j) * s
                q_walk = solve_at(b, q_walk)
                t_cursor += float(np.linalg.norm(b - prev_b) / speed)
                prev_b = b
                emit(b, t_cursor, q_walk, "transition", False)
        t_cursor += float(np.linalg.norm(p - u_i) / speed)
        q_i = solve_at(p, q_walk)
        emit(p, t_cursor, q_i, labels[i] if has_labels else None,
             pen_mask[i] if has_pen else False)
        src_to_out.append(len(out_path) - 1)

        transition_spans.append((transition_start, len(out_path) - 2))
        transitions_used += 1
        time_shift = t_cursor - src_t[i]
        q_prev = q_i

    q_traj = np.array(out_q)
    path_arr = np.array(out_path)
    t_arr = np.array(out_t)
    return q_traj, path_arr, t_arr, out_labels, out_pen, transition_spans


def plan_cartesian_trajectory(
    points: List[Dict],
    orientation_rpy_deg: Optional[Sequence[float]] = None,
    dt: float = JOINT_DT_DEFAULT,
    q_start_deg: Optional[Sequence[float]] = None,
) -> Dict:
    """Generate a Cartesian trajectory through timed waypoints.

    ``points`` -- list of ``{"x","y","z","t"}`` (metres, seconds; t strictly
    increasing, first t is usually 0).
    ``orientation_rpy_deg`` -- optional constant tool orientation (deg, ZYX).
    Defaults to tool pointing down (needed for drawing tasks).
    """
    if len(points) < 2:
        raise TrajectoryError("At least two Cartesian points are required.")
    if not (0.005 <= dt <= 0.2):
        raise TrajectoryError("Sampling step dt must be between 0.005 and 0.2 s.")

    pts = []
    for i, p in enumerate(points):
        try:
            xyz = np.array([float(p["x"]), float(p["y"]), float(p["z"])])
            t = float(p["t"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TrajectoryError(f"Point {i + 1} is malformed.") from exc
        if not np.all(np.isfinite(xyz)) or not math.isfinite(t):
            raise TrajectoryError(f"Point {i + 1} contains non-finite values.")
        pts.append((xyz, t))
    for (pa, ta), (pb, tb) in zip(pts[:-1], pts[1:]):
        if tb <= ta:
            raise TrajectoryError("Waypoint times must be strictly increasing.")
        if np.linalg.norm(pb - pa) < 1e-9:
            raise TrajectoryError("Consecutive waypoints must differ.")

    if orientation_rpy_deg is None:
        rpy = TOOL_Z_DOWN_RPY
    else:
        rpy = tuple(math.radians(v) for v in orientation_rpy_deg)
    R = rpy_to_matrix(*rpy)

    # Dense linear interpolation of the Cartesian path.
    total_time = pts[-1][1] - pts[0][1]
    if total_time <= 0:
        raise TrajectoryError("Total trajectory time must be positive.")
    t = np.arange(pts[0][1], pts[-1][1] + dt / 2, dt)
    t = np.clip(t, pts[0][1], pts[-1][1])
    ts = np.array([p[1] for p in pts])
    xyzs = np.array([p[0] for p in pts])
    path = np.empty((t.shape[0], 3))
    for k in range(3):
        path[:, k] = np.interp(t, ts, xyzs[:, k])

    # IK along the path with warm starting.
    q_start = None
    if q_start_deg is not None:
        q_start = np.deg2rad(np.asarray(q_start_deg, dtype=np.float64))
    q_traj, path, t, _, _, _ = _ik_along_path(path, t, R, q_start)

    qd = np.gradient(q_traj, t, axis=0, edge_order=2)
    qdd = np.gradient(qd, t, axis=0, edge_order=2)

    traj = {"t": t, "q": q_traj, "qd": qd, "qdd": qdd}
    return _finalize_trajectory(
        traj,
        method="cartesian-linear",
        space="cartesian",
        cartesian_waypoints=[
            {
                "x": float(p[0][0]),
                "y": float(p[0][1]),
                "z": float(p[0][2]),
                "t": float(p[1]),
            }
            for p in pts
        ],
        orientation_rpy_deg=[math.degrees(v) for v in rpy],
    )


# --------------------------------------------------------------------------- #
# Shared post-processing                                                       #
# --------------------------------------------------------------------------- #


def _ee_positions(q_traj: np.ndarray) -> np.ndarray:
    """FK along a trajectory -> (n, 3) end-effector positions [m]."""
    n = q_traj.shape[0]
    ee = np.empty((n, 3))
    for i in range(n):
        ee[i] = forward_kinematics(q_traj[i])[:3, 3]
    return ee


def _finalize_trajectory(
    traj: Dict[str, np.ndarray],
    method: str,
    space: str,
    **extra,
) -> Dict:
    """Sanity checks + end-effector path + serialisable result."""
    for name, arr in traj.items():
        if not np.all(np.isfinite(arr)):
            raise TrajectoryError(
                f"Trajectory generation failed: non-finite values in {name}."
            )

    # FK validation of the whole joint trajectory against limits.
    limits = np.array(parameter_store.spec.joint_limits_rad)
    if np.any(traj["q"] < limits[:, 0] - 1e-6) or np.any(
        traj["q"] > limits[:, 1] + 1e-6
    ):
        raise TrajectoryError(
            "Trajectory generation failed: joint limits violated."
        )

    ee = _ee_positions(traj["q"])
    duration = float(traj["t"][-1] - traj["t"][0])
    path_length = float(np.sum(np.linalg.norm(np.diff(ee, axis=0), axis=1)))

    result = {
        "method": method,
        "space": space,
        "samples": int(traj["t"].shape[0]),
        "duration": duration,
        "dt": float(np.mean(np.diff(traj["t"]))) if traj["t"].size > 1 else 0.0,
        "t": traj["t"].tolist(),
        "q": traj["q"].tolist(),          # rad
        "qd": traj["qd"].tolist(),        # rad/s
        "qdd": traj["qdd"].tolist(),      # rad/s^2
        "ee_path": ee.tolist(),           # m
        "ee_path_length": path_length,
    }
    result.update(extra)
    return result

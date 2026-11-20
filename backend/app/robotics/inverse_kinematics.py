"""Inverse kinematics with FK validation.

Strategy
--------
1. Numerical IK via Robotics Toolbox (Levenberg-Marquardt, multi-start).
2. Enforce joint limits during the solve and hard-check them afterwards.
3. Validate by re-running FK on the solution and reporting position and
   orientation error (spec §14).

Two entry points
----------------
* :func:`inverse_kinematics` -- standalone solve for a single pose (IK page).
* :func:`inverse_kinematics_path_sample` -- path-following solve that prefers
  the solution *closest in joint space* to the previous sample, keeping
  trajectories continuous across configuration-family boundaries.

No analytical shortcuts or hard-coded solutions -- every result comes from
solving the actual kinematic chain (spec §65).
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np
from spatialmath import SE3

from ..models.parameters import parameter_store
from ..utils.errors import IKNoSolutionError, IKUnreachableError
from ..utils.units import rotation_error_angle
from .kinematics import check_joint_limits, forward_kinematics
from .robot import create_robot

# Tolerances for accepting a solution.
POSITION_TOLERANCE_M = 5e-4      # 0.5 mm
ORIENTATION_TOLERANCE_RAD = math.radians(0.5)

# Number of independent random seeds tried by the standalone solver.
N_SEEDS = 16


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _pose_errors(q: np.ndarray, Tep: np.ndarray) -> tuple[float, float]:
    """Position error [m] and orientation error [rad] of FK(q) vs Tep."""
    T = forward_kinematics(q)
    pos_err = float(np.linalg.norm(T[:3, 3] - Tep[:3, 3]))
    rot_err = rotation_error_angle(Tep[:3, :3], T[:3, :3])
    return pos_err, rot_err


def _within_reach(target_xyz: Sequence[float]) -> bool:
    """Cheap geometric pre-check against an optimistic workspace envelope."""
    x, y, z = (float(v) for v in target_xyz)
    dh = parameter_store.dh_table()
    radial = sum(abs(row[2]) for row in dh) + sum(abs(row[1]) for row in dh[1:])
    base_height = dh[0][1]
    r = math.hypot(x, y)
    vertical_span = radial + base_height
    if r > radial * 1.05:
        return False
    if z > base_height + radial * 1.05:
        return False
    if z < -vertical_span * 1.05:
        return False
    return True


def _limits() -> np.ndarray:
    return np.array(parameter_store.spec.joint_limits_rad)


def _solve_seeds(
    robot, Tep_se3: SE3, seeds: List[np.ndarray], Tep: np.ndarray, ilimit: int = 40
):
    """Run IK from each seed; return valid candidate solutions."""
    limits = _limits()
    candidates: List[np.ndarray] = []
    for seed in seeds:
        seed = np.clip(np.asarray(seed, dtype=np.float64), limits[:, 0], limits[:, 1])
        try:
            sol = robot.ik_LM(
                Tep_se3, q0=seed, joint_limits=True, ilimit=ilimit, slimit=1, tol=1e-8
            )
        except Exception:
            continue
        q_sol = np.asarray(sol.q, dtype=np.float64).ravel()
        if not np.all(np.isfinite(q_sol)):
            continue
        pos_err, rot_err = _pose_errors(q_sol, Tep)
        if (
            pos_err <= POSITION_TOLERANCE_M
            and rot_err <= ORIENTATION_TOLERANCE_RAD
        ):
            candidates.append(q_sol)
    return candidates


def _wrapped_delta(q_new: float, q_ref: float, lo: float, hi: float) -> float:
    """Smallest equivalent joint displacement, honouring 2π-equivalence.

    A solution ``q_new`` is physically identical to ``q_new ± 2πk``; the
    wrapped value is only admissible if it stays inside the joint limits.
    """
    best = q_new - q_ref
    for k in (-2.0, -1.0, 0.0, 1.0, 2.0):
        q_alt = q_new + k * 2.0 * math.pi
        if lo - 1e-9 <= q_alt <= hi + 1e-9:
            d = q_alt - q_ref
            if abs(d) < abs(best):
                best = d
    return best


def _continuity_cost(q: np.ndarray, q_prev: np.ndarray, limits: np.ndarray) -> float:
    deltas = [
        _wrapped_delta(q[j], q_prev[j], limits[j, 0], limits[j, 1])
        for j in range(q.shape[0])
    ]
    return float(sum(d * d for d in deltas))


def _canonical_near(q: np.ndarray, q_prev: np.ndarray, limits: np.ndarray) -> np.ndarray:
    """Return the 2π-equivalent of ``q`` closest to ``q_prev`` (within limits)."""
    out = q.copy()
    for j in range(q.shape[0]):
        best_q, best_d = q[j], abs(q[j] - q_prev[j])
        for k in (-2.0, -1.0, 1.0, 2.0):
            q_alt = q[j] + k * 2.0 * math.pi
            if limits[j, 0] - 1e-9 <= q_alt <= limits[j, 1] + 1e-9:
                d = abs(q_alt - q_prev[j])
                if d < best_d:
                    best_q, best_d = q_alt, d
        out[j] = best_q
    return out


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def inverse_kinematics(
    position: Sequence[float],
    orientation_matrix: np.ndarray,
    q_guess: Optional[Sequence[float]] = None,
) -> Dict:
    """Solve IK for a full 6-DOF pose (standalone, multi-start).

    Returns dict with ``q`` (radians), ``position_error`` (m),
    ``orientation_error`` (rad) and a ``valid`` flag.
    """
    position = np.asarray(position, dtype=np.float64).ravel()
    if position.shape[0] != 3 or not np.all(np.isfinite(position)):
        raise IKNoSolutionError("Target position must be 3 finite values.")
    orientation_matrix = np.asarray(orientation_matrix, dtype=np.float64)
    if orientation_matrix.shape != (3, 3):
        raise IKNoSolutionError("Orientation must be a 3x3 rotation matrix.")

    if not _within_reach(position):
        raise IKUnreachableError()

    Tep = np.eye(4)
    Tep[:3, :3] = orientation_matrix
    Tep[:3, 3] = position
    Tep_se3 = SE3(Tep)

    robot = create_robot()
    limits = _limits()
    rng = np.random.default_rng(20260914)  # deterministic multi-start

    seeds: List[np.ndarray] = []
    if q_guess is not None:
        seeds.append(np.asarray(q_guess, dtype=np.float64).ravel())
    for _ in range(N_SEEDS):
        seeds.append(rng.uniform(limits[:, 0], limits[:, 1]))

    candidates = _solve_seeds(robot, Tep_se3, seeds, Tep)
    if not candidates:
        # Escalated retry with more seeds before declaring failure.
        extra = [rng.uniform(limits[:, 0], limits[:, 1]) for _ in range(2 * N_SEEDS)]
        candidates = _solve_seeds(robot, Tep_se3, extra, Tep, ilimit=60)
    if not candidates:
        raise IKNoSolutionError()

    # Pick the candidate with the smallest task-space error.
    best = min(candidates, key=lambda q: sum(_pose_errors(q, Tep)))
    check_joint_limits(best, tolerance_rad=1e-6)
    pos_err, rot_err = _pose_errors(best, Tep)
    return {
        "q": best,
        "position_error": pos_err,
        "orientation_error": rot_err,
        "position_error_mm": pos_err * 1e3,
        "orientation_error_deg": math.degrees(rot_err),
        "valid": bool(
            pos_err <= POSITION_TOLERANCE_M
            and rot_err <= ORIENTATION_TOLERANCE_RAD
        ),
    }


def find_alternative_configuration(
    position: np.ndarray,
    orientation_matrix: np.ndarray,
    q_ref: np.ndarray,
    n_seeds: int = 48,
) -> Optional[np.ndarray]:
    """Find a valid IK solution in a *different* configuration family.

    Searches with many random seeds and returns the valid candidate that is
    furthest (in joint space, 2π-normalised) from ``q_ref``; ``None`` if no
    distinct family exists for this pose.
    """
    position = np.asarray(position, dtype=np.float64).ravel()
    orientation_matrix = np.asarray(orientation_matrix, dtype=np.float64)
    Tep = np.eye(4)
    Tep[:3, :3] = orientation_matrix
    Tep[:3, 3] = position
    Tep_se3 = SE3(Tep)

    robot = create_robot()
    limits = _limits()
    rng = np.random.default_rng(555000)
    seeds = [rng.uniform(limits[:, 0], limits[:, 1]) for _ in range(n_seeds)]
    candidates = _solve_seeds(robot, Tep_se3, seeds, Tep, ilimit=50)

    best_q, best_cost = None, 0.0
    for q in candidates:
        q_n = _canonical_near(q, q_ref, limits)
        cost = _continuity_cost(q_n, q_ref, limits)
        if cost > best_cost:
            best_cost = cost
            best_q = q_n
    # Require a genuinely different configuration (> 30 deg joint deviation).
    if best_q is None or best_cost < math.radians(30.0) ** 2:
        return None
    return best_q


def inverse_kinematics_path_sample(
    position: np.ndarray,
    orientation_matrix: np.ndarray,
    q_prev: np.ndarray,
) -> np.ndarray:
    """IK for one path sample, preferring continuity with ``q_prev``.

    Seeds: previous solution, local perturbations around it, then uniform
    random seeds as fallback.  Among all valid candidates the one with the
    smallest joint-space displacement from ``q_prev`` wins (2π-equivalent
    representations are normalised).
    """
    Tep = np.eye(4)
    Tep[:3, :3] = orientation_matrix
    Tep[:3, 3] = position
    Tep_se3 = SE3(Tep)

    robot = create_robot()
    limits = _limits()
    rng = np.random.default_rng(987654321)  # deterministic per call

    local_perturbations = [
        np.deg2rad(1.0),
        np.deg2rad(3.0),
        np.deg2rad(8.0),
    ]
    seeds: List[np.ndarray] = [q_prev]
    for scale in local_perturbations:
        for _ in range(3):
            seeds.append(q_prev + rng.normal(0.0, scale, size=6))

    candidates = _solve_seeds(robot, Tep_se3, seeds, Tep)
    if not candidates:
        # Wider search before giving up (thin solution basins).
        wide = [rng.uniform(limits[:, 0], limits[:, 1]) for _ in range(N_SEEDS)]
        candidates = _solve_seeds(robot, Tep_se3, wide, Tep)
    if not candidates:
        wide = [rng.uniform(limits[:, 0], limits[:, 1]) for _ in range(2 * N_SEEDS)]
        candidates = _solve_seeds(robot, Tep_se3, wide, Tep, ilimit=60)
    if not candidates:
        raise IKNoSolutionError()

    q_best = min(
        candidates, key=lambda q: _continuity_cost(q, q_prev, limits)
    )
    q_best = _canonical_near(q_best, q_prev, limits)

    # Final FK validation.
    pos_err, rot_err = _pose_errors(q_best, Tep)
    if pos_err > POSITION_TOLERANCE_M or rot_err > ORIENTATION_TOLERANCE_RAD:
        raise IKNoSolutionError()
    return q_best

"""Forward kinematics and Jacobian.

All angles are radians, all lengths metres internally.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np

from ..models.parameters import parameter_store
from ..utils.errors import JointLimitError
from ..utils.units import matrix_to_rpy
from .dh import dh_chain, dh_frame_list
from .robot import create_robot


def check_joint_limits(
    q: Sequence[float], tolerance_rad: float = 1e-9
) -> np.ndarray:
    """Validate ``q`` (rad) against the published joint limits.

    Raises :class:`JointLimitError` listing every violated joint.
    """
    q = np.asarray(q, dtype=np.float64).ravel()
    limits = parameter_store.spec.joint_limits_rad
    if q.shape[0] != len(limits):
        raise JointLimitError(
            f"Expected {len(limits)} joints, got {q.shape[0]}."
        )
    violations: List[str] = []
    for i, (qi, (lo, hi)) in enumerate(zip(q, limits), start=1):
        if qi < lo - tolerance_rad or qi > hi + tolerance_rad:
            violations.append(
                f"J{i} = {np.degrees(qi):+.1f}° outside "
                f"[{np.degrees(lo):+.1f}°, {np.degrees(hi):+.1f}°]"
            )
    if violations:
        raise JointLimitError("Joint limit exceeded: " + "; ".join(violations))
    return q


def forward_kinematics(q_rad: Sequence[float]) -> np.ndarray:
    """Return the 4x4 end-effector transform T_06 for q (radians).

    Uses the NumPy DH implementation (verified against Robotics Toolbox in
    the test-suite).
    """
    q = check_joint_limits(q_rad)
    return dh_chain(q, parameter_store.dh_table())


def fk_frames(q_rad: Sequence[float]) -> List[np.ndarray]:
    """Return all frames T_00 .. T_06 (for coordinate-frame visualisation)."""
    q = check_joint_limits(q_rad)
    return dh_frame_list(q, parameter_store.dh_table())


def forward_kinematics_result(q_rad: Sequence[float]) -> Dict:
    """FK result decomposed into position, orientation and full matrix."""
    T = forward_kinematics(q_rad)
    roll, pitch, yaw = matrix_to_rpy(T[:3, :3])
    return {
        "position": {"x": float(T[0, 3]), "y": float(T[1, 3]), "z": float(T[2, 3])},
        "orientation": {
            "roll": float(np.degrees(roll)),
            "pitch": float(np.degrees(pitch)),
            "yaw": float(np.degrees(yaw)),
        },
        "transform": T.tolist(),
    }


def jacobian_world(q_rad: Sequence[float]) -> np.ndarray:
    """Return the 6x6 world-frame geometric Jacobian at q."""
    robot = create_robot()
    return np.asarray(robot.jacob0(np.asarray(q_rad, dtype=np.float64)))

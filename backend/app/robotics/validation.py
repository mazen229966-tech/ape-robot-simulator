"""Cross-validation utilities for the robotics engine.

These helpers are used by the test-suite (spec §40) and by sanity checks in
the API layer.
"""

from __future__ import annotations

import math

import numpy as np

from .dh import dh_chain, dh_transform
from .kinematics import forward_kinematics
from .robot import create_robot


def fk_matches_toolbox(q_rad, atol: float = 1e-9) -> bool:
    """Check NumPy DH chain against Robotics Toolbox FK."""
    robot = create_robot()
    T_np = dh_chain(np.asarray(q_rad, dtype=np.float64), _active_table())
    T_rtb = np.asarray(robot.fkine(np.asarray(q_rad, dtype=np.float64)).A)
    return bool(np.allclose(T_np, T_rtb, atol=atol))


def fk_is_rigid(T: np.ndarray, atol: float = 1e-9) -> bool:
    """Homogeneous transform sanity: orthonormal rotation, det = +1."""
    if T.shape != (4, 4):
        return False
    R = T[:3, :3]
    if not np.allclose(R @ R.T, np.eye(3), atol=atol):
        return False
    if not np.isclose(np.linalg.det(R), 1.0, atol=atol):
        return False
    if not np.allclose(T[3, :], np.array([0, 0, 0, 1]), atol=atol):
        return False
    return True


def fk_manual_reference(q_rad, dh_table) -> np.ndarray:
    """Independent reference implementation (explicit matrix products).

    Used by the FK unit test to compare against hand-built matrices.
    """
    T = np.eye(4)
    for qi, (_, d, a, alpha) in zip(q_rad, dh_table):
        T = T @ dh_transform(qi, d, a, alpha)
    return T


def _active_table():
    from ..models.parameters import parameter_store

    return parameter_store.dh_table()

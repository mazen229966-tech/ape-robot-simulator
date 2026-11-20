"""Unit conversion helpers.

Internal convention (SI): metres, radians, seconds, Newton, Newton-metre.
The UI shows mm / degrees; every conversion passes through these helpers so
units are never mixed silently.
"""

from __future__ import annotations

import math
from typing import List, Sequence

import numpy as np

DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi
MM2M = 1.0e-3
M2MM = 1.0e3


def deg_to_rad(values: Sequence[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) * DEG2RAD


def rad_to_deg(values: Sequence[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) * RAD2DEG


def mm_to_m(values: Sequence[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) * MM2M


def m_to_mm(values: Sequence[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) * M2MM


# --------------------------------------------------------------------------- #
# Roll / pitch / yaw  (ZYX convention: R = Rz(yaw) Ry(pitch) Rx(roll))        #
# --------------------------------------------------------------------------- #


def rpy_to_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Convert roll/pitch/yaw (radians, ZYX) to a 3x3 rotation matrix."""
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def matrix_to_rpy(R: np.ndarray) -> tuple[float, float, float]:
    """Convert a 3x3 rotation matrix to (roll, pitch, yaw) in radians (ZYX).

    Uses the numerically stable two-argument form; gimbal-lock (pitch near
    +/-90 deg) falls back to roll = 0.
    """
    sp = -R[2, 0]
    sp = max(-1.0, min(1.0, sp))
    pitch = math.asin(sp)
    if abs(abs(sp) - 1.0) < 1e-9:  # gimbal lock
        roll = 0.0
        yaw = math.atan2(-R[0, 1], R[1, 1])
    else:
        roll = math.atan2(R[2, 1], R[2, 2])
        yaw = math.atan2(R[1, 0], R[0, 0])
    return roll, pitch, yaw


def rotation_error_angle(R_desired: np.ndarray, R_actual: np.ndarray) -> float:
    """Angular error between two rotations [rad] (angle of R_d^T R_a)."""
    R = R_desired.T @ R_actual
    cos_angle = (np.trace(R) - 1.0) / 2.0
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.acos(cos_angle)


def wrap_to_pi(angle: float) -> float:
    """Wrap an angle to (-pi, pi]."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def validate_joint_vector(q: Sequence[float], dof: int = 6) -> np.ndarray:
    """Validate and convert a joint vector to float64 ndarray."""
    arr = np.asarray(q, dtype=np.float64).ravel()
    if arr.shape[0] != dof:
        raise ValueError(f"Expected {dof} joint values, got {arr.shape[0]}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Joint values must be finite numbers.")
    return arr

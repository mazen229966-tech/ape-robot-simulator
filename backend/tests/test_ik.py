"""IK tests: FK -> IK -> FK round trip and failure handling (spec §40)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.models.parameters import parameter_store
from app.robotics.inverse_kinematics import (
    POSITION_TOLERANCE_M,
    inverse_kinematics,
)
from app.robotics.kinematics import forward_kinematics
from app.utils.errors import IKNoSolutionError, IKUnreachableError
from app.utils.units import rpy_to_matrix

# Attainable poses (verified inside the Z-down feasible envelope).
TEST_POSES = [
    ([0.26, 0.0, 0.28], (math.pi, 0.0, 0.0)),
    ([0.24, 0.05, 0.28], (math.pi, 0.0, 0.0)),
    ([0.30, -0.05, 0.28], (math.pi, 0.0, 0.0)),
    ([0.30, 0.0, 0.30], (math.pi, 0.0, 0.0)),
]


def test_fk_ik_fk_round_trip():
    """q -> FK -> pose -> IK -> q2 -> FK -> pose2 ; error must be tiny."""
    limits = np.array(parameter_store.spec.joint_limits_rad)
    for pos, rpy in TEST_POSES:
        R = rpy_to_matrix(*rpy)
        sol = inverse_kinematics(pos, R)
        q = sol["q"]
        # joint limits respected
        assert np.all(q >= limits[:, 0] - 1e-9)
        assert np.all(q <= limits[:, 1] + 1e-9)
        # FK validation
        T = forward_kinematics(q)
        pos_err = np.linalg.norm(T[:3, 3] - np.array(pos))
        assert pos_err < POSITION_TOLERANCE_M
        assert sol["valid"]
        assert sol["position_error_mm"] < 0.5


def test_ik_orientation_error_small():
    R = rpy_to_matrix(math.pi, 0.0, 0.0)
    sol = inverse_kinematics([0.29, 0.0, 0.28], R)
    assert sol["orientation_error_deg"] < 0.5


def test_ik_unreachable_far_target():
    R = rpy_to_matrix(math.pi, 0.0, 0.0)
    with pytest.raises(IKUnreachableError):
        inverse_kinematics([5.0, 0.0, 0.3], R)  # 5 m away


def test_ik_no_solution_raises():
    """A point inside the kinematic envelope but with an impossible
    orientation/position combination must raise IKNoSolutionError."""
    R = rpy_to_matrix(math.pi, 0.0, 0.0)
    with pytest.raises((IKNoSolutionError, IKUnreachableError)):
        inverse_kinematics([0.02, 0.0, 0.30], R)  # almost above the base


def test_ik_with_guess_converges():
    R = rpy_to_matrix(math.pi, 0.0, 0.0)
    guess = np.deg2rad([0, -45, 60, 0, 75, 0])
    sol = inverse_kinematics([0.26, 0.0, 0.28], R, q_guess=guess)
    assert sol["valid"]

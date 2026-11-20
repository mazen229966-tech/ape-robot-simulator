"""Forward kinematics tests (spec §40: manual matrix comparison)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.models.parameters import parameter_store
from app.robotics.kinematics import (
    forward_kinematics,
    forward_kinematics_result,
    jacobian_world,
)
from app.robotics.validation import fk_is_rigid, fk_manual_reference
from app.utils.errors import JointLimitError


def test_fk_zero_configuration_manual():
    """FK at q = 0 verified against a hand-computed reference."""
    q = np.zeros(6)
    T = forward_kinematics(q)
    ref = fk_manual_reference(q, parameter_store.dh_table())
    assert np.allclose(T, ref, atol=1e-12)
    # Zero config: arm stretched along +x: x = a2 + a3 = 0.370 m.
    table = parameter_store.dh_table()
    assert math.isclose(T[0, 3], table[1][2] + table[2][2], abs_tol=1e-9)


def test_fk_output_is_rigid(rng):
    limits = np.array(parameter_store.spec.joint_limits_rad)
    for _ in range(10):
        q = rng.uniform(limits[:, 0], limits[:, 1])
        assert fk_is_rigid(forward_kinematics(q))


def test_fk_result_structure():
    res = forward_kinematics_result(np.deg2rad([0, -35, 55, 0, -20, 0]))
    assert set(res) == {"position", "orientation", "transform"}
    T = np.array(res["transform"])
    assert T.shape == (4, 4)
    assert np.allclose(T[:3, 3], list(res["position"].values()))
    # orientation angles must be finite degrees
    for v in res["orientation"].values():
        assert math.isfinite(v)


def test_fk_rejects_out_of_limits():
    with pytest.raises(JointLimitError):
        forward_kinematics(np.deg2rad([0, 0, 0, 0, 0, 400]))  # J6 limit ±360


def test_jacobian_shape_and_finite():
    q = np.deg2rad([10, -20, 30, 0, 40, 0])
    J = jacobian_world(q)
    assert J.shape == (6, 6)
    assert np.all(np.isfinite(J))

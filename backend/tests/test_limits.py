"""Joint limit tests (spec §40)."""

from __future__ import annotations

import numpy as np
import pytest

from app.models.parameters import parameter_store
from app.robotics.kinematics import check_joint_limits
from app.utils.errors import JointLimitError


def test_all_limits_enforced():
    limits_deg = parameter_store.spec.joint_limits_deg
    assert limits_deg == [
        (-165, 165),
        (-100, 100),
        (-70, 90),
        (-160, 160),
        (-130, 130),
        (-360, 360),
    ]


def test_inside_limits_ok():
    q = np.deg2rad([165, -100, 90, -160, 130, 360])
    assert np.allclose(check_joint_limits(q), q)


def test_each_joint_violation_detected():
    limits = parameter_store.spec.joint_limits_deg
    for j in range(6):
        for side in (+1, -1):
            q = np.zeros(6)
            q[j] = np.deg2rad(limits[j][1 if side > 0 else 0] + side * 1.0)
            with pytest.raises(JointLimitError):
                check_joint_limits(q)


def test_wrong_dof_rejected():
    with pytest.raises(JointLimitError):
        check_joint_limits(np.zeros(5))

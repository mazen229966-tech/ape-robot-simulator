"""Trajectory tests: polynomials, boundaries, finiteness (spec §40)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.robotics.trajectory import (
    cubic_trajectory,
    plan_cartesian_trajectory,
    plan_joint_trajectory,
    quintic_trajectory,
)
from app.utils.errors import TrajectoryError

Q0 = [0.0, -35.0, 55.0, 0.0, -20.0, 0.0]
QF = [30.0, 20.0, 80.0, -40.0, 50.0, 90.0]


@pytest.mark.parametrize("method", ["cubic", "quintic"])
def test_joint_trajectory_endpoints(method):
    traj = plan_joint_trajectory(Q0, QF, 3.0, 200, method)
    q = np.array(traj["q"])
    assert np.allclose(q[0], np.deg2rad(Q0), atol=1e-9)
    assert np.allclose(q[-1], np.deg2rad(QF), atol=1e-9)
    assert math.isclose(traj["duration"], 3.0)
    assert traj["samples"] == 200


def test_quintic_rest_boundary_conditions():
    traj = quintic_trajectory(np.zeros(6), np.ones(6), 2.0, 100)
    assert np.allclose(traj["qd"][0], 0, atol=1e-12)
    assert np.allclose(traj["qd"][-1], 0, atol=1e-12)
    assert np.allclose(traj["qdd"][0], 0, atol=1e-12)
    assert np.allclose(traj["qdd"][-1], 0, atol=1e-12)


def test_cubic_rest_boundary_conditions():
    traj = cubic_trajectory(np.zeros(6), np.ones(6), 2.0, 100)
    assert np.allclose(traj["qd"][0], 0, atol=1e-12)
    assert np.allclose(traj["qd"][-1], 0, atol=1e-12)


def test_cubic_position_midpoint():
    traj = cubic_trajectory(np.zeros(6), np.ones(6), 2.0, 101)
    # cubic with rest ends passes through the midpoint at t = T/2
    mid = traj["q"][50]
    assert np.allclose(mid, 0.5, atol=1e-9)


@pytest.mark.parametrize("method", ["cubic", "quintic"])
def test_joint_trajectory_no_nan_no_explosion(method):
    traj = plan_joint_trajectory(Q0, QF, 5.0, 400, method)
    for key in ("t", "q", "qd", "qdd", "ee_path"):
        arr = np.array(traj[key])
        assert np.all(np.isfinite(arr)), f"{key} not finite"
    assert np.max(np.abs(np.array(traj["qd"]))) < 20.0  # rad/s sanity


def test_joint_trajectory_rejects_bad_input():
    with pytest.raises(TrajectoryError):
        plan_joint_trajectory(Q0, QF, -1.0, 100, "quintic")
    with pytest.raises(TrajectoryError):
        plan_joint_trajectory([0] * 6, [0] * 6, 2.0, 100, "spline9")
    with pytest.raises(Exception):
        plan_joint_trajectory(Q0, [200.0, 0, 0, 0, 0, 0], 2.0, 100, "cubic")


def test_cartesian_trajectory_through_waypoints():
    points = [
        {"x": 0.24, "y": 0.0, "z": 0.28, "t": 0.0},
        {"x": 0.28, "y": 0.05, "z": 0.28, "t": 2.0},
        {"x": 0.30, "y": 0.0, "z": 0.28, "t": 4.0},
    ]
    traj = plan_cartesian_trajectory(points, dt=0.05)
    q = np.array(traj["q"])
    ee = np.array(traj["ee_path"])
    assert np.all(np.isfinite(q))
    # start and end match the requested waypoints
    assert np.allclose(ee[0], [0.24, 0.0, 0.28], atol=1e-3)
    assert np.allclose(ee[-1], [0.30, 0.0, 0.28], atol=1e-3)
    # joint limits respected along the whole trajectory
    limits = np.array(
        [
            [math.radians(lo), math.radians(hi)]
            for lo, hi in [
                (-165, 165), (-100, 100), (-70, 90),
                (-160, 160), (-130, 130), (-360, 360),
            ]
        ]
    )
    assert np.all(q >= limits[:, 0] - 1e-6)
    assert np.all(q <= limits[:, 1] + 1e-6)


def test_cartesian_trajectory_rejects_bad_times():
    points = [
        {"x": 0.24, "y": 0.0, "z": 0.28, "t": 0.0},
        {"x": 0.28, "y": 0.05, "z": 0.28, "t": 0.0},
    ]
    with pytest.raises(TrajectoryError):
        plan_cartesian_trajectory(points)

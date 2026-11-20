"""Dynamics tests: dimensions, finiteness, RNE agreement (spec §40)."""

from __future__ import annotations

import numpy as np

from app.robotics.dynamics import compute_torque, compute_torque_trajectory
from app.robotics.robot import create_robot
from app.robotics.trajectory import plan_joint_trajectory


def test_torque_components_match_rne(rng):
    robot = create_robot()
    for _ in range(5):
        q = rng.uniform(-1.0, 1.0, 6)
        qd = rng.uniform(-1.5, 1.5, 6)
        qdd = rng.uniform(-3.0, 3.0, 6)
        comp = compute_torque(q, qd, qdd)
        rne = np.asarray(robot.rne(q, qd, qdd)).ravel()
        assert np.allclose(comp["total"], rne, atol=1e-9)
        total = (
            comp["inertia"] + comp["coriolis"] + comp["gravity"] + comp["friction"]
        )
        assert np.allclose(total, comp["total"], atol=1e-12)


def test_static_gravity_only(rng):
    """With zero velocity/acceleration only gravity torque remains."""
    q = rng.uniform(-0.8, 0.8, 6)
    comp = compute_torque(q, np.zeros(6), np.zeros(6))
    assert np.allclose(comp["inertia"], 0, atol=1e-12)
    assert np.allclose(comp["coriolis"], 0, atol=1e-12)
    assert np.allclose(comp["friction"], 0, atol=1e-12)
    assert np.allclose(comp["total"], comp["gravity"], atol=1e-12)
    # J1 rotates about the vertical axis: gravity produces no J1 torque.
    assert abs(comp["gravity"][0]) < 1e-6


def test_gravity_load_magnitude_plausible():
    """Holding the arm straight out: tau2 ~ sum(m_i g x_i)."""
    comp = compute_torque(np.zeros(6), np.zeros(6), np.zeros(6))
    tau2 = comp["gravity"][1]
    assert 20.0 < tau2 < 150.0  # N m, plausible for a 23 kg arm


def test_trajectory_torque_dimensions_and_finiteness():
    traj = plan_joint_trajectory(
        [0, -35, 55, 0, -20, 0], [30, 20, 80, -40, 50, 90], 3.0, 80, "quintic"
    )
    dyn = compute_torque_trajectory(traj["t"], traj["q"], traj["qd"], traj["qdd"])
    n = traj["samples"]
    for name, arr in dyn["components"].items():
        a = np.array(arr)
        assert a.shape == (n, 6), name
        assert np.all(np.isfinite(a)), name
    assert dyn["rne_discrepancy_nm"] < 1e-6
    stats = dyn["stats"]["per_joint"]
    assert len(stats) == 6
    for s in stats:
        assert s["max_abs_torque_nm"] >= 0
        assert s["rms_torque_nm"] >= 0
        assert s["rms_torque_nm"] <= s["max_abs_torque_nm"] + 1e-9
    assert dyn["parameter_source"] == "Educational / Assumed"

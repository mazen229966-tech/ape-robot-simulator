"""DH model tests: matrix form, chain composition, toolbox agreement."""

from __future__ import annotations

import math

import numpy as np

from app.models.parameters import parameter_store
from app.robotics.dh import dh_chain, dh_frame_list, dh_transform
from app.robotics.validation import fk_matches_toolbox


def test_dh_transform_matches_expanded_matrix():
    """A_i must equal the textbook expanded standard-DH matrix."""
    theta, d, a, alpha = 0.7, 0.15, 0.25, -1.1
    A = dh_transform(theta, d, a, alpha)
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    expected = np.array(
        [
            [ct, -st * ca, st * sa, a * ct],
            [st, ct * ca, -ct * sa, a * st],
            [0.0, sa, ca, d],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    assert np.allclose(A, expected, atol=1e-12)


def test_dh_transform_is_rigid():
    A = dh_transform(0.3, 0.1, 0.2, math.pi / 3)
    R = A[:3, :3]
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert np.isclose(np.linalg.det(R), 1.0)
    assert np.allclose(A[3, :], [0, 0, 0, 1])


def test_chain_matches_manual_product():
    q = [0.1, -0.4, 0.9, 0.0, 0.5, -1.2]
    table = parameter_store.dh_table()
    T = dh_chain(q, table)
    manual = np.eye(4)
    for qi, (_, d, a, alpha) in zip(q, table):
        manual = manual @ dh_transform(qi, d, a, alpha)
    assert np.allclose(T, manual, atol=1e-12)


def test_frame_list_consistency():
    q = [0.2, 0.3, -0.5, 1.0, 0.4, 0.6]
    frames = dh_frame_list(q, parameter_store.dh_table())
    assert len(frames) == 7
    assert np.allclose(frames[0], np.eye(4))
    assert np.allclose(frames[-1], dh_chain(q, parameter_store.dh_table()))


def test_numpy_chain_matches_robotics_toolbox(rng):
    """Our NumPy FK must agree with Robotics Toolbox for random configs."""
    limits = np.array(parameter_store.spec.joint_limits_rad)
    for _ in range(8):
        q = rng.uniform(limits[:, 0], limits[:, 1])
        assert fk_matches_toolbox(q, atol=1e-9)


def test_workspace_reach_matches_official_max_radius():
    """Monte-Carlo workspace radius matches the official 454 mm max radius.

    The educational DH model is dimensioned so that the sampled workspace
    (uniform sampling inside the official joint limits) reaches ~454 mm.
    """
    from app.robotics.workspace import generate_workspace

    ws = generate_workspace(30_000, seed=2026)
    assert 445.0 <= ws["reach_mm"] <= 462.0

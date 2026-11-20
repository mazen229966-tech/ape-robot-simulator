"""Workspace tests (spec §40)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.models.parameters import parameter_store
from app.robotics.workspace import generate_workspace


def test_workspace_bounds_and_finiteness():
    ws = generate_workspace(5000, seed=42)
    b = ws["bounds_mm"]
    assert ws["samples"] == 5000
    assert ws["valid_samples"] == 5000
    for key, value in b.items():
        assert math.isfinite(value)
    assert b["x_max"] > b["x_min"]
    assert b["y_max"] > b["y_min"]
    assert b["z_max"] > b["z_min"]
    # Point cloud is finite and has the right size.
    pts = np.array(ws["points_mm"]).reshape(-1, 3)
    assert np.all(np.isfinite(pts))
    assert pts.shape[0] == ws["displayed_points"]


def test_workspace_envelope_within_geometry():
    """Everything must fit inside the robot's geometric envelope."""
    ws = generate_workspace(8000, seed=7)
    dh = parameter_store.dh_table()
    # absolute upper bound: sum of all |a| + |d| link dimensions
    envelope = sum(abs(r[1]) + abs(r[2]) for r in dh) * 1e3  # mm
    b = ws["bounds_mm"]
    for key, value in b.items():
        assert abs(value) <= envelope * 1.01
    assert ws["reach_mm"] <= envelope * 1.01


def test_workspace_symmetric_about_base_axis():
    """J1 spans +/-165 deg so the cloud is nearly rotationally symmetric."""
    ws = generate_workspace(8000, seed=9)
    b = ws["bounds_mm"]
    assert abs(b["x_max"] + b["x_min"]) < 0.15 * max(abs(b["x_max"]), 1)
    assert abs(b["y_max"] + b["y_min"]) < 0.15 * max(abs(b["y_max"]), 1)


def test_workspace_sample_validation():
    with pytest.raises(Exception):
        generate_workspace(10)  # below minimum
    with pytest.raises(Exception):
        generate_workspace(10**7)  # above maximum


def test_workspace_display_downsampling():
    ws = generate_workspace(60000, seed=3)
    assert ws["valid_samples"] == 60000
    assert ws["displayed_points"] <= 20000

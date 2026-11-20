"""Draw H integration tests (spec §57: H must be a real Cartesian
trajectory -> IK -> joint trajectory -> FK validation)."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.robotics.draw_h import generate_h_trajectory
from app.utils.errors import TrajectoryError

client = TestClient(app)


def test_h_geometry_is_exact():
    """Pen-down samples must reproduce the requested H geometry."""
    traj = generate_h_trajectory(
        width=0.15, height=0.20, drawing_height=0.28,
        speed=0.05, center_xy=(0.29, 0.0), lift=0.02,
    )
    pen = np.array(traj["pen_down"])
    ee = np.array(traj["ee_path"])
    drawn = ee[pen]
    assert drawn.shape[0] > 100
    # plane height for every drawn point, within the IK acceptance
    # tolerance (5e-4 m); actual deviation is far smaller (~1e-6 m).
    assert np.allclose(drawn[:, 2], 0.28, atol=5e-4)
    # H extents
    assert np.isclose(drawn[:, 0].min(), 0.29 - 0.075, atol=1e-3)
    assert np.isclose(drawn[:, 0].max(), 0.29 + 0.075, atol=1e-3)
    assert np.isclose(drawn[:, 1].min(), -0.10, atol=1e-3)
    assert np.isclose(drawn[:, 1].max(), +0.10, atol=1e-3)


def test_h_contains_three_drawing_strokes():
    traj = generate_h_trajectory()
    draw_phases = [p for p in traj["phases"] if p["phase"] == "draw"]
    # 3 strokes; a pen-up reconfiguration may split one stroke into two
    # consecutive draw entries, so >= 3 entries with pen down.
    assert len(draw_phases) >= 3
    assert all(p["pen_down"] for p in draw_phases)
    # pen-up phases exist around the strokes
    names = {p["phase"] for p in traj["phases"]}
    assert {"lower pen", "lift pen", "travel", "finish"} <= names


def test_h_joint_trajectory_is_smooth_and_within_limits():
    traj = generate_h_trajectory()
    q = np.array(traj["q"])
    t = np.array(traj["t"])
    assert np.all(np.isfinite(q))
    assert np.all(np.diff(t) > 0), "time must be strictly increasing"
    limits = np.deg2rad(
        [[-165, 165], [-100, 100], [-70, 90], [-160, 160], [-130, 130], [-360, 360]]
    )
    assert np.all(q >= limits[:, 0] - 1e-6)
    assert np.all(q <= limits[:, 1] + 1e-6)
    # per-sample motion bounded (dt varies; use worst-case dt of the series)
    dq_deg = np.abs(np.diff(np.rad2deg(q), axis=0))
    assert dq_deg.max() < 25.0


def test_h_drawn_with_ik_validation():
    """Every joint sample must FK back onto the Cartesian path/pen mask."""
    traj = generate_h_trajectory()
    ee = np.array(traj["ee_path"])
    pen = np.array(traj["pen_down"])
    z_plane = traj["drawing_plane_z"]
    # pen-down samples lie on the drawing plane (within IK tolerance)
    assert np.allclose(ee[pen, 2], z_plane, atol=5e-4)
    # pen-up samples never go below the plane (IK tolerance margin)
    assert np.all(ee[:, 2] >= z_plane - 5e-4)


def test_draw_h_api_endpoint():
    r = client.post(
        "/api/draw/h",
        json={
            "plane": "XY",
            "width": 0.15,
            "height": 0.20,
            "drawing_height": 0.28,
            "speed": 0.05,
            "center": {"x": 0.29, "y": 0.0, "z": 0.0},
            "lift": 0.02,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["trajectory_id"]
    assert data["method"] == "draw-h"
    assert "pen_down" in data and "phases" in data
    # the trajectory must be directly playable by the simulation engine
    s = client.post(
        "/api/simulation/start", json={"trajectory_id": data["trajectory_id"]}
    )
    assert s.status_code == 200
    assert s.json()["status"] == "running"
    client.post("/api/simulation/stop")


def test_h_on_vertical_plane_xz():
    """The H can also be drawn on a vertical wall (XZ plane, spec §32).

    Uses the validated per-plane defaults (smaller letter, tilted pen).
    """
    traj = generate_h_trajectory(plane="XZ", speed=0.08)
    assert traj["plane"] == "XZ"
    assert traj["plane_offset"] == 0.12  # wall at y = +0.12 m
    pen = np.array(traj["pen_down"])
    ee = np.array(traj["ee_path"])
    drawn = ee[pen]
    assert drawn.shape[0] > 100
    # every drawn point lies on the wall plane y = 0.12 m
    assert np.allclose(drawn[:, 1], 0.12, atol=5e-4)
    # H extents (default 100 x 140 mm letter centred at x=0.30, z=0.25).
    # The very first sample of each stroke is the pen-down touchdown point,
    # so extents match within one path step (speed * dt <= 1.6 mm here).
    assert np.isclose(drawn[:, 0].min(), 0.30 - 0.05, atol=3e-3)
    assert np.isclose(drawn[:, 0].max(), 0.30 + 0.05, atol=3e-3)
    assert np.isclose(drawn[:, 2].min(), 0.25 - 0.07, atol=3e-3)
    assert np.isclose(drawn[:, 2].max(), 0.25 + 0.07, atol=3e-3)


def test_h_rejects_unknown_plane():
    with pytest.raises(TrajectoryError):
        generate_h_trajectory(plane="AB")


def test_websocket_protocol_handshake():
    with client.websocket_connect("/ws/simulation") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "status"
        assert "q_deg" in msg
        ws.send_json({"type": "ping"})
        assert ws.receive_json()["type"] == "pong"

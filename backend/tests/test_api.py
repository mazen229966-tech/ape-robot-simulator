"""API integration tests (spec §40: end-to-end through FastAPI)."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_robot_endpoint():
    r = client.get("/api/robot")
    assert r.status_code == 200
    data = r.json()
    assert data["dof"] == 6
    assert data["official_specs"]["payload_rated_kg"] == 1.0
    assert "Educational" in data["kinematic_parameter_source"]
    assert "state" in data
    assert len(data["state"]["q_deg"]) == 6


def test_dh_get_and_export():
    r = client.get("/api/dh")
    assert r.status_code == 200
    data = r.json()
    assert len(data["links"]) == 6
    assert data["convention"].startswith("Standard")
    assert "Educational" in data["parameter_source"]
    r_csv = client.get("/api/dh/export?format=csv")
    assert r_csv.status_code == 200
    assert "theta" in r_csv.text


def test_dh_apply_and_reset():
    orig = client.get("/api/dh").json()
    modified = {
        "links": [
            {"d": l["d_m"], "a": l["a_m"], "alpha": math.degrees(l["alpha_rad"])}
            for l in orig["links"]
        ]
    }
    modified["links"][0]["d"] = 0.17
    r = client.post("/api/dh/apply", json=modified)
    assert r.status_code == 200
    assert "User modified" in r.json()["parameter_source"]
    r = client.post("/api/dh/reset")
    assert "Educational" in r.json()["parameter_source"]


def test_fk_endpoint_matches_spec_example():
    r = client.post(
        "/api/fk", json={"q": [30, -20, 40, 10, 30, 0], "unit": "deg"}
    )
    assert r.status_code == 200
    data = r.json()
    assert set(data["position"]) == {"x", "y", "z"}
    assert set(data["orientation"]) == {"roll", "pitch", "yaw"}
    assert len(data["transform"]) == 4
    # position in metres (SI internal convention)
    assert all(abs(v) < 1.5 for v in data["position"].values())


def test_fk_rejects_limit_violation():
    r = client.post("/api/fk", json={"q": [0, 0, 0, 0, 0, 400], "unit": "deg"})
    assert r.status_code == 422
    assert "Joint limit exceeded" in r.json()["detail"]


def test_ik_round_trip():
    fk = client.post(
        "/api/fk", json={"q": [10, -50, 70, 0, 60, 0], "unit": "deg"}
    ).json()
    pos = fk["position"]
    orient = fk["orientation"]
    r = client.post(
        "/api/ik",
        json={
            "position": pos,
            "orientation": orient,
            "q_guess": {"q": [10, -50, 70, 0, 60, 0], "unit": "deg"},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["valid"]
    assert data["position_error_mm"] < 0.5
    assert data["orientation_error_deg"] < 0.5


def test_ik_unreachable():
    r = client.post(
        "/api/ik",
        json={
            "position": {"x": 3.0, "y": 0.0, "z": 0.3},
            "orientation": {"roll": 180, "pitch": 0, "yaw": 0},
        },
    )
    assert r.status_code == 422


def test_workspace_endpoint():
    r = client.post("/api/workspace", json={"samples": 3000, "seed": 5})
    assert r.status_code == 200
    data = r.json()
    assert data["samples"] == 3000
    assert "bounds_mm" in data
    assert len(data["points_mm"]) == data["displayed_points"] * 3


def test_joint_trajectory_and_dynamics_flow():
    r = client.post(
        "/api/trajectory/joint",
        json={
            "q0": [0, -35, 55, 0, -20, 0],
            "qf": [30, 20, 80, -40, 50, 90],
            "duration": 3.0,
            "samples": 120,
            "method": "quintic",
        },
    )
    assert r.status_code == 200
    traj = r.json()
    tid = traj["trajectory_id"]
    assert tid

    d = client.post("/api/dynamics", json={"trajectory_id": tid})
    assert d.status_code == 200
    dyn = d.json()
    assert dyn["rne_discrepancy_nm"] < 1e-6
    assert len(dyn["stats"]["per_joint"]) == 6

    csv = client.get(f"/api/export/trajectory?trajectory_id={tid}&format=csv")
    assert csv.status_code == 200
    assert "q1_rad" in csv.text and "tau1_Nm" in csv.text


def test_simulation_lifecycle():
    r = client.post(
        "/api/trajectory/joint",
        json={
            "q0": [0, -35, 55, 0, -20, 0],
            "qf": [10, -25, 60, 0, -10, 20],
            "duration": 1.0,
            "samples": 50,
            "method": "cubic",
        },
    )
    tid = r.json()["trajectory_id"]
    r = client.post("/api/simulation/start", json={"trajectory_id": tid})
    assert r.status_code == 200
    assert r.json()["status"] == "running"
    r = client.post("/api/simulation/stop")
    assert r.json()["status"] == "stopped"
    r = client.get("/api/simulation")
    assert r.status_code == 200


def test_error_messages_are_clean():
    """No tracebacks leak to the client (spec §39)."""
    r = client.post("/api/dynamics", json={"trajectory_id": "does-not-exist"})
    assert r.status_code == 400
    assert "Traceback" not in r.text

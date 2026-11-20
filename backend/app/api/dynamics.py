"""Dynamics / torque endpoint (spec §27-30)."""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import DynamicsRequest
from ..robotics.dynamics import compute_torque_trajectory
from ..simulation.state import trajectory_store
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api", tags=["dynamics"])


@router.post("/dynamics")
def dynamics(req: DynamicsRequest) -> dict:
    try:
        traj = trajectory_store.get(req.trajectory_id)
        result = compute_torque_trajectory(
            traj["t"], traj["q"], traj["qd"], traj["qdd"]
        )
        # Attach torque to the trajectory so CSV export can include it (§44).
        traj["total_torque"] = result["components"]["total"]
        return result
    except RoboticsError as exc:
        raise_api_error(exc)

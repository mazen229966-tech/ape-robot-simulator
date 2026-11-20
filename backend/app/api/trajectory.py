"""Trajectory planning endpoints (spec §20, §21)."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter

from ..models.schemas import CartesianTrajectoryRequest, JointTrajectoryRequest
from ..robotics.trajectory import (
    plan_cartesian_trajectory,
    plan_joint_trajectory,
)
from ..simulation.state import trajectory_store
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api/trajectory", tags=["trajectory"])


@router.post("/joint")
def trajectory_joint(req: JointTrajectoryRequest) -> dict:
    try:
        if req.unit == "rad":
            q0 = np.rad2deg(req.q0).tolist()
            qf = np.rad2deg(req.qf).tolist()
        else:
            q0, qf = req.q0, req.qf
        traj = plan_joint_trajectory(q0, qf, req.duration, req.samples, req.method)
        traj["trajectory_id"] = trajectory_store.put(traj)
        return traj
    except RoboticsError as exc:
        raise_api_error(exc)


@router.post("/cartesian")
def trajectory_cartesian(req: CartesianTrajectoryRequest) -> dict:
    try:
        points = [p.model_dump() for p in req.points]
        rpy_deg = None
        if req.orientation is not None:
            rpy_deg = [
                req.orientation.roll,
                req.orientation.pitch,
                req.orientation.yaw,
            ]
        q_start_deg = None
        if req.q_start is not None:
            q_start_deg = (
                req.q_start.q
                if req.q_start.unit == "deg"
                else np.rad2deg(req.q_start.q).tolist()
            )
        traj = plan_cartesian_trajectory(
            points, orientation_rpy_deg=rpy_deg, dt=req.dt, q_start_deg=q_start_deg
        )
        traj["trajectory_id"] = trajectory_store.put(traj)
        return traj
    except RoboticsError as exc:
        raise_api_error(exc)

"""Draw-H endpoint (spec §31-34, §57)."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter

from ..models.schemas import DrawHRequest
from ..robotics.draw_h import generate_h_trajectory
from ..simulation.state import trajectory_store
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api", tags=["draw-h"])


@router.post("/draw/h")
def draw_h(req: DrawHRequest) -> dict:
    try:
        center_xy = None
        if req.center is not None:
            center_xy = (req.center.x, req.center.y)
        q_start_deg = None
        if req.q_start is not None:
            q_start_deg = (
                req.q_start.q
                if req.q_start.unit == "deg"
                else np.rad2deg(req.q_start.q).tolist()
            )
        traj = generate_h_trajectory(
            plane=req.plane,
            width=req.width,
            height=req.height,
            drawing_height=req.drawing_height,
            speed=req.speed,
            center_xy=center_xy,
            lift=req.lift,
            q_start_deg=q_start_deg,
        )
        traj["trajectory_id"] = trajectory_store.put(traj)
        return traj
    except RoboticsError as exc:
        raise_api_error(exc)

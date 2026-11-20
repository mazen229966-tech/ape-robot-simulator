"""Forward kinematics endpoint (spec §11, §38)."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter

from ..models.schemas import FKRequest
from ..robotics.kinematics import (
    check_joint_limits,
    forward_kinematics_result,
)
from ..simulation.state import robot_state
from ..utils.errors import RoboticsError, raise_api_error
from ..utils.units import deg_to_rad, rad_to_deg

router = APIRouter(prefix="/api", tags=["kinematics"])


@router.post("/fk")
def compute_fk(req: FKRequest) -> dict:
    try:
        q_rad = (
            deg_to_rad(req.q)
            if req.unit == "deg"
            else np.asarray(req.q, dtype=np.float64)
        )
        q_rad = check_joint_limits(q_rad)
        result = forward_kinematics_result(q_rad)
        robot_state.set_q(q_rad)
        return {
            "q_deg": rad_to_deg(q_rad).round(6).tolist(),
            "position": result["position"],
            "position_mm": {
                k: round(v * 1e3, 4) for k, v in result["position"].items()
            },
            "orientation": result["orientation"],
            "transform": [[round(v, 9) for v in row] for row in result["transform"]],
        }
    except RoboticsError as exc:
        raise_api_error(exc)

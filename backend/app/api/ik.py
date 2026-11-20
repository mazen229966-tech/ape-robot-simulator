"""Inverse kinematics endpoint with FK validation (spec §13, §14)."""

from __future__ import annotations

import math

from fastapi import APIRouter

from ..models.schemas import IKRequest
from ..robotics.inverse_kinematics import inverse_kinematics
from ..robotics.kinematics import forward_kinematics_result
from ..simulation.state import robot_state
from ..utils.errors import RoboticsError, raise_api_error
from ..utils.units import deg_to_rad, rpy_to_matrix

router = APIRouter(prefix="/api", tags=["kinematics"])


@router.post("/ik")
def compute_ik(req: IKRequest) -> dict:
    try:
        R = rpy_to_matrix(
            math.radians(req.orientation.roll),
            math.radians(req.orientation.pitch),
            math.radians(req.orientation.yaw),
        )
        q_guess = None
        if req.q_guess is not None:
            q_guess = (
                deg_to_rad(req.q_guess.q)
                if req.q_guess.unit == "deg"
                else req.q_guess.q
            )
        sol = inverse_kinematics(
            [req.position.x, req.position.y, req.position.z], R, q_guess
        )
        q_rad = sol["q"]
        fk = forward_kinematics_result(q_rad)
        robot_state.set_q(q_rad)
        return {
            "q_deg": [round(math.degrees(v), 4) for v in q_rad],
            "q_rad": [round(float(v), 9) for v in q_rad],
            "position_error_mm": round(sol["position_error_mm"], 4),
            "orientation_error_deg": round(sol["orientation_error_deg"], 4),
            "valid": sol["valid"],
            "fk_validation": {
                "position": fk["position"],
                "orientation": fk["orientation"],
            },
        }
    except RoboticsError as exc:
        raise_api_error(exc)

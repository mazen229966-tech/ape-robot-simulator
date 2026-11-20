"""Robot information and shared state endpoints.

GET  /api/robot         -- robot metadata + live state (all pages, §68)
POST /api/robot/state   -- set the current joint configuration
POST /api/robot/preset  -- home / zero presets
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from ..models.parameters import parameter_store
from ..models.schemas import RobotStateRequest
from ..robotics.kinematics import (
    check_joint_limits,
    forward_kinematics_result,
)
from ..simulation.state import robot_state
from ..utils.errors import RoboticsError, raise_api_error
from ..utils.units import deg_to_rad, rad_to_deg

router = APIRouter(prefix="/api", tags=["robot"])


def _state_payload(q_rad: np.ndarray) -> dict:
    fk = forward_kinematics_result(q_rad)
    return {
        "q_deg": rad_to_deg(q_rad).round(6).tolist(),
        "q_rad": q_rad.round(9).tolist(),
        "end_effector": fk,
    }


@router.get("/robot")
def get_robot() -> dict:
    spec = parameter_store.spec
    q = robot_state.q
    return {
        "name": spec.name,
        "manufacturer": spec.manufacturer,
        "dof": spec.dof,
        "official_specs": spec.official_specs,
        "joint_limits_deg": [list(lim) for lim in spec.joint_limits_deg],
        "joint_speeds_deg_s": spec.joint_speeds_deg_s,
        "home_position_deg": spec.home_position_deg,
        "kinematic_parameter_source": parameter_store.source,
        "dynamic_parameter_source": spec.dynamics_source,
        "gravity_m_s2": spec.gravity_m_s2,
        "state": _state_payload(q),
    }


class PresetRequest(BaseModel):
    preset: Literal["home", "zero"]


@router.post("/robot/state")
def set_robot_state(req: RobotStateRequest) -> dict:
    try:
        q_rad = deg_to_rad(req.q) if req.unit == "deg" else np.asarray(req.q)
        q_rad = check_joint_limits(q_rad)
        robot_state.set_q(q_rad)
        return _state_payload(q_rad)
    except RoboticsError as exc:
        raise_api_error(exc)


@router.post("/robot/preset")
def robot_preset(req: PresetRequest) -> dict:
    spec = parameter_store.spec
    if req.preset == "home":
        q_deg = np.array(spec.home_position_deg)
    else:
        q_deg = np.zeros(spec.dof)
    q_rad = check_joint_limits(deg_to_rad(q_deg))
    robot_state.set_q(q_rad)
    return _state_payload(q_rad)

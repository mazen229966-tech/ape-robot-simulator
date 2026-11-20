"""Pydantic request/response models for the REST API (spec §37)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

JOINT_COUNT = 6


class JointAngles(BaseModel):
    """Six joint values with an explicit unit."""

    q: List[float] = Field(..., min_length=JOINT_COUNT, max_length=JOINT_COUNT)
    unit: Literal["deg", "rad"] = "deg"

    @field_validator("q")
    @classmethod
    def _finite(cls, v):
        import math

        if not all(math.isfinite(x) for x in v):
            raise ValueError("Joint values must be finite.")
        return v


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class Orientation(BaseModel):
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class FKRequest(JointAngles):
    pass


class IKRequest(BaseModel):
    position: Vec3  # metres
    orientation: Orientation = Field(
        default_factory=Orientation,
        description="Tool orientation in degrees (ZYX roll/pitch/yaw).",
    )
    q_guess: Optional[JointAngles] = None


class WorkspaceRequest(BaseModel):
    samples: int = Field(default=10_000, ge=100, le=200_000)
    seed: Optional[int] = None


class JointTrajectoryRequest(BaseModel):
    q0: List[float] = Field(..., min_length=JOINT_COUNT, max_length=JOINT_COUNT)
    qf: List[float] = Field(..., min_length=JOINT_COUNT, max_length=JOINT_COUNT)
    duration: float = Field(..., gt=0, le=600)
    samples: int = Field(default=250, ge=2, le=5000)
    method: Literal["cubic", "quintic"] = "quintic"
    unit: Literal["deg", "rad"] = "deg"


class CartesianPoint(BaseModel):
    x: float  # metres
    y: float
    z: float
    t: float = Field(..., ge=0)


class CartesianTrajectoryRequest(BaseModel):
    points: List[CartesianPoint] = Field(..., min_length=2)
    orientation: Optional[Orientation] = Field(
        default=None,
        description="Constant tool orientation (deg). Default: tool down.",
    )
    dt: float = Field(default=0.02, ge=0.005, le=0.2)
    q_start: Optional[JointAngles] = None


class DynamicsRequest(BaseModel):
    trajectory_id: Optional[str] = Field(
        default=None,
        description="Defaults to the most recently generated trajectory.",
    )


class DrawHRequest(BaseModel):
    plane: Literal["XY", "XZ", "YZ"] = "XY"
    width: Optional[float] = Field(
        default=None, gt=0.01, le=0.5, description="metres (per-plane default if omitted)"
    )
    height: Optional[float] = Field(
        default=None, gt=0.01, le=0.5, description="metres (per-plane default if omitted)"
    )
    drawing_height: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=0.6,
        description=(
            "XY: plane height z [m]. XZ/YZ: z of the H centre [m]. "
            "Defaults per plane when omitted."
        ),
    )
    speed: float = Field(default=0.05, gt=0.001, le=0.5, description="m/s")
    center: Optional[Vec3] = Field(
        default=None,
        description=(
            "XY: H centre (x, y). XZ: (centre x, plane offset y). "
            "YZ: (plane offset x, centre y). z is always drawing_height."
        ),
    )
    lift: float = Field(
        default=0.02, gt=0.001, le=0.2, description="pen lift height [m]"
    )
    q_start: Optional[JointAngles] = None


class SimulationStartRequest(BaseModel):
    trajectory_id: Optional[str] = None
    speed: float = Field(default=1.0, gt=0.0, le=10.0)


class RobotStateRequest(JointAngles):
    pass


class DHRow(BaseModel):
    d: float = Field(..., description="metres")
    a: float = Field(..., description="metres")
    alpha: float = Field(..., description="degrees")


class DHApplyRequest(BaseModel):
    links: List[DHRow] = Field(..., min_length=JOINT_COUNT, max_length=JOINT_COUNT)

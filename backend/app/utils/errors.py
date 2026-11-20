"""Domain exceptions and API-safe error mapping.

Exceptions raised by the robotics engine are translated into user-friendly
messages; raw Python tracebacks are never exposed to the client (spec §39).
"""

from __future__ import annotations

from fastapi import HTTPException, status


class RoboticsError(Exception):
    """Base class for all domain errors."""


class RobotModelError(RoboticsError):
    """Invalid robot model / parameter configuration."""


class JointLimitError(RoboticsError):
    """Requested joint configuration exceeds the published joint limits."""


class InvalidParameterError(RoboticsError):
    """Invalid input parameter (DH row, trajectory input, ...)."""


class IKNoSolutionError(RoboticsError):
    """Inverse kinematics could not find a valid solution."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message or "No valid IK solution found within joint limits."
        )


class IKUnreachableError(RoboticsError):
    """Target pose lies outside the reachable workspace."""

    def __init__(self, message: str | None = None):
        super().__init__(message or "Target is outside reachable workspace.")


class TrajectoryError(RoboticsError):
    """Trajectory generation failed."""


class SimulationError(RoboticsError):
    """Simulation engine error."""


def raise_api_error(exc: RoboticsError) -> None:
    """Convert a domain error to an HTTPException with a clean message."""
    if isinstance(exc, JointLimitError):
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(exc, (IKNoSolutionError, IKUnreachableError)):
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(exc, TrajectoryError):
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(exc, InvalidParameterError):
        code = status.HTTP_400_BAD_REQUEST
    else:
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
    raise HTTPException(status_code=code, detail=str(exc))

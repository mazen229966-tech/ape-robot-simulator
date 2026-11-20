"""Workspace endpoint (spec §15, §16)."""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import WorkspaceRequest
from ..robotics.workspace import generate_workspace
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api", tags=["workspace"])


@router.post("/workspace")
def workspace(req: WorkspaceRequest) -> dict:
    try:
        return generate_workspace(req.samples, req.seed)
    except RoboticsError as exc:
        raise_api_error(exc)

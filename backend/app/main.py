"""FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

API documentation is served at /docs (spec §63).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import dh, draw, dynamics, export, fk, ik, robot_api, simulation, trajectory, workspace
from .api.simulation import simulation_websocket
from .utils.errors import RoboticsError

app = FastAPI(
    title="APE SV2-6045 Robot Simulator API",
    description=(
        "Robotics computation engine for the APE SV2-6045 6-DOF industrial "
        "robot simulation platform. All kinematic and dynamic parameters are "
        "EDUCATIONAL / ASSUMED unless explicitly marked official."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(robot_api.router)
app.include_router(dh.router)
app.include_router(fk.router)
app.include_router(ik.router)
app.include_router(workspace.router)
app.include_router(trajectory.router)
app.include_router(dynamics.router)
app.include_router(draw.router)
app.include_router(simulation.router)
app.include_router(export.router)

app.add_api_websocket_route("/ws/simulation", simulation_websocket)


@app.exception_handler(RoboticsError)
async def robotics_error_handler(_: Request, exc: RoboticsError) -> JSONResponse:
    """Domain errors become clean JSON messages (spec §39)."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(_: Request, __: Exception) -> JSONResponse:
    """No raw tracebacks are ever exposed to the UI."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal computation error. Please retry."},
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "ape-robot-simulator"}

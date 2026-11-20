"""Simulation control endpoints + WebSocket stream (spec §36, §51)."""

from __future__ import annotations

import asyncio
import json

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.schemas import SimulationStartRequest
from ..simulation.engine import simulation_engine
from ..simulation.state import robot_state
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

FRAME_INTERVAL_S = 1.0 / 30.0  # ~30 Hz WebSocket stream


@router.post("/start")
async def sim_start(req: SimulationStartRequest) -> dict:
    try:
        return await simulation_engine.start(req.trajectory_id, req.speed)
    except RoboticsError as exc:
        raise_api_error(exc)


@router.post("/stop")
async def sim_stop() -> dict:
    """Simulation stop (NOT a real industrial emergency stop, §51)."""
    return await simulation_engine.stop()


@router.post("/pause")
async def sim_pause() -> dict:
    return await simulation_engine.pause()


@router.post("/resume")
async def sim_resume() -> dict:
    return await simulation_engine.resume()


@router.get("")
def sim_status() -> dict:
    return simulation_engine.describe()


async def simulation_websocket(websocket: WebSocket) -> None:
    """Stream simulation frames to the client.

    Client -> server messages (JSON):
        {"type": "start", "trajectory_id": "...", "speed": 1.0}
        {"type": "pause"} | {"type": "resume"} | {"type": "stop"}
        {"type": "ping"}
    Server -> client messages:
        {"type": "frame", ...}  /  {"type": "status", ...}
    """
    await websocket.accept()
    try:
        await websocket.send_json(
            {
                "type": "status",
                "simulation": simulation_engine.describe(),
                "q_deg": np.rad2deg(robot_state.q).tolist(),
            }
        )
        last_sent = -1.0
        while True:
            # Drain incoming control messages without blocking the stream.
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=FRAME_INTERVAL_S)
                msg = json.loads(raw)
                kind = msg.get("type")
                if kind == "start":
                    desc = await simulation_engine.start(
                        msg.get("trajectory_id"), float(msg.get("speed", 1.0))
                    )
                    await websocket.send_json({"type": "status", "simulation": desc})
                elif kind == "pause":
                    desc = await simulation_engine.pause()
                    await websocket.send_json({"type": "status", "simulation": desc})
                elif kind == "resume":
                    desc = await simulation_engine.resume()
                    await websocket.send_json({"type": "status", "simulation": desc})
                elif kind == "stop":
                    desc = await simulation_engine.stop()
                    await websocket.send_json({"type": "status", "simulation": desc})
                elif kind == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass

            frame = simulation_engine.sample()
            if frame is not None and frame["time"] != last_sent:
                await websocket.send_json(frame)
                last_sent = frame["time"]
                if frame["status"] in ("done", "stopped"):
                    await websocket.send_json(
                        {"type": "status", "simulation": simulation_engine.describe()}
                    )
    except WebSocketDisconnect:
        pass
    except Exception:
        # Never leak server errors to the client (spec §39).
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

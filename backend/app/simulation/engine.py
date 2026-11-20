"""Simulation playback engine (WebSocket driven).

The engine owns a virtual clock that advances while a trajectory is playing.
WebSocket connections sample the clock and stream frames to the UI.

    status:  idle -> running <-> paused -> stopped / done

This is a *simulation* stop only -- the system never controls real hardware
(spec §51/§52).
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional

import numpy as np

from ..robotics.kinematics import forward_kinematics
from ..utils.errors import SimulationError
from .state import robot_state, trajectory_store


class SimulationEngine:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.status: str = "idle"          # idle | running | paused | stopped | done
        self.trajectory_id: Optional[str] = None
        self.speed: float = 1.0
        self._t0_wall: Optional[float] = None
        self._sim_time_offset: float = 0.0
        self._trajectory: Optional[Dict] = None
        self._t_arr: Optional[np.ndarray] = None
        self._q_arr: Optional[np.ndarray] = None

    # ------------------------------------------------------------------ #
    async def start(self, trajectory_id: Optional[str], speed: float) -> Dict:
        async with self._lock:
            traj = trajectory_store.get(trajectory_id)
            self._trajectory = traj
            self._t_arr = np.asarray(traj["t"], dtype=np.float64)
            self._q_arr = np.asarray(traj["q"], dtype=np.float64)
            self.trajectory_id = trajectory_store.last_id
            self.speed = float(speed)
            self._sim_time_offset = 0.0
            self._t0_wall = time.monotonic()
            self.status = "running"
            return self.describe()

    async def pause(self) -> Dict:
        async with self._lock:
            if self.status == "running":
                self._sim_time_offset = self._current_sim_time_unlocked()
                self.status = "paused"
            return self.describe()

    async def resume(self) -> Dict:
        async with self._lock:
            if self.status == "paused":
                self._t0_wall = time.monotonic()
                self.status = "running"
            return self.describe()

    async def stop(self) -> Dict:
        async with self._lock:
            if self.status in ("running", "paused"):
                self._sim_time_offset = self._current_sim_time_unlocked()
                self.status = "stopped"
            return self.describe()

    async def reset(self) -> Dict:
        async with self._lock:
            self.status = "idle"
            self._trajectory = None
            self._t_arr = None
            self._q_arr = None
            self._sim_time_offset = 0.0
            return self.describe()

    def describe(self) -> Dict:
        return {
            "status": self.status,
            "trajectory_id": self.trajectory_id,
            "speed": self.speed,
            "time": round(self._current_sim_time_unlocked(), 4),
            "duration": float(self._t_arr[-1]) if self._t_arr is not None else 0.0,
        }

    # ------------------------------------------------------------------ #
    def _current_sim_time_unlocked(self) -> float:
        if self._trajectory is None:
            return 0.0
        if self.status == "running" and self._t0_wall is not None:
            elapsed = (time.monotonic() - self._t0_wall) * self.speed
            return min(
                self._sim_time_offset + elapsed, float(self._t_arr[-1])
            )
        return self._sim_time_offset

    def sample(self) -> Optional[Dict]:
        """Return the frame at the current sim time (or None if idle)."""
        if self._trajectory is None or self._t_arr is None or self._q_arr is None:
            return None
        duration = float(self._t_arr[-1])
        t_sim = self._current_sim_time_unlocked()
        finished = t_sim >= duration - 1e-9

        if finished and self.status == "running":
            self._sim_time_offset = duration
            self.status = "done"

        q = np.empty(6)
        for j in range(6):
            q[j] = np.interp(t_sim, self._t_arr, self._q_arr[:, j])

        ee = forward_kinematics(q)[:3, 3]
        robot_state.set_q(q)

        return {
            "type": "frame",
            "status": self.status,
            "time": round(float(t_sim), 4),
            "duration": duration,
            "progress": float(t_sim / duration) if duration > 0 else 1.0,
            "q_rad": q.tolist(),
            "q_deg": np.rad2deg(q).tolist(),
            "position": {
                "x": float(ee[0]),
                "y": float(ee[1]),
                "z": float(ee[2]),
            },
        }


simulation_engine = SimulationEngine()

"""Shared robot state and trajectory store.

Every page works against the same robot state (spec §68): changing J1 in
Robot Control updates the Dashboard, the 3D viewer and FK results because
they all read from this single store.
"""

from __future__ import annotations

import threading
import uuid
from collections import OrderedDict
from typing import Dict, Optional

import numpy as np

from ..models.parameters import parameter_store
from ..utils.errors import InvalidParameterError


class RobotState:
    """Authoritative current joint configuration [rad]."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._q = np.deg2rad(
            np.array(parameter_store.spec.home_position_deg, dtype=np.float64)
        )

    @property
    def q(self) -> np.ndarray:
        with self._lock:
            return self._q.copy()

    def set_q(self, q) -> np.ndarray:
        q = np.asarray(q, dtype=np.float64).ravel()
        if q.shape[0] != 6 or not np.all(np.isfinite(q)):
            raise InvalidParameterError("Robot state requires 6 finite joint values.")
        with self._lock:
            self._q = q
        return self.q


class TrajectoryStore:
    """In-memory store of generated trajectories (bounded LRU)."""

    MAX_ENTRIES = 32

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: "OrderedDict[str, Dict]" = OrderedDict()
        self._last_id: Optional[str] = None

    def put(self, trajectory: Dict) -> str:
        tid = uuid.uuid4().hex[:12]
        with self._lock:
            self._items[tid] = trajectory
            self._last_id = tid
            while len(self._items) > self.MAX_ENTRIES:
                self._items.popitem(last=False)
        return tid

    def get(self, tid: Optional[str] = None) -> Dict:
        with self._lock:
            key = tid or self._last_id
            if key is None or key not in self._items:
                raise InvalidParameterError(
                    "No trajectory available. Generate a trajectory first."
                )
            return self._items[key]

    @property
    def last_id(self) -> Optional[str]:
        with self._lock:
            return self._last_id


robot_state = RobotState()
trajectory_store = TrajectoryStore()

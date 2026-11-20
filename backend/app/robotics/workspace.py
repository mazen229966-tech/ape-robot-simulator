"""Workspace analysis (Monte-Carlo point cloud).

Random joint configurations are sampled uniformly inside the published joint
limits, FK is evaluated in one vectorised pass (never per-point from the UI,
spec §15/§48) and the resulting point cloud is reduced server-side before it
is sent to the client.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ..models.parameters import parameter_store
from ..utils.errors import InvalidParameterError
from .dh import dh_chain

MAX_SAMPLES = 200_000
MIN_SAMPLES = 100
MAX_DISPLAY_POINTS = 20_000


def _vectorized_fk(q_batch: np.ndarray) -> np.ndarray:
    """FK for an (m, 6) array of joint vectors -> (m, 3) positions [m]."""
    dh = parameter_store.dh_table()
    m = q_batch.shape[0]
    positions = np.empty((m, 3), dtype=np.float64)
    # Per-link transforms are computed vectorially (pure numpy).
    T = np.tile(np.eye(4, dtype=np.float64), (m, 1, 1))
    for j, (_, d, a, alpha) in enumerate(dh):
        theta = q_batch[:, j]
        ct = np.cos(theta)
        st = np.sin(theta)
        ca = np.cos(alpha)
        sa = np.sin(alpha)
        A = np.zeros((m, 4, 4), dtype=np.float64)
        A[:, 0, 0] = ct
        A[:, 0, 1] = -st * ca
        A[:, 0, 2] = st * sa
        A[:, 0, 3] = a * ct
        A[:, 1, 0] = st
        A[:, 1, 1] = ct * ca
        A[:, 1, 2] = -ct * sa
        A[:, 1, 3] = a * st
        A[:, 2, 1] = sa
        A[:, 2, 2] = ca
        A[:, 2, 3] = d
        A[:, 3, 3] = 1.0
        T = np.einsum("mij,mjk->mik", T, A)
    positions[:] = T[:, :3, 3]
    return positions


def generate_workspace(
    samples: int, seed: int | None = None
) -> Dict:
    """Generate the reachable workspace point cloud.

    Returns
    -------
    dict with
      ``samples``            number of sampled configurations,
      ``points_mm``          flat list of display points in mm (x,y,z,...),
      ``displayed_points``   number of points actually sent to the client,
      ``bounds_mm``          min/max per axis in mm,
      ``reach_mm``           max horizontal radius sqrt(x^2+y^2) in mm.
    """
    if not isinstance(samples, int) or not (MIN_SAMPLES <= samples <= MAX_SAMPLES):
        raise InvalidParameterError(
            f"Number of samples must be an integer between "
            f"{MIN_SAMPLES} and {MAX_SAMPLES}."
        )

    limits = np.array(parameter_store.spec.joint_limits_rad)
    rng = np.random.default_rng(seed)
    q_batch = rng.uniform(low=limits[:, 0], high=limits[:, 1], size=(samples, 6))

    xyz = _vectorized_fk(q_batch)

    finite = np.all(np.isfinite(xyz), axis=1)
    xyz = xyz[finite]

    bounds = {
        "x_min": float(xyz[:, 0].min()),
        "x_max": float(xyz[:, 0].max()),
        "y_min": float(xyz[:, 1].min()),
        "y_max": float(xyz[:, 1].max()),
        "z_min": float(xyz[:, 2].min()),
        "z_max": float(xyz[:, 2].max()),
    }
    reach = float(np.max(np.hypot(xyz[:, 0], xyz[:, 1])))

    # Downsample for transport/display while keeping the full statistics.
    n = xyz.shape[0]
    if n > MAX_DISPLAY_POINTS:
        idx = np.linspace(0, n - 1, MAX_DISPLAY_POINTS).astype(int)
        display = xyz[idx]
    else:
        display = xyz

    points_mm = np.round(display * 1e3, 2)

    return {
        "samples": int(samples),
        "valid_samples": int(n),
        "displayed_points": int(display.shape[0]),
        "points_mm": points_mm.ravel().tolist(),
        "bounds_mm": {k: round(v * 1e3, 2) for k, v in bounds.items()},
        "reach_mm": round(reach * 1e3, 2),
    }


def assert_sane_workspace(result: Dict) -> None:
    """Validation helper used by the test-suite."""
    b = result["bounds_mm"]
    assert np.isfinite(result["reach_mm"])
    assert b["x_max"] > b["x_min"]
    assert b["y_max"] > b["y_min"]
    assert b["z_max"] > b["z_min"]

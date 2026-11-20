"""Standard (classic) Denavit-Hartenberg mathematics.

Convention
----------
The homogeneous transform of link *i* is

    A_i = Rz(theta_i) * Tz(d_i) * Tx(a_i) * Rx(alpha_i)

which expands to the well-known matrix

    [ cosθ  -sinθ cosα   sinθ sinα   a cosθ ]
    [ sinθ   cosθ cosα  -cosθ sinα   a sinθ ]
    [   0       sinα        cosα         d   ]
    [   0         0           0          1   ]

The full forward chain is ``T_06 = A1 A2 A3 A4 A5 A6``.

This module is implemented with plain NumPy so it can be cross-checked
independently of Robotics Toolbox (used in the unit tests).
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np


def dh_transform(theta: float, d: float, a: float, alpha: float) -> np.ndarray:
    """Return the 4x4 standard-DH transform A_i for one link (SI units)."""
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return np.array(
        [
            [ct, -st * ca, st * sa, a * ct],
            [st, ct * ca, -ct * sa, a * st],
            [0.0, sa, ca, d],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def dh_chain(
    q: Sequence[float], dh_table: Iterable[Sequence[float]]
) -> np.ndarray:
    """Return T_0n = A1 ... An for joint vector ``q`` (radians).

    ``dh_table`` rows are (theta_name, d, a, alpha); theta is taken from q.
    """
    T = np.eye(4, dtype=np.float64)
    for qi, (_, d, a, alpha) in zip(q, dh_table):
        T = T @ dh_transform(qi, d, a, alpha)
    return T


def dh_frame_list(
    q: Sequence[float], dh_table: Iterable[Sequence[float]]
) -> list[np.ndarray]:
    """Return the cumulative frames [T00, T01, ..., T0n]."""
    frames = [np.eye(4, dtype=np.float64)]
    T = np.eye(4, dtype=np.float64)
    for qi, (_, d, a, alpha) in zip(q, dh_table):
        T = T @ dh_transform(qi, d, a, alpha)
        frames.append(T.copy())
    return frames

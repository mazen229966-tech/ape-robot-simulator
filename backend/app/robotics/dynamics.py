"""Dynamics: inverse dynamics and torque decomposition.

The rigid-body dynamics equation

    τ = M(q)·q̈ + C(q,q̇)·q̇ + g(q) + F(q̇)

is evaluated with Robotics Toolbox's implementation of the recursive
Newton-Euler algorithm:

* ``M(q)·q̈``          inertia torque          (``robot.inertia``)
* ``C(q,q̇)·q̇``        Coriolis/centrifugal    (``robot.coriolis``)
* ``g(q)``            gravity torque           (``robot.gravload``)
* ``F(q̇)``            joint friction           (``robot.friction``)

The sum is cross-checked against the monolithic ``rne`` result in the test
suite.  All dynamic parameters are EDUCATIONAL / ASSUMED (see
``app.models.ape_sv45``) and labeled as such in the UI.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from ..models.parameters import parameter_store
from ..utils.errors import InvalidParameterError
from .robot import create_robot


def compute_torque(
    q: np.ndarray, qd: np.ndarray, qdd: np.ndarray
) -> Dict[str, np.ndarray]:
    """Torque decomposition for one configuration (arrays of length 6).

    Sign convention: every component is the torque the actuators must
    supply, so the sum equals ``robot.rne(q, qd, qdd)`` exactly:

        tau = M qdd + C qd + g(q) - friction(qd)

    (``robot.friction`` returns the friction force opposing motion).
    """
    robot = create_robot()
    q = np.asarray(q, dtype=np.float64)
    qd = np.asarray(qd, dtype=np.float64)
    qdd = np.asarray(qdd, dtype=np.float64)

    M = np.asarray(robot.inertia(q))
    C = np.asarray(robot.coriolis(q, qd))
    tau_gravity = np.asarray(robot.gravload(q)).ravel()
    tau_friction = -np.asarray(robot.friction(qd)).ravel()

    tau_inertia = M @ qdd
    tau_coriolis = (C @ qd).ravel()
    tau_total = tau_inertia + tau_coriolis + tau_gravity + tau_friction

    return {
        "inertia": tau_inertia,
        "coriolis": tau_coriolis,
        "gravity": tau_gravity,
        "friction": tau_friction,
        "total": tau_total,
    }


def compute_torque_trajectory(
    t: List[float],
    q: List[List[float]],
    qd: List[List[float]],
    qdd: List[List[float]],
) -> Dict:
    """Torque decomposition along a trajectory.

    Inputs are plain nested lists (SI: rad, rad/s, rad/s^2).
    """
    t_arr = np.asarray(t, dtype=np.float64)
    q_arr = np.asarray(q, dtype=np.float64)
    qd_arr = np.asarray(qd, dtype=np.float64)
    qdd_arr = np.asarray(qdd, dtype=np.float64)

    if not (t_arr.ndim == 1 and q_arr.ndim == 2):
        raise InvalidParameterError("Trajectory arrays have wrong shape.")
    n = t_arr.shape[0]
    if q_arr.shape[0] != n or qd_arr.shape[0] != n or qdd_arr.shape[0] != n:
        raise InvalidParameterError("Trajectory arrays have inconsistent length.")
    if q_arr.shape[1] != parameter_store.spec.dof:
        raise InvalidParameterError("Joint dimension mismatch in dynamics input.")
    for arr, name in (
        (q_arr, "q"),
        (qd_arr, "qd"),
        (qdd_arr, "qdd"),
        (t_arr, "t"),
    ):
        if not np.all(np.isfinite(arr)):
            raise InvalidParameterError(f"Non-finite values in '{name}'.")

    n_dof = q_arr.shape[1]
    components = {
        "inertia": np.empty((n, n_dof)),
        "coriolis": np.empty((n, n_dof)),
        "gravity": np.empty((n, n_dof)),
        "friction": np.empty((n, n_dof)),
        "total": np.empty((n, n_dof)),
    }

    robot = create_robot()
    for i in range(n):
        M = np.asarray(robot.inertia(q_arr[i]))
        C = np.asarray(robot.coriolis(q_arr[i], qd_arr[i]))
        g = np.asarray(robot.gravload(q_arr[i])).ravel()
        f = -np.asarray(robot.friction(qd_arr[i])).ravel()  # actuator side
        components["inertia"][i] = M @ qdd_arr[i]
        components["coriolis"][i] = (C @ qd_arr[i]).ravel()
        components["gravity"][i] = g
        components["friction"][i] = f

    components["total"] = (
        components["inertia"]
        + components["coriolis"]
        + components["gravity"]
        + components["friction"]
    )

    # Cross-check with the monolithic RNE result.
    rne_total = np.asarray(robot.rne(q_arr, qd_arr, qdd_arr))
    rne_total = rne_total.reshape(n, n_dof)
    max_rne_discrepancy = float(
        np.max(np.abs(components["total"] - rne_total))
    )

    stats = {"per_joint": []}
    for j in range(n_dof):
        tau = components["total"][:, j]
        stats["per_joint"].append(
            {
                "joint": j + 1,
                "max_abs_torque_nm": float(np.max(np.abs(tau))),
                "rms_torque_nm": float(np.sqrt(np.mean(tau**2))),
                "peak_torque_nm": float(tau[np.argmax(np.abs(tau))]),
            }
        )

    return {
        "t": t_arr.tolist(),
        "components": {k: v.tolist() for k, v in components.items()},
        "stats": stats,
        "rne_discrepancy_nm": max_rne_discrepancy,
        "parameter_source": parameter_store.spec.dynamics_source,
    }

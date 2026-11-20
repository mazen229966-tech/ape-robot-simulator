"""Robot model creation (Robotics Toolbox for Python).

``create_robot()`` builds an ``rtb.DHRobot`` from the *active* parameter
store, attaching both kinematic and (educational) dynamic parameters so the
same model serves FK, IK, workspace, trajectory and dynamics computations.
"""

from __future__ import annotations

import math

import numpy as np
import roboticstoolbox as rtb

from ..models.parameters import parameter_store
from ..utils.errors import RobotModelError


def create_robot() -> rtb.DHRobot:
    """Build the DHRobot from the currently active parameters.

    The model is rebuilt on demand so that parameter changes made through the
    DH page take effect immediately.  Construction is cheap (pure data).
    """
    spec = parameter_store.spec
    dh = parameter_store.dh_table()

    if len(dh) != spec.dof:
        raise RobotModelError(
            f"DH table has {len(dh)} rows but the robot has {spec.dof} DOF."
        )
    if len(spec.link_dynamics) != spec.dof:
        raise RobotModelError("Dynamic parameter set does not match DOF.")

    limits_rad = spec.joint_limits_rad

    links = []
    for i, ((_, d, a, alpha), dyn, qlim) in enumerate(
        zip(dh, spec.link_dynamics, limits_rad), start=1
    ):
        for value in (d, a, alpha):
            if not math.isfinite(value):
                raise RobotModelError(f"Link {i} has non-finite DH parameters.")
        links.append(
            rtb.RevoluteDH(
                d=float(d),
                a=float(a),
                alpha=float(alpha),
                qlim=np.array([qlim[0], qlim[1]], dtype=np.float64),
                m=float(dyn.mass),
                r=np.array(dyn.com, dtype=np.float64),
                I=np.array(dyn.inertia, dtype=np.float64),
                B=float(dyn.viscous_friction),
                Tc=float(dyn.coulomb_friction),
                G=float(dyn.gear_ratio),
                Jm=float(dyn.motor_inertia),
            )
        )

    robot = rtb.DHRobot(links, name=spec.name)
    # rtb convention: gravity vector expressed in the base frame; positive z
    # up, gravity magnitude acts downwards.
    robot.gravity = np.array([0.0, 0.0, spec.gravity_m_s2])
    return robot


def get_robot() -> rtb.DHRobot:
    """Alias used by the API layer."""
    return create_robot()

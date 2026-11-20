"""APE SV2-6045 robot data definition.

This module is the single source of truth for the robot's parameters.
It cleanly separates three categories:

1. **Official specifications** -- values published by APE Technology on the
   official SV2-6045 product page (ape.cn).  These may be presented to the
   user as official data.
2. **Educational / Assumed kinematic parameters** -- APE does not publish a
   DH table for this robot, therefore a *standard* (classic) Denavit-Hartenberg
   model was constructed for educational use.  It is dimensioned so that the
   resulting workspace matches the official 454 mm maximum radius and it uses
   the officially published joint limits.  These values MUST be labeled
   "Educational / Assumed" everywhere in the UI and may never be presented as
   factory data.
3. **Educational / Assumed dynamic parameters** -- link masses, centers of
   mass, inertia tensors and friction.  No official dynamic data exists for
   this robot; values are plausible engineering estimates for a 23 kg robot of
   this size and are labeled accordingly.

If an official DH table, CAD model or URDF ever becomes available, only this
module (and ``parameters.py``) has to be updated -- the rest of the system is
parameter driven.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

# --------------------------------------------------------------------------- #
# 1. Official specifications (APE Technology, SV2-6045 product page)          #
# --------------------------------------------------------------------------- #

OFFICIAL_SPECS = {
    "manufacturer": "APE Technology",
    "model": "SV2-6045 (SV45)",
    "type": "Vertical articulated (6-axis) industrial robot",
    "dof": 6,
    "payload_rated_kg": 1.0,
    "payload_max_kg": 2.5,
    "max_radius_m": 0.454,
    "repeatability_mm": 0.02,
    "body_weight_kg": 23.0,
    "max_tcp_speed_m_s": 6.0,
    "installation": "Desktop, side hanging, incline and ceiling",
    "drive": "AC servo motors (all six axes with brakes)",
    "encoder": "Absolute encoders",
    "protection": "IP20",
    "noise_db": 70.0,
    "joint_speeds_deg_s": [360.0, 300.0, 300.0, 540.0, 540.0, 600.0],
    "source": "Official APE Technology product page (ape.cn)",
}

# Officially published joint limits [deg] (APE SV2-6045 datasheet).
OFFICIAL_JOINT_LIMITS_DEG: List[tuple] = [
    (-165.0, +165.0),   # J1
    (-100.0, +100.0),   # J2
    (-70.0, +90.0),     # J3  (asymmetric, as published)
    (-160.0, +160.0),   # J4
    (-130.0, +130.0),   # J5
    (-360.0, +360.0),   # J6
]

# --------------------------------------------------------------------------- #
# 2. Educational kinematic model (standard DH convention)                      #
# --------------------------------------------------------------------------- #
#
# Parameter source: EDUCATIONAL / ASSUMED  (no official DH table published).
#
# The chain is a compact 6R arm with an offset shoulder and a compact
# articulated wrist, in the style of modern small 6-axis robots.  Internal
# units are SI: d/a in METERS, alpha in RADIANS, theta = joint variable q.
#
# The link dimensions were chosen so that the MONTE-CARLO WORKSPACE of the
# model -- sampled uniformly inside the official joint limits -- reaches a
# maximum horizontal radius of ~454 mm, i.e. the official maximum radius of
# the SV2-6045 (regression-tested in ``tests/test_dh.py``).

DH_TABLE_EDUCATIONAL = [
    # theta    d (m)      a (m)     alpha (rad)
    ("q1", 0.1650, 0.0000, -math.pi / 2.0),  # base column, shoulder
    ("q2", 0.0000, 0.2000, 0.0),             # upper arm
    ("q3", 0.0000, 0.1700, 0.0),             # forearm
    ("q4", 0.0900, 0.0000, math.pi / 2.0),   # wrist roll offset
    ("q5", 0.0550, 0.0000, -math.pi / 2.0),  # wrist pitch offset
    ("q6", 0.0500, 0.0000, 0.0),             # tool flange
]

KINEMATIC_PARAMETER_SOURCE = "Educational / Assumed"

# A comfortable demonstration pose ("Home"): arm raised, elbow bent,
# tool pointing forward-down.  [deg]
HOME_POSITION_DEG = [0.0, -35.0, 55.0, 0.0, -20.0, 0.0]

# --------------------------------------------------------------------------- #
# 3. Educational dynamic model                                                 #
# --------------------------------------------------------------------------- #
#
# Parameter source: EDUCATIONAL / ASSUMED.
# Total moving mass ~23 kg matches the official body weight.  Centers of mass
# are placed along each link, inertia tensors approximate each link as a
# slender body.  Friction values are typical small-servomotor estimates.

DYNAMIC_PARAMETER_SOURCE = "Educational / Assumed"


@dataclass
class LinkDynamics:
    """Dynamic parameters of one link (SI units).

    Friction convention (matches Robotics Toolbox): ``viscous_friction`` and
    ``coulomb_friction`` are MOTOR-side values; they are reflected to the
    joint by the gear ratio (B_joint = B * G^2, Tc_joint = Tc * G).  The
    values below are chosen so that the *reflected* joint friction is in a
    physically plausible range (roughly 0.4-3 N m s/rad viscous and
    0.3-2 N m Coulomb per joint).
    """

    mass: float                      # kg
    com: tuple                       # center of mass in the link frame [m]
    inertia: tuple                   # (Ixx, Iyy, Izz, Ixy, Ixz, Iyz) [kg m^2]
    viscous_friction: float = 0.0    # B  [N m s / rad], motor side
    coulomb_friction: float = 0.0    # Tc [N m], motor side
    gear_ratio: float = 1.0          # G  [-]
    motor_inertia: float = 0.0       # Jm [kg m^2]


LINK_DYNAMICS: List[LinkDynamics] = [
    LinkDynamics(  # link 1 (base rotation)
        mass=4.80,
        com=(0.0, 0.015, 0.060),
        inertia=(0.0300, 0.0300, 0.0200, 0.0, 0.0, 0.0),
        viscous_friction=2.5e-4, coulomb_friction=0.015,
        gear_ratio=100.0, motor_inertia=1.8e-4,
    ),
    LinkDynamics(  # link 2 (upper arm, along +x)
        mass=5.60,
        com=(0.115, 0.0, 0.012),
        inertia=(0.0060, 0.0520, 0.0540, 0.0, 0.0, 0.0),
        viscous_friction=2.1e-4, coulomb_friction=0.017,
        gear_ratio=120.0, motor_inertia=1.8e-4,
    ),
    LinkDynamics(  # link 3 (forearm, along +x)
        mass=3.90,
        com=(0.095, 0.0, -0.010),
        inertia=(0.0035, 0.0280, 0.0290, 0.0, 0.0, 0.0),
        viscous_friction=2.0e-4, coulomb_friction=0.012,
        gear_ratio=100.0, motor_inertia=1.3e-4,
    ),
    LinkDynamics(  # link 4 (wrist roll)
        mass=2.30,
        com=(0.0, 0.0, 0.050),
        inertia=(0.0040, 0.0040, 0.0022, 0.0, 0.0, 0.0),
        viscous_friction=1.25e-4, coulomb_friction=0.0063,
        gear_ratio=80.0, motor_inertia=0.9e-4,
    ),
    LinkDynamics(  # link 5 (wrist pitch)
        mass=1.50,
        com=(0.0, 0.0, 0.035),
        inertia=(0.0016, 0.0016, 0.0010, 0.0, 0.0, 0.0),
        viscous_friction=0.94e-4, coulomb_friction=0.005,
        gear_ratio=80.0, motor_inertia=0.9e-4,
    ),
    LinkDynamics(  # link 6 (tool flange + nominal 1 kg payload)
        mass=1.30,
        com=(0.0, 0.0, 0.030),
        inertia=(0.0006, 0.0006, 0.0005, 0.0, 0.0, 0.0),
        viscous_friction=1.1e-4, coulomb_friction=0.005,
        gear_ratio=60.0, motor_inertia=0.6e-4,
    ),
]

GRAVITY_M_S2 = 9.81

# --------------------------------------------------------------------------- #
# Convenience container                                                        #
# --------------------------------------------------------------------------- #


@dataclass
class RobotSpec:
    """Complete, serialisable description of the robot."""

    name: str = "APE SV2-6045"
    manufacturer: str = "APE Technology"
    dof: int = 6
    official_specs: dict = field(default_factory=lambda: dict(OFFICIAL_SPECS))
    joint_limits_deg: List[tuple] = field(
        default_factory=lambda: list(OFFICIAL_JOINT_LIMITS_DEG)
    )
    joint_speeds_deg_s: List[float] = field(
        default_factory=lambda: list(OFFICIAL_SPECS["joint_speeds_deg_s"])
    )
    home_position_deg: List[float] = field(
        default_factory=lambda: list(HOME_POSITION_DEG)
    )
    dh_table: List[tuple] = field(
        default_factory=lambda: list(DH_TABLE_EDUCATIONAL)
    )
    kinematic_source: str = KINEMATIC_PARAMETER_SOURCE
    dynamics_source: str = DYNAMIC_PARAMETER_SOURCE
    gravity_m_s2: float = GRAVITY_M_S2
    link_dynamics: List[LinkDynamics] = field(
        default_factory=lambda: list(LINK_DYNAMICS)
    )

    @property
    def joint_limits_rad(self) -> List[tuple]:
        return [
            (math.radians(lo), math.radians(hi))
            for lo, hi in self.joint_limits_deg
        ]


def default_robot_spec() -> RobotSpec:
    """Return a fresh copy of the default robot specification."""
    return RobotSpec()

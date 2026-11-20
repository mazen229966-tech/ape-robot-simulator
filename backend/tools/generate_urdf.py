"""Generate ``robot/urdf/sv2_6045.urdf`` from the educational DH model.

Construction rule (standard DH → URDF):
joint *i* origin = ``A_{i-1}(theta=0)`` expressed in the previous link frame,
axis ``z``.  The URDF chain then telescopes exactly into the DH chain because::

    Rz(q_i) · A_i(0) == A_i(q_i)

so the URDF TCP transform equals ``A1(q1)…A6(q6)`` for **every** joint
configuration (verified numerically by ``tests``/this script).  Link geometry
uses primitive shapes sized to the DH link lengths — a kinematic /
visualization surrogate for the real SV2-6045 housing (CAD not public).

Usage::

    cd backend && python tools/generate_urdf.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.ape_sv45 import DH_TABLE_EDUCATIONAL  # noqa: E402
from app.robotics import dh as dhm  # noqa: E402


def rpy_of(R: np.ndarray) -> tuple[float, float, float]:
    """ZYX Euler (URDF ``rpy``): R = Rz(yaw)·Ry(pitch)·Rx(roll)."""
    pitch = math.atan2(-R[2, 0], math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2))
    roll = math.atan2(R[2, 1], R[2, 2])
    yaw = math.atan2(R[1, 0], R[0, 0])
    return float(roll), float(pitch), float(yaw)


def fmt(v: float) -> str:
    if abs(v) < 1e-12:
        return "0"
    return f"{v:.9f}".rstrip("0").rstrip(".")


def pose_str(T: np.ndarray) -> str:
    r, p, y = rpy_of(T[:3, :3])
    return (
        f'xyz="{fmt(T[0, 3])} {fmt(T[1, 3])} {fmt(T[2, 3])}" '
        f'rpy="{fmt(r)} {fmt(p)} {fmt(y)}"'
    )


def main() -> None:
    # joint i origin = A_{i-1}(0); joint 1 origin = I; tool origin = A_6(0)
    origins = [np.eye(4)]
    for _, d, a, alpha in DH_TABLE_EDUCATIONAL:
        origins.append(dhm.dh_transform(0.0, d, a, alpha))

    d1 = DH_TABLE_EDUCATIONAL[0][1]
    a2 = DH_TABLE_EDUCATIONAL[1][2]
    a3 = DH_TABLE_EDUCATIONAL[2][2]
    d4 = DH_TABLE_EDUCATIONAL[3][1]
    d5 = DH_TABLE_EDUCATIONAL[4][1]
    d6 = DH_TABLE_EDUCATIONAL[5][1]

    L: list[str] = []
    add = L.append
    add('<?xml version="1.0"?>')
    add('<!-- URDF generated from the EDUCATIONAL DH model of the APE SV2-6045. -->')
    add('<!-- Kinematics match backend/app/models/ape_sv45.py exactly at every q. -->')
    add('<robot name="ape_sv2_6045">')

    def link(name: str, origin_xyz: str, orient_rpy: str, geom: str, mass: float, com: str | None = None) -> None:
        add(f'  <link name="{name}">')
        add('    <visual>')
        add(f'      <origin xyz="{origin_xyz}" rpy="{orient_rpy}"/>')
        add(f'      <geometry>{geom}</geometry>')
        add('    </visual>')
        add('    <inertial>')
        add(f'      <mass value="{fmt(mass)}"/>')
        add(f'      <origin xyz="{com or origin_xyz}"/>')
        add('      <inertia ixx="0.02" ixy="0" ixz="0" iyy="0.02" iyz="0" izz="0.01"/>')
        add('    </inertial>')
        add('  </link>')

    def joint(name: str, parent: str, child: str, T: np.ndarray, lower: float, upper: float) -> None:
        add(f'  <joint name="{name}" type="revolute">')
        add(f'    <parent link="{parent}"/><child link="{child}"/>')
        add(f'    <origin {pose_str(T)}/>')
        add('    <axis xyz="0 0 1"/>')
        add(f'    <limit effort="200" velocity="10.5" lower="{lower:.4f}" upper="{upper:.4f}"/>')
        add('  </joint>')

    limits = [
        (-math.radians(165), math.radians(165)),
        (-math.radians(100), math.radians(100)),
        (-math.radians(70), math.radians(90)),
        (-math.radians(160), math.radians(160)),
        (-math.radians(130), math.radians(130)),
        (-math.radians(360), math.radians(360)),
    ]

    # base column (fixed, height d1)
    link("base_link", f"0 0 {fmt(d1 / 2)}", "0 0 0",
         f'<cylinder radius="0.085" length="{fmt(d1)}"/>', 6.0)

    joint("joint1", "base_link", "link1", origins[0], *limits[0])
    # shoulder housing, extends up to joint-2 origin (Tz(d1) already behind us,
    # so this link carries the shoulder bulk around the J1 axis)
    link("link1", "0 0 0.03", "0 0 0",
         '<cylinder radius="0.07" length="0.11"/>', 4.5)

    joint("joint2", "link1", "link2", origins[1], *limits[1])
    # upper arm along +x2, length a2
    link("link2", f"{fmt(a2 / 2)} 0 0", f"0 {fmt(math.pi / 2)} 0",
         f'<cylinder radius="0.055" length="{fmt(a2)}"/>', 5.0)

    joint("joint3", "link2", "link3", origins[2], *limits[2])
    # forearm along +x3, length a3
    link("link3", f"{fmt(a3 / 2)} 0 0", f"0 {fmt(math.pi / 2)} 0",
         f'<cylinder radius="0.048" length="{fmt(a3)}"/>', 4.0)

    joint("joint4", "link3", "link4", origins[3], *limits[3])
    # wrist roll offset along +z4, length d4
    link("link4", f"0 0 {fmt(d4 / 2)}", "0 0 0",
         f'<cylinder radius="0.042" length="{fmt(d4)}"/>', 2.5)

    joint("joint5", "link4", "link5", origins[4], *limits[4])
    # wrist pitch offset along +z5, length d5
    link("link5", f"0 0 {fmt(d5 / 2)}", "0 0 0",
         f'<cylinder radius="0.036" length="{fmt(d5)}"/>', 1.8)

    joint("joint6", "link5", "link6", origins[5], *limits[5])
    # tool flange along +z6, length d6
    link("link6", f"0 0 {fmt(d6 / 2)}", "0 0 0",
         f'<cylinder radius="0.03" length="{fmt(d6)}"/>', 1.2)

    # TCP frame (fixed): completes the chain with A_6(0)
    add('  <joint name="tool_joint" type="fixed">')
    add('    <parent link="link6"/><child link="tool0"/>')
    add(f'    <origin {pose_str(origins[6])}/>')
    add('  </joint>')
    add('  <link name="tool0"/>')

    add("</robot>")

    out = Path(__file__).resolve().parents[2] / "robot" / "urdf" / "sv2_6045.urdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()

# DH Model & Forward Kinematics

## Standard (classic) Denavit–Hartenberg convention

Each link transform from frame *i−1* to frame *i*:

```
A_i(θ_i) = Rz(θ_i) · Tz(d_i) · Tx(a_i) · Rx(α_i)
```

```
     [ cosθ    −sinθ·cosα     sinθ·sinα     a·cosθ ]
A_i = [ sinθ     cosθ·cosα    −cosθ·sinα     a·sinθ ]
     [   0         sinα          cosα           d   ]
     [   0          0             0             1   ]
```

Parameters used (educational, SI):

| Link | θ       | d (m)  | a (m)  | α      |
|------|---------|--------|--------|--------|
| 1    | q1      | 0.165  | 0      | −90°   |
| 2    | q2      | 0      | 0.200  | 0      |
| 3    | q3      | 0      | 0.170  | 0      |
| 4    | q4      | 0.090  | 0      | +90°   |
| 5    | q5      | 0.055  | 0      | −90°   |
| 6    | q6      | 0.050  | 0      | 0      |

The dimensions were chosen so that the **Monte-Carlo workspace** of the model
(uniform sampling inside the official joint limits) reaches a maximum
horizontal radius of **≈ 454 mm** — the official maximum radius of the
SV2-6045 (regression-tested in `tests/test_dh.py`).

## Forward kinematics

```
T_06(q) = A1(q1) · A2(q2) · A3(q3) · A4(q4) · A5(q5) · A6(q6)

position:     p = [X, Y, Z]ᵀ = T_06[0:3, 3]
orientation:  R = T_06[0:3, 0:3]
roll/pitch/yaw (ZYX):  pitch = atan2(−R31, √(R11² + R21²))
                       roll  = atan2(R32, R33)
                       yaw   = atan2(R21, R11)
```

The NumPy implementation is verified equivalent to Robotics Toolbox
`fkine` to < 1e-10 m.

## Jacobian (geometric)

```
For revolute joint i:   Jv_i = z_{i−1} × (p_6 − p_{i−1}),   Jω_i = z_{i−1}
```

Used for velocity mapping `ẋ = J(q)·q̇` and IK conditioning diagnostics.

# Trajectory Planning

## Joint-space polynomials

### Cubic — `q(t) = a0 + a1 t + a2 t² + a3 t³`
Rest-to-rest boundary conditions `q(0)=q0, q(T)=qf, q̇(0)=q̇(T)=0`:

```
a0 = q0 ,  a1 = 0
a2 = 3(qf − q0)/T² ,  a3 = −2(qf − q0)/T³
```

Velocity/acceleration are continuous; acceleration is discontinuous at the
endpoints (finite jerk impulse).

### Quintic — `q(t) = Σ a_k t^k, k=0…5`
Rest-to-rest with zero acceleration at both ends (`q̈(0)=q̈(T)=0`):

```
a0 = q0 , a1 = a2 = 0
a3 = 10(qf−q0)/T³ ,  a4 = −15(qf−q0)/T⁴ ,  a5 = 6(qf−q0)/T⁵
```

Gives smooth jerk; used as the default interpolation.

## Cartesian trajectories

```
waypoints [(p_i, t_i)]  →  piecewise-linear path p(s),  s = constant speed
for each sample:  q_k = IK( p(s_k), R* )   (warm started from q_{k−1})
validate:  FK(q_k) within 0.5 mm of the path point
```

Time stamps come from the constant-speed assumption; the resulting `q(t)`
is FK-validated over its whole length before it is returned.

## Validation checks applied to every trajectory

- joint limits: `q_min ≤ q(t) ≤ q_max`
- joint speeds: `|q̇(t)| ≤` official per-joint maximum speeds
- continuity: per-sample jump < 15° (catches IK family flips)

Violations raise typed errors mapped to clean JSON responses.

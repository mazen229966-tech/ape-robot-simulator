# Inverse Kinematics

## Problem

Given a target pose `T* = [R*, p*]`, find `q` such that `FK(q) ≈ T*`
within `q_min ≤ q ≤ q_max` (official joint limits).

## Solver — numeric, multi-start

No closed form is derived for the educational DH set, so the simulator uses a
damped least-squares / Levenberg–Marquardt iteration with multiple random
restarts (deterministic per-call RNG seed):

```
error(q) = [ p* − FK_p(q) ;  ω(R*ᵀ FK_R(q)) ]        (6×1)
q_{k+1}  = q_k + (JᵀJ + λ²I)⁻¹ Jᵀ · error(q_k)       (LM step)
clamp(q_{k+1}) to joint limits
converged when |error| < ε  (ε ≈ 1e-6)
```

Multiple starts explore the configuration families (elbow up/down, wrist
flip); every converged solution is re-checked with FK.

## FK validation of solutions

Every accepted solution satisfies:

```
‖FK_p(q) − p*‖ ≤ 0.5 mm          AND          ∠(FK_R(q), R*) ≤ 0.5°
```

The API returns the achieved `position_error_mm` and `orientation_error_deg`
so the UI can display the validation, not just the solution.

## Warm start for trajectories

Cartesian trajectories seed each sample's IK with the previous sample's
solution, keeping the arm in one configuration family and producing smooth
`q(t)`.

## Configuration-family transitions (Draw H)

If a path segment cannot be followed without a > 25°/sample jump, the planner:
1. searches backwards for an *anchor* where an alternative configuration exists,
2. retraces pen-up at drawing height to the anchor (old family),
3. lifts, applies a 45-sample quintic blend to the alternative configuration,
4. continues via an air-bridge at lift height.

At most 2 transitions per path; more than that raises a `TrajectoryError`.

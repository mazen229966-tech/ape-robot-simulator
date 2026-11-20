# Dynamics & Torque Decomposition

## Equation of motion

```
τ = M(q)·q̈ + C(q, q̇)·q̇ + g(q) + F(q̇)
```

| Term | Meaning |
|---|---|
| `M(q)` | 6×6 inertia matrix |
| `C(q,q̇)·q̇` | Coriolis + centrifugal torques |
| `g(q)` | gravity loading |
| `F(q̇)` | viscous + Coulomb friction |

## Implementation

Computed with the **recursive Newton–Euler (RNE)** algorithm from Robotics
Toolbox for Python. The decomposition is obtained by selective evaluation:

```
gravity:    g(q)   = rne(q, 0, 0,  gravity)          (friction off)
inertia:    M·q̈   = rne(q, 0, q̈,  no gravity)
coriolis:   C·q̇   = rne(q, q̇, 0,  no gravity)
friction:   F(q̇)  = analytic viscous + Coulomb model
total:      τ      = M·q̈ + C·q̇ + g + F
```

The sum of components is asserted equal to the direct RNE evaluation
(`rne(q, q̇, q̈)`) — the test suite checks the discrepancy is ~1e-14 N·m,
i.e. the decomposition is exact, not approximate.

## Parameter source

APE publishes no mass/inertia data for the SV2-6045. Link masses (summing to
the official 23 kg body weight), centers of mass and inertia tensors are
**educational estimates** (slender-body approximations) and are labelled as
such in the API and UI. Torque values are therefore representative.

## Reported statistics

Per joint: max |τ|, RMS τ, peak τ — displayed in the Dynamics page and
exported with the trajectory CSV.

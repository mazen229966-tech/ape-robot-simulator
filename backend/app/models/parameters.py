"""Live robot parameter store.

Holds the *currently active* robot specification so it can be inspected,
modified (Apply Parameters on the DH page) and reset without touching the
default data in :mod:`app.models.ape_sv45`.

The store tracks the provenance of the kinematic parameters:

* ``Educational / Assumed``      -- untouched default educational DH table.
* ``Official / CAD``             -- would be set if official data were loaded.
* ``User modified (educational)``-- user edited the educational table.
"""

from __future__ import annotations

import math
import threading
from typing import Dict, List

from .ape_sv45 import (
    DH_TABLE_EDUCATIONAL,
    KINEMATIC_PARAMETER_SOURCE,
    RobotSpec,
    default_robot_spec,
)


class ParameterStore:
    """Thread-safe holder for the active robot specification."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._spec: RobotSpec = default_robot_spec()
        self._source: str = KINEMATIC_PARAMETER_SOURCE

    # ------------------------------------------------------------------ #
    @property
    def spec(self) -> RobotSpec:
        with self._lock:
            return self._spec

    @property
    def source(self) -> str:
        with self._lock:
            return self._source

    # ------------------------------------------------------------------ #
    def dh_table(self) -> List[tuple]:
        """Active DH table as list of (theta, d, a, alpha) tuples (SI)."""
        with self._lock:
            return list(self._spec.dh_table)

    def apply_dh_table(
        self,
        rows: List[Dict[str, float]],
        source_label: str = "User modified (educational)",
    ) -> None:
        """Replace the active DH table.

        ``rows`` -- six dicts with keys ``d``, ``a``, ``alpha`` (SI units:
        metres / metres / radians).  Values are validated for finiteness and
        basic plausibility.
        """
        if len(rows) != 6:
            raise ValueError("DH table must contain exactly 6 rows.")
        table: List[tuple] = []
        for i, row in enumerate(rows, start=1):
            d = float(row["d"])
            a = float(row["a"])
            alpha = float(row["alpha"])
            for name, value in (("d", d), ("a", a), ("alpha", alpha)):
                if not math.isfinite(value):
                    raise ValueError(f"Link {i}: {name} must be finite.")
            if abs(d) > 5.0 or abs(a) > 5.0:
                raise ValueError(
                    f"Link {i}: link dimensions above 5 m are not plausible "
                    "for this robot class."
                )
            table.append((f"q{i}", d, a, alpha))
        with self._lock:
            self._spec.dh_table = table
            self._source = source_label

    def reset(self) -> None:
        """Restore the default educational DH table."""
        with self._lock:
            self._spec = default_robot_spec()
            self._spec.dh_table = list(DH_TABLE_EDUCATIONAL)
            self._source = KINEMATIC_PARAMETER_SOURCE


# Process-wide singleton ---------------------------------------------------- #
parameter_store = ParameterStore()

# Draw H — the final demo

The letter **H** is drawn as a **real Cartesian trajectory**, never as a
pre-baked animation:

```
1. Corners on the drawing plane:
     P1 (left, top) → P2 (left, bottom)          pen DOWN  (stroke 1)
     pen UP, traverse
     P3 (left, mid)  → P4 (right, mid)           pen DOWN  (stroke 2, crossbar)
     pen UP, traverse
     P5 (right, top) → P6 (right, bottom)        pen DOWN  (stroke 3)

2. Linear Cartesian path with pen-up lifts (default 20 mm) between strokes,
   always along the outward plane normal.

3. IK per sample (warm started) → q(t).  If a configuration-family flip is
   unavoidable (workspace geometry), the planner inserts a pen-up
   retrace-lift-blend transition (see inverse_kinematics.md).

4. FK validation of every sample (≤ 0.5 mm from the nominal path).

5. Playback engine streams q(t) at ~30 Hz to the 3D viewer; the pen tip
   touches the drawing plane exactly during pen-down phases.
```

Supported drawing planes (spec §32):

* **XY** — horizontal surface at `z = drawing_height` (default 280 mm), tool
  axis pointing straight down, RPY = (180°, 0, 0).  Default letter:
  150 × 200 mm centred at (290, 0) mm.
* **XZ** — vertical wall at `y = center_y`, letter spanning x (width) and z
  (height, centred at `drawing_height`).  The pen is tilted 45° towards the
  wall (a horizontal tool is not continuously reachable inside the official
  joint limits).  Default letter: 100 × 140 mm on the wall y = 120 mm,
  centred at x = 300 mm, z = 250 mm.
* **YZ** — vertical wall at `x = center_x`; same conventions as XZ.  This
  wall is only marginally reachable for the educational model — generation
  may be rejected with a clear diagnostic.

Speed default 50 mm/s, dt = 20 ms.  A typical XY run: ~940 samples, ~19.5 s,
drawn points on the plane to < 0.1 mm, one family transition handled pen-up.

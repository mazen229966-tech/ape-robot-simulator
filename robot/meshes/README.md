# Meshes

The URDF `../urdf/sv2_6045.urdf` uses **primitive shapes** (cylinders) for all
links, so no external mesh files are required.

Rationale: APE has not published CAD data for the SV2-6045, and third-party
meshes would raise licensing questions. The primitive geometry is a kinematic
and visualization surrogate sized from the educational DH parameters; its
kinematics are verified identical to the simulator's DH model by
`backend/tests/test_urdf.py`.

If official CAD becomes available, drop the mesh files here and update the
URDF `<visual>`/`<collision>` blocks accordingly — no backend changes needed.

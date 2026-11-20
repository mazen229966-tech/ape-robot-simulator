"""Result export endpoints (spec §44): trajectory CSV / JSON."""

from __future__ import annotations

import io
import json

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

import pandas as pd

from ..simulation.state import trajectory_store
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/trajectory")
def export_trajectory(
    trajectory_id: str | None = Query(default=None),
    format: str = Query(default="csv", pattern="^(csv|json)$"),
):
    try:
        traj = trajectory_store.get(trajectory_id)
    except RoboticsError as exc:
        raise_api_error(exc)

    n = len(traj["t"])
    data = {"time_s": traj["t"]}
    for j in range(6):
        data[f"q{j + 1}_rad"] = [row[j] for row in traj["q"]]
        data[f"qd{j + 1}_rad_s"] = [row[j] for row in traj["qd"]]
        data[f"qdd{j + 1}_rad_s2"] = [row[j] for row in traj["qdd"]]
    if "total_torque" in traj:
        for j in range(6):
            data[f"tau{j + 1}_Nm"] = [row[j] for row in traj["total_torque"]]
    data["x_m"] = [p[0] for p in traj["ee_path"]]
    data["y_m"] = [p[1] for p in traj["ee_path"]]
    data["z_m"] = [p[2] for p in traj["ee_path"]]

    if format == "json":
        payload = {
            "meta": {
                "method": traj.get("method"),
                "space": traj.get("space"),
                "duration": traj.get("duration"),
                "samples": n,
            },
            "columns": data,
        }
        return json.loads(json.dumps(payload))

    df = pd.DataFrame(data)
    buf = io.StringIO()
    df.to_csv(buf, index=False, float_format="%.9g")
    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=trajectory.csv"
        },
    )

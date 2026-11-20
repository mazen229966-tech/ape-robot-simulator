"""DH table endpoints: read, apply, reset, export (spec §8)."""

from __future__ import annotations

import csv
import io
import math

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from ..models.parameters import parameter_store
from ..models.schemas import DHApplyRequest
from ..utils.errors import RoboticsError, raise_api_error

router = APIRouter(prefix="/api/dh", tags=["dh"])


def _table_payload() -> dict:
    rows = []
    for i, (_, d, a, alpha) in enumerate(parameter_store.dh_table(), start=1):
        rows.append(
            {
                "i": i,
                "theta": f"q{i}",
                "joint_type": "Revolute",
                "d_m": d,
                "a_m": a,
                "alpha_rad": alpha,
                "d_mm": round(d * 1e3, 4),
                "a_mm": round(a * 1e3, 4),
                "alpha_deg": round(math.degrees(alpha), 4),
            }
        )
    return {
        "convention": "Standard (classic) Denavit-Hartenberg",
        "transform_formula": "A_i = Rz(theta_i) Tz(d_i) Tx(a_i) Rx(alpha_i)",
        "units": {"theta": "degree", "d": "mm", "a": "mm", "alpha": "degree"},
        "parameter_source": parameter_store.source,
        "links": rows,
    }


@router.get("")
def get_dh() -> dict:
    return _table_payload()


@router.post("/apply")
def apply_dh(req: DHApplyRequest) -> dict:
    try:
        parameter_store.apply_dh_table(
            [
                {
                    "d": link.d,
                    "a": link.a,
                    "alpha": math.radians(link.alpha),
                }
                for link in req.links
            ]
        )
    except RoboticsError as exc:
        raise_api_error(exc)
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(exc))
    return _table_payload()


@router.post("/reset")
def reset_dh() -> dict:
    parameter_store.reset()
    return _table_payload()


@router.get("/export")
def export_dh(format: str = Query(default="csv", pattern="^(csv|json)$")):
    payload = _table_payload()
    if format == "json":
        return payload
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["i", "theta", "joint_type", "d_mm", "a_mm", "alpha_deg"])
    for row in payload["links"]:
        writer.writerow(
            [row["i"], row["theta"], row["joint_type"],
             row["d_mm"], row["a_mm"], row["alpha_deg"]]
        )
    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dh_table.csv"},
    )

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.exact_cell_intelligence import (
    build_exact_cell_intelligence,
)


router = APIRouter(
    prefix="/api/v1/intelligence",
    tags=["intelligence"],
)


@router.get(
    "/cell/{cell_id}"
)
def exact_cell_intelligence(
    cell_id: str,
    rainfall_change_percent: float = 100.0,
    radius_m: float = 5000.0,
):
    """
    Return the complete AwareOn intelligence state
    for one exact cell.
    """

    if not cell_id:
        raise HTTPException(
            status_code=400,
            detail="cell_id is required.",
        )

    if radius_m <= 0:
        raise HTTPException(
            status_code=400,
            detail="radius_m must be greater than 0.",
        )

    try:

        result = build_exact_cell_intelligence(
            cell_id=cell_id,
            rainfall_change_percent=(
                rainfall_change_percent
            ),
            radius_m=radius_m,
        )

        return {
            "success": True,
            **result,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Exact cell intelligence failed: "
                f"{exc}"
            ),
        )

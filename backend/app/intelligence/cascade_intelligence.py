from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import CascadeImpact, clamp


def _neighbors(cell_id: str) -> list[str]:
    try:
        x_text, y_text = str(cell_id).split("_", 1)
        x, y = int(x_text), int(y_text)
    except (TypeError, ValueError):
        return []
    return [f"{x+dx}_{y+dy}" for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1))]


def build_cascade_impact(root: Path, cell_id: str, radius_steps: int = 1) -> dict[str, Any]:
    state_path = root / "data" / "processed" / "intelligence" / "awareon_intelligence_state.csv"
    exposure_path = root / "data" / "processed" / "engines" / "exposure_impact_engine_output.csv"
    if not state_path.exists() or not exposure_path.exists():
        raise FileNotFoundError("Canonical intelligence or exposure artifact is missing.")

    state = pd.read_csv(state_path)
    exposure = pd.read_csv(exposure_path)
    state["cell_id"] = state["cell_id"].astype(str)
    exposure["cell_id"] = exposure["cell_id"].astype(str)
    merged = state.merge(exposure, on="cell_id", how="left", suffixes=("", "_exposure"))
    row = merged.loc[merged["cell_id"] == str(cell_id)]
    if row.empty:
        raise KeyError(f"Unknown cell: {cell_id}")
    origin = row.iloc[0]

    candidates = {str(cell_id)}
    frontier = {str(cell_id)}
    for _ in range(max(1, min(3, int(radius_steps)))):
        nxt = set()
        for item in frontier:
            nxt.update(_neighbors(item))
        frontier = nxt - candidates
        candidates.update(frontier)

    nearby = merged[merged["cell_id"].isin(candidates)].copy()
    nearby = nearby.dropna(subset=["unified_risk_score"])
    nearby["unified_risk_score"] = pd.to_numeric(nearby["unified_risk_score"], errors="coerce")
    nearby["exposure_score"] = pd.to_numeric(nearby["exposure_score"], errors="coerce").fillna(0.0)
    nearby = nearby.dropna(subset=["unified_risk_score"])

    domains = set()
    for value in nearby.get("dominant_exposure", pd.Series(dtype=str)).fillna("UNKNOWN"):
        domains.add(str(value))

    if not domains:
        domains.add("UNKNOWN")

    neighbor_risk = float(nearby["unified_risk_score"].mean()) if len(nearby) else float(origin["unified_risk_score"])
    cascade_score = clamp(
        0.55 * float(origin["unified_risk_score"])
        + 0.25 * float(origin["exposure_score"])
        + 0.20 * neighbor_risk
    )

    dependency_confidence = clamp(
        35.0
        + min(25.0, float(len(nearby)) * 5.0)
        + min(20.0, float(origin.get("confidence_score", 0.0)) * 0.2)
    )

    result = CascadeImpact(
        origin_cell_id=str(cell_id),
        impacted_cells=tuple(str(x) for x in nearby["cell_id"].tolist()),
        impacted_domains=tuple(sorted(domains)),
        cascade_score=cascade_score,
        dependency_confidence=dependency_confidence,
        modeled_proxy=True,
        assumptions=(
            "Connectivity is inferred from the AwareOn grid topology and exposure fields.",
            "No exact asset-to-asset dependency network is asserted by this layer.",
            "Impact is a modeled consequence proxy and requires asset-level verification before operational use.",
        ),
        evidence_ids=(
            f"STATE:{cell_id}",
            f"EXPOSURE:{cell_id}",
        ),
    )
    return result.to_dict()

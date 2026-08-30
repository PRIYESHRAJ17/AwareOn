from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category(value: Any) -> str:
    return str(value or "UNKNOWN").upper()


def link_cluster_to_exposure(
    cluster: dict[str, Any],
) -> dict[str, Any]:
    if not cluster:
        raise ValueError("Cluster is required.")

    cell_ids = cluster.get("cell_ids", [])

    if not isinstance(cell_ids, list):
        raise ValueError("cluster.cell_ids must be a list.")

    from backend.app.services.gis_service import load_exposure_lookup

    exposure_lookup = load_exposure_lookup()

    matched: list[dict[str, Any]] = []
    missing: list[str] = []

    for raw_cell_id in cell_ids:
        cell_id = str(raw_cell_id)
        row = exposure_lookup.get(cell_id)

        if row is None:
            missing.append(cell_id)
            continue

        matched.append(
            {
                "cell_id": cell_id,
                "exposure_score": _num(
                    row.get("exposure_score")
                ),
                "exposure_category": _category(
                    row.get("exposure_category")
                ),
                "transport_exposure": _num(
                    row.get("transport_exposure")
                ),
                "population_exposure": _num(
                    row.get("population_exposure_proxy")
                ),
                "infrastructure_exposure": _num(
                    row.get("infrastructure_exposure")
                ),
                "dominant_exposure": _category(
                    row.get("dominant_exposure")
                ),
            }
        )

    total_cells = len(cell_ids)
    matched_count = len(matched)

    if matched_count == 0:
        return {
            "cluster_id": cluster.get("cluster_id"),
            "cell_count": total_cells,
            "matched_cells": 0,
            "missing_cells": len(missing),
            "coverage": 0.0,
            "exposure_state": "NO_EXPOSURE_DATA",
            "impact_focus": "UNKNOWN",
            "dominant_exposure": "UNKNOWN",
            "exposure_summary": {},
            "dominant_exposure_counts": {},
            "top_exposed_cells": [],
        }

    exposure_values = [
        item["exposure_score"]
        for item in matched
    ]

    transport_values = [
        item["transport_exposure"]
        for item in matched
    ]

    population_values = [
        item["population_exposure"]
        for item in matched
    ]

    infrastructure_values = [
        item["infrastructure_exposure"]
        for item in matched
    ]

    mean_exposure = (
        sum(exposure_values) / matched_count
    )

    max_exposure = max(
        exposure_values
    )

    mean_transport = (
        sum(transport_values) / matched_count
    )

    mean_population = (
        sum(population_values) / matched_count
    )

    mean_infrastructure = (
        sum(infrastructure_values) / matched_count
    )

    high_exposure_cells = sum(
        1
        for value in exposure_values
        if value >= 60.0
    )

    dominant_counts: dict[str, int] = {}

    for item in matched:
        key = item["dominant_exposure"]
        dominant_counts[key] = (
            dominant_counts.get(key, 0) + 1
        )

    dominant_exposure = max(
        dominant_counts,
        key=dominant_counts.get,
    )

    if (
        mean_exposure >= 70.0
        or max_exposure >= 80.0
    ):
        exposure_state = "CRITICAL_EXPOSURE"

    elif mean_exposure >= 50.0:
        exposure_state = "HIGH_EXPOSURE"

    elif mean_exposure >= 30.0:
        exposure_state = "ELEVATED_EXPOSURE"

    else:
        exposure_state = "LIMITED_EXPOSURE"

    if (
        dominant_exposure == "TRANSPORT"
        and mean_transport >= 60.0
    ):
        impact_focus = "TRANSPORT"

    elif (
        dominant_exposure == "SETTLEMENT"
        or mean_population >= 60.0
    ):
        impact_focus = "POPULATION"

    elif mean_infrastructure >= 60.0:
        impact_focus = "INFRASTRUCTURE"

    else:
        impact_focus = dominant_exposure

    coverage = (
        matched_count / total_cells
        if total_cells > 0
        else 0.0
    )

    top_exposed = sorted(
        matched,
        key=lambda item: (
            item["exposure_score"],
            item["infrastructure_exposure"],
            item["transport_exposure"],
        ),
        reverse=True,
    )[:10]

    return {
        "cluster_id": cluster.get(
            "cluster_id"
        ),
        "cell_count": total_cells,
        "matched_cells": matched_count,
        "missing_cells": len(missing),
        "coverage": coverage,
        "exposure_state": exposure_state,
        "impact_focus": impact_focus,
        "dominant_exposure": dominant_exposure,
        "exposure_summary": {
            "mean_exposure": mean_exposure,
            "maximum_exposure": max_exposure,
            "mean_transport": mean_transport,
            "mean_population": mean_population,
            "mean_infrastructure": mean_infrastructure,
            "high_exposure_cells": high_exposure_cells,
        },
        "dominant_exposure_counts": dominant_counts,
        "top_exposed_cells": top_exposed,
    }

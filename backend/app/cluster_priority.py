from __future__ import annotations

from typing import Any


SEVERITY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank(value: Any) -> int:
    return SEVERITY_RANK.get(
        str(value or "").upper(),
        0,
    )


def _clamp(value: float) -> float:
    return max(
        0.0,
        min(100.0, value),
    )


def _priority_level(score: float) -> str:
    if score >= 85.0:
        return "P1_CRITICAL"

    if score >= 70.0:
        return "P2_HIGH"

    if score >= 50.0:
        return "P3_ELEVATED"

    return "P4_MONITOR"


def score_cluster(
    cluster: dict[str, Any],
) -> dict[str, Any]:

    if not cluster:
        raise ValueError(
            "Cluster is required."
        )

    cell_count = max(
        0,
        int(
            _num(
                cluster.get(
                    "cell_count"
                )
            )
        ),
    )

    mean_risk = _clamp(
        _num(
            cluster.get(
                "mean_risk"
            )
        )
    )

    maximum_risk = _clamp(
        _num(
            cluster.get(
                "maximum_risk"
            )
        )
    )

    extreme_cells = max(
        0,
        int(
            _num(
                cluster.get(
                    "extreme_cells"
                )
            )
        ),
    )

    warning_cells = max(
        0,
        int(
            _num(
                cluster.get(
                    "critical_or_warning_cells"
                )
            )
        ),
    )

    mean_confidence = _clamp(
        _num(
            cluster.get(
                "mean_confidence"
            )
        )
    )

    severity = str(
        cluster.get(
            "cluster_severity"
        )
        or "UNKNOWN"
    ).upper()

    severity_signal = (
        _rank(severity) / 3.0
    ) * 100.0

    size_signal = min(
        100.0,
        cell_count * 10.0,
    )

    extreme_ratio = (
        extreme_cells / cell_count
        if cell_count > 0
        else 0.0
    )

    warning_ratio = (
        warning_cells / cell_count
        if cell_count > 0
        else 0.0
    )

    extreme_signal = extreme_ratio * 100.0
    warning_signal = warning_ratio * 100.0

    risk_signal = (
        mean_risk * 0.60
        +
        maximum_risk * 0.40
    )

    priority_score = (
        risk_signal * 0.30
        +
        severity_signal * 0.20
        +
        size_signal * 0.15
        +
        extreme_signal * 0.15
        +
        warning_signal * 0.10
        +
        mean_confidence * 0.10
    )

    priority_score = _clamp(
        priority_score
    )

    priority_level = _priority_level(
        priority_score
    )

    if (
        priority_score >= 85.0
        and extreme_cells >= 3
    ):
        operational_posture = (
            "IMMEDIATE_REGIONAL_RESPONSE"
        )

    elif (
        priority_score >= 70.0
        and warning_ratio >= 0.40
    ):
        operational_posture = (
            "HIGH_PRIORITY_REGIONAL_REVIEW"
        )

    elif priority_score >= 50.0:
        operational_posture = (
            "ELEVATED_REGIONAL_MONITORING"
        )

    else:
        operational_posture = (
            "ROUTINE_REGIONAL_MONITORING"
        )

    if extreme_ratio >= 0.50:
        concentration = (
            "EXTREME_CONCENTRATION"
        )

    elif extreme_ratio >= 0.25:
        concentration = (
            "HIGH_EXTREME_CONCENTRATION"
        )

    elif warning_ratio >= 0.50:
        concentration = (
            "HIGH_WARNING_CONCENTRATION"
        )

    else:
        concentration = (
            "LIMITED_CONCENTRATION"
        )

    if mean_confidence >= 75.0:
        confidence_band = "HIGH"

    elif mean_confidence >= 50.0:
        confidence_band = "MODERATE"

    else:
        confidence_band = "LIMITED"

    return {
        "cluster_id": cluster.get(
            "cluster_id"
        ),
        "priority_score": round(
            priority_score,
            2,
        ),
        "priority_level": priority_level,
        "operational_posture": operational_posture,
        "concentration": concentration,
        "confidence": confidence_band,
        "components": {
            "risk_signal": round(
                risk_signal,
                2,
            ),
            "severity_signal": round(
                severity_signal,
                2,
            ),
            "size_signal": round(
                size_signal,
                2,
            ),
            "extreme_signal": round(
                extreme_signal,
                2,
            ),
            "warning_signal": round(
                warning_signal,
                2,
            ),
            "confidence_signal": round(
                mean_confidence,
                2,
            ),
        },
        "metrics": {
            "cell_count": cell_count,
            "mean_risk": mean_risk,
            "maximum_risk": maximum_risk,
            "extreme_cells": extreme_cells,
            "warning_cells": warning_cells,
            "extreme_ratio": round(
                extreme_ratio,
                4,
            ),
            "warning_ratio": round(
                warning_ratio,
                4,
            ),
            "mean_confidence": mean_confidence,
        },
    }


def rank_clusters(
    clusters: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    if not isinstance(
        clusters,
        list,
    ):
        raise ValueError(
            "clusters must be a list."
        )

    ranked = []

    for cluster in clusters:

        scored = score_cluster(
            cluster
        )

        ranked.append(
            {
                **cluster,
                "priority": scored,
            }
        )

    ranked.sort(
        key=lambda item: (
            _num(
                item["priority"].get(
                    "priority_score"
                )
            ),
            _num(
                item.get(
                    "maximum_risk"
                )
            ),
            _num(
                item.get(
                    "cell_count"
                )
            ),
        ),
        reverse=True,
    )

    for rank, cluster in enumerate(
        ranked,
        start=1,
    ):
        cluster["priority"][
            "priority_rank"
        ] = rank

    return ranked

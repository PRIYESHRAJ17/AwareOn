from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank(value: Any) -> int:
    return {
        "LOW": 0,
        "MODERATE": 1,
        "HIGH": 2,
        "EXTREME": 3,
    }.get(
        str(value or "").upper(),
        0,
    )


def _clamp(value: float) -> float:
    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


def _hotspot_level(score: float) -> str:
    if score >= 85.0:
        return "CRITICAL"

    if score >= 70.0:
        return "HIGH"

    if score >= 50.0:
        return "ELEVATED"

    return "MONITOR"


def rank_regional_hotspots(
    clusters: list[dict[str, Any]],
    top_n: int = 10,
) -> dict[str, Any]:

    if not isinstance(
        clusters,
        list,
    ):
        raise ValueError(
            "clusters must be a list."
        )

    if top_n <= 0:
        raise ValueError(
            "top_n must be greater than 0."
        )

    scored = []

    for cluster in clusters:

        if not isinstance(
            cluster,
            dict,
        ):
            continue

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

        cluster_severity = str(
            cluster.get(
                "cluster_severity"
            )
            or "UNKNOWN"
        ).upper()

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

        size_signal = min(
            100.0,
            cell_count * 10.0,
        )

        risk_signal = (
            mean_risk * 0.60
            +
            maximum_risk * 0.40
        )

        severity_signal = (
            _rank(
                cluster_severity
            )
            /
            3.0
        ) * 100.0

        extreme_signal = (
            extreme_ratio * 100.0
        )

        warning_signal = (
            warning_ratio * 100.0
        )

        hotspot_score = (
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

        hotspot_score = _clamp(
            hotspot_score
        )

        scored.append(
            {
                "cluster_id":
                    cluster.get(
                        "cluster_id"
                    ),

                "hotspot_score":
                    round(
                        hotspot_score,
                        2,
                    ),

                "hotspot_level":
                    _hotspot_level(
                        hotspot_score
                    ),

                "cluster_severity":
                    cluster_severity,

                "cell_count":
                    cell_count,

                "mean_risk":
                    mean_risk,

                "maximum_risk":
                    maximum_risk,

                "maximum_risk_cell":
                    cluster.get(
                        "maximum_risk_cell"
                    ),

                "extreme_cells":
                    extreme_cells,

                "warning_cells":
                    warning_cells,

                "mean_confidence":
                    mean_confidence,

                "centroid":
                    cluster.get(
                        "centroid"
                    ),

                "cell_ids":
                    cluster.get(
                        "cell_ids",
                        [],
                    ),

                "metrics":
                    {
                        "risk_signal":
                            round(
                                risk_signal,
                                2,
                            ),

                        "size_signal":
                            round(
                                size_signal,
                                2,
                            ),

                        "severity_signal":
                            round(
                                severity_signal,
                                2,
                            ),

                        "extreme_signal":
                            round(
                                extreme_signal,
                                2,
                            ),

                        "warning_signal":
                            round(
                                warning_signal,
                                2,
                            ),

                        "confidence_signal":
                            round(
                                mean_confidence,
                                2,
                            ),
                    },
            }
        )

    scored.sort(
        key=lambda item: (
            item["hotspot_score"],
            item["maximum_risk"],
            item["cell_count"],
        ),
        reverse=True,
    )

    ranked = scored[:top_n]

    for index, hotspot in enumerate(
        ranked,
        start=1,
    ):
        hotspot["rank"] = index

    if ranked:

        critical_count = sum(
            1
            for item in ranked
            if item["hotspot_level"] == "CRITICAL"
        )

        high_count = sum(
            1
            for item in ranked
            if item["hotspot_level"] == "HIGH"
        )

        top = ranked[0]

        regional_posture = (
            "CRITICAL"
            if critical_count > 0
            else "HIGH"
            if high_count > 0
            else "ELEVATED"
        )

        interpretation = (
            f"Top regional hotspot is "
            f"{top['cluster_id']} with a hotspot score "
            f"of {top['hotspot_score']:.2f}, "
            f"{top['cell_count']} cells, and maximum "
            f"risk {top['maximum_risk']:.2f}."
        )

    else:

        critical_count = 0
        high_count = 0
        regional_posture = "MONITOR"

        interpretation = (
            "No regional hotspots were available."
        )

    return {
        "hotspot_count":
            len(ranked),

        "available_clusters":
            len(scored),

        "regional_posture":
            regional_posture,

        "critical_hotspots":
            critical_count,

        "high_hotspots":
            high_count,

        "hotspots":
            ranked,

        "interpretation":
            interpretation,
    }

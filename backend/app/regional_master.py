from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    return str(value)


def build_regional_master(
    cluster: dict[str, Any],
    priority: dict[str, Any],
    exposure: dict[str, Any],
    evolution: dict[str, Any],
    command: dict[str, Any],
) -> dict[str, Any]:

    if not cluster:
        raise ValueError("cluster is required.")

    if not priority:
        raise ValueError("priority is required.")

    if not exposure:
        raise ValueError("exposure is required.")

    if not evolution:
        raise ValueError("evolution is required.")

    if not command:
        raise ValueError("command is required.")

    exposure_summary = exposure.get(
        "exposure_summary",
        {},
    )

    if not isinstance(
        exposure_summary,
        dict,
    ):
        exposure_summary = {}

    cluster_id = _text(
        cluster.get("cluster_id")
    )

    cell_count = int(
        _num(
            cluster.get("cell_count")
        )
    )

    extreme_cells = int(
        _num(
            cluster.get("extreme_cells")
        )
    )

    mean_risk = _num(
        cluster.get("mean_risk")
    )

    maximum_risk = _num(
        cluster.get("maximum_risk")
    )

    priority_score = _num(
        priority.get("priority_score")
    )

    priority_level = _text(
        priority.get("priority_level")
    )

    regional_posture = _text(
        command.get("regional_posture")
    )

    urgency = _text(
        command.get("urgency")
    )

    operational_focus = _text(
        command.get("operational_focus")
    )

    trajectory = _text(
        evolution.get("trajectory")
    )

    behavior = _text(
        evolution.get("cluster_behavior")
    )

    mean_risk_delta = _num(
        evolution.get("mean_risk_delta")
    )

    high_cell_delta = int(
        _num(
            evolution.get("high_cell_delta")
        )
    )

    extreme_cell_delta = int(
        _num(
            evolution.get("extreme_cell_delta")
        )
    )

    exposure_state = _text(
        exposure.get("exposure_state")
    )

    impact_focus = _text(
        exposure.get("impact_focus")
    )

    high_exposure_cells = int(
        _num(
            exposure_summary.get(
                "high_exposure_cells"
            )
        )
    )

    maximum_exposure = _num(
        exposure_summary.get(
            "maximum_exposure"
        )
    )

    exposure_coverage = _num(
        exposure.get("coverage")
    )

    confidence_score = _num(
        cluster.get("mean_confidence")
    )

    if confidence_score >= 75.0:
        confidence_band = "HIGH"
    elif confidence_score >= 50.0:
        confidence_band = "MODERATE"
    else:
        confidence_band = "LIMITED"

    if (
        regional_posture == "CRITICAL_AND_ESCALATING"
        and exposure_state == "CRITICAL_EXPOSURE"
    ):
        master_state = "CRITICAL_REGIONAL_ALERT"

    elif regional_posture.startswith(
        "CRITICAL"
    ):
        master_state = "CRITICAL_REGION"

    elif trajectory in {
        "ACCELERATING",
        "INCREASING",
    }:
        master_state = "ESCALATING_REGION"

    elif priority_score >= 70.0:
        master_state = "HIGH_PRIORITY_REGION"

    else:
        master_state = "REGIONAL_MONITORING"

    parts: list[str] = []

    parts.append(
        f"{cluster_id} contains {cell_count} "
        f"high-risk cells with mean risk "
        f"{mean_risk:.2f} and maximum risk "
        f"{maximum_risk:.2f}."
    )

    if extreme_cells > 0:
        parts.append(
            f"{extreme_cells} cells are EXTREME."
        )

    if trajectory == "ACCELERATING":
        parts.append(
            "Risk evolution is accelerating."
        )

    elif trajectory == "INCREASING":
        parts.append(
            "Risk is increasing."
        )

    if high_exposure_cells > 0:
        parts.append(
            f"{high_exposure_cells} cells "
            "have high exposure."
        )

    parts.append(
        f"Primary impact focus is {impact_focus}."
    )

    parts.append(
        f"Operational focus is "
        f"{operational_focus}."
    )

    if urgency == "IMMEDIATE":
        parts.append(
            "The regional posture requires "
            "immediate review."
        )

    elif urgency == "HIGH":
        parts.append(
            "The regional posture requires "
            "high-priority review."
        )

    return {
        "engine":
            "AWAREON_REGIONAL_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "cluster_id":
            cluster_id,

        "master_state":
            master_state,

        "regional_posture":
            regional_posture,

        "urgency":
            urgency,

        "priority":
            {
                "level":
                    priority_level,

                "score":
                    priority_score,
            },

        "risk":
            {
                "cell_count":
                    cell_count,

                "extreme_cells":
                    extreme_cells,

                "mean_risk":
                    mean_risk,

                "maximum_risk":
                    maximum_risk,

                "maximum_risk_cell":
                    cluster.get(
                        "maximum_risk_cell"
                    ),
            },

        "evolution":
            {
                "trajectory":
                    trajectory,

                "behavior":
                    behavior,

                "mean_risk_delta":
                    mean_risk_delta,

                "high_cell_delta":
                    high_cell_delta,

                "extreme_cell_delta":
                    extreme_cell_delta,
            },

        "exposure":
            {
                "state":
                    exposure_state,

                "impact_focus":
                    impact_focus,

                "high_exposure_cells":
                    high_exposure_cells,

                "maximum_exposure":
                    maximum_exposure,

                "coverage":
                    exposure_coverage,
            },

        "operational_focus":
            operational_focus,

        "confidence":
            {
                "score":
                    confidence_score,

                "band":
                    confidence_band,
            },

        "master_signal":
            {
                "regional_state":
                    master_state,

                "posture":
                    regional_posture,

                "urgency":
                    urgency,

                "trajectory":
                    trajectory,

                "exposure":
                    exposure_state,

                "impact_focus":
                    impact_focus,

                "priority":
                    priority_level,
            },

        "decision":
            " ".join(parts),
    }

from __future__ import annotations

from typing import Any


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_regional_command_intelligence(
    cluster: dict[str, Any],
    priority: dict[str, Any],
    exposure: dict[str, Any],
    evolution: dict[str, Any],
) -> dict[str, Any]:

    if not cluster:
        raise ValueError(
            "cluster is required."
        )

    if not priority:
        raise ValueError(
            "priority is required."
        )

    if not exposure:
        raise ValueError(
            "exposure is required."
        )

    if not evolution:
        raise ValueError(
            "evolution is required."
        )

    cluster_id = str(
        cluster.get(
            "cluster_id"
        )
        or "UNKNOWN_CLUSTER"
    )

    cluster_severity = str(
        cluster.get(
            "cluster_severity"
        )
        or "UNKNOWN"
    ).upper()

    operational_state = str(
        cluster.get(
            "operational_state"
        )
        or "UNKNOWN"
    ).upper()

    priority_score = _num(
        priority.get(
            "priority_score"
        )
    )

    priority_level = str(
        priority.get(
            "priority_level"
        )
        or "UNKNOWN"
    ).upper()

    exposure_state = str(
        exposure.get(
            "exposure_state"
        )
        or "UNKNOWN"
    ).upper()

    impact_focus = str(
        exposure.get(
            "impact_focus"
        )
        or "UNKNOWN"
    ).upper()

    trajectory = str(
        evolution.get(
            "trajectory"
        )
        or "UNKNOWN"
    ).upper()

    cluster_behavior = str(
        evolution.get(
            "cluster_behavior"
        )
        or "UNKNOWN"
    ).upper()

    high_risk_cells = int(
        _num(
            cluster.get(
                "cell_count"
            )
        )
    )

    extreme_cells = int(
        _num(
            cluster.get(
                "extreme_cells"
            )
        )
    )

    mean_risk = _num(
        cluster.get(
            "mean_risk"
        )
    )

    maximum_risk = _num(
        cluster.get(
            "maximum_risk"
        )
    )

    maximum_exposure = _num(
        exposure.get(
            "exposure_summary",
            {}
        ).get(
            "maximum_exposure"
        )
    )

    high_exposure_cells = int(
        _num(
            exposure.get(
                "exposure_summary",
                {}
            ).get(
                "high_exposure_cells"
            )
        )
    )

    if (
        cluster_severity == "EXTREME"
        and exposure_state == "CRITICAL_EXPOSURE"
        and trajectory == "ACCELERATING"
    ):
        regional_posture = (
            "CRITICAL_AND_ESCALATING"
        )

    elif (
        cluster_severity == "EXTREME"
        and exposure_state == "CRITICAL_EXPOSURE"
    ):
        regional_posture = (
            "CRITICAL_HIGH_IMPACT_REGION"
        )

    elif (
        cluster_severity in {
            "EXTREME",
            "HIGH",
        }
        and trajectory in {
            "ACCELERATING",
            "INCREASING",
        }
    ):
        regional_posture = (
            "ESCALATING_HIGH_RISK_REGION"
        )

    elif cluster_severity == "EXTREME":
        regional_posture = (
            "CRITICAL_REGION"
        )

    elif cluster_severity == "HIGH":
        regional_posture = (
            "HIGH_RISK_REGION"
        )

    else:
        regional_posture = (
            "ELEVATED_REGION"
        )

    if (
        impact_focus == "TRANSPORT"
    ):
        operational_focus = (
            "TRANSPORT_CORRIDOR_PROTECTION"
        )

    elif (
        impact_focus == "POPULATION"
    ):
        operational_focus = (
            "POPULATION_SAFETY_REVIEW"
        )

    elif (
        impact_focus == "INFRASTRUCTURE"
    ):
        operational_focus = (
            "INFRASTRUCTURE_PROTECTION"
        )

    else:
        operational_focus = (
            "MULTI_ASSET_REVIEW"
        )

    if (
        trajectory == "ACCELERATING"
        and
        cluster_behavior
        == "EXPANDING_RISK"
    ):
        urgency = "IMMEDIATE"

    elif (
        trajectory in {
            "ACCELERATING",
            "INCREASING",
        }
        or
        priority_score >= 70.0
    ):
        urgency = "HIGH"

    elif priority_score >= 50.0:
        urgency = "ELEVATED"

    else:
        urgency = "ROUTINE"

    confidence = _num(
        exposure.get(
            "mean_confidence"
        )
    )

    if confidence >= 75.0:
        confidence_band = "HIGH"
    elif confidence >= 50.0:
        confidence_band = "MODERATE"
    else:
        confidence_band = "LIMITED"

    decision_parts = [
        (
            f"{cluster_id} is a "
            f"{cluster_severity} regional risk cluster "
            f"containing {high_risk_cells} cells."
        )
    ]

    decision_parts.append(
        (
            f"Mean risk is {mean_risk:.2f} with a "
            f"maximum of {maximum_risk:.2f}."
        )
    )

    if trajectory == "ACCELERATING":
        decision_parts.append(
            "Risk evolution is accelerating."
        )

    elif trajectory == "INCREASING":
        decision_parts.append(
            "Risk is increasing across tested conditions."
        )

    if exposure_state == "CRITICAL_EXPOSURE":
        decision_parts.append(
            (
                f"Exposure is critical, with "
                f"{high_exposure_cells} high-exposure cells "
                f"and maximum exposure "
                f"{maximum_exposure:.2f}."
            )
        )

    decision_parts.append(
        f"Primary operational focus: {operational_focus}."
    )

    return {
        "cluster_id": cluster_id,

        "regional_posture":
            regional_posture,

        "urgency":
            urgency,

        "priority_level":
            priority_level,

        "priority_score":
            priority_score,

        "cluster_severity":
            cluster_severity,

        "operational_state":
            operational_state,

        "operational_focus":
            operational_focus,

        "evolution":
            {
                "trajectory":
                    trajectory,

                "behavior":
                    cluster_behavior,

                "mean_risk_delta":
                    _num(
                        evolution.get(
                            "mean_risk_delta"
                        )
                    ),

                "high_cell_delta":
                    int(
                        _num(
                            evolution.get(
                                "high_cell_delta"
                            )
                        )
                    ),

                "extreme_cell_delta":
                    int(
                        _num(
                            evolution.get(
                                "extreme_cell_delta"
                            )
                        )
                    ),
            },

        "risk":
            {
                "cell_count":
                    high_risk_cells,

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

        "exposure":
            {
                "state":
                    exposure_state,

                "impact_focus":
                    impact_focus,

                "maximum_exposure":
                    maximum_exposure,

                "high_exposure_cells":
                    high_exposure_cells,

                "coverage":
                    _num(
                        exposure.get(
                            "coverage"
                        )
                    ),
            },

        "confidence":
            confidence_band,

        "decision":
            " ".join(
                decision_parts
            ),
    }

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


def _int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _scenario_name(
    value: Any,
) -> str:
    return str(
        value or "UNKNOWN"
    )


def build_decision_brief(
    comparison: dict[str, Any],
    recommendation: dict[str, Any],
    priority: dict[str, Any],
) -> dict[str, Any]:

    if not comparison:
        raise ValueError(
            "Scenario comparison is required."
        )

    if not recommendation:
        raise ValueError(
            "Scenario recommendation is required."
        )

    if not priority:
        raise ValueError(
            "Scenario priority is required."
        )

    worst_mean = (
        comparison
        .get(
            "worst_mean_risk",
            {},
        )
    )

    trigger_shift = (
        comparison
        .get(
            "trigger_shift",
            {},
        )
    )

    scenario = (
        recommendation
        .get(
            "scenario"
        )
    )

    rainfall = _num(
        recommendation.get(
            "rainfall_change_percent"
        )
    )

    escalating = _int(
        recommendation.get(
            "escalating_cells"
        )
    )

    new_high = _int(
        recommendation.get(
            "new_high_or_extreme"
        )
    )

    new_extreme = _int(
        recommendation.get(
            "new_extreme_cells"
        )
    )

    mean_risk = _num(
        recommendation.get(
            "mean_risk_score"
        )
    )

    mean_change = _num(
        recommendation.get(
            "mean_risk_change"
        )
    )

    max_risk = _num(
        recommendation.get(
            "max_risk_score"
        )
    )

    recommendation_level = str(
        recommendation.get(
            "recommendation_level"
        )
        or "UNKNOWN"
    )

    baseline_trigger = str(
        trigger_shift.get(
            "baseline"
        )
        or "UNKNOWN"
    )

    worst_trigger = str(
        trigger_shift.get(
            "worst_case"
        )
        or "UNKNOWN"
    )

    priority_cells = (
        priority.get(
            "top_priority_cells",
            [],
        )
    )

    top_cells = []

    for item in priority_cells[:10]:

        top_cells.append(
            {
                "rank":
                    _int(
                        item.get(
                            "priority_rank"
                        )
                    ),

                "cell_id":
                    item.get(
                        "cell_id"
                    ),

                "transition":
                    item.get(
                        "transition"
                    ),

                "priority_score":
                    _num(
                        item.get(
                            "priority_score"
                        )
                    ),

                "priority_level":
                    item.get(
                        "priority_level"
                    ),

                "baseline_risk":
                    _num(
                        item.get(
                            "baseline_risk"
                        )
                    ),

                "scenario_risk":
                    _num(
                        item.get(
                            "scenario_risk"
                        )
                    ),

                "risk_change":
                    _num(
                        item.get(
                            "risk_change"
                        )
                    ),

                "exposure":
                    _num(
                        item.get(
                            "exposure_component"
                        )
                    ),

                "susceptibility":
                    _num(
                        item.get(
                            "susceptibility_component"
                        )
                    ),
            }
        )

    if new_extreme > 0:

        headline = (
            f"+{rainfall:.0f}% rainfall creates "
            f"{new_extreme} new EXTREME cells."
        )

    elif new_high > 0:

        headline = (
            f"+{rainfall:.0f}% rainfall creates "
            f"{new_high} new HIGH-or-higher cells."
        )

    elif escalating > 0:

        headline = (
            f"+{rainfall:.0f}% rainfall escalates "
            f"{escalating} cells."
        )

    elif mean_change > 0:

        headline = (
            f"+{rainfall:.0f}% rainfall increases "
            f"mean risk by {mean_change:.2f} points."
        )

    else:

        headline = (
            "The tested scenario produces limited "
            "change relative to baseline."
        )

    if recommendation_level == "IMMEDIATE_REVIEW":

        operational_posture = (
            "Immediate review"
        )

    elif recommendation_level == "HIGH_PRIORITY":

        operational_posture = (
            "High-priority review"
        )

    elif recommendation_level == "ENHANCED_MONITORING":

        operational_posture = (
            "Enhanced monitoring"
        )

    else:

        operational_posture = (
            "Routine monitoring"
        )

    if baseline_trigger != worst_trigger:

        trigger_statement = (
            f"Rainfall trigger category shifts "
            f"from {baseline_trigger} to {worst_trigger}."
        )

    else:

        trigger_statement = (
            f"Rainfall trigger remains {worst_trigger} "
            "across the tested range."
        )

    summary = (
        f"{headline} The worst tested scenario is "
        f"{_scenario_name(scenario)} with mean risk "
        f"{mean_risk:.2f} and maximum risk "
        f"{max_risk:.2f}. "
        f"{trigger_statement}"
    )

    return {
        "scenario":
            scenario,

        "rainfall_change_percent":
            rainfall,

        "headline":
            headline,

        "operational_posture":
            operational_posture,

        "recommendation_level":
            recommendation_level,

        "summary":
            summary,

        "metrics":
            {
                "mean_risk":
                    mean_risk,

                "mean_risk_change":
                    mean_change,

                "maximum_risk":
                    max_risk,

                "escalating_cells":
                    escalating,

                "new_high_or_extreme":
                    new_high,

                "new_extreme_cells":
                    new_extreme,

                "trigger_baseline":
                    baseline_trigger,

                "trigger_worst_case":
                    worst_trigger,

                "trigger_rank_change":
                    _int(
                        trigger_shift.get(
                            "rank_change"
                        )
                    ),
            },

        "priority_cells":
            top_cells,

        "actions":
            recommendation.get(
                "actions",
                []
            ),
    }

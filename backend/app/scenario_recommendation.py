from __future__ import annotations

from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


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


def _recommendation_level(
    escalating_cells: int,
    high_or_extreme: int,
    new_extreme: int,
    mean_change: float,
) -> str:

    if (
        new_extreme > 0
        or high_or_extreme >= 75
    ):
        return "IMMEDIATE_REVIEW"

    if (
        high_or_extreme >= 25
        or escalating_cells >= 50
        or mean_change >= 5
    ):
        return "HIGH_PRIORITY"

    if (
        high_or_extreme >= 10
        or escalating_cells >= 20
        or mean_change >= 2
    ):
        return "ENHANCED_MONITORING"

    return "ROUTINE_MONITORING"


def _build_actions(
    level: str,
    escalating_cells: int,
    high_or_extreme: int,
    new_extreme: int,
) -> list[str]:

    actions: list[str] = []

    if level == "IMMEDIATE_REVIEW":

        actions.append(
            "Immediately review the highest-ranked "
            "scenario-sensitive cells."
        )

        if new_extreme > 0:

            actions.append(
                "Prioritize newly EXTREME cells for "
                "operational assessment."
            )

    elif level == "HIGH_PRIORITY":

        actions.append(
            "Prioritize review of the highest-ranked "
            "escalating cells."
        )

        actions.append(
            "Compare current HIGH-risk areas against "
            "scenario-sensitive locations."
        )

    elif level == "ENHANCED_MONITORING":

        actions.append(
            "Increase monitoring of cells showing "
            "meaningful scenario escalation."
        )

        actions.append(
            "Review cells approaching the next risk "
            "category threshold."
        )

    else:

        actions.append(
            "Maintain routine monitoring of the "
            "scenario-sensitive cells."
        )

    if escalating_cells > 0:

        actions.append(
            f"{escalating_cells} cells show category "
            "escalation under this scenario."
        )

    if high_or_extreme > 0:

        actions.append(
            f"{high_or_extreme} cells become HIGH "
            "or higher."
        )

    return actions


def build_scenario_recommendation(
    scenario_summary: dict[str, Any],
    ranked_cells: list[dict[str, Any]],
) -> dict[str, Any]:

    scenarios = scenario_summary.get(
        "scenarios",
        [],
    )

    if not scenarios:

        raise ValueError(
            "Scenario recommendation requires "
            "scenario summary data."
        )

    worst = max(
        scenarios,
        key=lambda item: _num(
            item.get(
                "mean_risk_score"
            )
        ),
    )

    escalating_cells = _int(
        worst.get(
            "escalating_cells"
        )
    )

    high_or_extreme = _int(
        worst.get(
            "new_high_or_extreme"
        )
    )

    new_extreme = _int(
        worst.get(
            "new_extreme_cells"
        )
    )

    mean_change = _num(
        worst.get(
            "mean_risk_change"
        )
    )

    level = _recommendation_level(
        escalating_cells,
        high_or_extreme,
        new_extreme,
        mean_change,
    )

    actions = _build_actions(
        level,
        escalating_cells,
        high_or_extreme,
        new_extreme,
    )

    top_cells = []

    for index, item in enumerate(
        ranked_cells[:10],
        start=1,
    ):

        top_cells.append(
            {
                "rank": index,

                "cell_id": item.get(
                    "cell_id"
                ),

                "transition": item.get(
                    "transition"
                ),

                "baseline_risk": _num(
                    item.get(
                        "baseline_risk_score"
                    )
                ),

                "scenario_risk": _num(
                    item.get(
                        "scenario_risk_score"
                    )
                ),

                "risk_change": _num(
                    item.get(
                        "risk_score_change"
                    )
                ),

                "sensitivity_score": _num(
                    item.get(
                        "sensitivity_score"
                    )
                ),

                "priority_level": item.get(
                    "priority_level"
                ),

                "exposure_score": _num(
                    item.get(
                        "exposure_score"
                    )
                ),
            }
        )

    return {
        "scenario": worst.get(
            "scenario"
        ),

        "rainfall_change_percent": _num(
            worst.get(
                "rainfall_change_percent"
            )
        ),

        "recommendation_level": level,

        "mean_risk_score": _num(
            worst.get(
                "mean_risk_score"
            )
        ),

        "mean_risk_change": mean_change,

        "max_risk_score": _num(
            worst.get(
                "max_risk_score"
            )
        ),

        "escalating_cells":
            escalating_cells,

        "new_high_or_extreme":
            high_or_extreme,

        "new_extreme_cells":
            new_extreme,

        "actions":
            actions,

        "priority_cells":
            top_cells,
    }

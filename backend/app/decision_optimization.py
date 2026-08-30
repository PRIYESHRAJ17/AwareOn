from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _level(score: float) -> str:
    if score >= 85.0:
        return "P1"

    if score >= 70.0:
        return "P2"

    if score >= 50.0:
        return "P3"

    return "P4"


def optimize_response_options(
    assessment: dict[str, Any],
    intervention: dict[str, Any],
    field_inspection: dict[str, Any],
    monitoring: dict[str, Any],
    response: dict[str, Any],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError("assessment is required.")

    if not intervention:
        raise ValueError("intervention is required.")

    if not field_inspection:
        raise ValueError("field_inspection is required.")

    if not monitoring:
        raise ValueError("monitoring is required.")

    if not response:
        raise ValueError("response is required.")

    risk = _num(
        assessment.get(
            "unified_risk_score"
        )
    )

    confidence = _num(
        assessment.get(
            "confidence_score"
        )
    )

    intervention_score = _num(
        intervention.get(
            "score"
        )
    )

    field_targets = int(
        _num(
            field_inspection.get(
                "target_count"
            )
        )
    )

    monitoring_targets = int(
        _num(
            monitoring.get(
                "target_count"
            )
        )
    )

    response_level = str(
        response.get(
            "response_level"
        )
        or "ROUTINE"
    ).upper()

    exposure_focus = str(
        response.get(
            "operational_focus"
        )
        or "MULTI_ASSET"
    ).upper()

    options = [
        {
            "option": "IMMEDIATE_FIELD_ASSESSMENT",
            "objective": "REDUCE_UNCERTAINTY",
            "effort": 70.0,
            "coverage": 80.0,
            "speed": 95.0,
            "protection": 85.0,
        },
        {
            "option": "ENHANCED_MONITORING",
            "objective": "TRACK_EVOLUTION",
            "effort": 35.0,
            "coverage": 75.0,
            "speed": 90.0,
            "protection": 55.0,
        },
        {
            "option": "TARGETED_ASSET_PROTECTION",
            "objective": "REDUCE_EXPOSURE",
            "effort": 60.0,
            "coverage": 65.0,
            "speed": 75.0,
            "protection": 95.0,
        },
        {
            "option": "ROUTINE_REVIEW",
            "objective": "MAINTAIN_BASELINE",
            "effort": 15.0,
            "coverage": 30.0,
            "speed": 50.0,
            "protection": 25.0,
        },
    ]

    optimized = []

    for option in options:

        effort = option["effort"]
        coverage = option["coverage"]
        speed = option["speed"]
        protection = option["protection"]

        urgency_bonus = (
            10.0
            if response_level == "IMMEDIATE"
            and option["option"]
            == "IMMEDIATE_FIELD_ASSESSMENT"
            else 0.0
        )

        risk_need = min(
            100.0,
            risk,
        )

        exposure_need = min(
            100.0,
            intervention_score,
        )

        value = (
            risk_need * 0.25
            +
            exposure_need * 0.20
            +
            coverage * 0.15
            +
            speed * 0.15
            +
            protection * 0.20
            +
            confidence * 0.05
            -
            effort * 0.10
            +
            urgency_bonus
        )

        value = max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

        optimized.append(
            {
                "option":
                    option["option"],

                "objective":
                    option["objective"],

                "optimization_score":
                    round(
                        value,
                        2,
                    ),

                "effort":
                    effort,

                "coverage":
                    coverage,

                "speed":
                    speed,

                "protection":
                    protection,
            }
        )

    optimized.sort(
        key=lambda item: (
            item["optimization_score"],
            item["protection"],
            item["coverage"],
        ),
        reverse=True,
    )

    for index, item in enumerate(
        optimized,
        start=1,
    ):
        item["rank"] = index
        item["priority"] = _level(
            item["optimization_score"]
        )

    recommended = optimized[0]

    if response_level == "IMMEDIATE":
        decision_mode = "ACTION_FIRST"

    elif response_level == "HIGH":
        decision_mode = "BALANCED_ACTION"

    else:
        decision_mode = "MONITOR_FIRST"

    tradeoffs = {
        "risk":
            risk,

        "confidence":
            confidence,

        "intervention_priority":
            intervention_score,

        "field_targets":
            field_targets,

        "monitoring_targets":
            monitoring_targets,

        "response_level":
            response_level,

        "focus":
            exposure_focus,
    }

    interpretation = (
        f"Best-ranked response option is "
        f"{recommended['option']} with optimization "
        f"score {recommended['optimization_score']:.2f}. "
        f"Decision mode is {decision_mode}."
    )

    return {
        "engine":
            "AWAREON_DECISION_OPTIMIZATION",

        "version":
            "1.0",

        "status":
            "READY",

        "decision_mode":
            decision_mode,

        "recommended_option":
            recommended,

        "options":
            optimized,

        "tradeoffs":
            tradeoffs,

        "interpretation":
            interpretation,
    }

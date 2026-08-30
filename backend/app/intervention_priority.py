from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _priority(score: float) -> str:
    if score >= 85.0:
        return "P1"

    if score >= 70.0:
        return "P2"

    if score >= 50.0:
        return "P3"

    return "P4"


def build_intervention_priority(
    assessment: dict[str, Any],
    regional_master: dict[str, Any],
    early_warning_master: dict[str, Any],
    progression: dict[str, Any],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError("assessment is required.")

    if not regional_master:
        raise ValueError("regional_master is required.")

    if not early_warning_master:
        raise ValueError(
            "early_warning_master is required."
        )

    if not progression:
        raise ValueError("progression is required.")

    risk_score = _num(
        assessment.get(
            "unified_risk_score"
        )
    )

    confidence = _num(
        assessment.get(
            "confidence_score"
        )
    )

    severity = str(
        assessment.get(
            "severity"
        )
        or "UNKNOWN"
    ).upper()

    regional_priority = _num(
        regional_master.get(
            "priority",
            {}
        ).get(
            "score"
        )
    )

    exposure_state = str(
        regional_master.get(
            "exposure",
            {}
        ).get(
            "state"
        )
        or "UNKNOWN"
    ).upper()

    impact_focus = str(
        regional_master.get(
            "exposure",
            {}
        ).get(
            "impact_focus"
        )
        or "UNKNOWN"
    ).upper()

    warning_level = str(
        early_warning_master.get(
            "master_warning"
        )
        or "UNKNOWN"
    ).upper()

    warning_strength = _num(
        early_warning_master.get(
            "signal_strength"
        )
    )

    progression_priority = str(
        progression.get(
            "progression_priority"
        )
        or "UNKNOWN"
    ).upper()

    progression_direction = str(
        progression.get(
            "progression_direction"
        )
        or "UNKNOWN"
    ).upper()

    risk_component = min(
        100.0,
        risk_score,
    )

    regional_component = min(
        100.0,
        regional_priority,
    )

    warning_component = min(
        100.0,
        warning_strength,
    )

    confidence_component = min(
        100.0,
        confidence,
    )

    intervention_score = (
        risk_component * 0.35
        +
        regional_component * 0.25
        +
        warning_component * 0.20
        +
        confidence_component * 0.20
    )

    if exposure_state == "CRITICAL_EXPOSURE":
        intervention_score += 8.0

    elif exposure_state == "HIGH_EXPOSURE":
        intervention_score += 4.0

    if progression_direction == "INTENSIFYING":
        intervention_score += 5.0

    intervention_score = min(
        100.0,
        intervention_score,
    )

    priority = _priority(
        intervention_score
    )

    if impact_focus == "TRANSPORT":
        intervention_class = (
            "TRANSPORT_CORRIDOR_INSPECTION"
        )

    elif impact_focus == "POPULATION":
        intervention_class = (
            "POPULATION_SAFETY_ASSESSMENT"
        )

    elif impact_focus == "INFRASTRUCTURE":
        intervention_class = (
            "INFRASTRUCTURE_INSPECTION"
        )

    else:
        intervention_class = (
            "MULTI_ASSET_FIELD_ASSESSMENT"
        )

    if (
        priority == "P1"
        or
        severity == "EXTREME"
        and
        exposure_state == "CRITICAL_EXPOSURE"
    ):
        urgency = "IMMEDIATE"

    elif priority == "P2":
        urgency = "HIGH"

    elif priority == "P3":
        urgency = "ELEVATED"

    else:
        urgency = "ROUTINE"

    reasons = []

    if risk_score >= 70.0:
        reasons.append(
            "VERY_HIGH_CURRENT_RISK"
        )

    if regional_priority >= 70.0:
        reasons.append(
            "HIGH_REGIONAL_PRIORITY"
        )

    if exposure_state == "CRITICAL_EXPOSURE":
        reasons.append(
            "CRITICAL_EXPOSURE"
        )

    if warning_level in {
        "HIGH",
        "CRITICAL",
    }:
        reasons.append(
            "EARLY_WARNING_SUPPORT"
        )

    if progression_direction == "INTENSIFYING":
        reasons.append(
            "RISK_INTENSIFICATION"
        )

    if not reasons:
        reasons.append(
            "BASELINE_RISK_REVIEW"
        )

    if priority == "P1":
        recommendation = (
            "Initiate immediate field assessment and "
            "protect priority exposed assets."
        )

    elif priority == "P2":
        recommendation = (
            "Schedule high-priority field review and "
            "enhance monitoring of exposed assets."
        )

    elif priority == "P3":
        recommendation = (
            "Increase monitoring and prepare targeted "
            "field verification."
        )

    else:
        recommendation = (
            "Maintain routine monitoring and reassess "
            "if risk signals change."
        )

    return {
        "engine":
            "AWAREON_INTERVENTION_PRIORITY",

        "version":
            "1.0",

        "status":
            "READY",

        "priority":
            priority,

        "score":
            round(
                intervention_score,
                2,
            ),

        "urgency":
            urgency,

        "intervention_class":
            intervention_class,

        "impact_focus":
            impact_focus,

        "reasons":
            reasons,

        "components":
            {
                "risk":
                    round(
                        risk_component,
                        2,
                    ),

                "regional":
                    round(
                        regional_component,
                        2,
                    ),

                "warning":
                    round(
                        warning_component,
                        2,
                    ),

                "confidence":
                    round(
                        confidence_component,
                        2,
                    ),
            },

        "recommendation":
            recommendation,
    }

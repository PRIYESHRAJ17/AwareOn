from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _band(score: float) -> str:
    if score >= 80.0:
        return "VERY_HIGH"

    if score >= 60.0:
        return "HIGH"

    if score >= 40.0:
        return "MODERATE"

    return "LOW"


def build_decision_tradeoff(
    assessment: dict[str, Any],
    intervention: dict[str, Any],
    progression: dict[str, Any],
    exposure: dict[str, Any],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError("assessment is required.")

    if not intervention:
        raise ValueError("intervention is required.")

    if not progression:
        raise ValueError("progression is required.")

    if not exposure:
        raise ValueError("exposure is required.")

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

    scenario_change = _num(
        progression.get(
            "scenario",
            {},
        ).get(
            "risk_change"
        )
    )

    exposure_summary = exposure.get(
        "exposure_summary",
        {},
    )

    if not isinstance(
        exposure_summary,
        dict,
    ):
        exposure_summary = {}

    exposure_score = _num(
        exposure_summary.get(
            "mean_exposure"
        )
    )

    maximum_exposure = _num(
        exposure_summary.get(
            "maximum_exposure"
        )
    )

    risk_band = _band(risk)
    exposure_band = _band(exposure_score)
    confidence_band = _band(confidence)

    scenario_pressure = min(
        100.0,
        max(
            0.0,
            50.0 + scenario_change * 5.0,
        ),
    )

    confidence_gap = max(
        0.0,
        100.0 - confidence,
    )

    consequence_score = (
        risk * 0.45
        +
        exposure_score * 0.35
        +
        maximum_exposure * 0.20
    )

    uncertainty_penalty = (
        confidence_gap * 0.25
    )

    decision_strength = (
        consequence_score
        +
        scenario_pressure * 0.15
        -
        uncertainty_penalty
    )

    decision_strength = min(
        100.0,
        max(
            0.0,
            decision_strength,
        ),
    )

    if (
        risk >= 70.0
        and
        exposure_score >= 60.0
        and
        confidence >= 75.0
    ):
        tradeoff_state = (
            "HIGH_CONSEQUENCE_HIGH_CONFIDENCE"
        )

    elif (
        risk >= 70.0
        and
        confidence < 50.0
    ):
        tradeoff_state = (
            "HIGH_RISK_LOW_CONFIDENCE"
        )

    elif (
        risk >= 70.0
        and
        exposure_score < 40.0
    ):
        tradeoff_state = (
            "HIGH_RISK_LIMITED_EXPOSURE"
        )

    elif (
        exposure_score >= 60.0
        and
        risk < 50.0
    ):
        tradeoff_state = (
            "HIGH_EXPOSURE_MODERATE_RISK"
        )

    elif scenario_change > 0.0:
        tradeoff_state = (
            "SCENARIO_SENSITIVE_TRADEOFF"
        )

    else:
        tradeoff_state = (
            "BALANCED_TRADEOFF"
        )

    decision_posture = str(
        intervention.get(
            "urgency"
        )
        or "ROUTINE"
    ).upper()

    if (
        tradeoff_state
        == "HIGH_CONSEQUENCE_HIGH_CONFIDENCE"
    ):
        decision_logic = (
            "Act decisively because both consequence "
            "and evidence strength are high."
        )

    elif (
        tradeoff_state
        == "HIGH_RISK_LOW_CONFIDENCE"
    ):
        decision_logic = (
            "Prioritize evidence-gathering actions "
            "while avoiding unsupported escalation."
        )

    elif (
        tradeoff_state
        == "HIGH_RISK_LIMITED_EXPOSURE"
    ):
        decision_logic = (
            "Focus response on risk containment while "
            "avoiding disproportionate asset deployment."
        )

    elif (
        tradeoff_state
        == "HIGH_EXPOSURE_MODERATE_RISK"
    ):
        decision_logic = (
            "Prioritize exposure reduction and monitoring "
            "because consequences may be significant."
        )

    elif (
        tradeoff_state
        == "SCENARIO_SENSITIVE_TRADEOFF"
    ):
        decision_logic = (
            "Keep response adaptive because tested "
            "scenario conditions materially change risk."
        )

    else:
        decision_logic = (
            "Balance monitoring and intervention according "
            "to the current evidence."
        )

    return {
        "engine":
            "AWAREON_DECISION_TRADEOFF_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "tradeoff_state":
            tradeoff_state,

        "decision_posture":
            decision_posture,

        "risk":
            {
                "score":
                    risk,

                "band":
                    risk_band,
            },

        "exposure":
            {
                "mean_score":
                    exposure_score,

                "maximum_score":
                    maximum_exposure,

                "band":
                    exposure_band,
            },

        "confidence":
            {
                "score":
                    confidence,

                "band":
                    confidence_band,

                "uncertainty_gap":
                    confidence_gap,
            },

        "scenario":
            {
                "risk_change":
                    scenario_change,

                "pressure":
                    scenario_pressure,
            },

        "decision":
            {
                "intervention_score":
                    intervention_score,

                "consequence_score":
                    consequence_score,

                "uncertainty_penalty":
                    uncertainty_penalty,

                "decision_strength":
                    decision_strength,
            },

        "decision_logic":
            decision_logic,
    }

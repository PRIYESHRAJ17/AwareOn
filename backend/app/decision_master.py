from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_decision_master(
    intervention: dict[str, Any],
    infrastructure: dict[str, Any],
    field: dict[str, Any],
    monitoring: dict[str, Any],
    response: dict[str, Any],
    optimization: dict[str, Any],
    comparison: dict[str, Any],
    tradeoff: dict[str, Any],
    operational: dict[str, Any],
) -> dict[str, Any]:

    inputs = [
        intervention,
        infrastructure,
        field,
        monitoring,
        response,
        optimization,
        comparison,
        tradeoff,
        operational,
    ]

    if any(not item for item in inputs):
        raise ValueError(
            "All decision-intelligence inputs are required."
        )

    intervention_priority = str(
        intervention.get("priority") or "P4"
    ).upper()

    intervention_score = _num(
        intervention.get("score")
    )

    infrastructure_posture = str(
        infrastructure.get("regional_posture")
        or "UNKNOWN"
    ).upper()

    infrastructure_targets = int(
        _num(
            infrastructure.get("target_count")
        )
    )

    field_posture = str(
        field.get("field_posture")
        or "UNKNOWN"
    ).upper()

    field_targets = int(
        _num(
            field.get("target_count")
        )
    )

    monitoring_posture = str(
        monitoring.get("monitoring_posture")
        or "UNKNOWN"
    ).upper()

    monitoring_targets = int(
        _num(
            monitoring.get("target_count")
        )
    )

    response_level = str(
        response.get("response_level")
        or "ROUTINE"
    ).upper()

    command_posture = str(
        response.get("command_posture")
        or "UNKNOWN"
    ).upper()

    operational_focus = str(
        response.get("operational_focus")
        or "UNKNOWN"
    ).upper()

    decision_mode = str(
        optimization.get("decision_mode")
        or "UNKNOWN"
    ).upper()

    recommended_option = str(
        optimization.get(
            "recommended_option",
            {},
        ).get("option")
        or "UNKNOWN"
    ).upper()

    optimization_score = _num(
        optimization.get(
            "recommended_option",
            {},
        ).get("optimization_score")
    )

    comparison_count = int(
        _num(
            comparison.get("comparison_count")
        )
    )

    tradeoff_state = str(
        tradeoff.get("tradeoff_state")
        or "UNKNOWN"
    ).upper()

    decision_strength = _num(
        tradeoff.get(
            "decision",
            {},
        ).get("decision_strength")
    )

    time_horizon = str(
        operational.get("time_horizon")
        or "UNKNOWN"
    ).upper()

    primary_action = str(
        operational.get("primary_action")
        or "UNKNOWN"
    )

    master_urgency = (
        "IMMEDIATE"
        if response_level == "IMMEDIATE"
        or intervention_priority == "P1"
        else "HIGH"
        if intervention_priority == "P2"
        else "ELEVATED"
        if intervention_priority == "P3"
        else "ROUTINE"
    )

    if (
        intervention_priority == "P1"
        and
        tradeoff_state
        == "HIGH_CONSEQUENCE_HIGH_CONFIDENCE"
        and
        response_level == "IMMEDIATE"
    ):
        master_state = "ACTION_READY_CRITICAL"

    elif (
        response_level == "IMMEDIATE"
        or
        intervention_priority
        in {"P1", "P2"}
    ):
        master_state = "HIGH_PRIORITY_DECISION"

    elif response_level == "ELEVATED":
        master_state = "ENHANCED_DECISION_REVIEW"

    else:
        master_state = "MONITORING_DECISION"

    if (
        master_state
        == "ACTION_READY_CRITICAL"
    ):
        operational_posture = (
            "EXECUTE_IMMEDIATE_FIELD_REVIEW"
        )

    elif (
        master_state
        == "HIGH_PRIORITY_DECISION"
    ):
        operational_posture = (
            "EXECUTE_HIGH_PRIORITY_REVIEW"
        )

    elif (
        master_state
        == "ENHANCED_DECISION_REVIEW"
    ):
        operational_posture = (
            "ENHANCE_MONITORING_AND_PREPARE"
        )

    else:
        operational_posture = (
            "MAINTAIN_MONITORING"
        )

    if (
        decision_strength >= 85.0
    ):
        confidence_band = "VERY_HIGH"

    elif decision_strength >= 70.0:
        confidence_band = "HIGH"

    elif decision_strength >= 50.0:
        confidence_band = "MODERATE"

    else:
        confidence_band = "LIMITED"

    reasoning = [
        (
            f"Intervention priority is "
            f"{intervention_priority} with score "
            f"{intervention_score:.2f}."
        ),
        (
            f"Infrastructure intelligence identifies "
            f"{infrastructure_targets} priority targets."
        ),
        (
            f"Field intelligence identifies "
            f"{field_targets} inspection targets."
        ),
        (
            f"Monitoring intelligence covers "
            f"{monitoring_targets} priority locations."
        ),
        (
            f"The preferred response is "
            f"{recommended_option}."
        ),
        (
            f"Decision strength is "
            f"{decision_strength:.2f}."
        ),
    ]

    if tradeoff_state == "HIGH_CONSEQUENCE_HIGH_CONFIDENCE":
        reasoning.append(
            "High consequence and high evidence confidence "
            "support decisive action."
        )

    decision_statement = (
        f"{master_state}: {primary_action} "
        f"with {master_urgency.lower()} urgency. "
        f"Primary focus is {operational_focus}. "
        f"The preferred option is "
        f"{recommended_option}."
    )

    return {
        "engine":
            "AWAREON_DECISION_INTELLIGENCE_MASTER",

        "version":
            "1.0",

        "status":
            "READY",

        "master_state":
            master_state,

        "master_urgency":
            master_urgency,

        "operational_posture":
            operational_posture,

        "operational_focus":
            operational_focus,

        "response_level":
            response_level,

        "command_posture":
            command_posture,

        "time_horizon":
            time_horizon,

        "priority":
            {
                "level":
                    intervention_priority,

                "score":
                    intervention_score,
            },

        "decision":
            {
                "mode":
                    decision_mode,

                "recommended_option":
                    recommended_option,

                "optimization_score":
                    optimization_score,

                "comparison_count":
                    comparison_count,

                "tradeoff_state":
                    tradeoff_state,

                "decision_strength":
                    decision_strength,

                "confidence_band":
                    confidence_band,
            },

        "infrastructure":
            {
                "posture":
                    infrastructure_posture,

                "targets":
                    infrastructure_targets,
            },

        "field":
            {
                "posture":
                    field_posture,

                "targets":
                    field_targets,
            },

        "monitoring":
            {
                "posture":
                    monitoring_posture,

                "targets":
                    monitoring_targets,
            },

        "reasoning":
            reasoning,

        "decision_statement":
            decision_statement,
    }

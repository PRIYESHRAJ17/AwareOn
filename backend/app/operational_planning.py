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


def build_operational_plan(
    assessment: dict[str, Any],
    intervention: dict[str, Any],
    field_inspection: dict[str, Any],
    monitoring: dict[str, Any],
    response: dict[str, Any],
    optimization: dict[str, Any],
    tradeoff: dict[str, Any],
) -> dict[str, Any]:

    inputs = [
        assessment,
        intervention,
        field_inspection,
        monitoring,
        response,
        optimization,
        tradeoff,
    ]

    if any(not item for item in inputs):
        raise ValueError(
            "All operational planning inputs are required."
        )

    risk_score = _num(
        assessment.get(
            "unified_risk_score"
        )
    )

    confidence_score = _num(
        assessment.get(
            "confidence_score"
        )
    )

    priority = str(
        intervention.get(
            "priority"
        )
        or "P4"
    ).upper()

    intervention_class = str(
        intervention.get(
            "intervention_class"
        )
        or "GENERAL_REVIEW"
    ).upper()

    field_posture = str(
        field_inspection.get(
            "field_posture"
        )
        or "UNKNOWN"
    ).upper()

    field_targets = int(
        _num(
            field_inspection.get(
                "target_count"
            )
        )
    )

    monitoring_posture = str(
        monitoring.get(
            "monitoring_posture"
        )
        or "UNKNOWN"
    ).upper()

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

    command_posture = str(
        response.get(
            "command_posture"
        )
        or "UNKNOWN"
    ).upper()

    operational_focus = str(
        response.get(
            "operational_focus"
        )
        or "MULTI_ASSET_REVIEW"
    ).upper()

    recommended_option = str(
        optimization.get(
            "recommended_option",
            {},
        ).get(
            "option"
        )
        or "UNKNOWN"
    ).upper()

    decision_mode = str(
        optimization.get(
            "decision_mode"
        )
        or "UNKNOWN"
    ).upper()

    tradeoff_state = str(
        tradeoff.get(
            "tradeoff_state"
        )
        or "UNKNOWN"
    ).upper()

    if response_level == "IMMEDIATE":
        time_horizon = "NOW"

    elif response_level == "HIGH":
        time_horizon = "WITHIN_24_HOURS"

    elif response_level == "ELEVATED":
        time_horizon = "WITHIN_72_HOURS"

    else:
        time_horizon = "ROUTINE_CYCLE"

    if intervention_class == "TRANSPORT_CORRIDOR_INSPECTION":
        primary_action = (
            "Inspect priority transport corridors "
            "and identify access or slope hazards."
        )

    elif intervention_class == "INFRASTRUCTURE_INSPECTION":
        primary_action = (
            "Inspect priority infrastructure assets "
            "for current instability or damage."
        )

    elif intervention_class == "POPULATION_SAFETY_ASSESSMENT":
        primary_action = (
            "Assess exposed population areas and "
            "immediate safety conditions."
        )

    else:
        primary_action = (
            "Conduct targeted field assessment."
        )

    supporting_actions = [
        (
            f"Review the top {field_targets} "
            "field inspection targets."
        ),
        (
            f"Maintain monitoring across "
            f"{monitoring_targets} priority locations."
        ),
    ]

    if recommended_option == "TARGETED_ASSET_PROTECTION":
        supporting_actions.append(
            "Protect the highest-consequence exposed assets."
        )

    elif recommended_option == "ENHANCED_MONITORING":
        supporting_actions.append(
            "Increase monitoring frequency for priority cells."
        )

    escalation_triggers = [
        "New environmental anomaly.",
        "Sustained rising temporal signal.",
        "Additional positive scenario risk change.",
        "Observed field evidence of worsening conditions.",
    ]

    deescalation_triggers = [
        "Sustained decline in risk indicators.",
        "No new warning signals across the monitoring window.",
        "Field verification confirms stable conditions.",
    ]

    decision_rationale = (
        f"Risk is {risk_score:.2f} with confidence "
        f"{confidence_score:.2f}. "
        f"The decision state is {tradeoff_state}. "
        f"The selected decision mode is {decision_mode} "
        f"with primary option {recommended_option}."
    )

    return {
        "engine":
            "AWAREON_OPERATIONAL_DECISION_PLANNING",

        "version":
            "1.0",

        "status":
            "READY",

        "response_level":
            response_level,

        "time_horizon":
            time_horizon,

        "command_posture":
            command_posture,

        "operational_focus":
            operational_focus,

        "primary_action":
            primary_action,

        "supporting_actions":
            supporting_actions,

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

        "escalation_triggers":
            escalation_triggers,

        "deescalation_triggers":
            deescalation_triggers,

        "decision":
            {
                "priority":
                    priority,

                "mode":
                    decision_mode,

                "recommended_option":
                    recommended_option,

                "tradeoff_state":
                    tradeoff_state,
            },

        "decision_rationale":
            decision_rationale,
    }

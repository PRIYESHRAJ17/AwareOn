from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_response_recommendation(
    intervention: dict[str, Any],
    field_inspection: dict[str, Any],
    monitoring: dict[str, Any],
    early_warning: dict[str, Any],
    regional_command: dict[str, Any],
    progression: dict[str, Any],
) -> dict[str, Any]:

    inputs = [
        intervention,
        field_inspection,
        monitoring,
        early_warning,
        regional_command,
        progression,
    ]

    if any(not item for item in inputs):
        raise ValueError(
            "All response recommendation inputs are required."
        )

    intervention_priority = str(
        intervention.get("priority") or "P4"
    ).upper()

    intervention_urgency = str(
        intervention.get("urgency") or "ROUTINE"
    ).upper()

    intervention_class = str(
        intervention.get("intervention_class")
        or "GENERAL_REVIEW"
    ).upper()

    field_posture = str(
        field_inspection.get("field_posture")
        or "UNKNOWN"
    ).upper()

    field_targets = int(
        _num(
            field_inspection.get("target_count")
        )
    )

    immediate_targets = int(
        _num(
            field_inspection.get("immediate_targets")
        )
    )

    high_field_targets = int(
        _num(
            field_inspection.get("high_priority_targets")
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

    warning_level = str(
        early_warning.get("master_warning")
        or "NORMAL"
    ).upper()

    early_warning_posture = str(
        early_warning.get("operational_posture")
        or "UNKNOWN"
    ).upper()

    regional_posture = str(
        regional_command.get("regional_posture")
        or "UNKNOWN"
    ).upper()

    regional_urgency = str(
        regional_command.get("urgency")
        or "ROUTINE"
    ).upper()

    operational_focus = str(
        regional_command.get("operational_focus")
        or "MULTI_ASSET_REVIEW"
    ).upper()

    progression_state = str(
        progression.get("progression_state")
        or "UNKNOWN"
    ).upper()

    progression_direction = str(
        progression.get("progression_direction")
        or "UNKNOWN"
    ).upper()

    if (
        intervention_priority == "P1"
        or
        warning_level == "CRITICAL"
        or
        regional_urgency == "IMMEDIATE"
    ):
        response_level = "IMMEDIATE"

    elif (
        intervention_priority == "P2"
        or
        warning_level == "HIGH"
        or
        high_field_targets > 0
    ):
        response_level = "HIGH"

    elif (
        intervention_priority == "P3"
        or
        warning_level == "WATCH"
    ):
        response_level = "ELEVATED"

    else:
        response_level = "ROUTINE"

    primary_actions: list[str] = []
    secondary_actions: list[str] = []
    escalation_triggers: list[str] = []

    if intervention_class == "TRANSPORT_CORRIDOR_INSPECTION":
        primary_actions.append(
            "Inspect priority transport corridors."
        )
        secondary_actions.append(
            "Review slope conditions and access continuity."
        )

    elif intervention_class == "INFRASTRUCTURE_INSPECTION":
        primary_actions.append(
            "Inspect priority infrastructure assets."
        )

    elif intervention_class == "POPULATION_SAFETY_ASSESSMENT":
        primary_actions.append(
            "Review population exposure and safety conditions."
        )

    else:
        primary_actions.append(
            "Conduct targeted field assessment."
        )

    if field_targets > 0:
        secondary_actions.append(
            f"Prioritize the top {field_targets} field locations."
        )

    if monitoring_targets > 0:
        secondary_actions.append(
            f"Maintain monitoring on {monitoring_targets} priority locations."
        )

    if monitoring_posture == "REGULAR_MONITORING":
        secondary_actions.append(
            "Maintain regular monitoring and reassess on signal change."
        )

    elif monitoring_posture == "HIGH_FREQUENCY_MONITORING":
        secondary_actions.append(
            "Maintain high-frequency monitoring."
        )

    elif monitoring_posture == "CONTINUOUS_MONITORING":
        secondary_actions.append(
            "Maintain continuous monitoring."
        )

    if progression_direction == "INTENSIFYING":
        escalation_triggers.append(
            "Additional positive risk change under tested scenarios."
        )

    if progression_state == "CATEGORY_ESCALATION":
        escalation_triggers.append(
            "Observed category escalation."
        )

    if warning_level in {
        "HIGH",
        "CRITICAL",
    }:
        escalation_triggers.append(
            "Early-warning level increases."
        )

    escalation_triggers.append(
        "New environmental anomaly or sustained rising temporal signal."
    )

    if response_level == "IMMEDIATE":
        command_posture = (
            "ACTIVATE_HIGH_PRIORITY_FIELD_REVIEW"
        )

    elif response_level == "HIGH":
        command_posture = (
            "SCHEDULE_HIGH_PRIORITY_RESPONSE"
        )

    elif response_level == "ELEVATED":
        command_posture = (
            "ENHANCE_MONITORING_AND_PREPARE_RESPONSE"
        )

    else:
        command_posture = (
            "MAINTAIN_ROUTINE_RESPONSE_POSTURE"
        )

    confidence = _num(
        intervention.get(
            "components",
            {},
        ).get(
            "confidence"
        )
    )

    if confidence >= 75.0:
        confidence_band = "HIGH"
    elif confidence >= 50.0:
        confidence_band = "MODERATE"
    else:
        confidence_band = "LIMITED"

    interpretation = (
        f"Recommended response level is {response_level}. "
        f"Primary operational focus is {operational_focus}. "
        f"The recommended command posture is {command_posture}."
    )

    if progression_direction == "INTENSIFYING":
        interpretation += (
            " Risk is currently intensifying under tested scenario pressure."
        )

    return {
        "engine": "AWAREON_RESPONSE_RECOMMENDATION_INTELLIGENCE",
        "version": "1.0",
        "status": "READY",
        "response_level": response_level,
        "command_posture": command_posture,
        "operational_focus": operational_focus,
        "primary_intervention": intervention_class,
        "primary_actions": primary_actions,
        "secondary_actions": secondary_actions,
        "escalation_triggers": escalation_triggers,
        "field": {
            "posture": field_posture,
            "targets": field_targets,
            "immediate_targets": immediate_targets,
            "high_priority_targets": high_field_targets,
        },
        "monitoring": {
            "posture": monitoring_posture,
            "targets": monitoring_targets,
        },
        "warning": {
            "level": warning_level,
            "posture": early_warning_posture,
        },
        "regional": {
            "posture": regional_posture,
            "urgency": regional_urgency,
        },
        "progression": {
            "state": progression_state,
            "direction": progression_direction,
        },
        "confidence": {
            "score": confidence,
            "band": confidence_band,
        },
        "interpretation": interpretation,
    }

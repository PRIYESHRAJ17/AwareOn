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


def _priority(score: float) -> str:
    if score >= 85.0:
        return "P1"

    if score >= 70.0:
        return "P2"

    if score >= 50.0:
        return "P3"

    return "P4"


def prioritize_field_inspection(
    infrastructure_targets: list[dict[str, Any]],
    regional_posture: str = "UNKNOWN",
    top_n: int = 10,
) -> dict[str, Any]:

    if not isinstance(
        infrastructure_targets,
        list,
    ):
        raise ValueError(
            "infrastructure_targets must be a list."
        )

    if top_n <= 0:
        raise ValueError(
            "top_n must be greater than 0."
        )

    ranked = []

    for target in infrastructure_targets:

        if not isinstance(
            target,
            dict,
        ):
            continue

        cell_id = str(
            target.get(
                "cell_id"
            )
            or ""
        )

        if not cell_id:
            continue

        risk = _num(
            target.get(
                "risk_score"
            )
        )

        exposure = _num(
            target.get(
                "exposure_score"
            )
        )

        transport = _num(
            target.get(
                "transport_exposure"
            )
        )

        infrastructure = _num(
            target.get(
                "infrastructure_exposure"
            )
        )

        population = _num(
            target.get(
                "population_exposure"
            )
        )

        scenario_change = _num(
            target.get(
                "scenario_risk_change"
            )
        )

        confidence = _num(
            target.get(
                "confidence"
            )
        )

        existing_priority = str(
            target.get(
                "priority"
            )
            or "P4"
        ).upper()

        impact = max(
            transport,
            infrastructure,
            population,
        )

        scenario_signal = min(
            100.0,
            max(
                0.0,
                50.0
                +
                scenario_change * 5.0,
            ),
        )

        inspection_score = (
            risk * 0.35
            +
            exposure * 0.25
            +
            impact * 0.20
            +
            scenario_signal * 0.10
            +
            confidence * 0.10
        )

        if existing_priority == "P1":
            inspection_score += 8.0

        elif existing_priority == "P2":
            inspection_score += 4.0

        inspection_score = min(
            100.0,
            inspection_score,
        )

        priority = _priority(
            inspection_score
        )

        if priority == "P1":
            urgency = "IMMEDIATE"

        elif priority == "P2":
            urgency = "HIGH"

        elif priority == "P3":
            urgency = "ELEVATED"

        else:
            urgency = "ROUTINE"

        if transport >= max(
            infrastructure,
            population,
        ):
            inspection_type = (
                "TRANSPORT_CORRIDOR_INSPECTION"
            )

        elif infrastructure >= population:
            inspection_type = (
                "INFRASTRUCTURE_SITE_INSPECTION"
            )

        else:
            inspection_type = (
                "POPULATION_EXPOSURE_ASSESSMENT"
            )

        reasons = []

        if risk >= 70.0:
            reasons.append(
                "HIGH_CURRENT_RISK"
            )

        if exposure >= 60.0:
            reasons.append(
                "HIGH_EXPOSURE"
            )

        if impact >= 80.0:
            reasons.append(
                "CRITICAL_IMPACT"
            )

        if scenario_change > 0.0:
            reasons.append(
                "SCENARIO_PRESSURE"
            )

        if confidence >= 75.0:
            reasons.append(
                "HIGH_CONFIDENCE"
            )

        if not reasons:
            reasons.append(
                "BASELINE_INSPECTION"
            )

        ranked.append(
            {
                "cell_id":
                    cell_id,

                "inspection_priority":
                    priority,

                "inspection_score":
                    round(
                        inspection_score,
                        2,
                    ),

                "urgency":
                    urgency,

                "inspection_type":
                    inspection_type,

                "impact_focus":
                    target.get(
                        "impact_focus"
                    ),

                "risk_score":
                    risk,

                "exposure_score":
                    exposure,

                "impact_score":
                    impact,

                "scenario_risk_change":
                    scenario_change,

                "confidence":
                    confidence,

                "reasons":
                    reasons,
            }
        )

    ranked.sort(
        key=lambda item: (
            item["inspection_score"],
            item["risk_score"],
            item["exposure_score"],
        ),
        reverse=True,
    )

    selected = ranked[:top_n]

    for index, item in enumerate(
        selected,
        start=1,
    ):
        item["rank"] = index

    immediate = sum(
        1
        for item in selected
        if item["urgency"] == "IMMEDIATE"
    )

    high = sum(
        1
        for item in selected
        if item["urgency"] == "HIGH"
    )

    transport = sum(
        1
        for item in selected
        if item["inspection_type"]
        == "TRANSPORT_CORRIDOR_INSPECTION"
    )

    infrastructure = sum(
        1
        for item in selected
        if item["inspection_type"]
        == "INFRASTRUCTURE_SITE_INSPECTION"
    )

    population = sum(
        1
        for item in selected
        if item["inspection_type"]
        == "POPULATION_EXPOSURE_ASSESSMENT"
    )

    if immediate > 0:
        field_posture = "IMMEDIATE_FIELD_RESPONSE"

    elif high > 0:
        field_posture = "HIGH_PRIORITY_FIELD_REVIEW"

    elif selected:
        field_posture = "ELEVATED_FIELD_REVIEW"

    else:
        field_posture = "ROUTINE_MONITORING"

    if selected:
        interpretation = (
            f"{len(selected)} locations were prioritized "
            f"for field inspection. "
            f"{immediate} are immediate-priority and "
            f"{high} are high-priority."
        )

    else:
        interpretation = (
            "No field inspection targets were identified."
        )

    return {
        "engine":
            "AWAREON_FIELD_INSPECTION_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "regional_posture":
            regional_posture,

        "field_posture":
            field_posture,

        "target_count":
            len(selected),

        "available_targets":
            len(ranked),

        "immediate_targets":
            immediate,

        "high_priority_targets":
            high,

        "inspection_type_counts":
            {
                "transport":
                    transport,

                "infrastructure":
                    infrastructure,

                "population":
                    population,
            },

        "targets":
            selected,

        "interpretation":
            interpretation,
    }

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


def prioritize_monitoring(
    targets: list[dict[str, Any]],
    temporal_state: str = "UNKNOWN",
    warning_level: str = "UNKNOWN",
    top_n: int = 10,
) -> dict[str, Any]:

    if not isinstance(
        targets,
        list,
    ):
        raise ValueError(
            "targets must be a list."
        )

    if top_n <= 0:
        raise ValueError(
            "top_n must be greater than 0."
        )

    ranked = []

    temporal_state = str(
        temporal_state
        or "UNKNOWN"
    ).upper()

    warning_level = str(
        warning_level
        or "UNKNOWN"
    ).upper()

    for target in targets:

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

        impact = _num(
            target.get(
                "impact_score"
            )
        )

        monitoring_score = (
            risk * 0.35
            +
            exposure * 0.20
            +
            impact * 0.15
            +
            confidence * 0.10
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

        monitoring_score += (
            scenario_signal * 0.20
        )

        if (
            temporal_state
            == "ESCALATING_TEMPORAL_SIGNAL"
        ):
            monitoring_score += 8.0

        elif (
            temporal_state
            == "STABLE_TEMPORAL_SIGNAL"
        ):
            monitoring_score += 2.0

        if warning_level == "CRITICAL":
            monitoring_score += 8.0

        elif warning_level == "HIGH":
            monitoring_score += 5.0

        elif warning_level == "WATCH":
            monitoring_score += 2.0

        monitoring_score = min(
            100.0,
            monitoring_score,
        )

        priority = _priority(
            monitoring_score
        )

        if priority == "P1":
            frequency = "CONTINUOUS"
        elif priority == "P2":
            frequency = "HIGH_FREQUENCY"
        elif priority == "P3":
            frequency = "REGULAR"
        else:
            frequency = "ROUTINE"

        if scenario_change >= 5.0:
            trigger = "SCENARIO_SENSITIVE"

        elif warning_level in {
            "CRITICAL",
            "HIGH",
        }:
            trigger = "WARNING_STATE"

        elif risk >= 70.0:
            trigger = "HIGH_CURRENT_RISK"

        else:
            trigger = "BASELINE_MONITORING"

        ranked.append(
            {
                "cell_id": cell_id,
                "monitoring_priority": priority,
                "monitoring_score": round(
                    monitoring_score,
                    2,
                ),
                "frequency": frequency,
                "trigger": trigger,
                "risk_score": risk,
                "exposure_score": exposure,
                "impact_score": impact,
                "scenario_risk_change": scenario_change,
                "confidence": confidence,
            }
        )

    ranked.sort(
        key=lambda item: (
            item["monitoring_score"],
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

    continuous = sum(
        1
        for item in selected
        if item["frequency"] == "CONTINUOUS"
    )

    high_frequency = sum(
        1
        for item in selected
        if item["frequency"] == "HIGH_FREQUENCY"
    )

    regular = sum(
        1
        for item in selected
        if item["frequency"] == "REGULAR"
    )

    if continuous > 0:
        monitoring_posture = "CONTINUOUS_MONITORING"

    elif high_frequency > 0:
        monitoring_posture = "HIGH_FREQUENCY_MONITORING"

    elif regular > 0:
        monitoring_posture = "REGULAR_MONITORING"

    else:
        monitoring_posture = "ROUTINE_MONITORING"

    if selected:
        interpretation = (
            f"{len(selected)} locations were prioritized "
            "for monitoring. "
            f"{continuous} require continuous monitoring "
            f"and {high_frequency} require high-frequency "
            "monitoring."
        )

    else:
        interpretation = (
            "No monitoring targets were identified."
        )

    return {
        "engine":
            "AWAREON_MONITORING_PRIORITY_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "monitoring_posture":
            monitoring_posture,

        "target_count":
            len(selected),

        "available_targets":
            len(ranked),

        "frequency_counts":
            {
                "continuous":
                    continuous,

                "high_frequency":
                    high_frequency,

                "regular":
                    regular,
            },

        "targets":
            selected,

        "interpretation":
            interpretation,
    }

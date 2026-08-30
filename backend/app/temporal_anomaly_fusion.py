from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_temporal_anomaly_fusion(
    historical: dict[str, Any],
    acceleration: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:

    if not historical:
        raise ValueError("historical is required.")

    if not acceleration:
        raise ValueError("acceleration is required.")

    if not assessment:
        raise ValueError("assessment is required.")

    historical_direction = str(
        historical.get("direction") or "UNKNOWN"
    ).upper()

    historical_trajectory = str(
        historical.get("trajectory") or "UNKNOWN"
    ).upper()

    historical_score = _num(
        historical.get("trajectory_score")
    )

    anomaly_score = _num(
        assessment.get("environment_anomaly_score")
    )

    anomaly_category = str(
        assessment.get(
            "environment_anomaly_category"
        )
        or "UNKNOWN"
    ).upper()

    acceleration_state = str(
        acceleration.get("state") or "UNKNOWN"
    ).upper()

    acceleration_value = _num(
        acceleration.get("acceleration")
    )

    risk_rate = _num(
        acceleration.get("mean_risk_rate")
    )

    if historical_direction == "INCREASING":
        historical_signal = "INCREASING"

    elif historical_direction == "DECREASING":
        historical_signal = "DECREASING"

    else:
        historical_signal = "STABLE"

    if acceleration_state == "ACCELERATING":
        scenario_signal = "ACCELERATING"

    elif acceleration_state == "DECELERATING":
        scenario_signal = "DECELERATING"

    else:
        scenario_signal = "STEADY"

    if anomaly_score >= 75.0:
        anomaly_signal = "ANOMALOUS"

    elif anomaly_score >= 50.0:
        anomaly_signal = "ELEVATED"

    else:
        anomaly_signal = "NORMAL"

    if (
        historical_direction == "INCREASING"
        or acceleration_state == "ACCELERATING"
        or anomaly_score >= 75.0
    ):
        temporal_state = (
            "ESCALATING_TEMPORAL_SIGNAL"
        )

    elif (
        historical_direction == "DECREASING"
        or acceleration_state == "DECELERATING"
    ):
        temporal_state = (
            "DECLINING_TEMPORAL_SIGNAL"
        )

    else:
        temporal_state = (
            "STABLE_TEMPORAL_SIGNAL"
        )

    conflict = (
        historical_direction == "STABLE"
        and (
            acceleration_state == "ACCELERATING"
            or anomaly_score >= 75.0
        )
    )

    if (
        historical_direction == "INCREASING"
        and anomaly_score < 50.0
    ):
        conflict = True

    if conflict:
        alignment = (
            "TEMPORAL_SIGNAL_DIVERGENCE"
        )
    else:
        alignment = (
            "TEMPORAL_SIGNAL_ALIGNED"
        )

    if anomaly_score >= 75.0:
        anomaly_state = "HIGH_ANOMALY"

    elif anomaly_score >= 50.0:
        anomaly_state = "MODERATE_ANOMALY"

    else:
        anomaly_state = "NORMAL_ANOMALY"

    if conflict:
        interpretation = (
            "Temporal evidence is not fully aligned across "
            "historical trajectory, scenario response, and "
            "environmental anomaly signals."
        )

    elif temporal_state == "ESCALATING_TEMPORAL_SIGNAL":
        interpretation = (
            "Temporal evidence indicates an escalating "
            "environmental or scenario-linked signal."
        )

    else:
        interpretation = (
            "Temporal evidence is broadly stable across "
            "the available historical, scenario, and "
            "anomaly signals."
        )

    return {
        "engine":
            "AWAREON_TEMPORAL_ANOMALY_FUSION",

        "version":
            "1.0",

        "status":
            "READY",

        "temporal_state":
            temporal_state,

        "alignment":
            alignment,

        "anomaly_state":
            anomaly_state,

        "historical":
            {
                "direction":
                    historical_direction,

                "trajectory":
                    historical_trajectory,

                "score":
                    historical_score,
            },

        "scenario":
            {
                "acceleration_state":
                    acceleration_state,

                "acceleration":
                    acceleration_value,

                "mean_risk_rate":
                    risk_rate,
            },

        "environment":
            {
                "anomaly_score":
                    anomaly_score,

                "anomaly_category":
                    anomaly_category,

                "anomaly_signal":
                    anomaly_signal,
            },

        "signal_vector":
            [
                historical_signal,
                scenario_signal,
                anomaly_signal,
            ],

        "interpretation":
            interpretation,
    }

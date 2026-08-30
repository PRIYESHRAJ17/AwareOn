from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_temporal_scenario_coupling(
    historical: dict[str, Any],
    temporal_fusion: dict[str, Any],
    progression: dict[str, Any],
) -> dict[str, Any]:

    if not historical:
        raise ValueError("historical is required.")

    if not temporal_fusion:
        raise ValueError("temporal_fusion is required.")

    if not progression:
        raise ValueError("progression is required.")

    historical_direction = str(
        historical.get("direction") or "UNKNOWN"
    ).upper()

    historical_trajectory = str(
        historical.get("trajectory") or "UNKNOWN"
    ).upper()

    temporal_state = str(
        temporal_fusion.get("temporal_state") or "UNKNOWN"
    ).upper()

    alignment = str(
        temporal_fusion.get("alignment") or "UNKNOWN"
    ).upper()

    progression_state = str(
        progression.get("progression_state") or "UNKNOWN"
    ).upper()

    progression_direction = str(
        progression.get("progression_direction") or "UNKNOWN"
    ).upper()

    scenario_info = progression.get(
        "scenario",
        {},
    )

    if not isinstance(
        scenario_info,
        dict,
    ):
        scenario_info = {}

    scenario_change = _num(
        scenario_info.get(
            "risk_change"
        )
    )

    scenario_category = str(
        scenario_info.get(
            "category"
        )
        or "UNKNOWN"
    ).upper()

    if (
        historical_direction == "INCREASING"
        and scenario_change > 0.0
    ):
        coupling = "REINFORCING"

    elif (
        historical_direction == "DECREASING"
        and scenario_change > 0.0
    ):
        coupling = "COUNTERACTING"

    elif (
        historical_direction == "STABLE"
        and scenario_change > 0.0
    ):
        coupling = "NEUTRAL_BACKGROUND_WITH_SCENARIO_PRESSURE"

    elif (
        historical_direction == "INCREASING"
        and scenario_change <= 0.0
    ):
        coupling = "HISTORICAL_PRESSURE_WITHOUT_SCENARIO_ESCALATION"

    else:
        coupling = "WEAK_OR_MIXED"

    if scenario_change >= 5.0:
        scenario_pressure = "HIGH"

    elif scenario_change > 0.0:
        scenario_pressure = "MODERATE"

    else:
        scenario_pressure = "LOW"

    if historical_direction == "INCREASING":
        historical_pressure = "HIGH"

    elif historical_trajectory in {
        "GRADUALLY_RISING",
        "RISING_VOLATILE",
        "RAPIDLY_RISING",
        "RAPIDLY_RISING_VOLATILE",
    }:
        historical_pressure = "MODERATE"

    elif historical_direction == "DECREASING":
        historical_pressure = "DECLINING"

    else:
        historical_pressure = "LOW"

    if (
        coupling == "REINFORCING"
        and scenario_pressure == "HIGH"
    ):
        coupled_state = "HIGH_COUPLED_ESCALATION"

    elif (
        coupling == "REINFORCING"
        or scenario_pressure == "HIGH"
    ):
        coupled_state = "MODERATE_COUPLED_PRESSURE"

    elif (
        coupling
        == "NEUTRAL_BACKGROUND_WITH_SCENARIO_PRESSURE"
    ):
        coupled_state = "SCENARIO_DRIVEN_PRESSURE"

    elif coupling == "COUNTERACTING":
        coupled_state = "COUNTERACTING_SIGNALS"

    else:
        coupled_state = "LOW_COUPLING"

    if (
        progression_direction == "INTENSIFYING"
        and scenario_change > 0.0
    ):
        progression_support = "SCENARIO_INTENSIFICATION_CONFIRMED"

    elif progression_state != "NO_CONFIRMED_PROGRESSION":
        progression_support = "PROGRESSION_PRESENT"

    else:
        progression_support = "NO_PROGRESSION_CONFIRMED"

    if (
        coupled_state == "HIGH_COUPLED_ESCALATION"
    ):
        operational_signal = "ESCALATION_PRIORITY"

    elif (
        coupled_state
        in {
            "MODERATE_COUPLED_PRESSURE",
            "SCENARIO_DRIVEN_PRESSURE",
        }
    ):
        operational_signal = "ENHANCED_SCENARIO_MONITORING"

    elif coupled_state == "COUNTERACTING_SIGNALS":
        operational_signal = "REVIEW_SIGNAL_DISAGREEMENT"

    else:
        operational_signal = "ROUTINE_TEMPORAL_REVIEW"

    interpretation = (
        f"Temporal-scenario coupling is "
        f"{coupled_state}. "
        f"Historical pressure is {historical_pressure}, "
        f"while tested scenario pressure is "
        f"{scenario_pressure}. "
        f"The highest tested scenario reaches "
        f"{scenario_category} with risk change "
        f"{scenario_change:+.2f} points."
    )

    return {
        "engine": "AWAREON_TEMPORAL_SCENARIO_COUPLING",
        "version": "1.0",
        "status": "READY",

        "coupling": coupling,

        "coupled_state": coupled_state,

        "progression_support": progression_support,

        "operational_signal": operational_signal,

        "historical": {
            "direction": historical_direction,
            "trajectory": historical_trajectory,
            "pressure": historical_pressure,
        },

        "temporal": {
            "state": temporal_state,
            "alignment": alignment,
        },

        "scenario": {
            "risk_change": scenario_change,
            "category": scenario_category,
            "pressure": scenario_pressure,
        },

        "progression": {
            "state": progression_state,
            "direction": progression_direction,
        },

        "interpretation": interpretation,
    }

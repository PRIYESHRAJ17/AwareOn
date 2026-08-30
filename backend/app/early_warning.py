from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_early_warning_signal(
    historical: dict[str, Any],
    temporal_fusion: dict[str, Any],
    emerging_risk: dict[str, Any],
    assessment: dict[str, Any],
    scenario_summary: dict[str, Any],
) -> dict[str, Any]:

    if not historical:
        raise ValueError("historical is required.")

    if not temporal_fusion:
        raise ValueError("temporal_fusion is required.")

    if not emerging_risk:
        raise ValueError("emerging_risk is required.")

    if not assessment:
        raise ValueError("assessment is required.")

    if not scenario_summary:
        raise ValueError("scenario_summary is required.")

    historical_direction = str(
        historical.get("direction") or "UNKNOWN"
    ).upper()

    historical_trajectory = str(
        historical.get("trajectory") or "UNKNOWN"
    ).upper()

    anomaly_state = str(
        temporal_fusion.get("anomaly_state") or "UNKNOWN"
    ).upper()

    temporal_state = str(
        temporal_fusion.get("temporal_state") or "UNKNOWN"
    ).upper()

    emerging_state = str(
        emerging_risk.get("emerging_state") or "UNKNOWN"
    ).upper()

    emerging_score = _num(
        emerging_risk.get("score")
    )

    risk_score = _num(
        assessment.get("unified_risk_score")
    )

    severity = str(
        assessment.get("severity") or "UNKNOWN"
    ).upper()

    scenario_high = 0
    scenario_extreme = 0
    scenario_escalating = 0
    worst_mean_change = 0.0

    scenarios = scenario_summary.get(
        "scenarios",
        []
    )

    if isinstance(scenarios, list):
        for item in scenarios:
            scenario_high += int(
                _num(
                    item.get("new_high_or_extreme")
                )
            )

            scenario_extreme += int(
                _num(
                    item.get("new_extreme_cells")
                )
            )

            scenario_escalating += int(
                _num(
                    item.get("escalating_cells")
                )
            )

            worst_mean_change = max(
                worst_mean_change,
                _num(
                    item.get("mean_risk_change")
                ),
            )

    signals: list[dict[str, Any]] = []

    if historical_direction == "INCREASING":
        signals.append(
            {
                "signal": "HISTORICAL_RISING",
                "strength": "HIGH",
                "value": historical_direction,
            }
        )

    elif historical_trajectory in {
        "GRADUALLY_RISING",
        "RAPIDLY_RISING",
        "RAPIDLY_RISING_VOLATILE",
        "RISING_VOLATILE",
    }:
        signals.append(
            {
                "signal": "HISTORICAL_RISING",
                "strength": "MODERATE",
                "value": historical_trajectory,
            }
        )

    if temporal_state == "ESCALATING_TEMPORAL_SIGNAL":
        signals.append(
            {
                "signal": "TEMPORAL_ESCALATION",
                "strength": "HIGH",
                "value": temporal_state,
            }
        )

    if anomaly_state in {
        "MODERATE_ANOMALY",
        "HIGH_ANOMALY",
    }:
        signals.append(
            {
                "signal": "ENVIRONMENTAL_ANOMALY",
                "strength": "HIGH",
                "value": anomaly_state,
            }
        )

    if emerging_state != "NO_EMERGING_SIGNAL":
        signals.append(
            {
                "signal": "EMERGING_RISK",
                "strength": (
                    "HIGH"
                    if emerging_score >= 60.0
                    else "MODERATE"
                ),
                "value": emerging_state,
            }
        )

    if scenario_high > 0:
        signals.append(
            {
                "signal": "SCENARIO_HIGH_ESCALATION",
                "strength": "HIGH",
                "value": scenario_high,
            }
        )

    if scenario_extreme > 0:
        signals.append(
            {
                "signal": "SCENARIO_EXTREME_ESCALATION",
                "strength": "CRITICAL",
                "value": scenario_extreme,
            }
        )

    if scenario_escalating > 0:
        signals.append(
            {
                "signal": "SCENARIO_ESCALATION",
                "strength": "MODERATE",
                "value": scenario_escalating,
            }
        )

    high_signal_count = sum(
        1
        for item in signals
        if item["strength"] in {"HIGH", "CRITICAL"}
    )

    critical_signal_count = sum(
        1
        for item in signals
        if item["strength"] == "CRITICAL"
    )

    if critical_signal_count > 0:
        warning_level = "CRITICAL"

    elif high_signal_count >= 2:
        warning_level = "HIGH"

    elif high_signal_count == 1 or len(signals) >= 2:
        warning_level = "WATCH"

    elif risk_score >= 70.0 or severity in {
        "HIGH",
        "EXTREME",
    }:
        warning_level = "WATCH"

    else:
        warning_level = "NORMAL"

    if warning_level == "CRITICAL":
        signal_strength = 100.0

    elif warning_level == "HIGH":
        signal_strength = min(
            100.0,
            60.0 + high_signal_count * 10.0,
        )

    elif warning_level == "WATCH":
        signal_strength = min(
            75.0,
            35.0 + len(signals) * 8.0,
        )

    else:
        signal_strength = 20.0

    if warning_level == "CRITICAL":
        monitoring_posture = "IMMEDIATE_ACTION_REVIEW"

    elif warning_level == "HIGH":
        monitoring_posture = "ENHANCED_MONITORING"

    elif warning_level == "WATCH":
        monitoring_posture = "ACTIVE_WATCH"

    else:
        monitoring_posture = "ROUTINE_MONITORING"

    if scenario_high > 0 and risk_score >= 70.0:
        lead_signal = (
            "HIGH_CURRENT_RISK_WITH_SCENARIO_ESCALATION"
        )

    elif emerging_state != "NO_EMERGING_SIGNAL":
        lead_signal = (
            "EMERGING_ENVIRONMENTAL_RISK"
        )

    elif anomaly_state in {
        "MODERATE_ANOMALY",
        "HIGH_ANOMALY",
    }:
        lead_signal = "ENVIRONMENTAL_ANOMALY"

    elif historical_direction == "INCREASING":
        lead_signal = "HISTORICAL_RISK_INCREASE"

    else:
        lead_signal = "STRUCTURAL_RISK_BASELINE"

    confidence_score = _num(
        historical.get(
            "confidence",
            {}
        ).get("score")
    )

    if confidence_score >= 75.0:
        confidence_band = "HIGH"

    elif confidence_score >= 50.0:
        confidence_band = "MODERATE"

    else:
        confidence_band = "LIMITED"

    interpretation = (
        f"Early-warning level is {warning_level}. "
        f"The lead signal is {lead_signal}. "
        f"{len(signals)} warning signals are currently "
        "supported by the available evidence."
    )

    if scenario_high > 0:
        interpretation += (
            f" Scenario analysis identifies "
            f"{scenario_high} new HIGH-or-above cells "
            "across the tested conditions."
        )

    if scenario_extreme > 0:
        interpretation += (
            f" {scenario_extreme} new EXTREME cells "
            "are identified in tested scenarios."
        )

    return {
        "engine":
            "AWAREON_EARLY_WARNING_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "warning_level":
            warning_level,

        "signal_strength":
            round(
                signal_strength,
                2,
            ),

        "lead_signal":
            lead_signal,

        "monitoring_posture":
            monitoring_posture,

        "signal_count":
            len(signals),

        "high_signal_count":
            high_signal_count,

        "critical_signal_count":
            critical_signal_count,

        "signals":
            signals,

        "scenario_support":
            {
                "new_high_or_above":
                    scenario_high,

                "new_extreme":
                    scenario_extreme,

                "escalating_cells":
                    scenario_escalating,

                "worst_mean_risk_change":
                    worst_mean_change,
            },

        "confidence":
            {
                "score":
                    confidence_score,

                "band":
                    confidence_band,
            },

        "interpretation":
            interpretation,
    }

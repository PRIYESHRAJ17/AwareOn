from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def detect_emerging_risk(
    historical: dict[str, Any],
    temporal_fusion: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:

    if not historical:
        raise ValueError("historical is required.")

    if not temporal_fusion:
        raise ValueError("temporal_fusion is required.")

    if not assessment:
        raise ValueError("assessment is required.")

    changes = historical.get(
        "recent_vs_baseline",
        {},
    )

    rain_24 = abs(
        _num(
            changes.get(
                "rain_24h_change_percent"
            )
        )
    )

    rain_72 = abs(
        _num(
            changes.get(
                "rain_72h_change_percent"
            )
        )
    )

    rain_7d = abs(
        _num(
            changes.get(
                "rain_7d_change_percent"
            )
        )
    )

    soil = abs(
        _num(
            changes.get(
                "soil_change_percent"
            )
        )
    )

    volatility = abs(
        _num(
            changes.get(
                "volatility_change_percent"
            )
        )
    )

    anomaly_score = _num(
        assessment.get(
            "environment_anomaly_score"
        )
    )

    temporal_state = str(
        temporal_fusion.get(
            "temporal_state"
        )
        or "UNKNOWN"
    ).upper()

    alignment = str(
        temporal_fusion.get(
            "alignment"
        )
        or "UNKNOWN"
    ).upper()

    signal_count = 0
    signals: list[str] = []

    if rain_24 >= 10.0:
        signal_count += 1
        signals.append("RAINFALL_24H_CHANGE")

    if rain_72 >= 10.0:
        signal_count += 1
        signals.append("RAINFALL_72H_CHANGE")

    if rain_7d >= 10.0:
        signal_count += 1
        signals.append("RAINFALL_7D_CHANGE")

    if soil >= 5.0:
        signal_count += 1
        signals.append("SOIL_CHANGE")

    if volatility >= 10.0:
        signal_count += 1
        signals.append("VOLATILITY_CHANGE")

    if anomaly_score >= 50.0:
        signal_count += 1
        signals.append("ENVIRONMENT_ANOMALY")

    if temporal_state == "ESCALATING_TEMPORAL_SIGNAL":
        signal_count += 1
        signals.append("TEMPORAL_ESCALATION")

    if alignment == "TEMPORAL_SIGNAL_DIVERGENCE":
        signal_count += 1
        signals.append("TEMPORAL_DIVERGENCE")

    if signal_count >= 5:
        emerging_state = "HIGH_EMERGING_RISK"

    elif signal_count >= 3:
        emerging_state = "MODERATE_EMERGING_RISK"

    elif signal_count >= 1:
        emerging_state = "EARLY_EMERGING_SIGNAL"

    else:
        emerging_state = "NO_EMERGING_SIGNAL"

    if emerging_state == "HIGH_EMERGING_RISK":
        priority = "P1"

    elif emerging_state == "MODERATE_EMERGING_RISK":
        priority = "P2"

    elif emerging_state == "EARLY_EMERGING_SIGNAL":
        priority = "P3"

    else:
        priority = "P4"

    score = min(
        100.0,
        signal_count * 12.5,
    )

    if anomaly_score >= 75.0:
        score += 15.0

    elif anomaly_score >= 50.0:
        score += 7.5

    score = min(
        100.0,
        score,
    )

    if emerging_state == "NO_EMERGING_SIGNAL":
        interpretation = (
            "No active emerging-risk signal is supported "
            "by the available temporal evidence."
        )

    elif emerging_state == "EARLY_EMERGING_SIGNAL":
        interpretation = (
            "Early environmental changes are present and "
            "should be monitored for persistence."
        )

    elif emerging_state == "MODERATE_EMERGING_RISK":
        interpretation = (
            "Multiple temporal signals indicate emerging "
            "risk and warrant enhanced monitoring."
        )

    else:
        interpretation = (
            "Multiple independent temporal signals indicate "
            "a strong emerging-risk condition."
        )

    return {
        "engine": "AWAREON_EMERGING_RISK_DETECTION",
        "version": "1.0",
        "status": "READY",

        "emerging_state": emerging_state,

        "priority": priority,

        "score": round(
            score,
            2,
        ),

        "signal_count": signal_count,

        "signals": signals,

        "inputs": {
            "rain_24h_change_percent":
                rain_24,

            "rain_72h_change_percent":
                rain_72,

            "rain_7d_change_percent":
                rain_7d,

            "soil_change_percent":
                soil,

            "volatility_change_percent":
                volatility,

            "anomaly_score":
                anomaly_score,

            "temporal_state":
                temporal_state,

            "alignment":
                alignment,
        },

        "interpretation": interpretation,
    }

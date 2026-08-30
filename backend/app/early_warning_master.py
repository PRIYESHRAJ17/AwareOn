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


def build_early_warning_master(
    historical: dict[str, Any],
    regional_temporal: dict[str, Any],
    acceleration: dict[str, Any],
    anomaly_fusion: dict[str, Any],
    emerging_risk: dict[str, Any],
    early_warning: dict[str, Any],
    progression: dict[str, Any],
    coupling: dict[str, Any],
    multiscale: dict[str, Any],
) -> dict[str, Any]:

    inputs = [
        historical,
        regional_temporal,
        acceleration,
        anomaly_fusion,
        emerging_risk,
        early_warning,
        progression,
        coupling,
        multiscale,
    ]

    if any(not item for item in inputs):
        raise ValueError(
            "All early-warning intelligence inputs are required."
        )

    warning_level = str(
        early_warning.get(
            "warning_level"
        )
        or "UNKNOWN"
    ).upper()

    early_score = _num(
        early_warning.get(
            "signal_strength"
        )
    )

    emerging_state = str(
        emerging_risk.get(
            "emerging_state"
        )
        or "UNKNOWN"
    ).upper()

    progression_state = str(
        progression.get(
            "progression_state"
        )
        or "UNKNOWN"
    ).upper()

    progression_direction = str(
        progression.get(
            "progression_direction"
        )
        or "UNKNOWN"
    ).upper()

    coupling_state = str(
        coupling.get(
            "coupled_state"
        )
        or "UNKNOWN"
    ).upper()

    multiscale_overall = str(
        multiscale.get(
            "overall"
        )
        or "UNKNOWN"
    ).upper()

    multiscale_agreement = str(
        multiscale.get(
            "agreement"
        )
        or "UNKNOWN"
    ).upper()

    temporal_state = str(
        anomaly_fusion.get(
            "temporal_state"
        )
        or "UNKNOWN"
    ).upper()

    anomaly_state = str(
        anomaly_fusion.get(
            "anomaly_state"
        )
        or "UNKNOWN"
    ).upper()

    acceleration_state = str(
        acceleration.get(
            "state"
        )
        or "UNKNOWN"
    ).upper()

    historical_direction = str(
        historical.get(
            "direction"
        )
        or "UNKNOWN"
    ).upper()

    historical_confidence = _num(
        historical.get(
            "confidence",
            {},
        ).get(
            "score"
        )
    )

    emerging_score = _num(
        emerging_risk.get(
            "score"
        )
    )

    progression_priority = str(
        progression.get(
            "progression_priority"
        )
        or "UNKNOWN"
    ).upper()

    if warning_level == "CRITICAL":
        master_warning = "CRITICAL"

    elif (
        warning_level == "HIGH"
        or progression_priority == "P1"
    ):
        master_warning = "HIGH"

    elif (
        warning_level == "WATCH"
        or progression_priority in {
            "P2",
            "P3",
        }
    ):
        master_warning = "WATCH"

    else:
        master_warning = "NORMAL"

    if (
        master_warning == "CRITICAL"
        and
        progression_direction
        == "INTENSIFYING"
    ):
        master_state = (
            "CRITICAL_ESCALATING_SIGNAL"
        )

    elif (
        master_warning == "HIGH"
        and
        (
            acceleration_state
            == "ACCELERATING"
            or
            temporal_state
            == "ESCALATING_TEMPORAL_SIGNAL"
        )
    ):
        master_state = (
            "HIGH_ESCALATING_SIGNAL"
        )

    elif (
        master_warning == "WATCH"
        and
        coupling_state
        in {
            "MODERATE_COUPLED_PRESSURE",
            "SCENARIO_DRIVEN_PRESSURE",
        }
    ):
        master_state = (
            "WATCH_SCENARIO_SENSITIVE"
        )

    elif (
        master_warning == "WATCH"
    ):
        master_state = (
            "WATCH_STABLE_OR_MIXED_SIGNAL"
        )

    else:
        master_state = (
            "NORMAL_TEMPORAL_POSTURE"
        )

    if (
        master_state
        in {
            "CRITICAL_ESCALATING_SIGNAL",
            "HIGH_ESCALATING_SIGNAL",
        }
    ):
        operational_posture = (
            "ENHANCED_EARLY_WARNING"
        )

    elif master_state in {
        "WATCH_SCENARIO_SENSITIVE",
        "WATCH_STABLE_OR_MIXED_SIGNAL",
    }:
        operational_posture = (
            "ACTIVE_WATCH"
        )

    else:
        operational_posture = (
            "ROUTINE_MONITORING"
        )

    if multiscale_agreement == "STRONG":
        timescale_confidence = "HIGH"

    elif multiscale_agreement == "PARTIAL":
        timescale_confidence = "MODERATE"

    else:
        timescale_confidence = "LIMITED"

    evidence_count = 0

    if historical_confidence >= 75.0:
        evidence_count += 1

    if anomaly_state != "UNKNOWN":
        evidence_count += 1

    if progression_state != "NO_CONFIRMED_PROGRESSION":
        evidence_count += 1

    if coupling_state != "LOW_COUPLING":
        evidence_count += 1

    if multiscale_overall != "UNKNOWN":
        evidence_count += 1

    if evidence_count >= 4:
        evidence_strength = "STRONG"

    elif evidence_count >= 2:
        evidence_strength = "MODERATE"

    else:
        evidence_strength = "LIMITED"

    if (
        emerging_state
        == "NO_EMERGING_SIGNAL"
        and
        historical_direction
        == "STABLE"
        and
        warning_level
        == "WATCH"
    ):
        interpretation = (
            "Current early-warning posture is watch-level. "
            "Historical environmental evidence is stable, "
            "but current risk and tested scenario sensitivity "
            "support continued active monitoring."
        )

    elif master_warning == "CRITICAL":
        interpretation = (
            "Multiple intelligence layers support a critical "
            "early-warning posture requiring immediate review."
        )

    elif master_warning == "HIGH":
        interpretation = (
            "Multiple intelligence layers support a high "
            "early-warning posture requiring enhanced monitoring."
        )

    else:
        interpretation = (
            "Temporal intelligence does not indicate a critical "
            "early-warning condition."
        )

    return {
        "engine":
            "AWAREON_EARLY_WARNING_MASTER",

        "version":
            "1.0",

        "status":
            "READY",

        "master_warning":
            master_warning,

        "master_state":
            master_state,

        "operational_posture":
            operational_posture,

        "signal_strength":
            early_score,

        "evidence_strength":
            evidence_strength,

        "evidence_count":
            evidence_count,

        "historical":
            {
                "direction":
                    historical_direction,

                "confidence":
                    historical_confidence,
            },

        "temporal":
            {
                "state":
                    temporal_state,

                "anomaly":
                    anomaly_state,

                "acceleration":
                    acceleration_state,
            },

        "emerging":
            {
                "state":
                    emerging_state,

                "score":
                    emerging_score,
            },

        "progression":
            {
                "state":
                    progression_state,

                "direction":
                    progression_direction,

                "priority":
                    progression_priority,
            },

        "coupling":
            {
                "state":
                    coupling_state,
            },

        "multiscale":
            {
                "overall":
                    multiscale_overall,

                "agreement":
                    multiscale_agreement,

                "confidence":
                    timescale_confidence,
            },

        "interpretation":
            interpretation,
    }

from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_regional_temporal_intelligence(
    historical: dict[str, Any],
    regional_master: dict[str, Any],
) -> dict[str, Any]:

    if not historical:
        raise ValueError(
            "historical intelligence is required."
        )

    if not regional_master:
        raise ValueError(
            "regional master intelligence is required."
        )

    historical_info = historical.get(
        "confidence",
        {},
    )

    historical_change = historical.get(
        "recent_vs_baseline",
        {},
    )

    historical_trajectory = str(
        historical.get("trajectory") or "UNKNOWN"
    ).upper()

    historical_direction = str(
        historical.get("direction") or "UNKNOWN"
    ).upper()

    historical_category = str(
        historical.get("trajectory_category") or "UNKNOWN"
    ).upper()

    historical_score = _num(
        historical.get("trajectory_score")
    )

    confidence_score = _num(
        historical_info.get("score")
    )

    confidence_band = str(
        historical_info.get("band") or "UNKNOWN"
    ).upper()

    risk_info = regional_master.get(
        "risk",
        {},
    )

    evolution_info = regional_master.get(
        "evolution",
        {},
    )

    exposure_info = regional_master.get(
        "exposure",
        {},
    )

    regional_state = str(
        regional_master.get("master_state") or "UNKNOWN"
    ).upper()

    regional_posture = str(
        regional_master.get("regional_posture") or "UNKNOWN"
    ).upper()

    mean_risk = _num(
        risk_info.get("mean_risk")
    )

    maximum_risk = _num(
        risk_info.get("maximum_risk")
    )

    high_risk_cells = int(
        _num(
            risk_info.get("cell_count")
        )
    )

    extreme_cells = int(
        _num(
            risk_info.get("extreme_cells")
        )
    )

    cluster_trajectory = str(
        evolution_info.get("trajectory") or "UNKNOWN"
    ).upper()

    cluster_behavior = str(
        evolution_info.get("behavior") or "UNKNOWN"
    ).upper()

    risk_delta = _num(
        evolution_info.get("mean_risk_delta")
    )

    exposure_state = str(
        exposure_info.get("state") or "UNKNOWN"
    ).upper()

    impact_focus = str(
        exposure_info.get("impact_focus") or "UNKNOWN"
    ).upper()

    if (
        historical_direction == "INCREASING"
        and cluster_trajectory
        in {
            "INCREASING",
            "ACCELERATING",
        }
    ):
        alignment = "CONVERGENT_RISING"

    elif (
        historical_direction == "DECREASING"
        and cluster_trajectory
        in {
            "DECREASING",
            "DECELERATING",
        }
    ):
        alignment = "CONVERGENT_DECLINING"

    elif (
        historical_direction == "STABLE"
        and cluster_trajectory == "STABLE"
    ):
        alignment = "CONVERGENT_STABLE"

    else:
        alignment = "DIVERGENT"

    if historical_category == "EXTREME":
        temporal_risk_state = (
            "EXTREME_TEMPORAL_PRESSURE"
        )

    elif historical_category == "HIGH":
        temporal_risk_state = (
            "HIGH_TEMPORAL_PRESSURE"
        )

    elif historical_direction == "INCREASING":
        temporal_risk_state = (
            "ESCALATING_TEMPORAL_PRESSURE"
        )

    elif historical_direction == "STABLE":
        temporal_risk_state = (
            "STABLE_TEMPORAL_PRESSURE"
        )

    else:
        temporal_risk_state = (
            "MIXED_TEMPORAL_PRESSURE"
        )

    if (
        regional_posture == "CRITICAL_AND_ESCALATING"
        and historical_direction == "INCREASING"
    ):
        warning_signal = (
            "HIGH_CONFIDENCE_ESCALATION"
        )

    elif (
        regional_posture == "CRITICAL_AND_ESCALATING"
        and historical_direction == "STABLE"
    ):
        warning_signal = (
            "STRUCTURAL_RISK_WITH_STABLE_HISTORY"
        )

    elif historical_direction == "INCREASING":
        warning_signal = (
            "EMERGING_ESCALATION"
        )

    elif historical_direction == "DECREASING":
        warning_signal = (
            "DECLINING_ENVIRONMENTAL_SIGNAL"
        )

    else:
        warning_signal = (
            "STABLE_ENVIRONMENTAL_SIGNAL"
        )

    alignment_text = (
        "aligned"
        if alignment.startswith("CONVERGENT")
        else "not fully aligned"
    )

    interpretation = (
        f"Historical environmental trajectory is "
        f"{historical_trajectory} with direction "
        f"{historical_direction}. "
        f"The regional risk structure has mean risk "
        f"{mean_risk:.2f} and maximum risk "
        f"{maximum_risk:.2f} across "
        f"{high_risk_cells} high-risk cells. "
        f"{extreme_cells} regional cells are EXTREME. "
        f"Historical and regional evolution signals are "
        f"{alignment_text}. "
        f"Historical temporal evidence is based on "
        f"the available ERA5 source point."
    )

    return {
        "engine":
            "AWAREON_REGIONAL_TEMPORAL_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "historical":
            {
                "trajectory":
                    historical_trajectory,

                "direction":
                    historical_direction,

                "category":
                    historical_category,

                "score":
                    historical_score,

                "confidence":
                    confidence_score,

                "confidence_band":
                    confidence_band,
            },

        "regional":
            {
                "state":
                    regional_state,

                "posture":
                    regional_posture,

                "mean_risk":
                    mean_risk,

                "maximum_risk":
                    maximum_risk,

                "high_risk_cells":
                    high_risk_cells,

                "extreme_cells":
                    extreme_cells,

                "risk_delta":
                    risk_delta,

                "trajectory":
                    cluster_trajectory,

                "behavior":
                    cluster_behavior,
            },

        "temporal_alignment":
            alignment,

        "temporal_risk_state":
            temporal_risk_state,

        "warning_signal":
            warning_signal,

        "confidence":
            {
                "score":
                    confidence_score,

                "band":
                    confidence_band,
            },

        "recent_change":
            {
                "rain_24h_percent":
                    _num(
                        historical_change.get(
                            "rain_24h_change_percent"
                        )
                    ),

                "rain_72h_percent":
                    _num(
                        historical_change.get(
                            "rain_72h_change_percent"
                        )
                    ),

                "rain_7d_percent":
                    _num(
                        historical_change.get(
                            "rain_7d_change_percent"
                        )
                    ),

                "soil_percent":
                    _num(
                        historical_change.get(
                            "soil_change_percent"
                        )
                    ),

                "volatility_percent":
                    _num(
                        historical_change.get(
                            "volatility_change_percent"
                        )
                    ),
            },

        "exposure":
            {
                "state":
                    exposure_state,

                "impact_focus":
                    impact_focus,
            },

        "evidence_scope":
            {
                "spatial_points":
                    1,

                "limitation":
                    (
                        "Historical environmental trajectory "
                        "is derived from the available ERA5 "
                        "source point."
                    ),
            },

        "interpretation":
            interpretation,
    }

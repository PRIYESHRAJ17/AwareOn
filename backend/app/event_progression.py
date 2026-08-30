from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank(value: Any) -> int:
    ranks = {
        "LOW": 0,
        "MODERATE": 1,
        "HIGH": 2,
        "EXTREME": 3,
    }

    return ranks.get(
        str(value or "").upper(),
        0,
    )


def build_event_progression(
    assessment: dict[str, Any],
    early_warning: dict[str, Any],
    historical: dict[str, Any],
    scenario_records: list[dict[str, Any]],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError("assessment is required.")

    if not early_warning:
        raise ValueError("early_warning is required.")

    if not historical:
        raise ValueError("historical is required.")

    if not isinstance(
        scenario_records,
        list,
    ):
        raise ValueError(
            "scenario_records must be a list."
        )

    current_risk = _num(
        assessment.get(
            "unified_risk_score"
        )
    )

    current_severity = str(
        assessment.get(
            "severity"
        )
        or "UNKNOWN"
    ).upper()

    warning_level = str(
        early_warning.get(
            "warning_level"
        )
        or "UNKNOWN"
    ).upper()

    historical_direction = str(
        historical.get(
            "direction"
        )
        or "UNKNOWN"
    ).upper()

    baseline_records = []

    for item in scenario_records:

        rainfall = _num(
            item.get(
                "rainfall_change_percent"
            )
        )

        if rainfall == 0.0:
            baseline_records.append(
                item
            )

    if baseline_records:

        baseline_mean = (
            sum(
                _num(
                    item.get(
                        "risk_score"
                    )
                )
                for item in baseline_records
            )
            /
            len(
                baseline_records
            )
        )

    else:

        baseline_mean = 0.0

    if scenario_records:

        scenario_records_sorted = sorted(
            scenario_records,
            key=lambda item: _num(
                item.get(
                    "risk_score"
                )
            ),
        )

        highest_risk_scenario = (
            scenario_records_sorted[-1]
        )

        scenario_risk = _num(
            highest_risk_scenario.get(
                "risk_score"
            )
        )

        scenario_category = str(
            highest_risk_scenario.get(
                "risk_category"
            )
            or "UNKNOWN"
        ).upper()

        scenario_change = _num(
            highest_risk_scenario.get(
                "risk_score_change"
            )
        )

        scenario_rainfall = _num(
            highest_risk_scenario.get(
                "rainfall_change_percent"
            )
        )

    else:

        scenario_risk = 0.0
        scenario_category = "UNKNOWN"
        scenario_change = 0.0
        scenario_rainfall = 0.0

    current_rank = _rank(
        current_severity
    )

    scenario_rank = _rank(
        scenario_category
    )

    if (
        current_rank >= 3
        and
        scenario_change > 0.0
    ):

        progression_state = (
            "CRITICAL_RISK_WITH_FURTHER_PRESSURE"
        )

    elif (
        scenario_rank > current_rank
    ):

        progression_state = (
            "CATEGORY_ESCALATION"
        )

    elif scenario_change > 5.0:

        progression_state = (
            "RISK_INTENSIFICATION"
        )

    elif (
        historical_direction == "INCREASING"
        and
        scenario_change > 0.0
    ):

        progression_state = (
            "MULTI_SIGNAL_PROGRESSION"
        )

    else:

        progression_state = (
            "NO_CONFIRMED_PROGRESSION"
        )

    if scenario_change > 0.0:

        progression_direction = (
            "INTENSIFYING"
        )

    elif scenario_change < 0.0:

        progression_direction = (
            "EASING"
        )

    elif scenario_rank > current_rank:

        progression_direction = (
            "WORSENING"
        )

    elif scenario_rank < current_rank:

        progression_direction = (
            "IMPROVING"
        )

    else:

        progression_direction = (
            "STABLE"
        )

    if (
        warning_level == "CRITICAL"
        or
        progression_state
        == "CATEGORY_ESCALATION"
    ):

        progression_priority = "P1"

    elif (
        warning_level == "HIGH"
        or
        progression_state
        in {
            "CRITICAL_RISK_WITH_FURTHER_PRESSURE",
            "RISK_INTENSIFICATION",
            "MULTI_SIGNAL_PROGRESSION",
        }
    ):

        progression_priority = "P2"

    elif (
        warning_level == "WATCH"
        or
        progression_direction
        == "INTENSIFYING"
    ):

        progression_priority = "P3"

    else:

        progression_priority = "P4"

    risk_change_from_baseline = (
        current_risk
        -
        baseline_mean
    )

    if (
        current_rank >= 3
        and
        scenario_change > 0.0
    ):

        progression_confidence = "HIGH"

    elif (
        scenario_change > 0.0
        or
        historical_direction == "INCREASING"
    ):

        progression_confidence = "MODERATE"

    else:

        progression_confidence = "HIGH"

    interpretation = (
        f"Progression state is "
        f"{progression_state}. "
        f"Direction is "
        f"{progression_direction}. "
        f"Current severity is "
        f"{current_severity}, while the highest "
        f"tested scenario reaches "
        f"{scenario_category} under "
        f"+{scenario_rainfall:.0f}% rainfall."
    )

    if scenario_change > 0.0:

        interpretation += (
            f" Scenario risk increases by "
            f"+{scenario_change:.2f} points."
        )

    return {
        "engine":
            "AWAREON_EVENT_PROGRESSION_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "progression_state":
            progression_state,

        "progression_direction":
            progression_direction,

        "progression_priority":
            progression_priority,

        "confidence":
            progression_confidence,

        "current":
            {
                "risk_score":
                    current_risk,

                "severity":
                    current_severity,

                "category_rank":
                    current_rank,
            },

        "scenario":
            {
                "rainfall_change_percent":
                    scenario_rainfall,

                "risk_score":
                    scenario_risk,

                "category":
                    scenario_category,

                "category_rank":
                    scenario_rank,

                "risk_change":
                    scenario_change,

                "category_delta":
                    scenario_rank
                    -
                    current_rank,
            },

        "baseline":
            {
                "mean_risk":
                    baseline_mean,
            },

        "progression":
            {
                "risk_change_from_baseline":
                    risk_change_from_baseline,

                "historical_direction":
                    historical_direction,

                "warning_level":
                    warning_level,
            },

        "interpretation":
            interpretation,
    }

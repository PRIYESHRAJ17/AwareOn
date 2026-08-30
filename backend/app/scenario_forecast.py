from __future__ import annotations

from typing import Any


TRIGGER_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank(
    value: Any,
) -> int:
    return TRIGGER_RANK.get(
        str(value or "").upper(),
        -1,
    )


def _direction(
    values: list[float],
) -> str:

    if len(values) < 2:
        return "INSUFFICIENT_DATA"

    increasing = all(
        values[index]
        >=
        values[index - 1]
        for index in range(
            1,
            len(values),
        )
    )

    decreasing = all(
        values[index]
        <=
        values[index - 1]
        for index in range(
            1,
            len(values),
        )
    )

    if increasing:
        return "INCREASING"

    if decreasing:
        return "DECREASING"

    return "MIXED"


def _confidence(
    scenario_count: int,
    trigger_shifts: int,
    escalation_direction: str,
) -> str:

    if (
        scenario_count >= 4
        and
        trigger_shifts >= 1
        and
        escalation_direction == "INCREASING"
    ):
        return "MODERATE"

    if (
        scenario_count >= 3
        and
        escalation_direction == "INCREASING"
    ):
        return "LOW"

    return "LIMITED"


def build_scenario_forecast(
    curve: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:

    if not curve:
        raise ValueError(
            "Scenario curve data is required."
        )

    if not thresholds:
        raise ValueError(
            "Scenario threshold data is required."
        )

    points = curve.get(
        "points",
        [],
    )

    if not points:
        raise ValueError(
            "Scenario curve contains no points."
        )

    mean_values = [
        _num(
            item.get(
                "mean_risk_score"
            )
        )
        for item in points
    ]

    escalation_values = [
        _num(
            item.get(
                "escalating_cells"
            )
        )
        for item in points
    ]

    trigger_values = [
        _rank(
            item.get(
                "trigger_category"
            )
        )
        for item in points
    ]

    mean_direction = _direction(
        mean_values
    )

    escalation_direction = _direction(
        escalation_values
    )

    trigger_direction = _direction(
        trigger_values
    )

    strongest_tipping_region = (
        thresholds.get(
            "strongest_tipping_region"
        )
    )

    first_escalation = (
        thresholds.get(
            "first_escalation"
        )
    )

    first_new_high = (
        thresholds.get(
            "first_new_high"
        )
    )

    largest_escalation_jump = (
        thresholds.get(
            "largest_escalation_jump"
        )
    )

    worst_case = points[-1]

    if (
        strongest_tipping_region
        and
        strongest_tipping_region.get(
            "type"
        )
        == "TRIGGER_TRANSITION"
    ):

        trajectory_class = (
            "THRESHOLD_SENSITIVE"
        )

    elif (
        curve.get(
            "overall_curve_shape"
        )
        == "ACCELERATING"
    ):

        trajectory_class = (
            "ACCELERATING_RISK"
        )

    elif (
        mean_direction == "INCREASING"
        and
        escalation_direction == "INCREASING"
    ):

        trajectory_class = (
            "PROGRESSIVE_ESCALATION"
        )

    else:

        trajectory_class = (
            "MIXED_RESPONSE"
        )

    early_warning = None

    if first_escalation:
        early_warning = {
            "rainfall_change_percent":
                first_escalation.get(
                    "rainfall_change_percent"
                ),

            "scenario":
                first_escalation.get(
                    "scenario"
                ),

            "reason":
                "First observed category escalation.",
        }

    transition_region = None

    if strongest_tipping_region:

        transition_region = {
            "lower_bound_percent":
                strongest_tipping_region.get(
                    "lower_bound_percent"
                ),

            "upper_bound_percent":
                strongest_tipping_region.get(
                    "upper_bound_percent"
                ),

            "type":
                strongest_tipping_region.get(
                    "type"
                ),

            "score":
                strongest_tipping_region.get(
                    "transition_score"
                ),
        }

    trigger_categories = [
        item.get(
            "trigger_category"
        )
        for item in points
    ]

    unique_triggers = []

    for category in trigger_categories:

        if (
            category
            and
            category
            not in unique_triggers
        ):
            unique_triggers.append(
                category
            )

    confidence = _confidence(
        len(points),
        int(
            curve.get(
                "trigger_shift_count",
                0,
            )
        ),
        escalation_direction,
    )

    limitations = [
        "Trajectory is derived from the tested scenarios only.",

        "Only four rainfall scenarios are currently available.",

        "The detected transition is a region, not a continuous physical threshold.",

        "Unsimulated rainfall values should not be interpreted as observed outcomes.",
    ]

    return {
        "trajectory_class":
            trajectory_class,

        "confidence":
            confidence,

        "risk_direction":
            mean_direction,

        "escalation_direction":
            escalation_direction,

        "trigger_direction":
            trigger_direction,

        "trigger_categories":
            unique_triggers,

        "early_warning_point":
            early_warning,

        "first_new_high_point":
            (
                {
                    "rainfall_change_percent":
                        first_new_high.get(
                            "rainfall_change_percent"
                        ),

                    "scenario":
                        first_new_high.get(
                            "scenario"
                        ),

                    "new_high_or_extreme":
                        first_new_high.get(
                            "new_high_or_extreme"
                        ),
                }
                if first_new_high
                else None
            ),

        "transition_region":
            transition_region,

        "largest_escalation_jump":
            (
                {
                    "from_rainfall_percent":
                        largest_escalation_jump.get(
                            "from_rainfall_percent"
                        ),

                    "to_rainfall_percent":
                        largest_escalation_jump.get(
                            "to_rainfall_percent"
                        ),

                    "additional_escalating_cells":
                        largest_escalation_jump.get(
                            "escalating_cells_delta"
                        ),
                }
                if largest_escalation_jump
                else None
            ),

        "worst_tested_scenario":
            {
                "scenario":
                    worst_case.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    worst_case.get(
                        "rainfall_change_percent"
                    ),

                "mean_risk_score":
                    worst_case.get(
                        "mean_risk_score"
                    ),

                "escalating_cells":
                    worst_case.get(
                        "escalating_cells"
                    ),
            },

        "tested_scenario_count":
            len(points),

        "limitations":
            limitations,
    }

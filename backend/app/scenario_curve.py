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


def _int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _direction(
    first: float,
    second: float,
) -> str:

    if second > first:
        return "INCREASING"

    if second < first:
        return "DECREASING"

    return "FLAT"


def _curve_shape(
    increments: list[float],
) -> str:

    if len(increments) < 2:
        return "INSUFFICIENT_DATA"

    positive = all(
        value >= 0
        for value in increments
    )

    if not positive:
        return "NON_MONOTONIC"

    if all(
        abs(increments[i] - increments[0])
        < 0.25
        for i in range(1, len(increments))
    ):
        return "LINEAR"

    accelerating_pairs = 0
    decelerating_pairs = 0

    for index in range(
        1,
        len(increments),
    ):

        previous = increments[index - 1]
        current = increments[index]

        if current > previous:
            accelerating_pairs += 1

        elif current < previous:
            decelerating_pairs += 1

    if (
        accelerating_pairs == len(increments) - 1
        and
        decelerating_pairs == 0
    ):
        return "ACCELERATING"

    if (
        decelerating_pairs == len(increments) - 1
        and
        accelerating_pairs == 0
    ):
        return "DECELERATING"

    return "MIXED"


def analyze_scenario_curve(
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:

    if not scenarios:
        raise ValueError(
            "Scenario curve requires scenario data."
        )

    ordered = sorted(
        scenarios,
        key=lambda item: _num(
            item.get(
                "rainfall_change_percent"
            )
        ),
    )

    points: list[dict[str, Any]] = []

    for item in ordered:

        points.append(
            {
                "scenario":
                    item.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    _num(
                        item.get(
                            "rainfall_change_percent"
                        )
                    ),

                "mean_risk_score":
                    _num(
                        item.get(
                            "mean_risk_score"
                        )
                    ),

                "mean_risk_change":
                    _num(
                        item.get(
                            "mean_risk_change"
                        )
                    ),

                "max_risk_score":
                    _num(
                        item.get(
                            "max_risk_score"
                        )
                    ),

                "max_risk_change":
                    _num(
                        item.get(
                            "max_risk_change"
                        )
                    ),

                "escalating_cells":
                    _int(
                        item.get(
                            "escalating_cells"
                        )
                    ),

                "new_high_or_extreme":
                    _int(
                        item.get(
                            "new_high_or_extreme"
                        )
                    ),

                "new_extreme_cells":
                    _int(
                        item.get(
                            "new_extreme_cells"
                        )
                    ),

                "rainfall_trigger_score":
                    _num(
                        item.get(
                            "rainfall_trigger_score"
                        )
                    ),

                "trigger_category":
                    str(
                        item.get(
                            "trigger_category"
                        )
                        or ""
                    ).upper(),
            }
        )

    mean_increments: list[float] = []
    escalation_increments: list[float] = []

    for index in range(
        1,
        len(points),
    ):

        mean_delta = (
            points[index][
                "mean_risk_score"
            ]
            -
            points[index - 1][
                "mean_risk_score"
            ]
        )

        escalation_delta = (
            points[index][
                "escalating_cells"
            ]
            -
            points[index - 1][
                "escalating_cells"
            ]
        )

        mean_increments.append(
            mean_delta
        )

        escalation_increments.append(
            float(
                escalation_delta
            )
        )

    mean_curve_shape = _curve_shape(
        mean_increments
    )

    escalation_curve_shape = _curve_shape(
        escalation_increments
    )

    max_mean_change = max(
        points,
        key=lambda item:
            item[
                "mean_risk_change"
            ],
    )

    max_escalation = max(
        points,
        key=lambda item:
            item[
                "escalating_cells"
            ],
    )

    max_new_high = max(
        points,
        key=lambda item:
            item[
                "new_high_or_extreme"
            ],
    )

    trigger_progression = [
        point[
            "trigger_category"
        ]
        for point in points
    ]

    unique_trigger_categories = []

    for category in trigger_progression:

        if (
            category
            and
            category
            not in unique_trigger_categories
        ):
            unique_trigger_categories.append(
                category
            )

    trigger_shift_count = 0

    for index in range(
        1,
        len(trigger_progression),
    ):

        if (
            trigger_progression[index]
            !=
            trigger_progression[index - 1]
        ):
            trigger_shift_count += 1

    rainfall_range = (
        points[-1][
            "rainfall_change_percent"
        ]
        -
        points[0][
            "rainfall_change_percent"
        ]
    )

    mean_risk_range = (
        points[-1][
            "mean_risk_score"
        ]
        -
        points[0][
            "mean_risk_score"
        ]
    )

    escalation_range = (
        points[-1][
            "escalating_cells"
        ]
        -
        points[0][
            "escalating_cells"
        ]
    )

    risk_response_per_percent = (
        mean_risk_range
        /
        rainfall_range
        if rainfall_range > 0
        else 0.0
    )

    escalation_response_per_percent = (
        escalation_range
        /
        rainfall_range
        if rainfall_range > 0
        else 0.0
    )

    if (
        mean_curve_shape == "ACCELERATING"
        or
        escalation_curve_shape == "ACCELERATING"
    ):
        overall_shape = "ACCELERATING"

    elif (
        mean_curve_shape == "DECELERATING"
        and
        escalation_curve_shape
        == "DECELERATING"
    ):
        overall_shape = "DECELERATING"

    elif (
        mean_curve_shape == "LINEAR"
        and
        escalation_curve_shape == "LINEAR"
    ):
        overall_shape = "LINEAR"

    else:
        overall_shape = "MIXED"

    return {
        "scenario_count":
            len(points),

        "overall_curve_shape":
            overall_shape,

        "mean_risk_curve_shape":
            mean_curve_shape,

        "escalation_curve_shape":
            escalation_curve_shape,

        "rainfall_range_percent":
            rainfall_range,

        "mean_risk_range":
            mean_risk_range,

        "escalation_range":
            escalation_range,

        "mean_risk_response_per_percent":
            risk_response_per_percent,

        "escalation_response_per_percent":
            escalation_response_per_percent,

        "maximum_mean_change":
            {
                "scenario":
                    max_mean_change.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    max_mean_change.get(
                        "rainfall_change_percent"
                    ),

                "value":
                    max_mean_change.get(
                        "mean_risk_change"
                    ),
            },

        "maximum_escalation":
            {
                "scenario":
                    max_escalation.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    max_escalation.get(
                        "rainfall_change_percent"
                    ),

                "cells":
                    max_escalation.get(
                        "escalating_cells"
                    ),
            },

        "maximum_new_high":
            {
                "scenario":
                    max_new_high.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    max_new_high.get(
                        "rainfall_change_percent"
                    ),

                "cells":
                    max_new_high.get(
                        "new_high_or_extreme"
                    ),
            },

        "trigger_progression":
            trigger_progression,

        "unique_trigger_categories":
            unique_trigger_categories,

        "trigger_shift_count":
            trigger_shift_count,

        "points":
            points,
    }

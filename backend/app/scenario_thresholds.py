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


def _int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _rank(
    value: Any,
) -> int:
    return TRIGGER_RANK.get(
        str(value or "").upper(),
        -1,
    )


def detect_scenario_thresholds(
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:

    if not scenarios:
        raise ValueError(
            "Scenario thresholds require scenario data."
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

                "trigger_score":
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

    transitions: list[dict[str, Any]] = []

    for index in range(
        1,
        len(points),
    ):

        previous = points[index - 1]
        current = points[index]

        mean_delta = (
            current["mean_risk_score"]
            -
            previous["mean_risk_score"]
        )

        escalation_delta = (
            current["escalating_cells"]
            -
            previous["escalating_cells"]
        )

        new_high_delta = (
            current["new_high_or_extreme"]
            -
            previous["new_high_or_extreme"]
        )

        trigger_changed = (
            current["trigger_category"]
            !=
            previous["trigger_category"]
        )

        trigger_rank_delta = (
            _rank(
                current["trigger_category"]
            )
            -
            _rank(
                previous["trigger_category"]
            )
        )

        transitions.append(
            {
                "from_scenario":
                    previous["scenario"],

                "to_scenario":
                    current["scenario"],

                "from_rainfall_percent":
                    previous[
                        "rainfall_change_percent"
                    ],

                "to_rainfall_percent":
                    current[
                        "rainfall_change_percent"
                    ],

                "mean_risk_delta":
                    mean_delta,

                "escalating_cells_delta":
                    escalation_delta,

                "new_high_delta":
                    new_high_delta,

                "trigger_changed":
                    trigger_changed,

                "trigger_rank_delta":
                    trigger_rank_delta,
            }
        )

    first_escalation = next(
        (
            point
            for point in points
            if point["escalating_cells"] > 0
        ),
        None,
    )

    first_new_high = next(
        (
            point
            for point in points
            if point["new_high_or_extreme"] > 0
        ),
        None,
    )

    first_moderate_trigger = next(
        (
            point
            for point in points
            if _rank(
                point["trigger_category"]
            ) >= _rank("MODERATE")
        ),
        None,
    )

    largest_escalation_jump = max(
        transitions,
        key=lambda item:
            item["escalating_cells_delta"],
        default=None,
    )

    largest_mean_risk_jump = max(
        transitions,
        key=lambda item:
            item["mean_risk_delta"],
        default=None,
    )

    trigger_transitions = [
        item
        for item in transitions
        if item["trigger_changed"]
    ]

    candidate_regions: list[dict[str, Any]] = []

    for transition in transitions:

        score = 0.0

        if transition[
            "trigger_changed"
        ]:
            score += 40.0

        score += min(
            40.0,
            transition[
                "escalating_cells_delta"
            ] * 2.0,
        )

        score += min(
            20.0,
            transition[
                "new_high_delta"
            ],
        )

        candidate_regions.append(
            {
                **transition,
                "transition_score":
                    score,
            }
        )

    strongest_transition = max(
        candidate_regions,
        key=lambda item:
            item["transition_score"],
        default=None,
    )

    if strongest_transition:

        lower_bound = strongest_transition[
            "from_rainfall_percent"
        ]

        upper_bound = strongest_transition[
            "to_rainfall_percent"
        ]

        if (
            strongest_transition[
                "trigger_changed"
            ]
        ):
            tipping_type = (
                "TRIGGER_TRANSITION"
            )

        elif (
            strongest_transition[
                "escalating_cells_delta"
            ]
            >= 20
        ):
            tipping_type = (
                "ESCALATION_ACCELERATION"
            )

        elif (
            strongest_transition[
                "mean_risk_delta"
            ]
            >= 2
        ):
            tipping_type = (
                "RISK_RESPONSE_SHIFT"
            )

        else:
            tipping_type = (
                "LIMITED_TRANSITION"
            )

        tipping_region = {
            "lower_bound_percent":
                lower_bound,

            "upper_bound_percent":
                upper_bound,

            "type":
                tipping_type,

            "transition_score":
                strongest_transition[
                    "transition_score"
                ],
        }

    else:

        tipping_region = None

    return {
        "scenario_count":
            len(points),

        "first_escalation":
            first_escalation,

        "first_new_high":
            first_new_high,

        "first_moderate_trigger":
            first_moderate_trigger,

        "largest_escalation_jump":
            largest_escalation_jump,

        "largest_mean_risk_jump":
            largest_mean_risk_jump,

        "trigger_transitions":
            trigger_transitions,

        "candidate_tipping_regions":
            candidate_regions,

        "strongest_tipping_region":
            tipping_region,

        "points":
            points,

        "transitions":
            transitions,
    }

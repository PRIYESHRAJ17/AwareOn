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


def _trigger_rank(
    category: Any,
) -> int:
    return TRIGGER_RANK.get(
        str(category or "").upper(),
        -1,
    )


def _assessment(
    scenarios: list[dict[str, Any]],
) -> str:

    if not scenarios:
        return "NO_DATA"

    max_escalating = max(
        _int(
            item.get("escalating_cells")
        )
        for item in scenarios
    )

    max_new_high = max(
        _int(
            item.get("new_high_or_extreme")
        )
        for item in scenarios
    )

    trigger_categories = [
        str(
            item.get(
                "trigger_category"
            )
            or ""
        ).upper()
        for item in scenarios
    ]

    highest_trigger = max(
        trigger_categories,
        key=_trigger_rank,
        default="UNKNOWN",
    )

    worst_mean_change = max(
        _num(
            item.get(
                "mean_risk_change"
            )
        )
        for item in scenarios
    )

    if (
        highest_trigger == "EXTREME"
        or max_escalating >= 100
        or max_new_high >= 75
    ):
        return "SEVERE_ESCALATION"

    if (
        highest_trigger == "HIGH"
        or max_escalating >= 50
        or max_new_high >= 40
        or worst_mean_change >= 5
    ):
        return "HIGH_CONSEQUENCE"

    if (
        highest_trigger == "MODERATE"
        or max_escalating >= 20
        or max_new_high >= 15
        or worst_mean_change >= 2
    ):
        return "ELEVATED"

    return "LIMITED_CHANGE"


def compare_scenarios(
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:

    if not scenarios:
        raise ValueError(
            "Scenario comparison requires at least one scenario."
        )

    ordered = sorted(
        scenarios,
        key=lambda item: _num(
            item.get(
                "rainfall_change_percent"
            )
        ),
    )

    baseline = ordered[0]

    worst_mean = max(
        ordered,
        key=lambda item: _num(
            item.get(
                "mean_risk_score"
            )
        ),
    )

    worst_max = max(
        ordered,
        key=lambda item: _num(
            item.get(
                "max_risk_score"
            )
        ),
    )

    largest_mean_change = max(
        ordered,
        key=lambda item: _num(
            item.get(
                "mean_risk_change"
            )
        ),
    )

    largest_max_change = max(
        ordered,
        key=lambda item: _num(
            item.get(
                "max_risk_change"
            )
        ),
    )

    largest_escalation = max(
        ordered,
        key=lambda item: _int(
            item.get(
                "escalating_cells"
            )
        ),
    )

    largest_new_high = max(
        ordered,
        key=lambda item: _int(
            item.get(
                "new_high_or_extreme"
            )
        ),
    )

    largest_new_extreme = max(
        ordered,
        key=lambda item: _int(
            item.get(
                "new_extreme_cells"
            )
        ),
    )

    baseline_trigger = str(
        baseline.get(
            "trigger_category"
        )
        or ""
    ).upper()

    worst_trigger = max(
        ordered,
        key=lambda item: _trigger_rank(
            item.get(
                "trigger_category"
            )
        ),
    )

    highest_trigger = str(
        worst_trigger.get(
            "trigger_category"
        )
        or ""
    ).upper()

    trigger_delta = (
        _trigger_rank(highest_trigger)
        -
        _trigger_rank(baseline_trigger)
    )

    scenario_rows = []

    for item in ordered:

        rainfall = _num(
            item.get(
                "rainfall_change_percent"
            )
        )

        mean_change = _num(
            item.get(
                "mean_risk_change"
            )
        )

        max_change = _num(
            item.get(
                "max_risk_change"
            )
        )

        escalating = _int(
            item.get(
                "escalating_cells"
            )
        )

        new_high = _int(
            item.get(
                "new_high_or_extreme"
            )
        )

        new_extreme = _int(
            item.get(
                "new_extreme_cells"
            )
        )

        scenario_rows.append(
            {
                "scenario": item.get(
                    "scenario"
                ),

                "rainfall_change_percent":
                    rainfall,

                "mean_risk_score":
                    _num(
                        item.get(
                            "mean_risk_score"
                        )
                    ),

                "mean_risk_change":
                    mean_change,

                "max_risk_score":
                    _num(
                        item.get(
                            "max_risk_score"
                        )
                    ),

                "max_risk_change":
                    max_change,

                "escalating_cells":
                    escalating,

                "new_high_or_extreme":
                    new_high,

                "new_extreme_cells":
                    new_extreme,

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

                "trigger_score_change_from_baseline":
                    _num(
                        item.get(
                            "trigger_score_change_from_baseline"
                        )
                    ),
            }
        )

    overall_assessment = _assessment(
        ordered
    )

    return {
        "scenario_count":
            len(ordered),

        "baseline":
            scenario_rows[0],

        "worst_mean_risk":
            {
                "scenario":
                    worst_mean.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    _num(
                        worst_mean.get(
                            "rainfall_change_percent"
                        )
                    ),

                "mean_risk_score":
                    _num(
                        worst_mean.get(
                            "mean_risk_score"
                        )
                    ),

                "mean_risk_change":
                    _num(
                        worst_mean.get(
                            "mean_risk_change"
                        )
                    ),
            },

        "worst_max_risk":
            {
                "scenario":
                    worst_max.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    _num(
                        worst_max.get(
                            "rainfall_change_percent"
                        )
                    ),

                "max_risk_score":
                    _num(
                        worst_max.get(
                            "max_risk_score"
                        )
                    ),

                "max_risk_change":
                    _num(
                        worst_max.get(
                            "max_risk_change"
                        )
                    ),
            },

        "largest_mean_change":
            {
                "scenario":
                    largest_mean_change.get(
                        "scenario"
                    ),

                "value":
                    _num(
                        largest_mean_change.get(
                            "mean_risk_change"
                        )
                    ),
            },
        "largest_max_change":
            {
                "scenario":
                    largest_max_change.get(
                        "scenario"
                    ),

                "value":
                    _num(
                        largest_max_change.get(
                            "max_risk_change"
                        )
                    ),
            },

        "largest_escalation":
            {
                "scenario":
                    largest_escalation.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    _num(
                        largest_escalation.get(
                            "rainfall_change_percent"
                        )
                    ),

                "escalating_cells":
                    _int(
                        largest_escalation.get(
                            "escalating_cells"
                        )
                    ),
            },

        "largest_new_high_or_extreme":
            {
                "scenario":
                    largest_new_high.get(
                        "scenario"
                    ),

                "new_high_or_extreme":
                    _int(
                        largest_new_high.get(
                            "new_high_or_extreme"
                        )
                    ),
            },

        "largest_new_extreme":
            {
                "scenario":
                    largest_new_extreme.get(
                        "scenario"
                    ),

                "new_extreme_cells":
                    _int(
                        largest_new_extreme.get(
                            "new_extreme_cells"
                        )
                    ),
            },

        "trigger_progression":
            [
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

                    "trigger_category":
                        str(
                            item.get(
                                "trigger_category"
                            )
                            or ""
                        ).upper(),

                    "trigger_score":
                        _num(
                            item.get(
                                "rainfall_trigger_score"
                            )
                        ),
                }
                for item in ordered
            ],

        "trigger_shift":
            {
                "baseline":
                    baseline_trigger,

                "worst_case":
                    highest_trigger,

                "rank_change":
                    trigger_delta,
            },

        "overall_assessment":
            overall_assessment,

        "scenarios":
            scenario_rows,
    }

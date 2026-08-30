from __future__ import annotations

from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    return number


def _transition_text(
    baseline_category: str,
    scenario_category: str,
) -> str:
    baseline = str(
        baseline_category or "UNKNOWN"
    ).upper()

    scenario = str(
        scenario_category or "UNKNOWN"
    ).upper()

    if baseline == scenario:
        return scenario

    return f"{baseline} → {scenario}"


def _interpret_cell(
    baseline_category: str,
    worst_category: str,
    max_change: float,
    worst_rainfall: float,
    escalates: bool,
) -> str:
    baseline = str(
        baseline_category or "UNKNOWN"
    ).upper()

    worst = str(
        worst_category or "UNKNOWN"
    ).upper()

    if escalates:
        if worst == "EXTREME":
            return (
                "Scenario escalation reaches EXTREME "
                f"risk under +{worst_rainfall:.0f}% rainfall."
            )

        return (
            "Scenario escalation occurs, with risk moving "
            f"from {baseline} to {worst} under "
            f"+{worst_rainfall:.0f}% rainfall."
        )

    if max_change >= 5.0:
        return (
            f"Risk increases by {max_change:.2f} points "
            f"under +{worst_rainfall:.0f}% rainfall but "
            f"remains {worst}."
        )

    if max_change >= 2.0:
        return (
            f"Risk shows a moderate increase of "
            f"{max_change:.2f} points under "
            f"+{worst_rainfall:.0f}% rainfall without "
            "category escalation."
        )

    return (
        "Risk remains broadly stable across the tested "
        "rainfall scenarios, with a maximum increase of "
        f"{max_change:.2f} points."
    )


def analyze_cell_scenarios(
    cell_id: str,
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:

    if not scenarios:
        raise ValueError(
            "At least one scenario is required."
        )

    normalized: list[dict[str, Any]] = []

    for scenario in scenarios:

        rainfall_change = _num(
            scenario.get(
                "rainfall_change_percent"
            )
        )

        risk_score = _num(
            scenario.get(
                "risk_score"
            )
        )

        baseline_risk = _num(
            scenario.get(
                "baseline_risk_score"
            ),
            risk_score,
        )

        risk_change = _num(
            scenario.get(
                "risk_score_change"
            ),
            risk_score - baseline_risk,
        )

        baseline_category = str(
            scenario.get(
                "baseline_category"
            )
            or ""
        ).upper()

        risk_category = str(
            scenario.get(
                "risk_category"
            )
            or ""
        ).upper()

        category_change = int(
            _num(
                scenario.get(
                    "category_change"
                )
            )
        )

        escalates = bool(
            int(
                _num(
                    scenario.get(
                        "escalates"
                    )
                )
            )
        )

        relative_change = (
            (risk_change / baseline_risk) * 100.0
            if baseline_risk != 0
            else 0.0
        )

        normalized.append(
            {
                "scenario": scenario.get(
                    "scenario"
                ),
                "rainfall_change_percent": rainfall_change,
                "risk_score": risk_score,
                "baseline_risk_score": baseline_risk,
                "risk_score_change": risk_change,
                "relative_risk_change_percent": relative_change,
                "risk_category": risk_category,
                "baseline_category": baseline_category,
                "category_change": category_change,
                "escalates": escalates,
                "transition": _transition_text(
                    baseline_category,
                    risk_category,
                ),
            }
        )

    baseline = min(
        normalized,
        key=lambda item: abs(
            item[
                "rainfall_change_percent"
            ]
        ),
    )

    worst_case = max(
        normalized,
        key=lambda item: item[
            "risk_score"
        ],
    )

    maximum_change = max(
        normalized,
        key=lambda item: item[
            "risk_score_change"
        ],
    )

    highest_category = max(
        normalized,
        key=lambda item: CATEGORY_RANK.get(
            item[
                "risk_category"
            ],
            -1,
        ),
    )

    escalation_scenarios = [
        item
        for item in normalized
        if item["escalates"]
    ]

    interpretation = _interpret_cell(
        baseline_category=baseline[
            "risk_category"
        ],
        worst_category=highest_category[
            "risk_category"
        ],
        max_change=maximum_change[
            "risk_score_change"
        ],
        worst_rainfall=worst_case[
            "rainfall_change_percent"
        ],
        escalates=bool(
            escalation_scenarios
        ),
    )

    sensitivity = (
        maximum_change[
            "risk_score_change"
        ]
        /
        max(
            1.0,
            abs(
                maximum_change[
                    "rainfall_change_percent"
                ]
            ),
        )
    )

    return {
        "cell_id": cell_id,
        "scenario_count": len(
            normalized
        ),

        "baseline": baseline,

        "worst_case": worst_case,

        "maximum_change": maximum_change,

        "highest_category": highest_category[
            "risk_category"
        ],

        "escalation_count": len(
            escalation_scenarios
        ),

        "escalates": bool(
            escalation_scenarios
        ),

        "category_transition": _transition_text(
            baseline[
                "risk_category"
            ],
            highest_category[
                "risk_category"
            ],
        ),

        "max_risk_change": maximum_change[
            "risk_score_change"
        ],

        "max_relative_risk_change_percent":
            maximum_change[
                "relative_risk_change_percent"
            ],

        "scenario_sensitivity": sensitivity,

        "interpretation": interpretation,

        "scenarios": normalized,
    }


def analyze_scenario_summary(
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:

    if not scenarios:
        raise ValueError(
            "Scenario summary cannot be empty."
        )

    baseline = min(
        scenarios,
        key=lambda item: abs(
            _num(
                item.get(
                    "rainfall_change_percent"
                )
            )
        ),
    )

    worst_mean = max(
        scenarios,
        key=lambda item: _num(
            item.get(
                "mean_risk_score"
            )
        ),
    )

    worst_max = max(
        scenarios,
        key=lambda item: _num(
            item.get(
                "max_risk_score"
            )
        ),
    )

    highest_escalation = max(
        scenarios,
        key=lambda item: int(
            _num(
                item.get(
                    "escalating_cells"
                )
            )
        ),
    )

    highest_new_high = max(
        scenarios,
        key=lambda item: int(
            _num(
                item.get(
                    "new_high_or_extreme"
                )
            )
        ),
    )

    return {
        "scenario_count": len(
            scenarios
        ),

        "baseline_scenario": baseline.get(
            "scenario"
        ),

        "worst_mean_risk_scenario":
            worst_mean.get(
                "scenario"
            ),

        "worst_mean_risk": _num(
            worst_mean.get(
                "mean_risk_score"
            )
        ),

        "worst_max_risk_scenario":
            worst_max.get(
                "scenario"
            ),

        "worst_max_risk": _num(
            worst_max.get(
                "max_risk_score"
            )
        ),

        "highest_escalation_scenario":
            highest_escalation.get(
                "scenario"
            ),

        "highest_escalating_cells":
            int(
                _num(
                    highest_escalation.get(
                        "escalating_cells"
                    )
                )
            ),

        "highest_new_high_or_extreme_scenario":
            highest_new_high.get(
                "scenario"
            ),

        "highest_new_high_or_extreme":
            int(
                _num(
                    highest_new_high.get(
                        "new_high_or_extreme"
                    )
                )
            ),
    }

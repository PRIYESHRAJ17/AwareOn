from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank(category: Any) -> int:
    ranks = {
        "LOW": 0,
        "MODERATE": 1,
        "HIGH": 2,
        "EXTREME": 3,
    }
    return ranks.get(
        str(category or "").upper(),
        0,
    )


def _scenario_points(records: list[dict[str, Any]]) -> list[float]:
    points = set()

    for record in records:
        points.add(
            _num(
                record.get(
                    "rainfall_change_percent"
                )
            )
        )

    return sorted(points)


def summarize_cluster_state(
    records: list[dict[str, Any]]
) -> dict[str, Any]:

    if not records:
        return {
            "rainfall_change_percent": 0.0,
            "cell_count": 0,
            "high_or_above": 0,
            "extreme": 0,
            "mean_risk": 0.0,
            "max_risk": 0.0,
            "mean_change": 0.0,
        }

    high_count = 0
    extreme_count = 0
    risk_values = []
    change_values = []

    for record in records:
        category = record.get(
            "risk_category"
        )

        rank = _rank(category)

        if rank >= 2:
            high_count += 1

        if rank >= 3:
            extreme_count += 1

        risk_values.append(
            _num(
                record.get(
                    "risk_score"
                )
            )
        )

        change_values.append(
            _num(
                record.get(
                    "risk_score_change"
                )
            )
        )

    mean_risk = (
        sum(risk_values)
        /
        len(risk_values)
    )

    max_risk = max(
        risk_values
    )

    mean_change = (
        sum(change_values)
        /
        len(change_values)
    )

    rainfall = _num(
        records[0].get(
            "rainfall_change_percent"
        )
    )

    return {
        "rainfall_change_percent": rainfall,
        "cell_count": len(records),
        "high_or_above": high_count,
        "extreme": extreme_count,
        "mean_risk": mean_risk,
        "max_risk": max_risk,
        "mean_change": mean_change,
    }


def analyze_cluster_evolution(
    records: list[dict[str, Any]]
) -> dict[str, Any]:

    if not isinstance(
        records,
        list,
    ):
        raise ValueError(
            "records must be a list."
        )

    if not records:
        raise ValueError(
            "No scenario records supplied."
        )

    rainfall_points = _scenario_points(
        records
    )

    states = []

    for rainfall in rainfall_points:

        scenario_records = []

        for record in records:

            record_rainfall = _num(
                record.get(
                    "rainfall_change_percent"
                )
            )

            if record_rainfall == rainfall:
                scenario_records.append(
                    record
                )

        states.append(
            summarize_cluster_state(
                scenario_records
            )
        )
    if len(states) < 2:

        baseline = (
            states[0]
            if states
            else None
        )


        return {
            "trajectory": "INSUFFICIENT_POINTS",
            "cluster_behavior": "INSUFFICIENT_POINTS",
            "scenario_count": len(states),
            "states": states,
            "baseline": baseline,
            "worst_tested": baseline,
            "peak_cluster_state": baseline,
            "mean_risk_delta": 0.0,
            "high_cell_delta": 0,
            "extreme_cell_delta": 0,
            "transition_points": [],
            "transition_count": 0,
        }

    baseline = states[0]
    worst = states[-1]

    mean_risk_delta = (
        worst["mean_risk"]
        -
        baseline["mean_risk"]
    )

    high_cell_delta = (
        worst["high_or_above"]
        -
        baseline["high_or_above"]
    )

    extreme_cell_delta = (
        worst["extreme"]
        -
        baseline["extreme"]
    )

    transition_points = []

    for index in range(
        1,
        len(states),
    ):

        previous = states[index - 1]
        current = states[index]

        mean_delta = (
            current["mean_risk"]
            -
            previous["mean_risk"]
        )

        high_delta = (
            current["high_or_above"]
            -
            previous["high_or_above"]
        )

        extreme_delta = (
            current["extreme"]
            -
            previous["extreme"]
        )

        if (
            mean_delta != 0
            or
            high_delta != 0
            or
            extreme_delta != 0
        ):

            transition_points.append(
                {
                    "from_rainfall":
                        previous[
                            "rainfall_change_percent"
                        ],

                    "to_rainfall":
                        current[
                            "rainfall_change_percent"
                        ],

                    "mean_risk_delta":
                        mean_delta,

                    "high_cell_delta":
                        high_delta,

                    "extreme_cell_delta":
                        extreme_delta,
                }
            )

    if (
        states[-1]["mean_change"]
        >
        states[0]["mean_change"]
    ):

        trajectory = "ACCELERATING"

    elif (
        states[-1]["mean_change"]
        <
        states[0]["mean_change"]
    ):

        trajectory = "DECELERATING"

    elif mean_risk_delta > 0:

        trajectory = "INCREASING"

    elif mean_risk_delta < 0:

        trajectory = "DECREASING"

    else:

        trajectory = "STABLE"

    if (
        high_cell_delta > 0
        or
        extreme_cell_delta > 0
    ):

        cluster_behavior = "EXPANDING_RISK"

    elif mean_risk_delta > 0:

        cluster_behavior = (
            "INTENSIFYING_WITHOUT_CATEGORY_GROWTH"
        )

    elif mean_risk_delta < 0:

        cluster_behavior = "WEAKENING"

    else:

        cluster_behavior = "STABLE_CLUSTER"

    peak_cluster_state = max(
        states,
        key=lambda state: (
            state["extreme"],
            state["high_or_above"],
            state["mean_risk"],
        ),
    )

    return {
        "trajectory": trajectory,
        "cluster_behavior": cluster_behavior,
        "scenario_count": len(states),
        "states": states,
        "baseline": baseline,
        "worst_tested": worst,
        "peak_cluster_state": peak_cluster_state,
        "mean_risk_delta": mean_risk_delta,
        "high_cell_delta": high_cell_delta,
        "extreme_cell_delta": extreme_cell_delta,
        "transition_points": transition_points,
        "transition_count": len(
            transition_points
        ),
    }

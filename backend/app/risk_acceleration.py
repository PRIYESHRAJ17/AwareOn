from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_mean_risk(item: dict[str, Any]) -> float:
    if "mean_risk" in item:
        return _num(item["mean_risk"])

    if "mean_risk_score" in item:
        return _num(item["mean_risk_score"])

    return 0.0


def analyze_risk_acceleration(
    scenario_states: list[dict[str, Any]],
) -> dict[str, Any]:

    if not isinstance(
        scenario_states,
        list,
    ):
        raise ValueError(
            "scenario_states must be a list."
        )

    if len(scenario_states) < 2:
        return {
            "status": "INSUFFICIENT_POINTS",
            "state": "UNKNOWN",
            "mean_risk_rate": 0.0,
            "acceleration": 0.0,
            "transitions": [],
        }

    states = sorted(
        scenario_states,
        key=lambda item: _num(
            item.get(
                "rainfall_change_percent"
            )
        ),
    )

    rates: list[float] = []
    transitions: list[dict[str, Any]] = []

    for index in range(
        1,
        len(states),
    ):

        previous = states[index - 1]
        current = states[index]

        previous_rainfall = _num(
            previous.get(
                "rainfall_change_percent"
            )
        )

        current_rainfall = _num(
            current.get(
                "rainfall_change_percent"
            )
        )

        previous_risk = _get_mean_risk(
            previous
        )

        current_risk = _get_mean_risk(
            current
        )

        rainfall_delta = (
            current_rainfall
            -
            previous_rainfall
        )

        risk_delta = (
            current_risk
            -
            previous_risk
        )

        if rainfall_delta == 0:
            rate = 0.0
        else:
            rate = (
                risk_delta
                /
                rainfall_delta
            )

        rates.append(rate)

        transitions.append(
            {
                "from_rainfall":
                    previous_rainfall,
                "to_rainfall":
                    current_rainfall,
                "from_mean_risk":
                    previous_risk,
                "to_mean_risk":
                    current_risk,
                "risk_delta":
                    risk_delta,
                "risk_rate":
                    rate,
            }
        )

    mean_rate = (
        sum(rates)
        /
        len(rates)
    )

    acceleration = (
        rates[-1]
        -
        rates[0]
    )

    if acceleration > 0.005:
        state = "ACCELERATING"

    elif acceleration < -0.005:
        state = "DECELERATING"

    else:
        state = "STEADY"

    return {
        "status": "READY",
        "state": state,
        "mean_risk_rate": mean_rate,
        "acceleration": acceleration,
        "transitions": transitions,
    }

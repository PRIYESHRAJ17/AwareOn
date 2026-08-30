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


def _build_supported_statements(
    curve: dict[str, Any],
    thresholds: dict[str, Any],
    forecast: dict[str, Any],
) -> list[str]:

    statements: list[str] = []

    points = curve.get(
        "points",
        [],
    )

    if points:
        rainfall_values = [
            _num(
                point.get(
                    "rainfall_change_percent"
                )
            )
            for point in points
        ]

        statements.append(
            "The analysis is based on "
            f"{len(points)} evaluated rainfall scenarios "
            f"spanning {min(rainfall_values):.0f}% to "
            f"{max(rainfall_values):.0f}% change."
        )

    first_escalation = thresholds.get(
        "first_escalation"
    )

    if first_escalation:

        statements.append(
            "Category escalation is first observed at "
            f"+{_num(first_escalation.get('rainfall_change_percent')):.0f}% "
            "rainfall."
        )

    region = thresholds.get(
        "strongest_tipping_region"
    )

    if region:

        statements.append(
            "The strongest detected transition region spans "
            f"+{_num(region.get('lower_bound_percent')):.0f}% to "
            f"+{_num(region.get('upper_bound_percent')):.0f}% rainfall."
        )

    worst = forecast.get(
        "worst_tested_scenario"
    )

    if worst:

        statements.append(
            "The highest evaluated scenario is "
            f"+{_num(worst.get('rainfall_change_percent')):.0f}% rainfall."
        )

    return statements


def _build_boundaries(
    curve: dict[str, Any],
) -> list[str]:

    points = curve.get(
        "points",
        [],
    )

    boundaries: list[str] = []

    if not points:
        return boundaries

    rainfall_values = [
        _num(
            point.get(
                "rainfall_change_percent"
            )
        )
        for point in points
    ]

    minimum = min(
        rainfall_values
    )

    maximum = max(
        rainfall_values
    )

    boundaries.append(
        f"Rainfall changes below +{minimum:.0f}% "
        "are outside the lower tested range."
    )

    boundaries.append(
        f"Rainfall changes above +{maximum:.0f}% "
        "are outside the upper tested range."
    )

    boundaries.append(
        "Exact behavior between tested scenarios "
        "is not directly simulated by the current dataset."
    )

    boundaries.append(
        "The detected transition region should not be "
        "interpreted as an exact physical tipping point."
    )

    return boundaries


def _uncertainty_level(
    scenario_count: int,
    has_transition: bool,
) -> str:

    if (
        scenario_count >= 4
        and has_transition
    ):
        return "MODERATE"

    if scenario_count >= 3:
        return "MODERATE"

    return "HIGH"


def build_scenario_uncertainty(
    curve: dict[str, Any],
    thresholds: dict[str, Any],
    forecast: dict[str, Any],
) -> dict[str, Any]:

    if not curve:
        raise ValueError(
            "Scenario curve data is required."
        )

    if not thresholds:
        raise ValueError(
            "Scenario threshold data is required."
        )

    if not forecast:
        raise ValueError(
            "Scenario forecast data is required."
        )

    points = curve.get(
        "points",
        [],
    )

    transition = thresholds.get(
        "strongest_tipping_region"
    )

    uncertainty_level = _uncertainty_level(
        len(points),
        transition is not None,
    )

    supported = _build_supported_statements(
        curve,
        thresholds,
        forecast,
    )

    boundaries = _build_boundaries(
        curve
    )

    inferred = [
        "Risk response direction is inferred from "
        "the evaluated scenario sequence.",

        "The transition region is derived from changes "
        "in trigger and escalation behavior.",

        "The trajectory classification is an analytical "
        "interpretation of the tested scenarios.",
    ]

    not_supported = [
        "An exact continuous rainfall tipping point.",

        "Scenario outcomes at untested rainfall values.",

        "Behavior beyond the highest tested scenario.",

        "A guaranteed real-world future outcome.",
    ]

    return {
        "uncertainty_level":
            uncertainty_level,

        "scenario_count":
            len(points),

        "supported_evidence":
            supported,

        "derived_inferences":
            inferred,

        "unsupported_claims":
            not_supported,

        "boundaries":
            boundaries,

        "transition_region":
            (
                {
                    "lower_bound_percent":
                        transition.get(
                            "lower_bound_percent"
                        ),

                    "upper_bound_percent":
                        transition.get(
                            "upper_bound_percent"
                        ),

                    "type":
                        transition.get(
                            "type"
                        ),

                    "score":
                        transition.get(
                            "transition_score"
                        ),
                }
                if transition
                else None
            ),

        "highest_tested_rainfall_percent":
            max(
                (
                    _num(
                        point.get(
                            "rainfall_change_percent"
                        )
                    )
                    for point in points
                ),
                default=0.0,
            ),

        "lowest_tested_rainfall_percent":
            min(
                (
                    _num(
                        point.get(
                            "rainfall_change_percent"
                        )
                    )
                    for point in points
                ),
                default=0.0,
            ),
    }

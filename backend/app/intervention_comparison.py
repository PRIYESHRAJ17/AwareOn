from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _delta(a: float, b: float) -> float:
    return a - b


def compare_intervention_options(
    options: list[dict[str, Any]],
    recommended_option: str,
) -> dict[str, Any]:

    if not isinstance(options, list):
        raise ValueError("options must be a list.")

    if not options:
        raise ValueError("options cannot be empty.")

    recommended = None

    for option in options:
        if (
            str(option.get("option") or "")
            == recommended_option
        ):
            recommended = option
            break

    if recommended is None:
        raise ValueError(
            "recommended_option was not found."
        )

    comparisons = []

    rec_score = _num(
        recommended.get(
            "optimization_score"
        )
    )

    rec_effort = _num(
        recommended.get(
            "effort"
        )
    )

    rec_coverage = _num(
        recommended.get(
            "coverage"
        )
    )

    rec_speed = _num(
        recommended.get(
            "speed"
        )
    )

    rec_protection = _num(
        recommended.get(
            "protection"
        )
    )

    for option in options:

        name = str(
            option.get("option")
            or "UNKNOWN"
        )

        score = _num(
            option.get(
                "optimization_score"
            )
        )

        effort = _num(
            option.get("effort")
        )

        coverage = _num(
            option.get("coverage")
        )

        speed = _num(
            option.get("speed")
        )

        protection = _num(
            option.get("protection")
        )

        comparison_to_recommended = {
            "score_delta":
                round(
                    _delta(
                        score,
                        rec_score,
                    ),
                    2,
                ),

            "effort_delta":
                round(
                    _delta(
                        effort,
                        rec_effort,
                    ),
                    2,
                ),

            "coverage_delta":
                round(
                    _delta(
                        coverage,
                        rec_coverage,
                    ),
                    2,
                ),

            "speed_delta":
                round(
                    _delta(
                        speed,
                        rec_speed,
                    ),
                    2,
                ),

            "protection_delta":
                round(
                    _delta(
                        protection,
                        rec_protection,
                    ),
                    2,
                ),
        }

        strengths = []

        if speed > rec_speed:
            strengths.append(
                "FASTER_RESPONSE"
            )

        if protection > rec_protection:
            strengths.append(
                "STRONGER_PROTECTION"
            )

        if coverage > rec_coverage:
            strengths.append(
                "BROADER_COVERAGE"
            )

        if effort < rec_effort:
            strengths.append(
                "LOWER_EFFORT"
            )

        if not strengths:
            strengths.append(
                "NO_CLEAR_ADVANTAGE"
            )

        comparisons.append(
            {
                "option":
                    name,

                "score":
                    score,

                "priority":
                    option.get(
                        "priority"
                    ),

                "strengths":
                    strengths,

                "comparison_to_recommended":
                    comparison_to_recommended,
            }
        )

    comparisons.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    alternative_notes = []

    for item in comparisons:

        if item["option"] == recommended_option:
            continue

        score_gap = _num(
            item[
                "comparison_to_recommended"
            ].get(
                "score_delta"
            )
        )

        effort_gap = _num(
            item[
                "comparison_to_recommended"
            ].get(
                "effort_delta"
            )
        )

        protection_gap = _num(
            item[
                "comparison_to_recommended"
            ].get(
                "protection_delta"
            )
        )

        if protection_gap > 0:
            note = (
                f"{item['option']} provides stronger "
                "protection than the recommended option"
            )

        elif effort_gap < 0:
            note = (
                f"{item['option']} requires less effort "
                "than the recommended option"
            )

        else:
            note = (
                f"{item['option']} scores "
                f"{abs(score_gap):.2f} points "
                "below the recommended option"
            )

        alternative_notes.append(
            note
        )

    recommendation = (
        f"{recommended_option} remains the preferred "
        "intervention because it has the highest "
        f"optimization score of {rec_score:.2f}."
    )

    if alternative_notes:
        recommendation += (
            " Alternatives provide different trade-offs: "
            +
            "; ".join(
                alternative_notes
            )
            +
            "."
        )

    return {
        "engine":
            "AWAREON_INTERVENTION_COMPARISON",

        "version":
            "1.0",

        "status":
            "READY",

        "recommended_option":
            recommended_option,

        "recommended_score":
            rec_score,

        "comparison_count":
            len(comparisons),

        "comparisons":
            comparisons,

        "recommendation":
            recommendation,
    }

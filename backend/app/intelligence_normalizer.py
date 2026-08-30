from __future__ import annotations

from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "NORMAL": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "VERY_HIGH": 3,
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


def _category(
    value: Any,
) -> str:
    return str(
        value or "UNKNOWN"
    ).upper()


def _rank(
    category: str,
) -> int:
    return CATEGORY_RANK.get(
        _category(category),
        0,
    )


def _clamp(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


def normalize_probability(
    value: Any,
) -> float:
    number = _num(value)

    if 0.0 <= number <= 1.0:
        number *= 100.0

    return round(
        _clamp(number),
        4,
    )


def normalize_score(
    value: Any,
) -> float:
    return round(
        _clamp(
            _num(value)
        ),
        4,
    )


def normalize_category(
    category: Any,
) -> dict[str, Any]:

    normalized = _category(
        category
    )

    return {
        "category":
            normalized,

        "rank":
            _rank(
                normalized
            ),

        "is_elevated":
            _rank(
                normalized
            ) >= 1,

        "is_high_or_above":
            _rank(
                normalized
            ) >= 2,

        "is_extreme":
            _rank(
                normalized
            ) >= 3,
    }


def normalize_engine_output(
    engine_name: str,
    score: Any = None,
    category: Any = None,
    probability: Any = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:

    result: dict[str, Any] = {
        "engine":
            str(
                engine_name
            ),

        "score":
            None,

        "probability_percent":
            None,

        "category":
            None,

        "category_rank":
            None,

        "flags": {
            "elevated":
                False,

            "high_or_above":
                False,

            "extreme":
                False,
        },

        "metadata":
            dict(
                metadata or {}
            ),
    }

    if score is not None:
        result["score"] = normalize_score(
            score
        )

    if probability is not None:
        result[
            "probability_percent"
        ] = normalize_probability(
            probability
        )

    if category is not None:

        normalized_category = (
            normalize_category(
                category
            )
        )

        result["category"] = (
            normalized_category[
                "category"
            ]
        )

        result["category_rank"] = (
            normalized_category[
                "rank"
            ]
        )

        result["flags"] = {
            "elevated":
                normalized_category[
                    "is_elevated"
                ],

            "high_or_above":
                normalized_category[
                    "is_high_or_above"
                ],

            "extreme":
                normalized_category[
                    "is_extreme"
                ],
        }

    return result


def normalize_assessment(
    assessment: dict[str, Any],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError(
            "Assessment is required."
        )

    engines = [
        normalize_engine_output(
            "susceptibility",
            probability=assessment.get(
                "susceptibility_probability"
            ),
            category=assessment.get(
                "susceptibility_category"
            ),
        ),
        normalize_engine_output(
            "terrain_instability",
            score=assessment.get(
                "terrain_instability_score"
            ),
            category=assessment.get(
                "terrain_instability_category"
            ),
        ),
        normalize_engine_output(
            "exposure",
            score=assessment.get(
                "exposure_score"
            ),
            category=assessment.get(
                "exposure_category"
            ),
        ),
        normalize_engine_output(
            "spatial_pressure",
            score=assessment.get(
                "spatial_pressure_score"
            ),
            category=assessment.get(
                "spatial_category"
            ),
        ),
        normalize_engine_output(
            "rainfall_trigger",
            score=assessment.get(
                "rainfall_trigger_score"
            ),
            category=assessment.get(
                "rainfall_trigger_category"
            ),
        ),
        normalize_engine_output(
            "soil_wetness",
            score=assessment.get(
                "soil_wetness_score"
            ),
            category=assessment.get(
                "soil_wetness_category"
            ),
        ),
        normalize_engine_output(
            "temporal",
            category=assessment.get(
                "temporal_category"
            ),
            metadata={
                "trajectory":
                    assessment.get(
                        "temporal_trajectory"
                    )
            },
        ),
        normalize_engine_output(
            "environment_anomaly",
            score=assessment.get(
                "environment_anomaly_score"
            ),
            category=assessment.get(
                "environment_anomaly_category"
            ),
        ),
    ]

    elevated = [
        item
        for item in engines
        if item["flags"]["elevated"]
    ]

    high_or_above = [
        item
        for item in engines
        if item["flags"]["high_or_above"]
    ]

    extreme = [
        item
        for item in engines
        if item["flags"]["extreme"]
    ]

    scores = [
        item["score"]
        for item in engines
        if item["score"] is not None
    ]

    mean_score = (
        sum(scores) / len(scores)
        if scores
        else 0.0
    )

    return {
        "cell_id":
            assessment.get(
                "cell_id"
            ),

        "unified_risk_score":
            normalize_score(
                assessment.get(
                    "unified_risk_score"
                )
            ),

        "severity":
            _category(
                assessment.get(
                    "severity"
                )
            ),

        "warning_state":
            _category(
                assessment.get(
                    "warning_state"
                )
            ),

        "engines":
            engines,

        "engine_count":
            len(engines),

        "elevated_engine_count":
            len(elevated),

        "high_or_above_engine_count":
            len(high_or_above),

        "extreme_engine_count":
            len(extreme),

        "mean_engine_score":
            round(
                mean_score,
                4,
            ),

        "confidence_score":
            normalize_score(
                assessment.get(
                    "confidence_score"
                )
            ),

        "uncertainty_score":
            normalize_score(
                assessment.get(
                    "uncertainty_score"
                )
            ),
    }

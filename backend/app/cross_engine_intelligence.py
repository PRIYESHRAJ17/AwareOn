from __future__ import annotations

from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
    "VERY_HIGH": 3,
    "NORMAL": 0,
    "STABLE_LOW": 0,
}


ENGINE_FIELDS = {
    "susceptibility": (
        "susceptibility_probability",
        "susceptibility_category",
    ),
    "terrain_instability": (
        "terrain_instability_score",
        "terrain_instability_category",
    ),
    "exposure": (
        "exposure_score",
        "exposure_category",
    ),
    "spatial_pressure": (
        "spatial_pressure_score",
        "spatial_category",
    ),
    "rainfall_trigger": (
        "rainfall_trigger_score",
        "rainfall_trigger_category",
    ),
    "soil_wetness": (
        "soil_wetness_score",
        "soil_wetness_category",
    ),
    "temporal": (
        None,
        "temporal_category",
    ),
    "environment_anomaly": (
        "environment_anomaly_score",
        "environment_anomaly_category",
    ),
    "confidence": (
        "confidence_score",
        "confidence_category",
    ),
}


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category_rank(
    value: Any,
) -> int:
    return CATEGORY_RANK.get(
        str(value or "").upper(),
        0,
    )


def _category(
    value: Any,
) -> str:
    return str(
        value or "UNKNOWN"
    ).upper()


def _normalize_score(
    value: Any,
) -> float:
    return max(
        0.0,
        min(
            100.0,
            _num(value),
        ),
    )


def _engine_state(
    name: str,
    score_field: str | None,
    category_field: str,
    assessment: dict[str, Any],
) -> dict[str, Any]:

    score = None

    if score_field:
        raw = assessment.get(
            score_field
        )

        if raw is not None:
            score = _normalize_score(
                raw
            )

    category = _category(
        assessment.get(
            category_field
        )
    )

    return {
        "engine": name,
        "score": score,
        "category": category,
        "category_rank": _category_rank(
            category
        ),
    }


def build_cross_engine_intelligence(
    assessment: dict[str, Any],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError(
            "Assessment data is required."
        )

    cell_id = assessment.get(
        "cell_id"
    )

    if not cell_id:
        raise ValueError(
            "Assessment must contain cell_id."
        )

    engines: list[dict[str, Any]] = []

    for name, fields in ENGINE_FIELDS.items():

        score_field, category_field = fields

        engines.append(
            _engine_state(
                name=name,
                score_field=score_field,
                category_field=category_field,
                assessment=assessment,
            )
        )

    actionable_engines = [
        item
        for item in engines
        if item["engine"]
        not in {
            "confidence",
        }
    ]

    ranked_engines = sorted(
        [
            item
            for item in actionable_engines
            if item["score"] is not None
        ],
        key=lambda item: (
            item["score"],
            item["category_rank"],
        ),
        reverse=True,
    )

    dominant_drivers = []

    for item in ranked_engines[:3]:

        dominant_drivers.append(
            {
                "engine":
                    item["engine"],

                "score":
                    item["score"],

                "category":
                    item["category"],
            }
        )

    severe_engines = [
        item
        for item in actionable_engines
        if item["category_rank"] >= 2
    ]

    low_engines = [
        item
        for item in actionable_engines
        if item["category_rank"] == 0
    ]

    extreme_engines = [
        item
        for item in actionable_engines
        if item["category_rank"] >= 3
    ]

    category_ranks = [
        item["category_rank"]
        for item in actionable_engines
    ]

    if category_ranks:
        agreement_span = (
            max(category_ranks)
            -
            min(category_ranks)
        )
    else:
        agreement_span = 0

    if agreement_span == 0:
        evidence_pattern = "CONSENSUS"

    elif agreement_span == 1:
        evidence_pattern = "BROAD_ALIGNMENT"

    elif agreement_span == 2:
        evidence_pattern = "MIXED_SIGNAL"

    else:
        evidence_pattern = "STRONG_DIVERGENCE"

    current_risk = _normalize_score(
        assessment.get(
            "unified_risk_score"
        )
    )

    confidence = _normalize_score(
        assessment.get(
            "confidence_score"
        )
    )

    uncertainty = _normalize_score(
        assessment.get(
            "uncertainty_score"
        )
    )

    high_confidence = (
        confidence >= 75.0
    )

    if (
        current_risk >= 75.0
        and high_confidence
        and len(extreme_engines) >= 2
    ):
        evidence_strength = "VERY_STRONG"

    elif (
        current_risk >= 50.0
        and high_confidence
        and len(severe_engines) >= 2
    ):
        evidence_strength = "STRONG"

    elif len(severe_engines) >= 1:
        evidence_strength = "MODERATE"

    else:
        evidence_strength = "LIMITED"

    warning_state = _category(
        assessment.get(
            "warning_state"
        )
    )

    severity = _category(
        assessment.get(
            "severity"
        )
    )

    rainfall_category = _category(
        assessment.get(
            "rainfall_trigger_category"
        )
    )

    soil_category = _category(
        assessment.get(
            "soil_wetness_category"
        )
    )

    temporal_category = _category(
        assessment.get(
            "temporal_category"
        )
    )

    static_structural_support = [
        "susceptibility",
        "terrain_instability",
        "spatial_pressure",
    ]

    dynamic_signals = [
        "rainfall_trigger",
        "soil_wetness",
        "temporal",
        "environment_anomaly",
    ]

    static_supporting = [
        item
        for item in dominant_drivers
        if item["engine"]
        in static_structural_support
    ]

    dynamic_supporting = [
        item
        for item in dominant_drivers
        if item["engine"]
        in dynamic_signals
    ]

    evidence_summary_parts = []

    if static_supporting:

        names = ", ".join(
            item["engine"]
            for item in static_supporting
        )

        evidence_summary_parts.append(
            "Structural/spatial evidence is led by "
            f"{names}."
        )

    if dynamic_supporting:

        names = ", ".join(
            item["engine"]
            for item in dynamic_supporting
        )

        evidence_summary_parts.append(
            "Dynamic evidence is led by "
            f"{names}."
        )

    if (
        rainfall_category == "LOW"
        and
        soil_category == "LOW"
        and
        temporal_category == "LOW"
    ):

        evidence_summary_parts.append(
            "Current rainfall, soil-wetness and temporal "
            "signals are comparatively low."
        )

    if not evidence_summary_parts:

        evidence_summary_parts.append(
            "The current evidence pattern is mixed and "
            "requires contextual interpretation."
        )

    evidence_summary = " ".join(
        evidence_summary_parts
    )

    attention_flags = []

    if current_risk >= 75.0:
        attention_flags.append(
            "VERY_HIGH_CURRENT_RISK"
        )

    if uncertainty >= 25.0:
        attention_flags.append(
            "ELEVATED_UNCERTAINTY"
        )

    if (
        len(extreme_engines) >= 2
    ):
        attention_flags.append(
            "MULTI_ENGINE_EXTREME_SUPPORT"
        )

    if (
        len(low_engines) >= 3
        and
        current_risk >= 75.0
    ):
        attention_flags.append(
            "HIGH_RISK_WITH_LOW_DYNAMIC_SIGNALS"
        )

    if not attention_flags:
        attention_flags.append(
            "NO_SPECIAL_CONFLICT_FLAG"
        )

    return {
        "cell_id": cell_id,

        "severity": severity,

        "warning_state": warning_state,

        "unified_risk_score":
            current_risk,

        "confidence_score":
            confidence,

        "uncertainty_score":
            uncertainty,

        "confidence_high":
            high_confidence,

        "engine_count":
            len(engines),

        "severe_engine_count":
            len(severe_engines),

        "extreme_engine_count":
            len(extreme_engines),

        "low_engine_count":
            len(low_engines),

        "evidence_pattern":
            evidence_pattern,

        "evidence_strength":
            evidence_strength,

        "dominant_drivers":
            dominant_drivers,

        "attention_flags":
            attention_flags,

        "evidence_summary":
            evidence_summary,

        "engines":
            engines,
    }

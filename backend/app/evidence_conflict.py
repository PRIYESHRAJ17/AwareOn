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


STATIC_ENGINES = {
    "susceptibility",
    "terrain_instability",
    "spatial_pressure",
    "exposure",
}


DYNAMIC_ENGINES = {
    "rainfall_trigger",
    "soil_wetness",
    "temporal",
    "environment_anomaly",
}


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank(
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


def _group_summary(
    engines: list[dict[str, Any]],
    names: set[str],
) -> dict[str, Any]:

    selected = [
        item
        for item in engines
        if item["engine"] in names
    ]

    if not selected:
        return {
            "engine_count": 0,
            "high_or_above": 0,
            "extreme": 0,
            "mean_score": 0.0,
        }

    scored = [
        item
        for item in selected
        if item["score"] is not None
    ]

    return {
        "engine_count":
            len(selected),

        "high_or_above":
            sum(
                1
                for item in selected
                if item["category_rank"] >= 2
            ),

        "extreme":
            sum(
                1
                for item in selected
                if item["category_rank"] >= 3
            ),

        "mean_score":
            (
                sum(
                    item["score"]
                    for item in scored
                )
                /
                len(scored)
                if scored
                else 0.0
            ),
    }


def classify_evidence_state(
    cross_engine: dict[str, Any],
) -> dict[str, Any]:

    if not cross_engine:
        raise ValueError(
            "Cross-engine intelligence is required."
        )

    engines = cross_engine.get(
        "engines",
        [],
    )

    if not engines:
        raise ValueError(
            "Cross-engine intelligence contains no engines."
        )

    static = _group_summary(
        engines,
        STATIC_ENGINES,
    )

    dynamic = _group_summary(
        engines,
        DYNAMIC_ENGINES,
    )

    risk = _num(
        cross_engine.get(
            "unified_risk_score"
        )
    )

    confidence = _num(
        cross_engine.get(
            "confidence_score"
        )
    )

    uncertainty = _num(
        cross_engine.get(
            "uncertainty_score"
        )
    )

    static_dominant = (
        static["high_or_above"] >= 2
        and
        static["mean_score"] >= 60.0
        and
        dynamic["mean_score"] < 40.0
    )

    dynamic_dominant = (
        dynamic["high_or_above"] >= 2
        and
        dynamic["mean_score"] >= 60.0
    )

    broad_convergence = (
        static["high_or_above"] >= 2
        and
        dynamic["high_or_above"] >= 2
    )

    strong_conflict = (
        static["high_or_above"] >= 2
        and
        dynamic["high_or_above"] == 0
        and
        risk >= 50.0
    )

    if broad_convergence:
        state = "MULTI_ENGINE_CONVERGENCE"

    elif static_dominant:
        state = "STRUCTURAL_DOMINANCE"

    elif dynamic_dominant:
        state = "DYNAMIC_CONVERGENCE"

    elif strong_conflict:
        state = "EVIDENCE_CONFLICT"

    else:
        state = "LIMITED_EVIDENCE"

    if state == "MULTI_ENGINE_CONVERGENCE":

        interpretation = (
            "Multiple structural and dynamic engines "
            "support the current risk state."
        )

    elif state == "STRUCTURAL_DOMINANCE":

        interpretation = (
            "Current risk is primarily supported by "
            "structural and spatial conditions rather "
            "than current dynamic triggers."
        )

    elif state == "DYNAMIC_CONVERGENCE":

        interpretation = (
            "Current risk is strongly supported by "
            "multiple active environmental signals."
        )

    elif state == "EVIDENCE_CONFLICT":

        interpretation = (
            "Current risk is elevated despite weak "
            "dynamic signals; structural evidence is "
            "stronger than current environmental triggers."
        )

    else:

        interpretation = (
            "The available engine evidence does not "
            "show a strong unified pattern."
        )

    caution_flags: list[str] = []

    if state == "STRUCTURAL_DOMINANCE":
        caution_flags.append(
            "LOW_DYNAMIC_SIGNAL_WITH_HIGH_STRUCTURAL_RISK"
        )

    if state == "EVIDENCE_CONFLICT":
        caution_flags.append(
            "REVIEW_EVIDENCE_DISAGREEMENT"
        )

    if uncertainty >= 25.0:
        caution_flags.append(
            "ELEVATED_UNCERTAINTY"
        )

    if confidence < 60.0:
        caution_flags.append(
            "LOWER_CONFIDENCE"
        )

    if not caution_flags:
        caution_flags.append(
            "NO_MAJOR_EVIDENCE_CONFLICT"
        )

    confidence_band = (
        "HIGH"
        if confidence >= 75.0
        else "MODERATE"
        if confidence >= 50.0
        else "LOW"
    )

    return {
        "cell_id":
            cross_engine.get(
                "cell_id"
            ),

        "evidence_state":
            state,

        "interpretation":
            interpretation,

        "confidence":
            confidence,

        "confidence_band":
            confidence_band,

        "uncertainty":
            uncertainty,

        "risk":
            risk,

        "static_evidence":
            static,

        "dynamic_evidence":
            dynamic,

        "caution_flags":
            caution_flags,

        "structural_dynamic_gap":
            (
                static["mean_score"]
                -
                dynamic["mean_score"]
            ),
    }

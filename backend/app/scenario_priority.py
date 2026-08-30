from __future__ import annotations

from typing import Any


CATEGORY_RANK = {
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


def _rank(
    category: Any,
) -> int:
    return CATEGORY_RANK.get(
        str(category or "").upper(),
        0,
    )


def _normalize(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


def calculate_scenario_priority(
    record: dict[str, Any],
) -> dict[str, Any]:

    baseline_risk = _num(
        record.get(
            "baseline_risk_score"
        )
    )

    scenario_risk = _num(
        record.get(
            "scenario_risk_score"
        )
    )

    risk_change = max(
        0.0,
        _num(
            record.get(
                "risk_score_change"
            )
        ),
    )

    exposure = _normalize(
        _num(
            record.get(
                "exposure_score"
            )
        )
    )

    susceptibility = _normalize(
        _num(
            record.get(
                "susceptibility_probability"
            )
            * 100.0
        )
    )

    trigger = _normalize(
        (
            _num(
                record.get(
                    "rainfall_trigger_score"
                )
            )
            /
            100.0
        )
        * 100.0
    )

    baseline_category = str(
        record.get(
            "baseline_category"
        )
        or ""
    ).upper()

    scenario_category = str(
        record.get(
            "scenario_category"
        )
        or ""
    ).upper()

    category_delta = max(
        0,
        _rank(
            scenario_category
        )
        -
        _rank(
            baseline_category
        ),
    )

    category_score = (
        100.0
        if category_delta >= 3
        else 85.0
        if category_delta == 2
        else 65.0
        if category_delta == 1
        else 0.0
    )

    deterioration_score = _normalize(
        risk_change * 10.0
    )

    final_risk_score = _normalize(
        scenario_risk
    )

    priority_score = (
        category_score * 0.35
        +
        final_risk_score * 0.20
        +
        deterioration_score * 0.20
        +
        susceptibility * 0.10
        +
        exposure * 0.10
        +
        trigger * 0.05
    )

    priority_score = _normalize(
        priority_score
    )

    if priority_score >= 85.0:
        priority_level = "P1_CRITICAL"

    elif priority_score >= 70.0:
        priority_level = "P2_HIGH"

    elif priority_score >= 50.0:
        priority_level = "P3_ELEVATED"

    else:
        priority_level = "P4_MONITOR"

    return {
        "cell_id":
            record.get(
                "cell_id"
            ),

        "scenario":
            record.get(
                "scenario"
            ),

        "rainfall_change_percent":
            _num(
                record.get(
                    "rainfall_change_percent"
                )
            ),

        "baseline_risk":
            baseline_risk,

        "scenario_risk":
            scenario_risk,

        "risk_change":
            risk_change,

        "baseline_category":
            baseline_category,

        "scenario_category":
            scenario_category,

        "transition":
            (
                f"{baseline_category} → "
                f"{scenario_category}"
                if baseline_category
                != scenario_category
                else scenario_category
            ),

        "category_delta":
            category_delta,

        "category_score":
            category_score,

        "risk_score_component":
            final_risk_score,

        "deterioration_component":
            deterioration_score,

        "susceptibility_component":
            susceptibility,

        "exposure_component":
            exposure,

        "trigger_component":
            trigger,

        "priority_score":
            priority_score,

        "priority_level":
            priority_level,
    }


def rank_scenario_priority(
    records: list[dict[str, Any]],
    top_k: int = 25,
) -> dict[str, Any]:

    if not records:
        raise ValueError(
            "Scenario priority requires cell records."
        )

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    ranked = [
        calculate_scenario_priority(
            record
        )
        for record in records
    ]

    ranked.sort(
        key=lambda item: (
            item["category_delta"],
            item["priority_score"],
            item["scenario_risk"],
            item["risk_change"],
            item["exposure_component"],
            item["susceptibility_component"],
        ),
        reverse=True,
    )

    for index, item in enumerate(
        ranked,
        start=1,
    ):

        item["priority_rank"] = index

    escalation_count = sum(
        1
        for item in ranked
        if item["category_delta"] > 0
    )

    critical_count = sum(
        1
        for item in ranked
        if item["priority_level"]
        == "P1_CRITICAL"
    )

    high_count = sum(
        1
        for item in ranked
        if item["priority_level"]
        == "P2_HIGH"
    )

    return {
        "record_count":
            len(ranked),

        "escalating_cells":
            escalation_count,

        "critical_priority_cells":
            critical_count,

        "high_priority_cells":
            high_count,

        "top_k":
            min(
                top_k,
                len(ranked),
            ),

        "top_priority_cells":
            ranked[
                :top_k
            ],

        "all_cells":
            ranked,
    }

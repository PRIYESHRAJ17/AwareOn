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


def _int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _rank(
    category: Any,
) -> int:
    return CATEGORY_RANK.get(
        str(category or "").upper(),
        0,
    )


def _priority_band(
    score: float,
) -> str:
    if score >= 85.0:
        return "P1_CRITICAL"

    if score >= 70.0:
        return "P2_HIGH"

    if score >= 50.0:
        return "P3_ELEVATED"

    return "P4_MONITOR"


def _sensitivity_band(
    score: float,
) -> str:
    if score >= 85.0:
        return "VERY_HIGH"

    if score >= 65.0:
        return "HIGH"

    if score >= 40.0:
        return "MODERATE"

    return "LOW"


def _transition_weight(
    baseline_category: str,
    scenario_category: str,
) -> float:

    baseline_rank = _rank(
        baseline_category
    )

    scenario_rank = _rank(
        scenario_category
    )

    category_delta = max(
        0,
        scenario_rank - baseline_rank,
    )

    if category_delta >= 3:
        return 100.0

    if category_delta == 2:
        return 85.0

    if category_delta == 1:
        return 65.0

    return 0.0


def _cell_sensitivity_score(
    record: dict[str, Any],
) -> float:

    risk_change = max(
        0.0,
        _num(
            record.get(
                "risk_score_change"
            )
        ),
    )

    scenario_risk = max(
        0.0,
        min(
            100.0,
            _num(
                record.get(
                    "risk_score"
                )
            ),
        ),
    )

    baseline_category = str(
        record.get(
            "baseline_category"
        )
        or ""
    ).upper()

    scenario_category = str(
        record.get(
            "risk_category"
        )
        or ""
    ).upper()

    transition_score = _transition_weight(
        baseline_category,
        scenario_category,
    )

    # Score the absolute risk movement.
    change_score = min(
        100.0,
        (risk_change / 10.0) * 100.0,
    )

    # Existing severity matters because a cell already
    # near a dangerous threshold deserves greater attention.
    severity_score = scenario_risk

    # Explicit escalation gets an additional signal.
    escalation_bonus = (
        15.0
        if _int(
            record.get(
                "escalates"
            )
        )
        else 0.0
    )

    score = (
        (change_score * 0.30)
        +
        (severity_score * 0.30)
        +
        (transition_score * 0.40)
        +
        escalation_bonus
    )

    return max(
        0.0,
        min(
            100.0,
            score,
        ),
    )


def rank_scenario_cells(
    records: list[dict[str, Any]],
    top_k: int = 25,
) -> dict[str, Any]:

    if not records:
        raise ValueError(
            "Scenario sensitivity requires cell records."
        )

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    ranked: list[dict[str, Any]] = []

    for record in records:

        baseline_risk = _num(
            record.get(
                "baseline_risk_score"
            )
        )

        scenario_risk = _num(
            record.get(
                "risk_score"
            )
        )

        risk_change = _num(
            record.get(
                "risk_score_change"
            )
        )

        baseline_category = str(
            record.get(
                "baseline_category"
            )
            or ""
        ).upper()

        scenario_category = str(
            record.get(
                "risk_category"
            )
            or ""
        ).upper()

        category_change = (
            _rank(
                scenario_category
            )
            -
            _rank(
                baseline_category
            )
        )

        sensitivity_score = (
            _cell_sensitivity_score(
                record
            )
        )

        escalation = bool(
            _int(
                record.get(
                    "escalates"
                )
            )
        )

        relative_change = (
            (risk_change / baseline_risk) * 100.0
            if baseline_risk != 0.0
            else 0.0
        )

        transition = (
            f"{baseline_category} → {scenario_category}"
            if baseline_category != scenario_category
            else scenario_category
        )

        ranked.append(
            {
                "cell_id": record.get(
                    "cell_id"
                ),

                "scenario": record.get(
                    "scenario"
                ),

                "rainfall_change_percent": _num(
                    record.get(
                        "rainfall_change_percent"
                    )
                ),

                "baseline_risk_score":
                    baseline_risk,

                "scenario_risk_score":
                    scenario_risk,

                "risk_score_change":
                    risk_change,

                "relative_risk_change_percent":
                    relative_change,

                "baseline_category":
                    baseline_category,

                "scenario_category":
                    scenario_category,

                "category_change":
                    category_change,

                "transition":
                    transition,

                "escalates":
                    escalation,

                "rainfall_trigger_score":
                    _num(
                        record.get(
                            "rainfall_trigger_score"
                        )
                    ),

                "susceptibility_probability":
                    _num(
                        record.get(
                            "susceptibility_probability"
                        )
                    ),

                "exposure_score":
                    _num(
                        record.get(
                            "exposure_score"
                        )
                    ),

                "sensitivity_score":
                    sensitivity_score,

                "sensitivity_band":
                    _sensitivity_band(
                        sensitivity_score
                    ),

                "priority_level":
                    _priority_band(
                        sensitivity_score
                    ),
            }
        )

    # Ranking philosophy:
    # 1. Category escalation
    # 2. Magnitude of category movement
    # 3. Sensitivity score
    # 4. Worst-case risk
    # 5. Absolute risk change
    ranked.sort(
        key=lambda item: (
            1
            if item["escalates"]
            else 0,

            item["category_change"],

            item["sensitivity_score"],

            item["scenario_risk_score"],

            item["risk_score_change"],
        ),
        reverse=True,
    )

    for index, item in enumerate(
        ranked,
        start=1,
    ):
        item[
            "sensitivity_rank"
        ] = index

    escalating = [
        item
        for item in ranked
        if item["escalates"]
    ]

    extreme_escalations = [
        item
        for item in ranked
        if (
            item["category_change"] > 0
            and
            item["scenario_category"] == "EXTREME"
        )
    ]

    high_or_extreme_escalations = [
        item
        for item in ranked
        if (
            item["category_change"] > 0
            and
            _rank(
                item["scenario_category"]
            ) >= _rank("HIGH")
        )
    ]

    very_high_sensitivity = [
        item
        for item in ranked
    ]

    return {
        "record_count":
            len(ranked),

        "top_k":
            min(
                top_k,
                len(ranked),
            ),

        "escalating_cells":
            len(escalating),

        "high_or_extreme_escalations":
            len(
                high_or_extreme_escalations
            ),

        "extreme_escalations":
            len(
                extreme_escalations
            ),

        "very_high_sensitivity_cells":
            len(
                very_high_sensitivity
            ),

        "top_cells":
            ranked[
                :top_k
            ],

        "all_cells":
            ranked,
    }

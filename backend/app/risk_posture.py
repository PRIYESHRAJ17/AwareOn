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


def _scenario_escalates(
    scenario: dict[str, Any],
) -> bool:
    return bool(
        scenario.get(
            "escalates"
        )
    )


def _scenario_sensitivity(
    scenario: dict[str, Any],
) -> float:

    change = max(
        0.0,
        _num(
            scenario.get(
                "risk_score_change"
            )
        ),
    )

    category_delta = max(
        0,
        _rank(
            scenario.get(
                "risk_category"
            )
        )
        -
        _rank(
            scenario.get(
                "baseline_category"
            )
        ),
    )

    category_signal = (
        100.0
        if category_delta >= 3
        else 85.0
        if category_delta == 2
        else 65.0
        if category_delta == 1
        else 0.0
    )

    change_signal = min(
        100.0,
        change * 10.0,
    )

    return (
        category_signal * 0.60
        +
        change_signal * 0.40
    )


def build_risk_posture(
    assessment: dict[str, Any],
    scenario_records: list[dict[str, Any]],
) -> dict[str, Any]:

    if not assessment:
        raise ValueError(
            "Assessment data is required."
        )

    if not scenario_records:
        raise ValueError(
            "Scenario records are required."
        )

    current_risk = _num(
        assessment.get(
            "unified_risk_score"
        )
    )

    severity = _category(
        assessment.get(
            "severity"
        )
    )

    warning_state = _category(
        assessment.get(
            "warning_state"
        )
    )

    evidence_state = _category(
        assessment.get(
            "evidence_state"
        )
    )

    confidence = _num(
        assessment.get(
            "confidence_score"
        )
    )

    baseline_records = [
        item
        for item in scenario_records
        if _num(
            item.get(
                "rainfall_change_percent"
            )
        ) == 0.0
    ]

    baseline_category = (
        _category(
            baseline_records[0].get(
                "risk_category"
            )
        )
        if baseline_records
        else severity
    )

    worst_case = max(
        scenario_records,
        key=lambda item: _num(
            item.get(
                "risk_score"
            )
        ),
    )

    escalating_scenarios = [
        item
        for item in scenario_records
        if _scenario_escalates(
            item
        )
    ]

    most_sensitive = max(
        scenario_records,
        key=_scenario_sensitivity,
    )

    future_category = _category(
        worst_case.get(
            "risk_category"
        )
    )

    future_risk = _num(
        worst_case.get(
            "risk_score"
        )
    )

    future_change = _num(
        worst_case.get(
            "risk_score_change"
        )
    )

    category_delta = (
        _rank(
            future_category
        )
        -
        _rank(
            baseline_category
        )
    )

    rainfall = _num(
        worst_case.get(
            "rainfall_change_percent"
        )
    )

    if (
        _rank(
            severity
        ) >= 3
        and
        len(escalating_scenarios) > 0
    ):

        posture = (
            "CURRENTLY_CRITICAL_AND_SCENARIO_SENSITIVE"
        )

    elif (
        category_delta >= 1
        and
        rainfall <= 50
    ):

        posture = (
            "ESCALATION_WATCH"
        )

    elif (
        category_delta >= 1
    ):

        posture = (
            "STRESS_SENSITIVE"
        )

    elif (
        _rank(
            severity
        ) >= 2
        and
        len(escalating_scenarios) == 0
    ):

        posture = (
            "CURRENT_RISK_DOMINANT"
        )

    elif (
        current_risk >= 50
    ):

        posture = (
            "ELEVATED_MONITORING"
        )

    else:

        posture = (
            "BASELINE_MONITORING"
        )

    if evidence_state == "EVIDENCE_CONFLICT":

        evidence_note = (
            "Current engine evidence is not fully aligned; "
            "structural evidence should be interpreted alongside "
            "the weaker dynamic signals."
        )

    elif evidence_state == "MULTI_ENGINE_CONVERGENCE":

        evidence_note = (
            "Multiple engine groups provide converging support "
            "for the current risk state."
        )

    elif evidence_state == "STRUCTURAL_DOMINANCE":

        evidence_note = (
            "Current risk is primarily supported by structural "
            "and spatial conditions."
        )

    elif evidence_state == "DYNAMIC_CONVERGENCE":

        evidence_note = (
            "Current risk is strongly supported by active "
            "environmental signals."
        )

    else:

        evidence_note = (
            "Evidence strength should be interpreted with "
            "the available engine coverage."
        )

    scenario_note = (
        f"Under the highest tested rainfall scenario "
        f"(+{rainfall:.0f}%), risk reaches {future_risk:.2f}"
        f" with a change of +{future_change:.2f} points."
    )

    if category_delta > 0:

        transition_note = (
            f"Category changes from {baseline_category} "
            f"to {future_category}."
        )

    else:

        transition_note = (
            f"Category remains {future_category} across "
            "the highest tested scenario."
        )

    if most_sensitive:

        sensitivity_note = (
            f"The strongest scenario response occurs under "
            f"+{_num(most_sensitive.get('rainfall_change_percent')):.0f}% "
            f"rainfall with {_num(most_sensitive.get('risk_score_change')):.2f} "
            "points of risk increase."
        )

    else:

        sensitivity_note = (
            "No distinct scenario sensitivity signal was detected."
        )

    if confidence >= 75:

        confidence_note = (
            "Current assessment confidence is HIGH."
        )

    elif confidence >= 50:

        confidence_note = (
            "Current assessment confidence is MODERATE."
        )

    else:

        confidence_note = (
            "Current assessment confidence is LOW."
        )

    return {
        "cell_id":
            assessment.get(
                "cell_id"
            ),

        "posture":
            posture,

        "current": {
            "risk_score":
                current_risk,

            "severity":
                severity,

            "warning_state":
                warning_state,

            "baseline_category":
                baseline_category,

            "evidence_state":
                evidence_state,

            "confidence":
                confidence,
        },

        "future": {
            "worst_tested_rainfall_percent":
                rainfall,

            "risk_score":
                future_risk,

            "risk_change":
                future_change,

            "category":
                future_category,

            "category_delta":
                category_delta,

            "escalating_scenarios":
                len(
                    escalating_scenarios
                ),
        },

        "scenario_sensitivity": {
            "cell_id":
                most_sensitive.get(
                    "cell_id"
                ),

            "rainfall_change_percent":
                _num(
                    most_sensitive.get(
                        "rainfall_change_percent"
                    )
                ),

            "risk_change":
                _num(
                    most_sensitive.get(
                        "risk_score_change"
                    )
                ),

            "category":
                _category(
                    most_sensitive.get(
                        "risk_category"
                    )
                ),

            "transition":
                (
                    f"{_category(most_sensitive.get('baseline_category'))} "
                    f"→ "
                    f"{_category(most_sensitive.get('risk_category'))}"
                ),
        },

        "interpretation": {
            "evidence":
                evidence_note,

            "scenario":
                scenario_note,

            "transition":
                transition_note,

            "sensitivity":
                sensitivity_note,

            "confidence":
                confidence_note,
        },
    }

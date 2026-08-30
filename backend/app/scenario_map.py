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


def _band(
    category_change: int,
    risk_change: float,
    risk_score: float,
) -> str:

    if category_change >= 3:
        return "EXTREME_ESCALATION"

    if category_change == 2:
        return "MAJOR_ESCALATION"

    if category_change == 1:
        return "ESCALATING"

    if risk_score >= 70.0:
        return "HIGH_RISK_STABLE"

    if risk_change >= 5.0:
        return "RISK_INCREASE"

    if risk_change >= 2.0:
        return "MODERATE_INCREASE"

    return "STABLE"


def build_scenario_map(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    if not records:
        raise ValueError(
            "Scenario map requires cell records."
        )

    scenario_name = str(
        records[0].get(
            "scenario"
        )
        or ""
    )

    rainfall_change = _num(
        records[0].get(
            "rainfall_change_percent"
        )
    )

    cells: list[dict[str, Any]] = []

    for record in records:

        cell_id = str(
            record.get(
                "cell_id"
            )
            or ""
        )

        if not cell_id:
            continue

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

        escalates = bool(
            _int(
                record.get(
                    "escalates"
                )
            )
        )

        cells.append(
            {
                "cell_id": cell_id,

                "scenario":
                    scenario_name,

                "rainfall_change_percent":
                    rainfall_change,

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

                "category_change":
                    category_change,

                "transition":
                    (
                        f"{baseline_category} → "
                        f"{scenario_category}"
                        if baseline_category
                        != scenario_category
                        else scenario_category
                    ),

                "escalates":
                    escalates,

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

                "map_band":
                    _band(
                        category_change,
                        risk_change,
                        scenario_risk,
                    ),
            }
        )

    escalating = [
        cell
        for cell in cells
        if cell["escalates"]
    ]

    category_changes = [
        cell
        for cell in cells
        if cell["category_change"] > 0
    ]

    high_or_extreme = [
        cell
        for cell in cells
        if _rank(
            cell["scenario_category"]
        ) >= _rank("HIGH")
        and
        _rank(
            cell["baseline_category"]
        ) < _rank("HIGH")
    ]

    extreme = [
        cell
        for cell in cells
        if (
            cell["scenario_category"]
            == "EXTREME"
            and
            cell["baseline_category"]
            != "EXTREME"
        )
    ]

    top_change = sorted(
        cells,
        key=lambda item: (
            item["category_change"],
            item["risk_change"],
            item["scenario_risk"],
        ),
        reverse=True,
    )

    highest_risk = sorted(
        cells,
        key=lambda item: (
            item["scenario_risk"],
            item["risk_change"],
        ),
        reverse=True,
    )

    return {
        "scenario": scenario_name,

        "rainfall_change_percent":
            rainfall_change,

        "cell_count":
            len(cells),

        "escalating_cells":
            len(escalating),

        "category_change_cells":
            len(category_changes),

        "new_high_or_extreme_cells":
            len(high_or_extreme),

        "new_extreme_cells":
            len(extreme),

        "scenario_risk_max":
            max(
                (
                    cell["scenario_risk"]
                    for cell in cells
                ),
                default=0.0,
            ),

        "scenario_risk_mean":
            (
                sum(
                    cell["scenario_risk"]
                    for cell in cells
                )
                /
                len(cells)
                if cells
                else 0.0
            ),

        "risk_change_mean":
            (
                sum(
                    cell["risk_change"]
                    for cell in cells
                )
                /
                len(cells)
                if cells
                else 0.0
            ),

        "risk_change_max":
            max(
                (
                    cell["risk_change"]
                    for cell in cells
                ),
                default=0.0,
            ),

        "top_sensitive_cells":
            top_change[:25],

        "highest_risk_cells":
            highest_risk[:25],

        "cells":
            cells,
    }

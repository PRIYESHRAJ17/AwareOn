from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def rank_infrastructure_impact(
    exposure_cells: list[dict[str, Any]],
    risk_lookup: dict[str, dict[str, Any]],
    scenario_lookup: dict[str, dict[str, Any]] | None = None,
    top_n: int = 10,
) -> dict[str, Any]:

    if not isinstance(
        exposure_cells,
        list,
    ):
        raise ValueError(
            "exposure_cells must be a list."
        )

    if not isinstance(
        risk_lookup,
        dict,
    ):
        raise ValueError(
            "risk_lookup must be a dictionary."
        )

    if scenario_lookup is None:
        scenario_lookup = {}

    if not isinstance(
        scenario_lookup,
        dict,
    ):
        raise ValueError(
            "scenario_lookup must be a dictionary."
        )

    if top_n <= 0:
        raise ValueError(
            "top_n must be greater than 0."
        )

    ranked = []

    for item in exposure_cells:

        if not isinstance(
            item,
            dict,
        ):
            continue

        cell_id = str(
            item.get(
                "cell_id"
            )
            or ""
        )

        if not cell_id:
            continue

        risk = risk_lookup.get(
            cell_id,
            {},
        )

        scenario = scenario_lookup.get(
            cell_id,
            {},
        )

        risk_score = _num(
            risk.get(
                "unified_risk_score"
            )
        )

        exposure_score = _num(
            item.get(
                "exposure_score"
            )
        )

        transport = _num(
            item.get(
                "transport_exposure"
            )
        )

        infrastructure = _num(
            item.get(
                "infrastructure_exposure"
            )
        )

        population = _num(
            item.get(
                "population_exposure"
            )
        )

        confidence = _num(
            risk.get(
                "confidence_score"
            )
        )

        scenario_change = _num(
            scenario.get(
                "risk_change"
            )
        )

        impact_component = max(
            transport,
            infrastructure,
            population,
        )

        scenario_component = min(
            100.0,
            max(
                0.0,
                50.0 + scenario_change * 5.0,
            ),
        )

        priority_score = (
            risk_score * 0.35
            +
            exposure_score * 0.25
            +
            impact_component * 0.20
            +
            scenario_component * 0.10
            +
            confidence * 0.10
        )

        priority_score = min(
            100.0,
            max(
                0.0,
                priority_score,
            ),
        )

        if impact_component >= 80.0:
            impact_level = "CRITICAL"

        elif impact_component >= 60.0:
            impact_level = "HIGH"

        elif impact_component >= 40.0:
            impact_level = "ELEVATED"

        else:
            impact_level = "MONITOR"

        if priority_score >= 85.0:
            priority = "P1"

        elif priority_score >= 70.0:
            priority = "P2"

        elif priority_score >= 50.0:
            priority = "P3"

        else:
            priority = "P4"

        if transport >= max(
            infrastructure,
            population,
        ):
            focus = "TRANSPORT"

        elif infrastructure >= population:
            focus = "INFRASTRUCTURE"

        else:
            focus = "POPULATION"

        ranked.append(
            {
                "cell_id":
                    cell_id,

                "priority":
                    priority,

                "priority_score":
                    round(
                        priority_score,
                        2,
                    ),

                "impact_level":
                    impact_level,

                "impact_focus":
                    focus,

                "risk_score":
                    risk_score,

                "exposure_score":
                    exposure_score,

                "transport_exposure":
                    transport,

                "infrastructure_exposure":
                    infrastructure,

                "population_exposure":
                    population,

                "scenario_risk_change":
                    scenario_change,

                "confidence":
                    confidence,
            }
        )

    ranked.sort(
        key=lambda item: (
            item["priority_score"],
            item["risk_score"],
            item["exposure_score"],
        ),
        reverse=True,
    )

    selected = ranked[:top_n]

    for index, item in enumerate(
        selected,
        start=1,
    ):
        item["rank"] = index

    if selected:

        critical = sum(
            1
            for item in selected
            if item["impact_level"]
            == "CRITICAL"
        )

        high = sum(
            1
            for item in selected
            if item["impact_level"]
            == "HIGH"
        )

        transport = sum(
            1
            for item in selected
            if item["impact_focus"]
            == "TRANSPORT"
        )

        infrastructure = sum(
            1
            for item in selected
            if item["impact_focus"]
            == "INFRASTRUCTURE"
        )

        population = sum(
            1
            for item in selected
            if item["impact_focus"]
            == "POPULATION"
        )

        posture = (
            "CRITICAL"
            if critical > 0
            else "HIGH"
            if high > 0
            else "ELEVATED"
        )

        interpretation = (
            f"{len(selected)} priority infrastructure "
            "targets were ranked. "
            f"{critical} are CRITICAL impact targets "
            f"and {high} are HIGH impact targets."
        )

    else:

        critical = 0
        high = 0
        transport = 0
        infrastructure = 0
        population = 0
        posture = "MONITOR"

        interpretation = (
            "No infrastructure impact targets were ranked."
        )

    return {
        "engine":
            "AWAREON_INFRASTRUCTURE_IMPACT_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "target_count":
            len(selected),

        "available_targets":
            len(ranked),

        "regional_posture":
            posture,

        "critical_targets":
            critical,

        "high_targets":
            high,

        "focus_counts":
            {
                "transport":
                    transport,

                "infrastructure":
                    infrastructure,

                "population":
                    population,
            },

        "targets":
            selected,

        "interpretation":
            interpretation,
    }

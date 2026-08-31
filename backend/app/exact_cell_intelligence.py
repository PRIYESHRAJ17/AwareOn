from __future__ import annotations

from typing import Any

from backend.app.services.gis_service import gis_service
from backend.app.cross_engine_intelligence import (
    build_cross_engine_intelligence,
)
from backend.app.evidence_conflict import (
    classify_evidence_state,
)
from backend.app.risk_posture import (
    build_risk_posture,
)
from backend.app.cross_cell_patterns import (
    analyze_cross_cell_pattern,
)
from backend.app.unified_posture import (
    build_unified_posture,
)
from backend.app.cell_neighborhood import (
    resolve_cell_neighborhood,
)
from backend.app.intelligence_cache import (
    intelligence_cache,
)


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_exact_cell_intelligence(
    cell_id: str,
    rainfall_change_percent: float = 100.0,
    radius_m: float = 5000.0,
) -> dict[str, Any]:

    if not cell_id:
        raise ValueError(
            "cell_id is required."
        )

    change = float(
        rainfall_change_percent
    )

    radius = float(
        radius_m
    )

    if radius <= 0:
        raise ValueError(
            "radius_m must be greater than 0."
        )

    cache_key = (
        "exact_cell",
        str(cell_id),
        change,
        radius,
    )

    cached = intelligence_cache.get(
        cache_key
    )

    if cached is not None:
        return cached

    gis_cell = gis_service.get_cell(
        str(cell_id)
    )

    if gis_cell is None:
        raise ValueError(
            f"GIS cell not found: {cell_id}"
        )

    from backend.app.services.assessment_service import (
        assessment_service,
    )

    current = (
        assessment_service.get_assessment(
            str(cell_id)
        )
    )

    if current is None:
        raise ValueError(
            f"Assessment not found: {cell_id}"
        )

    cross_engine = (
        build_cross_engine_intelligence(
            current
        )
    )

    evidence_state = (
        classify_evidence_state(
            cross_engine
        )
    )

    assessment_for_posture = dict(
        current
    )

    assessment_for_posture[
        "evidence_state"
    ] = evidence_state[
        "evidence_state"
    ]

    # --------------------------------------------------------
    # CELL-LEVEL SCENARIO DATA
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # scenario_service.simulate() returns aggregate
    # scenario statistics. It does not return per-cell
    # records under "records".
    #
    # get_cell_scenarios(cell_id) is the canonical
    # cell-level scenario source.
    # --------------------------------------------------------

    from backend.app.services.scenario_service import (
        scenario_service,
    )

    cell_scenarios = (
        scenario_service.get_cell_scenarios(
            str(cell_id)
        )
    )

    if not isinstance(
        cell_scenarios,
        dict,
    ):
        raise TypeError(
            "Cell scenario service returned "
            "an invalid result."
        )

    scenario_records = (
        cell_scenarios.get(
            "scenarios",
            [],
        )
    )

    if not isinstance(
        scenario_records,
        list,
    ) or not scenario_records:
        raise ValueError(
            "Cell scenario service returned "
            "no scenario records."
        )

    exact_scenario = next(
        (
            item
            for item in scenario_records
            if (
                abs(
                    _num(
                        item.get(
                            "rainfall_change_percent"
                        )
                    )
                    - change
                )
                < 1e-9
            )
        ),
        None,
    )

    if exact_scenario is None:
        available = [
            _num(
                item.get(
                    "rainfall_change_percent"
                )
            )
            for item in scenario_records
            if isinstance(
                item,
                dict,
            )
        ]

        raise ValueError(
            "Requested rainfall scenario "
            f"{change} was not found for cell "
            f"{cell_id}. Available scenarios: "
            f"{available}"
        )

    current_risk_posture = build_risk_posture(
        assessment_for_posture,
        scenario_records,
    )

    neighborhood = (
        resolve_cell_neighborhood(
            str(cell_id),
            radius,
        )
    )

    feature_collection = (
        neighborhood.get(
            "feature_collection",
            {
                "type":
                    "FeatureCollection",
                "features":
                    [],
            },
        )
    )

    spatial_pattern = (
        analyze_cross_cell_pattern(
            feature_collection,
            radius,
        )
    )

    unified_posture = (
        build_unified_posture(
            assessment_for_posture,
            current_risk_posture,
            cross_engine,
            evidence_state,
            spatial_pattern,
        )
    )

    scenario_name = (
        exact_scenario.get(
            "scenario"
        )
    )

    scenario_risk = (
        exact_scenario.get(
            "risk_score"
        )
    )

    scenario_risk_change = (
        exact_scenario.get(
            "risk_score_change"
        )
    )

    scenario_category = (
        exact_scenario.get(
            "risk_category"
        )
    )

    result = {
        "cell_id":
            str(cell_id),

        # Preserve the canonical assessment under the structure
        # consumed by build_cell_evidence_package().
        "current_assessment":
            dict(current),

        "rainfall_change_percent":
            change,

        "radius_m":
            radius,

        "current_assessment":
            current,

        "gis_cell":
            gis_cell,

        "cross_engine":
            cross_engine,

        "evidence_state":
            evidence_state,

        "scenario":
            {
                "scenario":
                    scenario_name,

                "rainfall_change_percent":
                    _num(
                        exact_scenario.get(
                            "rainfall_change_percent"
                        )
                    ),

                "cell":
                    exact_scenario,

                "scenario_count":
                    len(
                        scenario_records
                    ),
            },

        "current_risk_posture":
            current_risk_posture,

        "neighborhood":
            {
                "radius_m":
                    radius,

                "neighbor_count":
                    neighborhood.get(
                        "neighbor_count",
                        0,
                    ),

                "centroid_utm":
                    neighborhood.get(
                        "centroid_utm"
                    ),

                "centroid_wgs84":
                    neighborhood.get(
                        "centroid_wgs84"
                    ),

                "target_present":
                    neighborhood.get(
                        "target_present",
                        False,
                    ),

                "target_distance_m":
                    neighborhood.get(
                        "target_distance_m"
                    ),
            },

        "spatial_pattern":
            spatial_pattern,

        "unified_posture":
            unified_posture,

        "signal_summary":
            {
                "current_risk_score":
                    _num(
                        current.get(
                            "unified_risk_score"
                        )
                    ),

                "current_severity":
                    current.get(
                        "severity"
                    ),

                "current_warning":
                    current.get(
                        "warning_state"
                    ),

                "scenario":
                    scenario_name,

                "scenario_risk":
                    _num(
                        scenario_risk
                    ),

                "scenario_risk_change":
                    _num(
                        scenario_risk_change
                    ),

                "scenario_category":
                    scenario_category,

                "baseline_category":
                    exact_scenario.get(
                        "baseline_category"
                    ),

                "neighbor_count":
                    neighborhood.get(
                        "neighbor_count",
                        0,
                    ),

                "high_risk_neighbors":
                    spatial_pattern.get(
                        "high_risk_cells",
                        0,
                    ),

                "extreme_neighbors":
                    spatial_pattern.get(
                        "extreme_cells",
                        0,
                    ),

                "spatial_pattern":
                    spatial_pattern.get(
                        "pattern"
                    ),

                "spatial_confidence":
                    spatial_pattern.get(
                        "confidence"
                    ),

                "evidence_state":
                    evidence_state.get(
                        "evidence_state"
                    ),

                "evidence_strength":
                    cross_engine.get(
                        "evidence_strength"
                    ),

                "confidence":
                    current.get(
                        "confidence_score"
                    ),

                "unified_posture":
                    unified_posture.get(
                        "unified_posture"
                    ),

                "priority_level":
                    unified_posture.get(
                        "priority_level"
                    ),

                "priority_score":
                    unified_posture.get(
                        "priority_score"
                    ),

                "unified_confidence":
                    unified_posture.get(
                        "confidence"
                    ),

                "unified_confidence_band":
                    unified_posture.get(
                        "confidence_band"
                    ),
            },
    }

    intelligence_cache.set(
        cache_key,
        result,
    )

    return result

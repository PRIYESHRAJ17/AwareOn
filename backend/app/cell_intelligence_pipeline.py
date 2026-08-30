from __future__ import annotations

from time import perf_counter
from typing import Any

from backend.app.services.assessment_service import (
    assessment_service,
)

from backend.app.services.scenario_service import (
    scenario_service,
)

from backend.app.cross_engine_intelligence import (
    build_cross_engine_intelligence,
)

from backend.app.evidence_conflict import (
    classify_evidence_state,
)

from backend.app.risk_posture import (
    build_risk_posture,
)

from backend.app.cell_neighborhood import (
    resolve_cell_neighborhood,
)

from backend.app.cross_cell_patterns import (
    analyze_cross_cell_pattern,
)

from backend.app.unified_posture import (
    build_unified_posture,
)

from backend.app.intelligence_pipeline import (
    run_pipeline,
)


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_cell_intelligence_pipeline(
    cell_id: str,
    rainfall_change_percent: float = 100.0,
    radius_m: float = 5000.0,
) -> dict[str, Any]:

    if not cell_id:
        raise ValueError(
            "cell_id is required."
        )

    if radius_m <= 0:
        raise ValueError(
            "radius_m must be greater than 0."
        )

    change = float(
        rainfall_change_percent
    )

    started = perf_counter()

    def load_current(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        result = (
            assessment_service
            .get_assessment(
                cell_id
            )
        )

        if result is None:
            raise ValueError(
                f"Assessment not found: {cell_id}"
            )

        return {
            "assessment":
                result,
        }

    def build_cross_engine(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        assessment = state[
            "assessment"
        ]

        cross_engine = (
            build_cross_engine_intelligence(
                assessment
            )
        )

        return {
            "cross_engine":
                cross_engine,
        }

    def resolve_evidence(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        evidence = (
            classify_evidence_state(
                state[
                    "cross_engine"
                ]
            )
        )

        return {
            "evidence_state":
                evidence,
        }

    def run_scenario(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        simulation = (
            scenario_service
            .simulate(
                change
            )
        )

        records = simulation.get(
            "records",
            [],
        )

        if not records:
            raise ValueError(
                "Scenario simulation returned no records."
            )

        return {
            "scenario_result":
                simulation,

            "scenario_records":
                records,
        }

    def build_risk_posture_step(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        assessment = dict(
            state[
                "assessment"
            ]
        )

        evidence_state = state[
            "evidence_state"
        ]

        assessment[
            "evidence_state"
        ] = evidence_state[
            "evidence_state"
        ]

        posture = (
            build_risk_posture(
                assessment,
                state[
                    "scenario_records"
                ],
            )
        )

        return {
            "risk_posture":
                posture,
        }

    def resolve_neighborhood(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        neighborhood = (
            resolve_cell_neighborhood(
                cell_id,
                radius_m,
            )
        )

        return {
            "neighborhood":
                neighborhood,
        }

    def analyze_spatial(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        neighborhood = state[
            "neighborhood"
        ]

        pattern = (
            analyze_cross_cell_pattern(
                neighborhood[
                    "feature_collection"
                ],
                radius_m,
            )
        )

        return {
            "spatial_pattern":
                pattern,
        }

    def build_unified(
        state: dict[str, Any],
    ) -> dict[str, Any]:

        assessment = dict(
            state[
                "assessment"
            ]
        )

        evidence_state = state[
            "evidence_state"
        ]

        assessment[
            "evidence_state"
        ] = evidence_state[
            "evidence_state"
        ]

        unified = (
            build_unified_posture(
                assessment,
                state[
                    "risk_posture"
                ],
                state[
                    "cross_engine"
                ],
                evidence_state,
                state[
                    "spatial_pattern"
                ],
            )
        )

        return {
            "unified_posture":
                unified,
        }

    result = run_pipeline(
        [
            (
                "current_assessment",
                load_current,
            ),
            (
                "cross_engine",
                build_cross_engine,
            ),
            (
                "evidence_resolution",
                resolve_evidence,
            ),
            (
                "scenario",
                run_scenario,
            ),
            (
                "risk_posture",
                build_risk_posture_step,
            ),
            (
                "neighborhood",
                resolve_neighborhood,
            ),
            (
                "spatial_pattern",
                analyze_spatial,
            ),
            (
                "unified_posture",
                build_unified,
            ),
        ]
    )

    elapsed_ms = (
        perf_counter()
        -
        started
    ) * 1000.0

    output = {
        "success":
            result.success,

        "cell_id":
            cell_id,

        "rainfall_change_percent":
            change,

        "data":
            result.data,

        "pipeline_timings_ms":
            result.timings_ms,

        "pipeline_total_ms":
            round(
                elapsed_ms,
                3,
            ),

        "errors":
            result.errors,
    }

    if not result.success:
        return output

    data = result.data

    assessment = data[
        "assessment"
    ]

    scenario_records = data[
        "scenario_records"
    ]

    exact_scenario = next(
        (
            item
            for item in scenario_records
            if str(
                item.get(
                    "cell_id"
                )
            )
            == str(cell_id)
        ),
        None,
    )

    output["summary"] = {
        "current_risk":
            _num(
                assessment.get(
                    "unified_risk_score"
                )
            ),

        "current_severity":
            assessment.get(
                "severity"
            ),

        "warning_state":
            assessment.get(
                "warning_state"
            ),

        "scenario_risk":
            (
                _num(
                    exact_scenario.get(
                        "risk_score"
                    )
                )
                if exact_scenario
                else None
            ),

        "scenario_risk_change":
            (
                _num(
                    exact_scenario.get(
                        "risk_score_change"
                    )
                )
                if exact_scenario
                else None
            ),

        "neighbor_count":
            data[
                "neighborhood"
            ].get(
                "neighbor_count"
            ),

        "spatial_pattern":
            data[
                "spatial_pattern"
            ].get(
                "pattern"
            ),

        "evidence_state":
            data[
                "evidence_state"
            ].get(
                "evidence_state"
            ),

        "unified_posture":
            data[
                "unified_posture"
            ].get(
                "unified_posture"
            ),

        "priority_level":
            data[
                "unified_posture"
            ].get(
                "priority_level"
            ),

        "confidence_band":
            data[
                "unified_posture"
            ].get(
                "confidence_band"
            ),
    }

    return output

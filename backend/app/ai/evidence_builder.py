from __future__ import annotations

from typing import Any


def _item(
    evidence_id: str,
    evidence_type: str,
    claim: str,
    value: Any,
    source_id: str,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_tool": "exact_cell_intelligence",
        "evidence_type": evidence_type,
        "claim": claim,
        "value": value,
        "source_id": source_id,
        "confidence": None,
        "metadata": {},
    }


def build_cell_evidence_package(
    payload: dict[str, Any],
) -> dict[str, Any]:

    if not isinstance(payload, dict):
        raise TypeError(
            "payload must be a dictionary."
        )

    cell_id = str(
        payload.get(
            "cell_id",
            "",
        )
    )

    if not cell_id:
        raise ValueError(
            "payload.cell_id is required."
        )

    # --------------------------------------------------------
    # Canonical compact signal layer
    # --------------------------------------------------------

    signal_summary = payload.get(
        "signal_summary",
        {},
    )

    if not isinstance(
        signal_summary,
        dict,
    ):
        signal_summary = {}

    # --------------------------------------------------------
    # Canonical current assessment layer
    # --------------------------------------------------------

    current_assessment = payload.get(
        "current_assessment",
        {},
    )

    if not isinstance(
        current_assessment,
        dict,
    ):
        current_assessment = {}

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def signal(
        key: str,
        default: Any = None,
    ) -> Any:

        if key in signal_summary:
            return signal_summary.get(key)

        return default

    def assessment(
        key: str,
        default: Any = None,
    ) -> Any:

        if key in current_assessment:
            return current_assessment.get(key)

        return default

    def canonical(
        key: str,
        default: Any = None,
    ) -> Any:

        value = signal(
            key,
            None,
        )

        if value is not None:
            return value

        return assessment(
            key,
            default,
        )

    items: list[
        dict[str, Any]
    ] = []

    def add(
        suffix: str,
        evidence_type: str,
        claim: str,
        value: Any,
        *,
        source_id: str | None = None,
    ) -> None:

        items.append(
            _item(
                evidence_id=(
                    f"CELL-{cell_id}-{suffix}"
                ),
                evidence_type=evidence_type,
                claim=claim,
                value=value,
                source_id=(
                    source_id
                    or
                    f"cell:{cell_id}:{suffix}"
                ),
            )
        )

    # ========================================================
    # CURRENT RISK
    # ========================================================

    current_risk = canonical(
        "current_risk_score"
    )

    add(
        "risk",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has a current "
            "risk score."
        ),
        current_risk,
    )

    severity = canonical(
        "current_severity"
    )

    add(
        "severity",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has severity "
            f"{severity}."
        ),
        severity,
    )

    warning = signal(
        "current_warning",
        None,
    )

    if warning is None:
        warning = assessment(
            "warning_state"
        )

    add(
        "warning",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has warning state "
            f"{warning}."
        ),
        warning,
    )

    # ========================================================
    # SUSCEPTIBILITY
    # ========================================================

    susceptibility = canonical(
        "susceptibility_category"
    )

    add(
        "susceptibility",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has susceptibility "
            f"category {susceptibility}."
        ),
        susceptibility,
    )

    # ========================================================
    # TERRAIN
    # ========================================================

    terrain = canonical(
        "terrain_instability_category"
    )

    add(
        "terrain",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has terrain "
            f"instability category {terrain}."
        ),
        terrain,
    )

    # ========================================================
    # EXPOSURE
    # ========================================================

    exposure_category = canonical(
        "exposure_category"
    )

    dominant_exposure = canonical(
        "dominant_exposure"
    )

    add(
        "exposure",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has exposure "
            f"category {exposure_category} with "
            f"dominant exposure {dominant_exposure}."
        ),
        {
            "category": exposure_category,
            "dominant": dominant_exposure,
        },
    )

    # ========================================================
    # SPATIAL PRESSURE
    # ========================================================

    spatial_pressure = canonical(
        "spatial_pressure_score"
    )

    add(
        "spatial_pressure",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has spatial pressure "
            f"score {spatial_pressure}."
        ),
        spatial_pressure,
    )

    # ========================================================
    # RAINFALL TRIGGER
    # ========================================================

    rainfall_trigger_score = canonical(
        "rainfall_trigger_score"
    )

    rainfall_trigger_category = canonical(
        "rainfall_trigger_category"
    )

    add(
        "rainfall_trigger",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has rainfall trigger "
            f"category {rainfall_trigger_category}."
        ),
        {
            "score": rainfall_trigger_score,
            "category": rainfall_trigger_category,
        },
    )

    # ========================================================
    # SOIL
    # ========================================================

    soil_score = canonical(
        "soil_wetness_score"
    )

    soil_category = canonical(
        "soil_wetness_category"
    )

    add(
        "soil",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has soil wetness "
            f"category {soil_category}."
        ),
        {
            "score": soil_score,
            "category": soil_category,
        },
    )

    # ========================================================
    # TEMPORAL
    # ========================================================

    temporal_trajectory = canonical(
        "temporal_trajectory"
    )

    temporal_category = canonical(
        "temporal_category"
    )

    add(
        "temporal",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has temporal "
            f"trajectory {temporal_trajectory}."
        ),
        {
            "trajectory":
                temporal_trajectory,
            "category":
                temporal_category,
        },
    )

    # ========================================================
    # ENVIRONMENT ANOMALY
    # ========================================================

    anomaly_score = canonical(
        "environment_anomaly_score"
    )

    anomaly_category = canonical(
        "environment_anomaly_category"
    )

    add(
        "anomaly",
        "MODEL_OUTPUT",
        (
            f"Cell {cell_id} has environment "
            f"anomaly category {anomaly_category}."
        ),
        {
            "score": anomaly_score,
            "category": anomaly_category,
        },
    )

    # ========================================================
    # SCENARIO
    # ========================================================

    scenario = signal(
        "scenario"
    )

    scenario_risk = signal(
        "scenario_risk"
    )

    scenario_change = signal(
        "scenario_risk_change"
    )

    scenario_category = signal(
        "scenario_category"
    )

    # Fallback directly into the nested scenario object.
    scenario_block = payload.get(
        "scenario",
        {},
    )

    if isinstance(
        scenario_block,
        dict,
    ):

        if scenario is None:
            scenario = scenario_block.get(
                "scenario"
            )

        if (
            scenario_risk is None
            or scenario_change is None
            or scenario_category is None
        ):

            cell_scenario = scenario_block.get(
                "cell",
                {},
            )

            if isinstance(
                cell_scenario,
                dict,
            ):

                if scenario_risk is None:
                    scenario_risk = cell_scenario.get(
                        "risk_score"
                    )

                if scenario_change is None:
                    scenario_change = cell_scenario.get(
                        "risk_score_change"
                    )

                if scenario_category is None:
                    scenario_category = cell_scenario.get(
                        "risk_category"
                    )

    add(
        "scenario",
        "SIMULATED",
        (
            f"Scenario risk for cell {cell_id} "
            f"is {scenario_risk}."
        ),
        scenario_risk,
    )

    add(
        "scenario_change",
        "SIMULATED",
        (
            f"Scenario risk change for cell {cell_id} "
            f"is {scenario_change}."
        ),
        scenario_change,
    )

    add(
        "scenario_category",
        "SIMULATED",
        (
            f"Scenario category for cell {cell_id} "
            f"is {scenario_category}."
        ),
        scenario_category,
    )

    # ========================================================
    # NEIGHBORHOOD
    # ========================================================

    neighbor_block = payload.get(
        "neighborhood",
        {},
    )

    if not isinstance(
        neighbor_block,
        dict,
    ):
        neighbor_block = {}

    neighbor_count = signal(
        "neighbor_count",
        neighbor_block.get(
            "neighbor_count",
            0,
        ),
    )

    add(
        "neighbors",
        "DERIVED",
        (
            f"Neighborhood analysis for cell {cell_id} "
            f"contains {neighbor_count} cells."
        ),
        neighbor_count,
    )

    # ========================================================
    # SPATIAL PATTERN
    # ========================================================

    spatial_block = payload.get(
        "spatial_pattern",
        {},
    )

    if not isinstance(
        spatial_block,
        dict,
    ):
        spatial_block = {}

    high_neighbors = signal(
        "high_risk_neighbors",
        spatial_block.get(
            "high_risk_cells",
            0,
        ),
    )

    extreme_neighbors = signal(
        "extreme_neighbors",
        spatial_block.get(
            "extreme_cells",
            0,
        ),
    )

    spatial_pattern = signal(
        "spatial_pattern",
        spatial_block.get(
            "pattern"
        ),
    )

    add(
        "high_neighbors",
        "DERIVED",
        (
            f"Cell {cell_id} has "
            f"{high_neighbors} high-risk neighbors."
        ),
        high_neighbors,
    )

    add(
        "extreme_neighbors",
        "DERIVED",
        (
            f"Cell {cell_id} has "
            f"{extreme_neighbors} extreme neighbors."
        ),
        extreme_neighbors,
    )

    add(
        "spatial_pattern",
        "DERIVED",
        (
            f"Cell {cell_id} has spatial pattern "
            f"{spatial_pattern}."
        ),
        spatial_pattern,
    )

    # ========================================================
    # EVIDENCE STATE
    # ========================================================

    evidence_state = signal(
        "evidence_state"
    )

    if evidence_state is None:
        evidence_block = payload.get(
            "evidence_state",
            {},
        )

        if isinstance(
            evidence_block,
            dict,
        ):
            evidence_state = evidence_block.get(
                "evidence_state"
            )

    add(
        "evidence_state",
        "DERIVED",
        (
            f"Evidence state for cell {cell_id} "
            f"is {evidence_state}."
        ),
        evidence_state,
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = signal(
        "confidence"
    )

    if confidence is None:
        confidence = assessment(
            "confidence_score"
        )

    add(
        "confidence",
        "DERIVED",
        (
            f"Cell {cell_id} has confidence "
            f"{confidence}."
        ),
        confidence,
    )

    # ========================================================
    # UNIFIED POSTURE
    # ========================================================

    unified_posture = signal(
        "unified_posture"
    )

    if unified_posture is None:
        posture_block = payload.get(
            "unified_posture",
            {},
        )

        if isinstance(
            posture_block,
            dict,
        ):
            unified_posture = posture_block.get(
                "unified_posture"
            )

    add(
        "posture",
        "DERIVED",
        (
            f"Unified posture for cell {cell_id} "
            f"is {unified_posture}."
        ),
        unified_posture,
    )

    # ========================================================
    # PRIORITY
    # ========================================================

    priority_level = signal(
        "priority_level"
    )

    if priority_level is None:
        posture_block = payload.get(
            "unified_posture",
            {},
        )

        if isinstance(
            posture_block,
            dict,
        ):
            priority_level = posture_block.get(
                "priority_level"
            )

    priority_score = signal(
        "priority_score"
    )

    if priority_score is None:
        posture_block = payload.get(
            "unified_posture",
            {},
        )

        if isinstance(
            posture_block,
            dict,
        ):
            priority_score = posture_block.get(
                "priority_score"
            )

    # The canonical evidence value is the priority level.
    # Keep the numeric score in metadata so no information
    # is lost without changing the canonical value semantics.
    priority_item = _item(
        evidence_id=(
            f"CELL-{cell_id}-priority"
        ),
        evidence_type="DERIVED",
        claim=(
            f"Cell {cell_id} has priority "
            f"level {priority_level}."
        ),
        value=priority_level,
        source_id=(
            f"cell:{cell_id}:priority"
        ),
    )

    priority_item["metadata"] = {
        "priority_score":
            priority_score,
    }

    items.append(
        priority_item
    )

    # ========================================================
    # PACKAGE
    # ========================================================

    return {
        "query": (
            f"Exact AwareOn intelligence for "
            f"cell {cell_id}."
        ),
        "cell_id": cell_id,
        "count": len(items),
        "items": items,
    }


__all__ = [
    "build_cell_evidence_package",
]

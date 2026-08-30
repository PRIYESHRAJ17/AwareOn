from __future__ import annotations

from typing import Any

from backend.app.ai.evidence import (
    EvidencePackage,
    EvidenceType,
    classify_evidence_type,
)


# ============================================================
# NUMERIC HELPER
# ============================================================

def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# GROUND TOOL RESULT
# ============================================================

def ground_tool_result(
    tool_name: str,
    result: dict[str, Any],
    query: str,
) -> EvidencePackage:

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "Tool result must be a dictionary."
        )

    package = EvidencePackage(
        query=query,
    )

    # ========================================================
    # EXACT CELL INTELLIGENCE
    # ========================================================

    if tool_name == "exact_cell_intelligence":

        cell_id = str(
            result.get(
                "cell_id",
            )
            or "UNKNOWN"
        )

        summary = result.get(
            "signal_summary",
            {},
        )

        if isinstance(
            summary,
            dict,
        ):

            risk = summary.get(
                "current_risk_score"
            )

            severity = summary.get(
                "current_severity"
            )

            scenario = summary.get(
                "scenario_risk"
            )

            scenario_change = summary.get(
                "scenario_risk_change"
            )

            if risk is not None:

                package.add(
                    source_tool=tool_name,
                    evidence_type=(
                        EvidenceType.MODEL_OUTPUT
                    ),
                    claim=(
                        f"Cell {cell_id} has a "
                        "current risk score."
                    ),
                    value=_num(
                        risk
                    ),
                    source_id=(
                        f"cell:{cell_id}:risk"
                    ),
                )

            if severity is not None:

                package.add(
                    source_tool=tool_name,
                    evidence_type=(
                        EvidenceType.MODEL_OUTPUT
                    ),
                    claim=(
                        f"Cell {cell_id} has "
                        f"severity {severity}."
                    ),
                    value=severity,
                    source_id=(
                        f"cell:{cell_id}:severity"
                    ),
                )

            if scenario is not None:

                package.add(
                    source_tool=tool_name,
                    evidence_type=(
                        EvidenceType.SIMULATED
                    ),
                    claim=(
                        f"Scenario risk for cell "
                        f"{cell_id} is "
                        f"{_num(scenario):.2f}."
                    ),
                    value=_num(
                        scenario
                    ),
                    source_id=(
                        f"cell:{cell_id}:scenario"
                    ),
                )

            if scenario_change is not None:

                package.add(
                    source_tool=tool_name,
                    evidence_type=(
                        EvidenceType.SIMULATED
                    ),
                    claim=(
                        f"Scenario risk change "
                        f"for cell {cell_id} "
                        f"is "
                        f"{_num(scenario_change):+.2f}."
                    ),
                    value=_num(
                        scenario_change
                    ),
                    source_id=(
                        f"cell:{cell_id}:scenario_change"
                    ),
                )

        # ----------------------------------------------------
        # Unified posture
        # ----------------------------------------------------

        unified = result.get(
            "unified_posture"
        )

        if isinstance(
            unified,
            dict,
        ):

            posture = unified.get(
                "unified_posture"
            )

            if posture:

                package.add(
                    source_tool=tool_name,
                    evidence_type=(
                        EvidenceType.DERIVED
                    ),
                    claim=(
                        f"Unified posture for cell "
                        f"{cell_id} is {posture}."
                    ),
                    value=posture,
                    source_id=(
                        f"cell:{cell_id}:posture"
                    ),
                )

    # ========================================================
    # REGIONAL INTELLIGENCE
    # ========================================================

    elif tool_name == "regional_intelligence":

        package.add(
            source_tool=tool_name,
            evidence_type=(
                EvidenceType.MODEL_OUTPUT
            ),
            claim=(
                "Regional intelligence provides "
                "a consolidated spatial risk state."
            ),
            value={
                "regional_state":
                    result.get(
                        "regional_state"
                    ),
                "cell_count":
                    result.get(
                        "cell_count"
                    ),
                "high_or_extreme_cells":
                    result.get(
                        "high_or_extreme_cells"
                    ),
                "extreme_cells":
                    result.get(
                        "extreme_cells"
                    ),
                "mean_risk_score":
                    result.get(
                        "mean_risk_score"
                    ),
            },
            source_id=(
                "regional:intelligence"
            ),
        )

    # ========================================================
    # HISTORICAL TRAJECTORY
    # ========================================================

    elif tool_name == "historical_trajectory":

        trajectory = result.get(
            "trajectory"
        )

        direction = result.get(
            "direction"
        )

        score = result.get(
            "trajectory_score"
        )

        if trajectory:

            package.add(
                source_tool=tool_name,
                evidence_type=(
                    EvidenceType.OBSERVED
                ),
                claim=(
                    "Historical environmental "
                    f"trajectory is {trajectory}."
                ),
                value=trajectory,
                source_id=(
                    "historical:trajectory"
                ),
            )

        if direction:

            package.add(
                source_tool=tool_name,
                evidence_type=(
                    EvidenceType.DERIVED
                ),
                claim=(
                    "Historical environmental "
                    f"direction is {direction}."
                ),
                value=direction,
                source_id=(
                    "historical:direction"
                ),
            )

        if score is not None:

            package.add(
                source_tool=tool_name,
                evidence_type=(
                    EvidenceType.DERIVED
                ),
                claim=(
                    "Historical trajectory score "
                    "was calculated from the "
                    "available environmental record."
                ),
                value=_num(
                    score
                ),
                source_id=(
                    "historical:score"
                ),
            )

    # ========================================================
    # SCENARIO SIMULATION
    # ========================================================

    elif tool_name == "scenario_simulation":

        rainfall = result.get(
            "rainfall_change_percent"
        )

        package.add(
            source_tool=tool_name,
            evidence_type=(
                EvidenceType.SIMULATED
            ),
            claim=(
                "Scenario simulation produced "
                "modeled outcomes under the "
                "specified rainfall perturbation."
            ),
            value={
                "rainfall_change_percent":
                    rainfall,
                "result":
                    result,
            },
            source_id=(
                "scenario:simulation"
            ),
        )

    # ========================================================
    # NEARBY CELLS
    # ========================================================

    elif tool_name == "nearby_cells":

        features = result.get(
            "features",
            [],
        )

        package.add(
            source_tool=tool_name,
            evidence_type=(
                EvidenceType.OBSERVED
            ),
            claim=(
                "GIS nearby-cell lookup returned "
                "the spatially relevant AwareOn cells."
            ),
            value={
                "feature_count":
                    len(features)
                if isinstance(
                    features,
                    list,
                )
                else 0,
            },
            source_id=(
                "gis:nearby_cells"
            ),
        )

    # ========================================================
    # EARLY WARNING
    # ========================================================

    elif tool_name == "early_warning_master":

        package.add(
            source_tool=tool_name,
            evidence_type=(
                EvidenceType.DERIVED
            ),
            claim=(
                "AwareOn early-warning intelligence "
                "produced a consolidated warning state."
            ),
            value={
                "master_warning":
                    result.get(
                        "master_warning"
                    ),
                "master_state":
                    result.get(
                        "master_state"
                    ),
                "operational_posture":
                    result.get(
                        "operational_posture"
                    ),
            },
            source_id=(
                "warning:master"
            ),
        )

    # ========================================================
    # DECISION MASTER
    # ========================================================

    elif tool_name == "decision_master":

        package.add(
            source_tool=tool_name,
            evidence_type=(
                EvidenceType.RECOMMENDATION
            ),
            claim=(
                "AwareOn decision intelligence "
                "produced a consolidated operational "
                "decision."
            ),
            value={
                "master_state":
                    result.get(
                        "master_state"
                    ),
                "master_urgency":
                    result.get(
                        "master_urgency"
                    ),
                "operational_posture":
                    result.get(
                        "operational_posture"
                    ),
                "operational_focus":
                    result.get(
                        "operational_focus"
                    ),
                "response_level":
                    result.get(
                        "response_level"
                    ),
            },
            source_id=(
                "decision:master"
            ),
        )

    # ========================================================
    # GENERIC AWAREON TOOL
    # ========================================================

    else:

        evidence_type = (
            classify_evidence_type(
                tool_name
            )
        )

        package.add(
            source_tool=tool_name,
            evidence_type=evidence_type,
            claim=(
                f"Tool {tool_name} produced "
                "a validated AwareOn intelligence result."
            ),
            value=result,
            source_id=(
                f"tool:{tool_name}"
            ),
        )

    return package


# ============================================================
# MERGE EVIDENCE
# ============================================================

def merge_evidence(
    packages: list[EvidencePackage],
) -> EvidencePackage:

    if not packages:

        return EvidencePackage(
            query="",
        )

    merged = EvidencePackage(
        query=packages[0].query,
    )

    for package in packages:

        if not isinstance(
            package,
            EvidencePackage,
        ):
            raise TypeError(
                "All items in packages must "
                "be EvidencePackage instances."
            )

        merged.items.extend(
            package.items
        )

    return merged

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.ai.agent_tools import (
    execute_regional_intelligence,
)
from backend.app.ai.temporal_orchestrator import (
    run_temporal_intelligence,
)
from backend.app.services.assessment_service import (
    assessment_service,
)
from backend.app.services.scenario_service import (
    scenario_service,
)
from backend.app.regional_command import (
    build_regional_command_intelligence,
)
from backend.app.regional_master import (
    build_regional_master,
)
from backend.app.cluster_priority import (
    score_cluster,
)
from backend.app.cluster_exposure import (
    link_cluster_to_exposure,
)
from backend.app.cluster_evolution import (
    analyze_cluster_evolution,
)
from backend.app.infrastructure_impact import (
    rank_infrastructure_impact,
)
from backend.app.field_inspection import (
    prioritize_field_inspection,
)
from backend.app.monitoring_priority import (
    prioritize_monitoring,
)
from backend.app.intervention_priority import (
    build_intervention_priority,
)
from backend.app.response_recommendation import (
    build_response_recommendation,
)
from backend.app.decision_optimization import (
    optimize_response_options,
)
from backend.app.intervention_comparison import (
    compare_intervention_options,
)
from backend.app.decision_tradeoff import (
    build_decision_tradeoff,
)
from backend.app.operational_planning import (
    build_operational_plan,
)
from backend.app.decision_master import (
    build_decision_master,
)


@dataclass(frozen=True)
class DecisionIntelligenceResult:
    status: str
    cell_id: str
    regional_intelligence: dict[str, Any]
    cluster: dict[str, Any]
    priority: dict[str, Any]
    exposure: dict[str, Any]
    evolution: dict[str, Any]
    regional_command: dict[str, Any]
    regional_master: dict[str, Any]
    temporal: dict[str, Any]
    intervention: dict[str, Any]
    infrastructure: dict[str, Any]
    field_inspection: dict[str, Any]
    monitoring: dict[str, Any]
    response: dict[str, Any]
    optimization: dict[str, Any]
    comparison: dict[str, Any]
    tradeoff: dict[str, Any]
    operational: dict[str, Any]
    decision_master: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "cell_id": self.cell_id,
            "regional_intelligence": self.regional_intelligence,
            "cluster": self.cluster,
            "priority": self.priority,
            "exposure": self.exposure,
            "evolution": self.evolution,
            "regional_command": self.regional_command,
            "regional_master": self.regional_master,
            "temporal": self.temporal,
            "intervention": self.intervention,
            "infrastructure": self.infrastructure,
            "field_inspection": self.field_inspection,
            "monitoring": self.monitoring,
            "response": self.response,
            "optimization": self.optimization,
            "comparison": self.comparison,
            "tradeoff": self.tradeoff,
            "operational": self.operational,
            "decision_master": self.decision_master,
        }


def _require_dict(
    value: Any,
    name: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(
            f"{name} must be a dictionary."
        )

    if not value:
        raise ValueError(
            f"{name} cannot be empty."
        )

    return value


def _require_list(
    value: Any,
    name: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise TypeError(
            f"{name} must be a list."
        )

    if not value:
        raise ValueError(
            f"{name} cannot be empty."
        )

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise TypeError(
                f"{name}[{index}] must be a dictionary."
            )

    return value


def _regional_core(
    regional: dict[str, Any],
) -> dict[str, Any]:

    tool_results = regional.get(
        "tool_results"
    )

    if isinstance(
        tool_results,
        dict,
    ):
        nested = tool_results.get(
            "regional_intelligence"
        )

        if isinstance(
            nested,
            dict,
        ):
            regional = nested

    return _require_dict(
        regional,
        "regional_intelligence",
    )


def _build_cluster(
    regional: dict[str, Any],
    scenario_records: list[dict[str, Any]],
) -> dict[str, Any]:

    spatial = regional.get(
        "spatial_pattern",
        {},
    )

    if not isinstance(
        spatial,
        dict,
    ):
        spatial = {}

    maximum = regional.get(
        "maximum_risk",
        {},
    )

    if not isinstance(
        maximum,
        dict,
    ):
        maximum = {}

    top_cells = regional.get(
        "top_cells",
        [],
    )

    if not isinstance(
        top_cells,
        list,
    ):
        top_cells = []

    cell_ids: list[str] = []

    for item in top_cells:
        if not isinstance(
            item,
            dict,
        ):
            continue

        raw_cell_id = item.get(
            "cell_id"
        )

        if raw_cell_id is not None:
            cell_ids.append(
                str(raw_cell_id)
            )

    fallback_cell = maximum.get(
        "cell_id"
    )

    if (
        not cell_ids
        and fallback_cell is not None
    ):
        cell_ids.append(
            str(fallback_cell)
        )

    if not cell_ids:
        raise ValueError(
            "Regional intelligence contains "
            "no usable cell IDs."
        )

    cell_count = int(
        regional.get(
            "cell_count",
            len(cell_ids),
        )
        or len(cell_ids)
    )

    mean_risk = float(
        regional.get(
            "mean_risk_score",
            0.0,
        )
        or 0.0
    )

    maximum_risk = float(
        maximum.get(
            "risk_score",
            spatial.get(
                "maximum_risk",
                mean_risk,
            ),
        )
        or mean_risk
    )

    extreme_cells = int(
        regional.get(
            "extreme_cells",
            0,
        )
        or 0
    )

    watch_cells = int(
        regional.get(
            "watch_cells",
            0,
        )
        or 0
    )

    mean_confidence = float(
        regional.get(
            "mean_confidence",
            0.0,
        )
        or 0.0
    )

    cluster_severity = (
        "EXTREME"
        if extreme_cells > 0
        else (
            "HIGH"
            if (
                int(
                    regional.get(
                        "high_or_extreme_cells",
                        0,
                    )
                    or 0
                )
                > 0
            )
            else "MODERATE"
        )
    )

    return {
        "cluster_id":
            "REGIONAL_CLUSTER",

        "cell_ids":
            cell_ids,

        "cell_count":
            cell_count,

        "mean_risk":
            mean_risk,

        "maximum_risk":
            maximum_risk,

        "maximum_risk_cell":
            maximum.get(
                "cell_id"
            ),

        "extreme_cells":
            extreme_cells,

        "critical_or_warning_cells":
            watch_cells,

        "mean_confidence":
            mean_confidence,

        "cluster_severity":
            cluster_severity,

        "scenario_records":
            scenario_records,
    }


def _build_risk_lookup(
    cell_ids: list[str],
) -> dict[str, dict[str, Any]]:

    lookup: dict[
        str,
        dict[str, Any],
    ] = {}

    for cell_id in cell_ids:
        assessment = (
            assessment_service.get_assessment(
                str(cell_id)
            )
        )

        if isinstance(
            assessment,
            dict,
        ):
            lookup[str(cell_id)] = assessment

    if not lookup:
        raise ValueError(
            "No assessments were available "
            "for regional targets."
        )

    return lookup


def _build_scenario_lookup(
    cell_ids: list[str],
) -> dict[str, dict[str, Any]]:

    lookup: dict[
        str,
        dict[str, Any],
    ] = {}

    for cell_id in cell_ids:
        payload = (
            scenario_service.get_cell_scenarios(
                str(cell_id)
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            continue

        records = payload.get(
            "scenarios",
            [],
        )

        if not isinstance(
            records,
            list,
        ) or not records:
            continue

        valid_records = [
            item
            for item in records
            if isinstance(
                item,
                dict,
            )
        ]

        if not valid_records:
            continue

        worst = max(
            valid_records,
            key=lambda item: float(
                item.get(
                    "risk_score",
                    0.0,
                )
                or 0.0
            ),
        )

        lookup[str(cell_id)] = {
            "risk_change":
                worst.get(
                    "risk_score_change",
                    0.0,
                ),

            "risk_score":
                worst.get(
                    "risk_score",
                    0.0,
                ),

            "risk_category":
                worst.get(
                    "risk_category",
                    "UNKNOWN",
                ),
        }

    return lookup


def _extract_targets(
    payload: dict[str, Any],
    keys: tuple[str, ...],
) -> list[dict[str, Any]]:

    for key in keys:
        value = payload.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return [
                item
                for item in value
                if isinstance(
                    item,
                    dict,
                )
            ]

    return []


def run_decision_intelligence(
    *,
    cell_id: str,
    latitude: float,
    longitude: float,
) -> DecisionIntelligenceResult:

    if not isinstance(
        cell_id,
        str,
    ) or not cell_id.strip():
        raise ValueError(
            "cell_id is required."
        )

    # ========================================================
    # 1. REGIONAL INTELLIGENCE
    # ========================================================

    regional_payload = (
        execute_regional_intelligence(
            latitude=float(latitude),
            longitude=float(longitude),
        )
    )

    regional = _regional_core(
        regional_payload
    )

    # ========================================================
    # 2. TARGET CELL ASSESSMENT
    # ========================================================

    assessment = (
        assessment_service.get_assessment(
            str(cell_id)
        )
    )

    assessment = _require_dict(
        assessment,
        "assessment",
    )

    # ========================================================
    # 3. TARGET CELL SCENARIOS
    # ========================================================

    target_scenarios = (
        scenario_service.get_cell_scenarios(
            str(cell_id)
        )
    )

    target_scenarios = _require_dict(
        target_scenarios,
        "target_scenarios",
    )

    scenario_records = _require_list(
        target_scenarios.get(
            "scenarios",
            [],
        ),
        "target_scenarios.scenarios",
    )

    # ========================================================
    # 4. REGIONAL CLUSTER
    # ========================================================

    cluster = _build_cluster(
        regional,
        scenario_records,
    )

    if str(cell_id) not in cluster[
        "cell_ids"
    ]:
        cluster[
            "cell_ids"
        ].append(
            str(cell_id)
        )

    # ========================================================
    # 5. CLUSTER PRIORITY
    # ========================================================

    priority = score_cluster(
        cluster
    )

    priority = _require_dict(
        priority,
        "priority",
    )

    # ========================================================
    # 6. CLUSTER EXPOSURE
    # ========================================================

    exposure = link_cluster_to_exposure(
        cluster
    )

    exposure = _require_dict(
        exposure,
        "exposure",
    )

    # ========================================================
    # 7. CLUSTER EVOLUTION
    # ========================================================

    evolution = analyze_cluster_evolution(
        scenario_records
    )

    evolution = _require_dict(
        evolution,
        "evolution",
    )

    # ========================================================
    # 8. REGIONAL COMMAND
    # ========================================================

    regional_command = (
        build_regional_command_intelligence(
            cluster=cluster,
            priority=priority,
            exposure=exposure,
            evolution=evolution,
        )
    )

    regional_command = _require_dict(
        regional_command,
        "regional_command",
    )

    # ========================================================
    # 9. REGIONAL MASTER
    # ========================================================

    regional_master = build_regional_master(
        cluster=cluster,
        priority=priority,
        exposure=exposure,
        evolution=evolution,
        command=regional_command,
    )

    regional_master = _require_dict(
        regional_master,
        "regional_master",
    )

    # ========================================================
    # 10. TEMPORAL INTELLIGENCE
    # ========================================================

    temporal_result = (
        run_temporal_intelligence(
            cell_id=str(cell_id),
            regional_intelligence=regional,
        )
    )

    if hasattr(
        temporal_result,
        "to_dict",
    ):
        temporal = temporal_result.to_dict()
    else:
        temporal = temporal_result

    temporal = _require_dict(
        temporal,
        "temporal",
    )

    early_warning_master = _require_dict(
        temporal.get(
            "early_warning_master",
            {},
        ),
        "early_warning_master",
    )

    progression = _require_dict(
        temporal.get(
            "progression",
            {},
        ),
        "progression",
    )

    early_warning = _require_dict(
        temporal.get(
            "early_warning",
            {},
        ),
        "early_warning",
    )

    # ========================================================
    # 11. INTERVENTION PRIORITY
    # ========================================================

    intervention = (
        build_intervention_priority(
            assessment=assessment,
            regional_master=regional_master,
            early_warning_master=(
                early_warning_master
            ),
            progression=progression,
        )
    )

    intervention = _require_dict(
        intervention,
        "intervention",
    )

    # ========================================================
    # 12. RISK / SCENARIO LOOKUPS
    # ========================================================

    risk_lookup = _build_risk_lookup(
        cluster["cell_ids"]
    )

    scenario_lookup = _build_scenario_lookup(
        cluster["cell_ids"]
    )

    # ========================================================
    # 13. INFRASTRUCTURE IMPACT
    # ========================================================

    exposure_cells = _extract_targets(
        exposure,
        (
            "top_exposed_cells",
            "selected_targets",
            "targets",
        ),
    )

    if not exposure_cells:
        exposure_cells = [
            {
                "cell_id":
                    item,
                "exposure_score":
                    0.0,
                "transport_exposure":
                    0.0,
                "infrastructure_exposure":
                    0.0,
                "population_exposure":
                    0.0,
            }
            for item in cluster[
                "cell_ids"
            ]
        ]

    infrastructure = (
        rank_infrastructure_impact(
            exposure_cells=exposure_cells,
            risk_lookup=risk_lookup,
            scenario_lookup=scenario_lookup,
            top_n=10,
        )
    )

    infrastructure = _require_dict(
        infrastructure,
        "infrastructure",
    )

    # ========================================================
    # 14. FIELD INSPECTION
    # ========================================================

    infrastructure_targets = _extract_targets(
        infrastructure,
        (
            "selected_targets",
            "targets",
            "top_targets",
            "ranked",
        ),
    )

    if not infrastructure_targets:
        infrastructure_targets = exposure_cells

    field_inspection = (
        prioritize_field_inspection(
            infrastructure_targets=(
                infrastructure_targets
            ),
            regional_posture=str(
                regional_master.get(
                    "regional_posture",
                    "UNKNOWN",
                )
            ),
            top_n=10,
        )
    )

    field_inspection = _require_dict(
        field_inspection,
        "field_inspection",
    )

    # ========================================================
    # 15. MONITORING
    # ========================================================

    monitoring_targets = _extract_targets(
        field_inspection,
        (
            "selected",
            "targets",
            "ranked",
        ),
    )

    if not monitoring_targets:
        monitoring_targets = (
            infrastructure_targets
        )

    anomaly_fusion = temporal.get(
        "anomaly_fusion",
        {},
    )

    if not isinstance(
        anomaly_fusion,
        dict,
    ):
        anomaly_fusion = {}

    monitoring = prioritize_monitoring(
        targets=monitoring_targets,
        temporal_state=str(
            anomaly_fusion.get(
                "temporal_state",
                "UNKNOWN",
            )
        ),
        warning_level=str(
            early_warning.get(
                "warning_level",
                "UNKNOWN",
            )
        ),
        top_n=10,
    )

    monitoring = _require_dict(
        monitoring,
        "monitoring",
    )

    # ========================================================
    # 16. RESPONSE RECOMMENDATION
    # ========================================================

    response = build_response_recommendation(
        intervention=intervention,
        field_inspection=field_inspection,
        monitoring=monitoring,
        early_warning=early_warning,
        regional_command=regional_command,
        progression=progression,
    )

    response = _require_dict(
        response,
        "response",
    )

    # ========================================================
    # 17. DECISION OPTIMIZATION
    # ========================================================

    optimization = (
        optimize_response_options(
            assessment=assessment,
            intervention=intervention,
            field_inspection=field_inspection,
            monitoring=monitoring,
            response=response,
        )
    )

    optimization = _require_dict(
        optimization,
        "optimization",
    )

    options = optimization.get(
        "options",
        [],
    )

    if not isinstance(
        options,
        list,
    ) or not options:
        raise ValueError(
            "Decision optimization produced "
            "no intervention options."
        )

    options = [
        item
        for item in options
        if isinstance(
            item,
            dict,
        )
    ]

    if not options:
        raise ValueError(
            "Decision optimization produced "
            "no valid intervention options."
        )

    # IMPORTANT:
    # recommended_option is a dictionary in the real
    # optimizer output. The comparison layer expects only
    # the canonical option-name string.
    recommended_option = optimization.get(
        "recommended_option"
    )

    if isinstance(
        recommended_option,
        dict,
    ):
        recommended_name = (
            recommended_option.get(
                "option"
            )
        )
    else:
        recommended_name = (
            recommended_option
        )

    if not recommended_name:
        ranked = sorted(
            options,
            key=lambda item: float(
                item.get(
                    "optimization_score",
                    0.0,
                )
                or 0.0
            ),
            reverse=True,
        )

        recommended_name = (
            ranked[0].get(
                "option"
            )
            if ranked
            else None
        )

    if not recommended_name:
        raise ValueError(
            "Decision optimization did not provide "
            "a recommended intervention."
        )

    recommended_name = str(
        recommended_name
    ).strip()

    # ========================================================
    # 18. INTERVENTION COMPARISON
    # ========================================================

    comparison = (
        compare_intervention_options(
            options=options,
            recommended_option=recommended_name,
        )
    )

    comparison = _require_dict(
        comparison,
        "comparison",
    )

    # ========================================================
    # 19. TRADE-OFF
    # ========================================================

    tradeoff = build_decision_tradeoff(
        assessment=assessment,
        intervention=intervention,
        progression=progression,
        exposure=exposure,
    )

    tradeoff = _require_dict(
        tradeoff,
        "tradeoff",
    )

    # ========================================================
    # 20. OPERATIONAL PLAN
    # ========================================================

    operational = build_operational_plan(
        assessment=assessment,
        intervention=intervention,
        field_inspection=field_inspection,
        monitoring=monitoring,
        response=response,
        optimization=optimization,
        tradeoff=tradeoff,
    )

    operational = _require_dict(
        operational,
        "operational",
    )

    # ========================================================
    # 21. DECISION MASTER
    # ========================================================

    decision_master = build_decision_master(
        intervention=intervention,
        infrastructure=infrastructure,
        field=field_inspection,
        monitoring=monitoring,
        response=response,
        optimization=optimization,
        comparison=comparison,
        tradeoff=tradeoff,
        operational=operational,
    )

    decision_master = _require_dict(
        decision_master,
        "decision_master",
    )

    return DecisionIntelligenceResult(
        status="READY",
        cell_id=str(cell_id),
        regional_intelligence=regional,
        cluster=cluster,
        priority=priority,
        exposure=exposure,
        evolution=evolution,
        regional_command=regional_command,
        regional_master=regional_master,
        temporal=temporal,
        intervention=intervention,
        infrastructure=infrastructure,
        field_inspection=field_inspection,
        monitoring=monitoring,
        response=response,
        optimization=optimization,
        comparison=comparison,
        tradeoff=tradeoff,
        operational=operational,
        decision_master=decision_master,
    )


__all__ = [
    "DecisionIntelligenceResult",
    "run_decision_intelligence",
]

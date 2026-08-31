from __future__ import annotations

from typing import Any


from backend.app.ai.model_tool_loop import (
    build_ollama_tool,
)


# ============================================================
# CORE AWAREON EXECUTORS
# ============================================================


def execute_exact_cell_intelligence(
    cell_id: str,
) -> dict[str, Any]:

    from backend.app.exact_cell_intelligence import (
        build_exact_cell_intelligence,
    )

    result = build_exact_cell_intelligence(
        str(cell_id),
        100.0,
        5000.0,
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "exact_cell_intelligence returned "
            "a non-dictionary result."
        )

    return result


def execute_regional_intelligence(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    from backend.app.ai.regional_investigator import (
        investigate_region,
    )

    result = investigate_region(
        (
            "Analyze AwareOn regional intelligence "
            f"around {latitude}, {longitude}."
        ),
        latitude=float(latitude),
        longitude=float(longitude),
    )

    if hasattr(
        result,
        "to_dict",
    ):
        payload = result.to_dict()

    elif isinstance(
        result,
        dict,
    ):
        payload = result

    else:
        raise TypeError(
            "regional_intelligence returned "
            "an unsupported result type."
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(
            "regional_intelligence payload must "
            "be a dictionary."
        )

    return payload


def execute_scenario_simulation(
    rainfall_change_percent: float,
) -> dict[str, Any]:

    from backend.app.services.scenario_service import (
        scenario_service,
    )

    result = scenario_service.simulate(
        float(rainfall_change_percent)
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "scenario_simulation returned "
            "a non-dictionary result."
        )

    return result


def execute_historical_event_intelligence(
    query: str,
    limit: int = 10,
    radius_m: float = 25_000.0,
) -> dict[str, Any]:

    from backend.app.ai.historical_event_intelligence import (
        build_historical_event_intelligence,
    )

    result = build_historical_event_intelligence(
        query,
        limit=int(limit),
        radius_m=float(radius_m),
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "historical_event_intelligence returned "
            "a non-dictionary result."
        )

    return result


def execute_historical_trajectory(
    recent_days: int = 365,
    baseline_years: int = 5,
) -> dict[str, Any]:

    from backend.app.historical_trajectory import (
        build_historical_trajectory,
    )

    result = build_historical_trajectory(
        recent_days=int(recent_days),
        baseline_years=int(baseline_years),
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "historical_trajectory returned "
            "a non-dictionary result."
        )

    return result


# ============================================================
# FULL TEMPORAL / EARLY-WARNING ORCHESTRATION
# ============================================================


def execute_temporal_orchestrator(
    cell_id: str,
    latitude: float,
    longitude: float,
    recent_days: int = 30,
    baseline_years: int = 5,
) -> dict[str, Any]:

    from backend.app.ai.temporal_orchestrator import (
        run_temporal_intelligence,
    )

    # --------------------------------------------------------
    # Hop 1:
    # Obtain canonical regional intelligence.
    # --------------------------------------------------------

    regional_payload = (
        execute_regional_intelligence(
            latitude=float(latitude),
            longitude=float(longitude),
        )
    )

    tool_results = regional_payload.get(
        "tool_results",
        {},
    )

    if not isinstance(
        tool_results,
        dict,
    ):
        raise ValueError(
            "Regional investigation did not return "
            "a valid tool_results dictionary."
        )

    regional_intelligence = tool_results.get(
        "regional_intelligence",
    )

    if not isinstance(
        regional_intelligence,
        dict,
    ):
        raise ValueError(
            "Regional investigation did not return "
            "regional_intelligence."
        )

    # --------------------------------------------------------
    # Hop 2:
    # Execute the complete temporal intelligence graph.
    # --------------------------------------------------------

    result = run_temporal_intelligence(
        cell_id=str(cell_id),
        regional_intelligence=regional_intelligence,
        recent_days=int(recent_days),
        baseline_years=int(baseline_years),
    )

    if hasattr(
        result,
        "to_dict",
    ):
        payload = result.to_dict()

    elif isinstance(
        result,
        dict,
    ):
        payload = result

    else:
        raise TypeError(
            "temporal_orchestrator returned "
            "an unsupported result type."
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(
            "temporal_orchestrator payload must "
            "be a dictionary."
        )

    # Preserve the upstream result so the agent has
    # explicit multi-hop provenance.
    payload["orchestration"] = {
        "hop_1": {
            "tool":
                "regional_intelligence",

            "status":
                "READY",
        },

        "hop_2": {
            "tool":
                "temporal_orchestrator",

            "status":
                payload.get(
                    "status",
                    "UNKNOWN",
                ),
        },
    }

    payload["regional_source"] = (
        regional_intelligence
    )

    return payload


# ============================================================
# EARLY-WARNING MASTER
# ============================================================


def execute_early_warning_master(
    historical: dict[str, Any],
    regional_temporal: dict[str, Any],
    acceleration: dict[str, Any],
    anomaly_fusion: dict[str, Any],
    emerging_risk: dict[str, Any],
    early_warning: dict[str, Any],
    progression: dict[str, Any],
    coupling: dict[str, Any],
    multiscale: dict[str, Any],
) -> dict[str, Any]:

    from backend.app.early_warning_master import (
        build_early_warning_master,
    )

    result = build_early_warning_master(
        historical=historical,
        regional_temporal=regional_temporal,
        acceleration=acceleration,
        anomaly_fusion=anomaly_fusion,
        emerging_risk=emerging_risk,
        early_warning=early_warning,
        progression=progression,
        coupling=coupling,
        multiscale=multiscale,
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "early_warning_master returned "
            "a non-dictionary result."
        )

    return result


# ============================================================
# DECISION MASTER
# ============================================================


def execute_decision_master(
    intervention: dict[str, Any],
    infrastructure: dict[str, Any],
    field: dict[str, Any],
    monitoring: dict[str, Any],
    response: dict[str, Any],
    optimization: dict[str, Any],
    comparison: dict[str, Any],
    tradeoff: dict[str, Any],
    operational: dict[str, Any],
) -> dict[str, Any]:

    from backend.app.decision_master import (
        build_decision_master,
    )

    result = build_decision_master(
        intervention=intervention,
        infrastructure=infrastructure,
        field=field,
        monitoring=monitoring,
        response=response,
        optimization=optimization,
        comparison=comparison,
        tradeoff=tradeoff,
        operational=operational,
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "decision_master returned "
            "a non-dictionary result."
        )

    return result


# ============================================================
# TOOL SCHEMA HELPER
# ============================================================


def _schema(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
) -> dict[str, Any]:

    return build_ollama_tool(
        name,
        description,
        {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    )


# ============================================================
# OLLAMA TOOL DEFINITIONS
# ============================================================


def get_awareon_tools() -> list[dict[str, Any]]:

    return [

        # ----------------------------------------------------
        # EXACT CELL
        # ----------------------------------------------------

        _schema(
            "exact_cell_intelligence",
            (
                "Build comprehensive AwareOn intelligence "
                "for one exact risk cell."
            ),
            {
                "cell_id": {
                    "type": "string",
                    "description": (
                        "AwareOn spatial cell ID, "
                        "for example 506_422."
                    ),
                },
            },
            [
                "cell_id",
            ],
        ),

        # ----------------------------------------------------
        # REGIONAL
        # ----------------------------------------------------

        _schema(
            "regional_intelligence",
            (
                "Analyze AwareOn regional risk around "
                "a geographic coordinate."
            ),
            {
                "latitude": {
                    "type": "number",
                },
                "longitude": {
                    "type": "number",
                },
            },
            [
                "latitude",
                "longitude",
            ],
        ),

        # ----------------------------------------------------
        # SCENARIO
        # ----------------------------------------------------

        _schema(
            "scenario_simulation",
            (
                "Simulate the AwareOn risk system under "
                "a specified rainfall change."
            ),
            {
                "rainfall_change_percent": {
                    "type": "number",
                },
            },
            [
                "rainfall_change_percent",
            ],
        ),

        # ----------------------------------------------------
        # HISTORICAL
        # ----------------------------------------------------

        _schema(
            "historical_trajectory",
            (
                "Analyze the long-term environmental "
                "trajectory using the historical AwareOn "
                "environmental time series."
            ),
            {
                "recent_days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3650,
                },
                "baseline_years": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            [],
        ),

        # ----------------------------------------------------
        # FULL TEMPORAL ORCHESTRATOR
        # ----------------------------------------------------

        _schema(
            "temporal_orchestrator",
            (
                "Execute the complete AwareOn temporal and "
                "early-warning intelligence chain for a cell. "
                "This performs regional intelligence first, "
                "then runs historical, acceleration, anomaly "
                "fusion, emerging risk, early warning, event "
                "progression, temporal-scenario coupling, "
                "multiscale temporal analysis, and the final "
                "early-warning master."
            ),
            {
                "cell_id": {
                    "type": "string",
                    "description": (
                        "AwareOn spatial cell ID, "
                        "for example 506_422."
                    ),
                },
                "latitude": {
                    "type": "number",
                    "description": (
                        "Latitude associated with the "
                        "regional investigation."
                    ),
                },
                "longitude": {
                    "type": "number",
                    "description": (
                        "Longitude associated with the "
                        "regional investigation."
                    ),
                },
                "recent_days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3650,
                },
                "baseline_years": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            [
                "cell_id",
                "latitude",
                "longitude",
            ],
        ),

        # ----------------------------------------------------
        # EARLY-WARNING MASTER
        # ----------------------------------------------------

        _schema(
            "early_warning_master",
            (
                "Produce consolidated AwareOn early-warning "
                "intelligence from validated temporal and "
                "warning layers."
            ),
            {
                "historical": {
                    "type": "object",
                },
                "regional_temporal": {
                    "type": "object",
                },
                "acceleration": {
                    "type": "object",
                },
                "anomaly_fusion": {
                    "type": "object",
                },
                "emerging_risk": {
                    "type": "object",
                },
                "early_warning": {
                    "type": "object",
                },
                "progression": {
                    "type": "object",
                },
                "coupling": {
                    "type": "object",
                },
                "multiscale": {
                    "type": "object",
                },
            },
            [
                "historical",
                "regional_temporal",
                "acceleration",
                "anomaly_fusion",
                "emerging_risk",
                "early_warning",
                "progression",
                "coupling",
                "multiscale",
            ],
        ),

        # ----------------------------------------------------
        # DECISION MASTER
        # ----------------------------------------------------

        _schema(
            "decision_master",
            (
                "Produce consolidated AwareOn decision "
                "intelligence from validated operational "
                "and intervention layers."
            ),
            {
                "intervention": {
                    "type": "object",
                },
                "infrastructure": {
                    "type": "object",
                },
                "field": {
                    "type": "object",
                },
                "monitoring": {
                    "type": "object",
                },
                "response": {
                    "type": "object",
                },
                "optimization": {
                    "type": "object",
                },
                "comparison": {
                    "type": "object",
                },
                "tradeoff": {
                    "type": "object",
                },
                "operational": {
                    "type": "object",
                },
            },
            [
                "intervention",
                "infrastructure",
                "field",
                "monitoring",
                "response",
                "optimization",
                "comparison",
                "tradeoff",
                "operational",
            ],
        ),
    ]


# ============================================================
# EXECUTOR REGISTRY
# ============================================================


def get_awareon_executors() -> dict[str, Any]:

    return {
        "exact_cell_intelligence":
            execute_exact_cell_intelligence,

        "regional_intelligence":
            execute_regional_intelligence,

        "scenario_simulation":
            execute_scenario_simulation,

        "historical_trajectory":
            execute_historical_trajectory,

        "historical_event_intelligence":
            execute_historical_event_intelligence,

        "temporal_orchestrator":
            execute_temporal_orchestrator,

        "early_warning_master":
            execute_early_warning_master,

        "decision_master":
            execute_decision_master,
    }


__all__ = [
    "execute_exact_cell_intelligence",
    "execute_regional_intelligence",
    "execute_scenario_simulation",
    "execute_historical_trajectory",
    "execute_historical_event_intelligence",
    "execute_temporal_orchestrator",
    "execute_early_warning_master",
    "execute_decision_master",
    "get_awareon_tools",
    "get_awareon_executors",
]

from pathlib import Path

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from backend.app.core.engine_registry import get_engines
from backend.app.intelligence_api import router as intelligence_router
from backend.app.core.schemas import (
    AlertResponse,
    AssessmentResponse,
    EngineRegistryResponse,
    HealthResponse,
    IncidentResponse,
    RiskRecord,
    RiskResponse,
    GISCellResponse,
)


from backend.app.services.assessment_service import (
    assessment_service,
)

from backend.app.services.gis_service import (
    gis_service,
)

from backend.app.services.scenario_service import (
    scenario_service,
)


from backend.app.scenario_map import (
    build_scenario_map,
)

from backend.app.scenario_comparison import (
    compare_scenarios,
)

from backend.app.scenario_sensitivity import (
    rank_scenario_cells,
)

from backend.app.scenario_priority import (
    rank_scenario_priority,
)

from backend.app.scenario_recommendation import (
    build_scenario_recommendation,
)

from backend.app.scenario_decision import (
    build_decision_brief,
)


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INTELLIGENCE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "intelligence"
)

ENGINE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "engines"
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="AwareOn API",
    description=(
        "Landslide risk intelligence backend "
        "for the AwareOn system."
    ),
    version="0.9.0",
)
app.include_router(
    intelligence_router
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_origin_regex=r"https://.*\\.netlify\\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GENERIC CSV HELPER
# ============================================================

def load_csv(
    filename: str,
) -> pd.DataFrame:

    path = (
        INTELLIGENCE_DIR
        / filename
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Data file not found: "
                f"{filename}"
            ),
        )

    return pd.read_csv(
        path
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "AwareOn",
        "status": "online",
        "version": "0.9.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():

    return HealthResponse(
        status="healthy",

        intelligence_dir_exists=(
            INTELLIGENCE_DIR.exists()
        ),

        engine_dir_exists=(
            ENGINE_DIR.exists()
        ),
    )


# ============================================================
# ENGINE REGISTRY
# ============================================================

@app.get(
    "/api/v1/engines",
    response_model=EngineRegistryResponse,
)
def engines():

    registry = get_engines()

    return EngineRegistryResponse(
        count=len(registry),

        engines=[
            {
                "engine_id":
                    engine.engine_id,

                "name":
                    engine.name,

                "description":
                    engine.description,

                "output_file":
                    engine.output_file,
            }
            for engine in registry
        ],
    )


# ============================================================
# ALL RISK RECORDS
# ============================================================

@app.get(
    "/api/v1/risk",
    response_model=RiskResponse,
)
def risk():

    df = load_csv(
        "awareon_risk_decisions.csv"
    )

    return RiskResponse(
        count=len(df),

        data=df.to_dict(
            orient="records"
        ),
    )


# ============================================================
# SINGLE CELL RISK
# ============================================================

@app.get(
    "/api/v1/risk/{cell_id}",
    response_model=RiskRecord,
)
def risk_for_cell(
    cell_id: str,
):

    df = load_csv(
        "awareon_risk_decisions.csv"
    )

    matches = df[
        df["cell_id"]
        .astype(str)
        ==
        str(cell_id)
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Cell not found: "
                f"{cell_id}"
            ),
        )

    return RiskRecord(
        **matches.iloc[0].to_dict()
    )


# ============================================================
# UNIFIED ASSESSMENT
# ============================================================

@app.get(
    "/api/v1/assessment/{cell_id}",
    response_model=AssessmentResponse,
)
def assessment(
    cell_id: str,
):

    result = (
        assessment_service
        .get_assessment(
            cell_id
        )
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Cell not found: "
                f"{cell_id}"
            ),
        )

    return AssessmentResponse(
        **result
    )


# ============================================================
# GIS — SINGLE CELL
# ============================================================

@app.get(
    "/api/v1/gis/cell/{cell_id}",
    response_model=GISCellResponse,
)
def gis_cell(
    cell_id: str,
):

    try:

        result = (
            gis_service
            .get_cell(
                cell_id
            )
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"GIS cell not found: "
                f"{cell_id}"
            ),
        )

    return GISCellResponse(
        **result
    )


# ============================================================
# GIS — BOUNDARY
# ============================================================

@app.get(
    "/api/v1/gis/boundary"
)
def gis_boundary():

    try:

        result = (
            gis_service
            .get_boundary()
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# GIS — RISK LAYER
# ============================================================

@app.get(
    "/api/v1/gis/risk-layer"
)
def gis_risk_layer():

    try:

        result = (
            gis_service
            .get_risk_layer()
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# GIS — EXPOSURE LAYER
# ============================================================

@app.get(
    "/api/v1/gis/exposure-layer"
)
def gis_exposure_layer():

    try:

        result = (
            gis_service
            .get_exposure_layer()
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# GIS — HISTORICAL HOTSPOTS
# ============================================================

@app.get(
    "/api/v1/gis/historical-hotspots"
)
def gis_historical_hotspots():

    try:

        result = (
            gis_service
            .get_historical_hotspots()
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# GIS — PRIORITY INCIDENTS
# ============================================================

@app.get(
    "/api/v1/gis/priority-incidents"
)
def gis_priority_incidents():

    try:

        result = (
            gis_service
            .get_priority_incidents()
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# GIS — NEARBY CELLS
# ============================================================

@app.get(
    "/api/v1/gis/nearby"
)
def gis_nearby(
    latitude: float,
    longitude: float,
    radius_m: float = 5000.0,
):

    try:

        result = (
            gis_service
            .get_nearby_cells(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
            )
        )

        return JSONResponse(
            content=result
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# ALERTS
# ============================================================

@app.get(
    "/api/v1/alerts",
    response_model=AlertResponse,
)
def alerts():

    df = load_csv(
        "awareon_alerts.csv"
    )

    return AlertResponse(
        count=len(df),

        data=df.to_dict(
            orient="records"
        ),
    )


# ============================================================
# INCIDENTS
# ============================================================

@app.get(
    "/api/v1/incidents",
    response_model=IncidentResponse,
)
def incidents():

    df = load_csv(
        "awareon_prioritized_incidents.csv"
    )

    return IncidentResponse(
        count=len(df),

        data=df.to_dict(
            orient="records"
        ),
    )


# ============================================================
# SCENARIO — SUMMARY
# ============================================================

@app.get(
    "/api/v1/scenario/summary"
)
def scenario_summary():

    try:

        result = (
            scenario_service
            .get_summary()
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# SCENARIO — UNIFIED DECISION
# ============================================================

@app.get(
    "/api/v1/scenario/decision/{rainfall_change_percent}"
)
def scenario_decision(
    rainfall_change_percent: float,
):

    change = float(
        rainfall_change_percent
    )

    supported_values = {
        0.0,
        25.0,
        50.0,
        100.0,
    }

    if change not in supported_values:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "Unsupported rainfall scenario.",

                "supported_values":
                    sorted(
                        supported_values
                    ),

                "requested":
                    change,
            },
        )

    try:

        # ----------------------------------------------------
        # 1. Complete scenario summary
        # ----------------------------------------------------

        summary = (
            scenario_service
            .get_summary()
        )

        scenarios = summary.get(
            "scenarios",
            [],
        )

        if not scenarios:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Scenario summary "
                    "returned no scenarios."
                ),
            )


        # ----------------------------------------------------
        # 2. Requested scenario simulation
        # ----------------------------------------------------

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

            raise HTTPException(
                status_code=500,
                detail=(
                    "Scenario simulation "
                    "returned no records."
                ),
            )


        # ----------------------------------------------------
        # 3. Scenario comparison
        # ----------------------------------------------------

        comparison = (
            compare_scenarios(
                scenarios
            )
        )


        # ----------------------------------------------------
        # 4. Cell sensitivity
        # ----------------------------------------------------

        sensitivity = (
            rank_scenario_cells(
                records,
                top_k=1298,
            )
        )


        # ----------------------------------------------------
        # 5. Operational priority
        # ----------------------------------------------------

        priority = (
            rank_scenario_priority(
                sensitivity[
                    "all_cells"
                ],
                top_k=25,
            )
        )


        # ----------------------------------------------------
        # 6. Scenario recommendation
        # ----------------------------------------------------

        recommendation = (
            build_scenario_recommendation(
                summary,
                priority[
                    "top_priority_cells"
                ],
            )
        )


        # ----------------------------------------------------
        # 7. Decision brief
        # ----------------------------------------------------

        decision = (
            build_decision_brief(
                comparison,
                recommendation,
                priority,
            )
        )


        # ----------------------------------------------------
        # 8. Spatial intelligence
        # ----------------------------------------------------

        spatial = (
            build_scenario_map(
                records
            )
        )


        # ----------------------------------------------------
        # Return ONE authoritative object
        # ----------------------------------------------------

        return JSONResponse(
            content={
                "supported": True,

                "requested_rainfall_change_percent":
                    change,

                "scenario":
                    simulation.get(
                        "scenario"
                    ),

                "decision":
                    decision,

                "comparison":
                    comparison,

                "recommendation":
                    recommendation,

                "priority":
                    priority,

                "sensitivity_summary":
                    {
                        "record_count":
                            sensitivity[
                                "record_count"
                            ],

                        "escalating_cells":
                            sensitivity[
                                "escalating_cells"
                            ],

                        "high_or_extreme_escalations":
                            sensitivity[
                                "high_or_extreme_escalations"
                            ],

                        "extreme_escalations":
                            sensitivity[
                                "extreme_escalations"
                            ],

                        "very_high_sensitivity_cells":
                            sensitivity[
                                "very_high_sensitivity_cells"
                            ],
                    },

                "spatial":
                    spatial,
            }
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# SCENARIO — SPATIAL MAP INTELLIGENCE
# ============================================================

@app.get(
    "/api/v1/scenario/map/{rainfall_change_percent}"
)
def scenario_map(
    rainfall_change_percent: float,
):

    change = float(
        rainfall_change_percent
    )

    supported_values = {
        0.0,
        25.0,
        50.0,
        100.0,
    }

    if change not in supported_values:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "Unsupported rainfall scenario.",

                "supported_values":
                    sorted(
                        supported_values
                    ),

                "requested":
                    change,
            },
        )

    try:

        result = (
            scenario_service
            .simulate(
                change
            )
        )

        records = result.get(
            "records",
            [],
        )

        if not records:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Scenario simulation "
                    "returned no records."
                ),
            )

        map_result = (
            build_scenario_map(
                records
            )
        )

        return JSONResponse(
            content={
                "supported": True,
                **map_result,
            }
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# SCENARIO — SINGLE CELL
# ============================================================

@app.get(
    "/api/v1/scenario/{cell_id}"
)
def scenario_cell(
    cell_id: str,
):

    try:

        result = (
            scenario_service
            .get_cell_scenarios(
                cell_id
            )
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Scenario cell not found: "
                f"{cell_id}"
            ),
        )

    return JSONResponse(
        content=result
    )


# ============================================================
# SCENARIO — SIMULATE
# ============================================================

@app.post(
    "/api/v1/scenario/simulate"
)
def scenario_simulate(
    payload: dict,
):

    # --------------------------------------------------------
    # Accept either:
    #
    # rainfall_change_percent
    #
    # OR
    #
    # rainfall_multiplier
    #
    # Example:
    # {"rainfall_change_percent": 25}
    #
    # or:
    #
    # {"rainfall_multiplier": 1.25}
    # --------------------------------------------------------

    rainfall_change = payload.get(
        "rainfall_change_percent"
    )

    if rainfall_change is None:

        rainfall_multiplier = (
            payload.get(
                "rainfall_multiplier"
            )
        )

        if (
            rainfall_multiplier
            is not None
        ):

            try:

                rainfall_change = (
                    (
                        float(
                            rainfall_multiplier
                        )
                        - 1.0
                    )
                    * 100.0
                )

            except (
                TypeError,
                ValueError,
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "rainfall_multiplier "
                        "must be numeric."
                    ),
                )

    if rainfall_change is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Provide "
                "'rainfall_change_percent' "
                "or "
                "'rainfall_multiplier'."
            ),
        )

    try:

        rainfall_change = float(
            rainfall_change
        )

    except (
        TypeError,
        ValueError,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Rainfall scenario value "
                "must be numeric."
            ),
        )

    if not (
        rainfall_change
        >=
        0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Rainfall change cannot "
                "be negative."
            ),
        )

    try:

        result = (
            scenario_service
            .simulate(
                rainfall_change
            )
        )

        return JSONResponse(
            content=result
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# API INFORMATION
# ============================================================

@app.get(
    "/api/v1"
)
def api_info():

    return {
        "name": "AwareOn API",

        "version": "0.9.0",

        "status": "online",

        "groups": {

            "risk": [
                "/api/v1/risk",
                "/api/v1/risk/{cell_id}",
            ],

            "assessment": [
                "/api/v1/assessment/{cell_id}",
            ],

            "gis": [
                "/api/v1/gis/cell/{cell_id}",
                "/api/v1/gis/boundary",
                "/api/v1/gis/risk-layer",
                "/api/v1/gis/exposure-layer",
                "/api/v1/gis/historical-hotspots",
                "/api/v1/gis/priority-incidents",
                "/api/v1/gis/nearby",
            ],

            "alerts": [
                "/api/v1/alerts",
            ],

            "incidents": [
                "/api/v1/incidents",
            ],

            "scenario": [
                "/api/v1/scenario/summary",
                "/api/v1/scenario/decision/{rainfall_change_percent}",
                "/api/v1/scenario/map/{rainfall_change_percent}",
                "/api/v1/scenario/{cell_id}",
                "/api/v1/scenario/simulate",
            ],
        },
    }

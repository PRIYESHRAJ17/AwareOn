from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from backend.app.core.engine_registry import get_engines
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


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INTELLIGENCE_DIR = (
    ROOT / "data" / "processed" / "intelligence"
)

ENGINE_DIR = (
    ROOT / "data" / "processed" / "engines"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="AwareOn API",
    description=(
        "Landslide risk intelligence backend "
        "for the AwareOn system."
    ),
    version="0.6.0",
)


# ============================================================
# HELPERS
# ============================================================

def load_csv(filename: str) -> pd.DataFrame:

    path = INTELLIGENCE_DIR / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Data file not found: {filename}",
        )

    return pd.read_csv(path)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "AwareOn",
        "status": "online",
        "version": "0.6.0",
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
                "engine_id": engine.engine_id,
                "name": engine.name,
                "description": engine.description,
                "output_file": engine.output_file,
            }
            for engine in registry
        ],
    )


# ============================================================
# RISK — ALL CELLS
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
# RISK — SINGLE CELL
# ============================================================

@app.get(
    "/api/v1/risk/{cell_id}",
    response_model=RiskRecord,
)
def risk_for_cell(cell_id: str):

    df = load_csv(
        "awareon_risk_decisions.csv"
    )

    matches = df[
        df["cell_id"].astype(str)
        == str(cell_id)
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Cell not found: {cell_id}",
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
def assessment(cell_id: str):

    result = (
        assessment_service
        .get_assessment(cell_id)
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cell not found: {cell_id}",
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
def gis_cell(cell_id: str):

    try:

        result = gis_service.get_cell(
            cell_id
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"GIS cell not found: {cell_id}",
        )

    return GISCellResponse(
        **result
    )


# ============================================================
# GIS — SIKKIM BOUNDARY
# ============================================================

@app.get(
    "/api/v1/gis/boundary"
)
def gis_boundary():

    try:

        boundary = (
            gis_service
            .get_boundary()
        )

        return JSONResponse(
            content=boundary
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
@app.get(
    "/api/v1/gis/risk-layer"
)
def gis_risk_layer():

    try:

        return JSONResponse(
            content=(
                gis_service
                .get_risk_layer()
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
@app.get(
    "/api/v1/gis/nearby"
)
def gis_nearby(
    latitude: float,
    longitude: float,
    radius_m: float = 5000.0,
):

    try:

        result = gis_service.get_nearby_cells(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
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

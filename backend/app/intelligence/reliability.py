from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

import pandas as pd

EXPECTED_ENGINES = (
    "susceptibility_engine_output.csv",
    "rainfall_trigger_engine_output.csv",
    "soil_wetness_engine_output.csv",
    "terrain_instability_engine_output.csv",
    "sar_evidence_engine_output.csv",
    "historical_event_engine_output.csv",
    "anomaly_detection_engine_output.csv",
    "exposure_impact_engine_output.csv",
    "spatial_propagation_engine_output.csv",
    "temporal_risk_engine_output.csv",
    "confidence_uncertainty_engine_output.csv",
    "explanation_recommendation_engine_output.csv",
)


def health_snapshot(root: Path) -> dict[str, Any]:
    intelligence = root / "data" / "processed" / "intelligence"
    engines = root / "data" / "processed" / "engines"
    state_path = intelligence / "awareon_intelligence_state.csv"

    checks: list[dict[str, Any]] = []

    for filename in EXPECTED_ENGINES:
        path = engines / filename
        ok = path.exists() and path.stat().st_size > 0
        checks.append({"name": f"engine:{filename}", "status": "PASS" if ok else "FAIL"})

    state_ok = state_path.exists()
    state_rows = 0
    state_columns = 0
    state_issue = None
    if state_ok:
        try:
            state = pd.read_csv(state_path, nrows=5)
            state_columns = len(state.columns)
            state_rows = len(pd.read_csv(state_path, usecols=["cell_id"]))
            required = {
                "cell_id",
                "confidence_score",
                "uncertainty_score",
                "confidence_category",
                "confidence_explanation",
                "model_input_degraded",
                "environment_input_degraded",
            }
            missing = sorted(required - set(state.columns))
            if missing:
                state_issue = f"missing columns: {missing}"
                state_ok = False
        except Exception as exc:
            state_ok = False
            state_issue = str(exc)
    checks.append({"name": "canonical_intelligence_state", "status": "PASS" if state_ok else "FAIL", "details": state_issue})

    rasterio_available = importlib.util.find_spec("rasterio") is not None
    gdalinfo_available = importlib.util.find_spec("osgeo") is not None

    return {
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "DEGRADED",
        "checks": checks,
        "state_rows": state_rows,
        "state_columns": state_columns,
        "rasterio_available": rasterio_available,
        "osgeo_available": gdalinfo_available,
        "ai_provider": os.getenv("AWAREON_AI_PROVIDER", "ollama"),
        "ai_model": os.getenv("AWAREON_AI_MODEL", "qwen3.5:9b"),
        "ai_fallback_model": os.getenv("AWAREON_AI_FALLBACK_MODEL", "nemotron-3-nano:4b-q8_0"),
        "silent_fallback_forbidden": True,
    }

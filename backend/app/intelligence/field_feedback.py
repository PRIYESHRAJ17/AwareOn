from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import FieldObservation, clamp, utc_now
from .provenance import provenance_store


def _observation_id(cell_id: str, observed_condition: str, observed_at: str, observer: str) -> str:
    raw = f"{cell_id}|{observed_condition}|{observed_at}|{observer}"
    return "OBS-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20].upper()


def submit_observation(
    root: Path,
    *,
    cell_id: str,
    observed_condition: str,
    severity: float,
    observer: str,
    observed_at: str | None = None,
    notes: str = "",
    source: str = "FIELD",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observed_at = observed_at or utc_now()
    observation = FieldObservation(
        observation_id=_observation_id(cell_id, observed_condition, observed_at, observer),
        cell_id=str(cell_id),
        observed_condition=str(observed_condition).strip(),
        severity=clamp(severity),
        observer=str(observer).strip() or "UNKNOWN",
        observed_at=observed_at,
        submitted_at=utc_now(),
        source=str(source),
        notes=str(notes or ""),
        metadata=dict(metadata or {}),
    )
    observation_id = provenance_store.add_field_observation(observation)
    return compare_observation_to_prediction(root, observation_id)


def compare_observation_to_prediction(root: Path, observation_id: str) -> dict[str, Any]:
    observations = provenance_store.list_field_observations("", limit=1) if False else None
    db_path = provenance_store.path
    import sqlite3, json
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM field_observations WHERE observation_id=?",
            (observation_id,),
        ).fetchone()
    if row is None:
        raise KeyError(f"Unknown field observation: {observation_id}")

    state_path = root / "data" / "processed" / "intelligence" / "awareon_intelligence_state.csv"
    state = pd.read_csv(state_path)
    state["cell_id"] = state["cell_id"].astype(str)
    match = state.loc[state["cell_id"] == str(row["cell_id"])]
    if match.empty:
        raise KeyError(f"Unknown prediction cell: {row['cell_id']}")
    prediction = match.iloc[0]

    predicted_risk = float(prediction["unified_risk_score"])
    predicted_confidence = float(prediction["confidence_score"])
    observed = float(row["severity"])
    discrepancy = observed - predicted_risk
    agreement = clamp(100.0 - abs(discrepancy))

    if abs(discrepancy) <= 15:
        status = "ALIGNED"
    elif discrepancy > 15:
        status = "FIELD_HIGHER_THAN_MODEL"
    else:
        status = "FIELD_LOWER_THAN_MODEL"

    return {
        "observation_id": observation_id,
        "cell_id": str(row["cell_id"]),
        "observed_condition": row["observed_condition"],
        "observed_severity": observed,
        "predicted_risk": predicted_risk,
        "prediction_confidence": predicted_confidence,
        "discrepancy": discrepancy,
        "agreement_score": agreement,
        "reconciliation_status": status,
        "learning_eligible": bool(abs(discrepancy) > 15),
        "limitations": [
            "A field observation is treated as evidence, not an automatic correction to the model.",
            "Model parameters are not changed by this comparison.",
        ],
    }

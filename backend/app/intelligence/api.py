from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from .alert_lifecycle import alert_ledger, derive_operational_state
from .cascade_intelligence import build_cascade_impact
from .field_feedback import compare_observation_to_prediction, submit_observation
from .knowledge_manager import search_knowledge
from .reliability import health_snapshot
from .scenario_resilience import build_resilience_profile
from .validation import run_full_validation


ROOT = Path(__file__).resolve().parents[3]

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


@router.get("/health")
def intelligence_health() -> dict[str, Any]:
    return health_snapshot(ROOT)


@router.get("/cell/{cell_id}/resilience")
def cell_resilience(cell_id: str) -> dict[str, Any]:
    try:
        return build_resilience_profile(ROOT, cell_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cell/{cell_id}/cascade")
def cell_cascade(cell_id: str) -> dict[str, Any]:
    try:
        return build_cascade_impact(ROOT, cell_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/alerts/{cell_id}/state")
def alert_state(cell_id: str) -> dict[str, Any]:
    return {
        "cell_id": cell_id,
        "state": alert_ledger.current_state(cell_id),
        "events": alert_ledger.store.list_alert_events(cell_id),
    }


@router.post("/alerts/{cell_id}/evaluate")
def evaluate_alert(cell_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    required = ("risk_score", "confidence_score", "dynamic_signal")
    missing = [key for key in required if key not in payload]
    if missing:
        raise HTTPException(status_code=400, detail={"message": "Missing fields", "missing": missing})
    current = alert_ledger.current_state(cell_id)
    decision = derive_operational_state(
        float(payload["risk_score"]),
        float(payload["confidence_score"]),
        float(payload["dynamic_signal"]),
        current_state=current,
        persistence_count=int(payload.get("persistence_count", 1)),
    )
    decision = decision.__class__(
        cell_id=cell_id,
        state=decision.state,
        risk_score=decision.risk_score,
        confidence_score=decision.confidence_score,
        uncertainty_score=decision.uncertainty_score,
        dynamic_signal=decision.dynamic_signal,
        reason=decision.reason,
        evidence_ids=tuple(str(x) for x in payload.get("evidence_ids", [])),
        generated_at=decision.generated_at,
    )
    return decision.to_dict()


@router.post("/alerts/{cell_id}/transition")
def transition_alert(cell_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return alert_ledger.transition(
            cell_id,
            str(payload["target_state"]),
            actor=str(payload.get("actor", "SYSTEM")),
            reason=str(payload.get("reason", "No reason provided")),
            evidence_ids=[str(x) for x in payload.get("evidence_ids", [])],
        )
    except KeyError:
        raise HTTPException(status_code=400, detail="target_state is required")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/field/observation")
def field_observation(payload: dict[str, Any]) -> dict[str, Any]:
    required = ("cell_id", "observed_condition", "severity", "observer")
    missing = [key for key in required if key not in payload]
    if missing:
        raise HTTPException(status_code=400, detail={"missing": missing})
    try:
        return submit_observation(
            ROOT,
            cell_id=str(payload["cell_id"]),
            observed_condition=str(payload["observed_condition"]),
            severity=float(payload["severity"]),
            observer=str(payload["observer"]),
            observed_at=payload.get("observed_at"),
            notes=str(payload.get("notes", "")),
            source=str(payload.get("source", "FIELD")),
            metadata=payload.get("metadata") or {},
        )
    except (ValueError, KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/field/{cell_id}")
def field_observations(cell_id: str) -> dict[str, Any]:
    observations = alert_ledger.store.list_field_observations(cell_id)
    return {"cell_id": cell_id, "count": len(observations), "observations": observations}


@router.get("/knowledge/search")
def knowledge(query: str, limit: int = 10) -> dict[str, Any]:
    return {"query": query, "results": search_knowledge(query, limit=limit)}


@router.post("/validate")
def validate() -> dict[str, Any]:
    return run_full_validation(ROOT)

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any


ALERT_STATES = (
    "NORMAL",
    "WATCH",
    "ADVISORY",
    "WARNING",
    "CRITICAL",
    "RESOLVED",
    "EXPIRED",
)

OBSERVATION_STATUSES = (
    "SUBMITTED",
    "VERIFIED",
    "REJECTED",
    "STALE",
)

EVIDENCE_TYPES = (
    "CURRENT",
    "HISTORICAL",
    "DERIVED",
    "SIMULATED",
    "FORECAST",
    "FIELD",
    "KNOWLEDGE",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return min(upper, max(lower, float(value)))


def finite(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if math.isfinite(parsed) else float(default)


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_type: str
    source: str
    source_id: str | None
    source_timestamp: str | None
    ingestion_timestamp: str
    freshness_seconds: float | None
    geographic_scope: str | None
    dataset_version: str | None
    provenance: dict[str, Any]
    quality: float
    conflict_state: str
    claim: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def checksum(self) -> str:
        return stable_hash(self.to_dict())


@dataclass(frozen=True)
class AlertDecision:
    cell_id: str
    state: str
    risk_score: float
    confidence_score: float
    uncertainty_score: float
    dynamic_signal: float
    reason: str
    evidence_ids: tuple[str, ...] = ()
    generated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenarioProfile:
    cell_id: str
    supported_scenarios: tuple[str, ...]
    baseline_risk: float
    worst_case_risk: float
    worst_case_scenario: str
    max_risk_delta: float
    threshold_crossings: tuple[str, ...]
    monotonic_rainfall_response: bool
    robustness_score: float
    evidence_type: str = "SIMULATED"
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CascadeImpact:
    origin_cell_id: str
    impacted_cells: tuple[str, ...]
    impacted_domains: tuple[str, ...]
    cascade_score: float
    dependency_confidence: float
    modeled_proxy: bool
    assumptions: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FieldObservation:
    observation_id: str
    cell_id: str
    observed_condition: str
    severity: float
    observer: str
    observed_at: str
    submitted_at: str
    source: str
    verification_status: str = "SUBMITTED"
    notes: str = ""
    evidence_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionTrace:
    trace_id: str
    query: str
    domain: str
    intent: str
    tools_used: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verification_status: str
    model_provider: str | None
    model_name: str | None
    degraded: bool
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_evidence(record: EvidenceRecord) -> None:
    if not record.evidence_id:
        raise ValueError("Evidence ID is required.")
    if record.evidence_type not in EVIDENCE_TYPES:
        raise ValueError(f"Unsupported evidence type: {record.evidence_type}")
    if not record.source:
        raise ValueError("Evidence source is required.")
    if not record.claim.strip():
        raise ValueError("Evidence claim is required.")
    if not 0.0 <= float(record.quality) <= 100.0:
        raise ValueError("Evidence quality must be 0-100.")


def validate_alert_state(state: str) -> None:
    if state not in ALERT_STATES:
        raise ValueError(f"Unsupported alert state: {state}")


def validate_field_observation(observation: FieldObservation) -> None:
    if not observation.cell_id or "_" not in observation.cell_id:
        raise ValueError("A valid AwareOn cell_id is required.")
    if not observation.observed_condition.strip():
        raise ValueError("Observed condition is required.")
    if not 0.0 <= float(observation.severity) <= 100.0:
        raise ValueError("Field severity must be 0-100.")
    if observation.verification_status not in OBSERVATION_STATUSES:
        raise ValueError("Unsupported field observation status.")

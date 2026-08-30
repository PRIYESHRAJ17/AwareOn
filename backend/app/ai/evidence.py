from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


# ============================================================
# EVIDENCE TYPES
# ============================================================

class EvidenceType:
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    SIMULATED = "SIMULATED"
    INFERRED = "INFERRED"
    RECOMMENDATION = "RECOMMENDATION"


# ============================================================
# EVIDENCE ITEM
# ============================================================

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_tool: str
    evidence_type: str
    claim: str
    value: Any = None
    source_id: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# EVIDENCE PACKAGE
# ============================================================

@dataclass
class EvidencePackage:
    query: str
    items: list[EvidenceItem] = field(
        default_factory=list
    )

    def add(
        self,
        source_tool: str,
        evidence_type: str,
        claim: str,
        value: Any = None,
        source_id: str | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceItem:

        if not claim.strip():
            raise ValueError(
                "Evidence claim cannot be empty."
            )

        if not 0.0 <= (
            confidence
            if confidence is not None
            else 0.0
        ) <= 100.0:
            raise ValueError(
                "Evidence confidence must be "
                "between 0 and 100."
            )

        item = EvidenceItem(
            evidence_id=(
                f"EVD-{uuid4().hex[:12].upper()}"
            ),
            source_tool=source_tool,
            evidence_type=evidence_type,
            claim=claim,
            value=value,
            source_id=source_id,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.items.append(
            item
        )

        return item

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "count": len(self.items),
            "items": [
                item.to_dict()
                for item in self.items
            ],
        }


# ============================================================
# PROVENANCE BUILDER
# ============================================================

def build_provenance(
    source_tool: str,
    evidence_type: str,
    claim: str,
    *,
    value: Any = None,
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:

    if confidence is not None:
        if not 0.0 <= confidence <= 100.0:
            raise ValueError(
                "confidence must be between 0 and 100."
            )

    item = EvidenceItem(
        evidence_id=(
            f"EVD-{uuid4().hex[:12].upper()}"
        ),
        source_tool=source_tool,
        evidence_type=evidence_type,
        claim=claim,
        value=value,
        source_id=source_id,
        confidence=confidence,
        metadata=metadata or {},
    )

    return item.to_dict()


# ============================================================
# EVIDENCE TYPE HELPERS
# ============================================================

def classify_evidence_type(
    source_tool: str,
) -> str:

    simulated_tools = {
        "scenario_simulation",
        "scenario_forecast",
        "scenario_sensitivity",
        "scenario_thresholds",
    }

    observed_tools = {
        "nearby_cells",
        "historical_trajectory",
    }

    recommendation_tools = {
        "decision_master",
        "response_recommendation",
        "intervention_priority",
        "field_inspection",
        "monitoring_priority",
    }

    if source_tool in simulated_tools:
        return EvidenceType.SIMULATED

    if source_tool in observed_tools:
        return EvidenceType.OBSERVED

    if source_tool in recommendation_tools:
        return EvidenceType.RECOMMENDATION

    return EvidenceType.MODEL_OUTPUT

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ============================================================
# EXECUTION TRACE
# ============================================================

@dataclass
class AgentStep:
    step_number: int
    action: str
    target: str
    status: str
    result_summary: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "action": self.action,
            "target": self.target,
            "status": self.status,
            "result_summary": self.result_summary,
            "metadata": self.metadata,
        }


# ============================================================
# INVESTIGATION MEMORY
# ============================================================

# AWAREON LEARNING CANDIDATE PROPOSAL V6
@dataclass
class LearningCandidateProposal:
    candidate_id: str
    category: str
    query: str
    observation: str
    evidence: tuple[str, ...]
    confidence: float
    approved: bool = False
    approval_required: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "category": self.category,
            "query": self.query,
            "observation": self.observation,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "approved": self.approved,
            "approval_required": self.approval_required,
            "created_at": self.created_at,
        }

@dataclass
class InvestigationMemory:
    investigation_id: str
    query: str
    created_at: str
    steps: list[AgentStep] = field(
        default_factory=list
    )
    facts: list[dict[str, Any]] = field(
        default_factory=list
    )
    evidence_ids: list[str] = field(
        default_factory=list
    )
    learning_candidates: list[LearningCandidateProposal] = field(
        default_factory=list
    )

    def add_step(
        self,
        action: str,
        target: str,
        status: str,
        result_summary: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AgentStep:

        step = AgentStep(
            step_number=len(self.steps) + 1,
            action=action,
            target=target,
            status=status,
            result_summary=result_summary,
            metadata=metadata or {},
        )

        self.steps.append(step)

        return step

    def add_fact(
        self,
        claim: str,
        value: Any,
        source: str,
        evidence_type: str,
    ) -> None:

        self.facts.append(
            {
                "claim": claim,
                "value": value,
                "source": source,
                "evidence_type": evidence_type,
            }
        )

    def add_evidence_id(
        self,
        evidence_id: str,
    ) -> None:

        if evidence_id not in self.evidence_ids:
            self.evidence_ids.append(
                evidence_id
            )

    def add_learning_candidate(
        self,
        category: str,
        observation: str,
        evidence: list[str] | tuple[str, ...],
        confidence: float,
    ) -> LearningCandidateProposal:
        # Review-gated proposal only; no model or production-policy mutation.
        import math
        candidate_evidence = tuple(dict.fromkeys(str(item) for item in evidence if str(item).strip()))
        numeric_confidence = float(confidence)
        if not category or not observation or not candidate_evidence:
            raise ValueError("learning candidate requires category, observation, and evidence")
        if not math.isfinite(numeric_confidence) or not 0.0 <= numeric_confidence <= 1.0:
            raise ValueError("learning candidate confidence must be finite and within [0,1]")
        candidate = LearningCandidateProposal(
            candidate_id=f"LC-{self.investigation_id}-{len(self.learning_candidates) + 1:03d}",
            category=str(category),
            query=self.query,
            observation=str(observation),
            evidence=candidate_evidence,
            confidence=numeric_confidence,
        )
        self.learning_candidates.append(candidate)
        for evidence_id in candidate_evidence:
            self.add_evidence_id(evidence_id)
        self.add_step(
            action="LEARNING_CANDIDATE",
            target="investigation_memory",
            status="PROPOSED",
            result_summary=f"Review-gated candidate {candidate.candidate_id} created; no model or policy mutation.",
            metadata={"candidate_id": candidate.candidate_id, "approval_required": True},
        )
        return candidate

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id":
                self.investigation_id,

            "query":
                self.query,

            "created_at":
                self.created_at,

            "steps": [
                item.to_dict()
                for item in self.steps
            ],

            "facts":
                self.facts,

            "evidence_ids":
                self.evidence_ids,

            "learning_candidates": [
                item.to_dict()
                for item in self.learning_candidates
            ],

        }


# ============================================================
# MEMORY FACTORY
# ============================================================

def create_investigation_memory(
    investigation_id: str,
    query: str,
) -> InvestigationMemory:

    return InvestigationMemory(
        investigation_id=investigation_id,
        query=query,
        created_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

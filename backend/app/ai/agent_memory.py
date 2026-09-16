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

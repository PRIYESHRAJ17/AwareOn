from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EvidenceItem:
    source_type: str
    source_id: str
    claim: str
    value: Any = None
    status: str = "SUPPORTED"


@dataclass
class AIResponse:
    answer: str
    domain: str
    intent: str
    confidence: float
    evidence: list[EvidenceItem] = field(
        default_factory=list
    )
    tools_used: list[str] = field(
        default_factory=list
    )
    inferences: list[str] = field(
        default_factory=list
    )
    limitations: list[str] = field(
        default_factory=list
    )
    refusal_reason: str | None = None
    # AWAREON INTELLIGENCE CONTRACT V1
    claims: list[dict[str, Any]] = field(
        default_factory=list
    )
    evidence_ids: list[str] = field(
        default_factory=list
    )
    uncertainties: list[str] = field(
        default_factory=list
    )
    model_identity: dict[str, Any] = field(
        default_factory=dict
    )
    verification: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:

        if not isinstance(
            self.answer,
            str,
        ) or not self.answer.strip():

            raise ValueError(
                "AIResponse.answer must be non-empty."
            )

        if not 0.0 <= self.confidence <= 100.0:

            raise ValueError(
                "AIResponse.confidence must be "
                "between 0 and 100."
            )

        if not isinstance(
            self.evidence,
            list,
        ):
            raise ValueError(
                "evidence must be a list."
            )

        if not isinstance(
            self.tools_used,
            list,
        ):
            raise ValueError(
                "tools_used must be a list."
            )

        # AWAREON INTELLIGENCE PROVENANCE V1
        # Build canonical claim-to-evidence links from supplied evidence.
        if not self.evidence_ids:
            self.evidence_ids = []
        for item in self.evidence:
            source_id = str(getattr(item, "source_id", "") or "").strip()
            claim = str(getattr(item, "claim", "") or "").strip()
            if source_id and source_id not in self.evidence_ids:
                self.evidence_ids.append(source_id)
            if claim:
                mapped = {
                    "claim": claim,
                    "evidence_ids": [source_id] if source_id else [],
                    "status": str(getattr(item, "status", "SUPPORTED") or "SUPPORTED").upper(),
                    "source_type": str(getattr(item, "source_type", "")),
                }
                if mapped not in self.claims:
                    self.claims.append(mapped)

        if not self.model_identity:
            import os
            self.model_identity = {
                "provider": os.getenv("AWAREON_AI_PROVIDER", "ollama"),
                "model": os.getenv("AWAREON_AI_MODEL", "qwen3.5:9b"),
                "fallback_model": os.getenv("AWAREON_AI_FALLBACK_MODEL", "nemotron-3-nano:4b-q8_0"),
            }
        if self.confidence < 60.0 and "Low response confidence." not in self.uncertainties:
            self.uncertainties.append("Low response confidence.")
        for limitation in self.limitations:
            if limitation not in self.uncertainties:
                self.uncertainties.append(limitation)


def build_out_of_domain_response(
    query: str,
    *,
    confidence: float,
) -> AIResponse:

    response = AIResponse(
        answer=(
            "This question is outside AwareOn's "
            "specialized research domain. AwareOn is "
            "designed for landslide, environmental, "
            "spatial, temporal, scenario, warning, "
            "exposure, and operational-risk intelligence."
        ),
        domain="OUTSIDE_DOMAIN",
        intent="UNKNOWN",
        confidence=float(confidence),
        limitations=[
            "No AwareOn specialized intelligence "
            "was used because the query is outside "
            "the system's defined research scope."
        ],
        refusal_reason=(
            f"Out-of-domain query: {query}"
        ),
    )

    response.validate()

    return response


def build_ambiguous_response(
    *,
    confidence: float,
) -> AIResponse:

    response = AIResponse(
        answer=(
            "I need a little more context to determine "
            "which AwareOn intelligence capability "
            "should investigate this."
        ),
        domain="AMBIGUOUS",
        intent="UNKNOWN",
        confidence=float(confidence),
        limitations=[
            "The query did not provide enough "
            "information for reliable routing."
        ],
    )

    response.validate()

    return response

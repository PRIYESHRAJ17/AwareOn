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


def build_out_of_domain_response(
    query: str,
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
        confidence=99.0,
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


def build_ambiguous_response() -> AIResponse:

    response = AIResponse(
        answer=(
            "I need a little more context to determine "
            "which AwareOn intelligence capability "
            "should investigate this."
        ),
        domain="AMBIGUOUS",
        intent="UNKNOWN",
        confidence=50.0,
        limitations=[
            "The query did not provide enough "
            "information for reliable routing."
        ],
    )

    response.validate()

    return response

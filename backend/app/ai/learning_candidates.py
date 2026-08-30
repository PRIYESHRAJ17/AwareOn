from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from backend.app.ai.learning_memory import (
    LearningRecord,
    learning_memory,
)


@dataclass(frozen=True)
class LearningCandidate:
    query: str
    lesson: str
    evidence_ids: tuple[str, ...]
    confidence: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "lesson": self.lesson,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


# ============================================================
# HELPERS
# ============================================================

def _clean(value: Any) -> str:
    return " ".join(
        str(value or "").split()
    ).strip()


def _claim_text(claim: Any) -> str:
    return _clean(
        getattr(
            claim,
            "claim",
            "",
        )
    )


def _claim_evidence(claim: Any) -> list[str]:
    return list(
        getattr(
            claim,
            "evidence_ids",
            [],
        )
        or []
    )


def _is_verified(claim: Any) -> bool:
    return (
        str(
            getattr(
                claim,
                "status",
                "",
            )
        ).upper()
        == "VERIFIED"
    )


def _is_generalizable(
    lesson: str,
) -> bool:
    text = lesson.lower()

    # A reusable lesson should describe a relationship,
    # pattern, interpretation, or diagnostic principle.
    relationship_markers = (
        "can ",
        "may ",
        "when ",
        "even when ",
        "despite ",
        "associated with ",
        "driven by ",
        "dominated by ",
        "suggests ",
        "indicates ",
        "pattern",
        "relationship",
        "combination",
        "convergence",
        "divergence",
        "structural",
        "spatial",
        "temporal",
    )

    if not any(
        marker in text
        for marker in relationship_markers
    ):
        return False

    # Reject obvious one-record memorization.
    if re.search(
        r"\b\d{2,4}[_-]\d{2,4}\b",
        lesson,
    ):
        return False

    # Reject lessons whose main content is a raw score dump.
    number_count = len(
        re.findall(
            r"[-+]?\d+(?:\.\d+)?",
            lesson,
        )
    )

    if number_count > 2:
        return False

    forbidden = (
        "change threshold",
        "change formula",
        "modify engine",
        "rewrite risk",
        "change weight",
        "alter policy",
        "disable verifier",
    )

    if any(
        phrase in text
        for phrase in forbidden
    ):
        return False

    return True


# ============================================================
# PATTERN BUILDER
# ============================================================

def _build_structural_pattern(
    claims: list[Any],
) -> tuple[
    str,
    list[str],
] | None:

    verified = [
        claim
        for claim in claims
        if _is_verified(claim)
    ]

    if len(verified) < 3:
        return None

    text = " ".join(
        _claim_text(
            claim
        )
        for claim in verified
    ).lower()

    evidence_ids: list[str] = []

    for claim in verified:
        for evidence_id in _claim_evidence(
            claim
        ):
            if evidence_id not in evidence_ids:
                evidence_ids.append(
                    evidence_id
                )

    # --------------------------------------------------------
    # Detect the specific high-value AwareOn pattern.
    # --------------------------------------------------------

    has_extreme_severity = (
        "severity extreme" in text
    )

    has_very_high_susceptibility = (
        "susceptibility category very_high"
        in text
    )

    has_extreme_terrain = (
        "terrain instability category extreme"
        in text
    )

    has_high_exposure = (
        "exposure category high" in text
    )

    has_strong_spatial = (
        "spatial pressure score" in text
        or
        "spatial pattern high_risk_cluster"
        in text
    )

    has_low_dynamic = (
        "rainfall trigger category low" in text
        or
        "soil wetness category low" in text
        or
        "temporal trajectory stable_low"
        in text
    )

    if (
        has_extreme_severity
        and has_very_high_susceptibility
        and has_extreme_terrain
        and has_strong_spatial
    ):

        lesson = (
            "AwareOn extreme risk can be driven by a "
            "combination of very high susceptibility, "
            "extreme terrain instability, and strong "
            "spatial pressure or clustering; therefore "
            "extreme current risk should not be interpreted "
            "solely from short-term rainfall or soil signals."
        )

        if has_high_exposure:
            lesson += (
                " High exposed-asset or transport exposure "
                "can further increase operational importance."
            )

        if has_low_dynamic:
            lesson += (
                " This pattern can remain present even when "
                "some current dynamic environmental indicators "
                "are LOW or the short-term temporal state is stable."
            )

        return (
            lesson,
            evidence_ids,
        )

    return None


# ============================================================
# CANDIDATE BUILDER
# ============================================================

def build_learning_candidate(
    query: str,
    verified_claims: list[Any],
) -> LearningCandidate | None:

    pattern = _build_structural_pattern(
        verified_claims
    )

    if pattern is None:
        return None

    lesson, evidence_ids = pattern

    if not _is_generalizable(
        lesson
    ):
        return None

    return LearningCandidate(
        query=_clean(
            query
        ),
        lesson=lesson,
        evidence_ids=tuple(
            evidence_ids
        ),
        confidence=0.90,
        rationale=(
            "Generalizable pattern derived only from "
            "verified AwareOn claims. The candidate "
            "describes an interpretable relationship "
            "rather than memorizing a single cell."
        ),
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_learning_candidate(
    candidate: LearningCandidate | None,
) -> bool:

    if candidate is None:
        return False

    if not candidate.query:
        return False

    if not candidate.lesson:
        return False

    if not candidate.evidence_ids:
        return False

    if not (
        0.0
        <= candidate.confidence
        <= 1.0
    ):
        return False

    if candidate.confidence < 0.80:
        return False

    if not _is_generalizable(
        candidate.lesson
    ):
        return False

    return True


# ============================================================
# STORE
# ============================================================

def store_validated_candidate(
    candidate: LearningCandidate | None,
) -> LearningRecord | None:

    if not validate_learning_candidate(
        candidate
    ):
        return None

    existing = learning_memory.search(
        candidate.lesson,
        limit=10,
    )

    for record in existing:

        if (
            record.lesson.lower()
            == candidate.lesson.lower()
        ):
            return record

    return learning_memory.store(
        query=candidate.query,
        lesson=candidate.lesson,
        evidence_ids=list(
            candidate.evidence_ids
        ),
        confidence=candidate.confidence,
        status="VALIDATED",
    )

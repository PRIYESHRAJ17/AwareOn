from __future__ import annotations

import hashlib
from typing import Any

from .provenance import provenance_store


def propose_lesson(
    lesson: str,
    evidence_ids: list[str],
    confidence: float,
    *,
    scope: str = "AWAREON",
) -> dict[str, Any]:
    lesson = " ".join(str(lesson).split()).strip()
    if not lesson:
        raise ValueError("Lesson is required.")
    if not evidence_ids:
        raise ValueError("Evidence-linked learning is required.")
    if not 0.0 <= float(confidence) <= 1.0:
        raise ValueError("Learning confidence must be 0-1.")
    knowledge_id = "KNOW-" + hashlib.sha256(
        (lesson + "|" + "|".join(sorted(evidence_ids))).encode("utf-8")
    ).hexdigest()[:20].upper()
    return {
        "knowledge_id": knowledge_id,
        "lesson": lesson,
        "evidence_ids": sorted(set(evidence_ids)),
        "confidence": float(confidence),
        "scope": scope,
        "status": "CANDIDATE",
        "policy_mutation": False,
    }


def validate_lesson(candidate: dict[str, Any]) -> dict[str, Any]:
    if not candidate.get("evidence_ids"):
        raise ValueError("Candidate has no evidence links.")
    lesson = str(candidate.get("lesson", ""))
    forbidden = (
        "change threshold",
        "change formula",
        "change weight",
        "disable verifier",
        "alter policy",
    )
    if any(item in lesson.lower() for item in forbidden):
        raise ValueError("Learning candidate attempts prohibited policy mutation.")
    confidence = float(candidate.get("confidence", 0.0))
    if confidence < 0.80:
        raise ValueError("Learning candidate confidence is below validation threshold.")
    return {**candidate, "status": "VALIDATED"}


def commit_lesson(candidate: dict[str, Any]) -> dict[str, Any]:
    validated = validate_lesson(candidate)
    provenance_store.add_knowledge(
        validated["knowledge_id"],
        validated["lesson"],
        validated["evidence_ids"],
        float(validated["confidence"]),
        scope=str(validated.get("scope", "AWAREON")),
        status="VALIDATED",
    )
    return {**validated, "committed": True}


def search_knowledge(query: str, limit: int = 10) -> list[dict[str, Any]]:
    return provenance_store.knowledge_search(query, limit=limit)

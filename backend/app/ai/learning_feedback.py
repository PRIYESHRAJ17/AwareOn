from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.ai.learning_memory import (
    LearningMemory,
    LearningRecord,
    learning_memory,
)


@dataclass(frozen=True)
class LearningFeedback:
    query: str
    records: tuple[LearningRecord, ...]
    context: str

    @property
    def count(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "count": self.count,
            "records": [
                record.to_dict()
                for record in self.records
            ],
            "context": self.context,
        }


def retrieve_learning_feedback(
    query: str,
    *,
    memory: LearningMemory | None = None,
    limit: int = 5,
    min_confidence: float = 0.80,
) -> LearningFeedback:

    if not isinstance(query, str):
        raise TypeError(
            "query must be a string."
        )

    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0."
        )

    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError(
            "min_confidence must be between 0 and 1."
        )

    store = (
        memory
        if memory is not None
        else learning_memory
    )

    records = store.search(
        query,
        limit=max(
            limit * 2,
            limit,
        ),
    )

    validated: list[LearningRecord] = []

    for record in records:
        if str(
            record.status
        ).upper() != "VALIDATED":
            continue

        if record.confidence < min_confidence:
            continue

        validated.append(
            record
        )

        if len(validated) >= limit:
            break

    context_lines: list[str] = []

    for index, record in enumerate(
        validated,
        start=1,
    ):
        context_lines.append(
            (
                f"Lesson {index}: "
                f"{record.lesson}"
            )
        )

    if context_lines:
        context = (
            "Previously validated AwareOn lessons. "
            "Use these only as learned guidance; "
            "current canonical evidence always takes precedence.\n"
            + "\n".join(context_lines)
        )
    else:
        context = (
            "No previously validated AwareOn lessons "
            "were relevant to this query."
        )

    return LearningFeedback(
        query=query,
        records=tuple(validated),
        context=context,
    )


def learning_context_for_query(
    query: str,
    *,
    memory: LearningMemory | None = None,
    limit: int = 5,
) -> str:
    return retrieve_learning_feedback(
        query,
        memory=memory,
        limit=limit,
    ).context


__all__ = [
    "LearningFeedback",
    "retrieve_learning_feedback",
    "learning_context_for_query",
]

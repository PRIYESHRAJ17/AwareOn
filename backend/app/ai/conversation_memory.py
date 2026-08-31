from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationTurn:
    query: str
    answer: str
    intent: str
    status: str
    facts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "intent": self.intent,
            "status": self.status,
            "facts": self.facts,
        }


@dataclass
class ConversationMemory:
    session_id: str
    turns: list[ConversationTurn] = field(
        default_factory=list
    )

    def add_turn(
        self,
        *,
        query: str,
        answer: str,
        intent: str,
        status: str,
        facts: list[dict[str, Any]] | None = None,
    ) -> None:

        self.turns.append(
            ConversationTurn(
                query=query,
                answer=answer,
                intent=intent,
                status=status,
                facts=list(
                    facts or []
                ),
            )
        )

    @property
    def last_turn(self) -> ConversationTurn | None:
        if not self.turns:
            return None

        return self.turns[-1]

    @property
    def recent_turns(self) -> list[ConversationTurn]:
        return self.turns[-6:]

    def context_text(self) -> str:
        if not self.turns:
            return ""

        lines = [
            "CONVERSATION CONTEXT:"
        ]

        for index, turn in enumerate(
            self.recent_turns,
            start=1,
        ):

            lines.append(
                (
                    f"TURN {index}: "
                    f"USER={turn.query}"
                )
            )

            if turn.intent:
                lines.append(
                    f"INTENT={turn.intent}"
                )

            if turn.facts:
                lines.append(
                    "FACTS="
                    + str(
                        turn.facts
                    )
                )

            if turn.answer:
                lines.append(
                    "ANSWER="
                    + turn.answer
                )

        return "\n".join(lines)

    def resolve_references(
        self,
        query: str,
    ) -> str:

        last = self.last_turn

        if last is None:
            return query

        text = query.strip()
        lower = text.lower()

        references = (
            "that",
            "that situation",
            "that slope",
            "same slope",
            "same area",
            "that area",
            "this area",
            "this slope",
            "there",
            "it",
            "they",
            "those",
            "the same",
            "previously",
            "earlier",
        )

        needs_context = any(
            phrase in lower
            for phrase in references
        )

        if not needs_context:
            return query

        previous_query = last.query.strip()

        previous_facts = []

        for fact in last.facts[:8]:

            if not isinstance(
                fact,
                dict,
            ):
                continue

            claim = str(
                fact.get(
                    "claim",
                    "",
                )
            ).strip()

            if claim:
                previous_facts.append(
                    claim
                )

        lines = [
            "CONTEXT FROM PREVIOUS TURN:",
            f"Previous user question: {previous_query}",
        ]

        if previous_facts:
            lines.append(
                "Relevant established facts:"
            )

            lines.extend(
                f"- {fact}"
                for fact in previous_facts[:5]
            )

        lines.extend(
            [
                "",
                "CURRENT USER QUESTION:",
                text,
                "",
                (
                    "Resolve references using only the "
                    "previous-turn context above."
                ),
            ]
        )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_count": len(
                self.turns
            ),
            "turns": [
                turn.to_dict()
                for turn in self.turns
            ],
        }


def create_conversation_memory(
    session_id: str,
) -> ConversationMemory:

    return ConversationMemory(
        session_id=session_id
    )


__all__ = [
    "ConversationTurn",
    "ConversationMemory",
    "create_conversation_memory",
]

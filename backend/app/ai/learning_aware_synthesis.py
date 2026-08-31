from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.ai.domain_retrieval import (
    build_semantic_knowledge_context,
)
from backend.app.ai.evidence_synthesis import (
    EvidenceSynthesisResult,
    synthesize_with_verification,
)
from backend.app.ai.learning_feedback import (
    LearningFeedback,
    retrieve_learning_feedback,
)
from backend.app.ai.learning_memory import (
    LearningMemory,
)
from backend.app.ai.model_adapter import (
    AwareOnModelAdapter,
)


# ============================================================
# RESULT
# ============================================================


@dataclass(frozen=True)
class LearningAwareSynthesisResult:
    synthesis: EvidenceSynthesisResult
    learning: LearningFeedback
    knowledge: dict[str, Any]

    @property
    def status(self) -> str:
        return self.synthesis.status

    @property
    def answer(self) -> str:
        return self.synthesis.answer

    def to_dict(self) -> dict[str, Any]:
        result = self.synthesis.to_dict()

        result["learning_feedback"] = (
            self.learning.to_dict()
        )

        result["domain_knowledge"] = (
            self.knowledge
        )

        return result


# ============================================================
# KNOWLEDGE → EVIDENCE
# ============================================================


def _knowledge_to_evidence(
    knowledge: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert retrieved AwareOn domain knowledge into an
    explicitly labeled evidence package.

    This keeps general knowledge separate from:
      - current model outputs
      - historical observations
      - simulated outputs
      - derived outputs

    Current AwareOn evidence must still take precedence over
    general domain knowledge.
    """

    if not isinstance(
        knowledge,
        dict,
    ):
        raise TypeError(
            "knowledge must be a dictionary."
        )

    query = str(
        knowledge.get(
            "query",
            "",
        )
    )

    items = knowledge.get(
        "items",
        [],
    )

    if not isinstance(
        items,
        list,
    ):
        items = []

    evidence_items: list[
        dict[str, Any]
    ] = []

    for item in items:
        if not isinstance(
            item,
            dict,
        ):
            continue

        entry_id = str(
            item.get(
                "entry_id",
                "",
            )
        ).strip()

        title = str(
            item.get(
                "title",
                "",
            )
        ).strip()

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if not entry_id or not content:
            continue

        scope = str(
            item.get(
                "scope",
                "GENERAL_DOMAIN",
            )
        )

        source_type = str(
            item.get(
                "source_type",
                "CURATED_DOMAIN_KNOWLEDGE",
            )
        )

        source = str(
            item.get(
                "source",
                "AwareOn domain knowledge",
            )
        )

        source_date = item.get(
            "source_date"
        )

        claim = (
            content
            if not title
            else f"{title}: {content}"
        )

        evidence_items.append(
            {
                "evidence_id":
                    f"KNOW-{entry_id}",

                "source_tool":
                    "awareon_domain_knowledge",

                "evidence_type":
                    "DOMAIN_KNOWLEDGE",

                "claim":
                    claim,

                "value":
                    content,

                "source_id":
                    f"knowledge:{entry_id}",

                "confidence":
                    1.0,

                "metadata":
                    {
                        "entry_id":
                            entry_id,

                        "topic":
                            item.get(
                                "topic"
                            ),

                        "scope":
                            scope,

                        "source_type":
                            source_type,

                        "source":
                            source,

                        "source_date":
                            source_date,

                        "not_current_observation":
                            True,

                        "knowledge_only":
                            True,
                    },
            }
        )

    return {
        "query":
            query,

        "items":
            evidence_items,

        "count":
            len(evidence_items),
    }


# ============================================================
# SYSTEM PROMPT
# ============================================================


def build_learning_system_prompt(
    base_system_prompt: str,
    learning: LearningFeedback,
    knowledge: dict[str, Any],
) -> str:

    base = str(
        base_system_prompt or ""
    ).strip()

    if not base:
        raise ValueError(
            "base_system_prompt cannot be empty."
        )

    guardrails = """
AWAREON KNOWLEDGE AND EVIDENCE RULES:

1. Retrieved domain knowledge is allowed for general
   AwareOn-domain questions.

2. Retrieved domain knowledge is explicitly labeled
   DOMAIN_KNOWLEDGE and must not be described as a
   current observation.

3. Current canonical AwareOn evidence takes precedence
   over general domain knowledge.

4. Historical information must be described as historical
   when it comes from historical/source evidence.

5. Simulated outputs must be described as simulated.

6. Derived outputs must be described as derived.

7. Never invent numbers, dates, locations, categories,
   observations, events, or recommendations.

8. If a requested fact is not supported by the supplied
   knowledge or current evidence, say that it is not
   established by the available AwareOn sources.

9. Do not transform general scientific/domain knowledge
   into a claim about a specific current cell or region.

10. Do not transform a historical event into a current
    risk observation.

11. Answer the user's actual question directly and naturally.
    Do not require the user to use predefined keywords.

12. Match explanation depth to the user's apparent level:
    beginner questions should receive accessible explanations;
    technical questions may receive deeper technical detail.

13. Learned lessons are guidance only. Current canonical
    evidence always wins over learned experience.

14. Never use a learned lesson to manufacture unsupported
    current facts.
"""

    knowledge_context = str(
        knowledge.get(
            "context",
            "",
        )
        or ""
    ).strip()

    if not knowledge_context:
        knowledge_context = (
            "No specific retrieved domain-knowledge "
            "context is available."
        )

    return (
        base
        + "\n\n"
        + guardrails.strip()
        + "\n\n"
        + "RETRIEVED AWAREON DOMAIN KNOWLEDGE:\n"
        + knowledge_context
        + "\n\n"
        + "RETRIEVED VALIDATED LEARNING:\n"
        + learning.context
    )


# ============================================================
# SYNTHESIS
# ============================================================


def synthesize_with_learning(
    adapter: AwareOnModelAdapter,
    system_prompt: str,
    user_prompt: str,
    evidence: dict[str, Any],
    *,
    max_correction_rounds: int = 2,
    learning_memory: LearningMemory | None = None,
    learning_limit: int = 5,
    knowledge_limit: int = 6,
) -> LearningAwareSynthesisResult:

    if not isinstance(
        user_prompt,
        str,
    ):
        raise TypeError(
            "user_prompt must be a string."
        )

    if not user_prompt.strip():
        raise ValueError(
            "user_prompt cannot be empty."
        )

    # --------------------------------------------------------
    # 1. RETRIEVE VALIDATED LEARNING
    # --------------------------------------------------------

    learning = retrieve_learning_feedback(
        user_prompt,
        memory=learning_memory,
        limit=learning_limit,
    )

    # --------------------------------------------------------
    # 2. RETRIEVE DOMAIN KNOWLEDGE
    # --------------------------------------------------------

    knowledge = build_semantic_knowledge_context(
        user_prompt,
        limit=knowledge_limit,
    )

    # --------------------------------------------------------
    # 3. BUILD KNOWLEDGE EVIDENCE
    # --------------------------------------------------------

    knowledge_evidence = (
        _knowledge_to_evidence(
            knowledge
        )
    )

    # --------------------------------------------------------
    # 4. MERGE CURRENT EVIDENCE + DOMAIN KNOWLEDGE
    # --------------------------------------------------------

    current_items = []

    if isinstance(
        evidence,
        dict,
    ):
        raw_items = evidence.get(
            "items",
            [],
        )

        if isinstance(
            raw_items,
            list,
        ):
            current_items = [
                item
                for item in raw_items
                if isinstance(
                    item,
                    dict,
                )
            ]

    knowledge_items = (
        knowledge_evidence.get(
            "items",
            [],
        )
    )

    merged_items = []

    # IMPORTANT:
    # Current AwareOn evidence goes first.
    # Domain knowledge is supplemental.
    merged_items.extend(
        current_items
    )

    merged_items.extend(
        knowledge_items
    )

    merged_evidence = {
        "query":
            user_prompt,

        "items":
            merged_items,

        "count":
            len(merged_items),
    }

    # --------------------------------------------------------
    # 5. BUILD LEARNING-AWARE SYSTEM PROMPT
    # --------------------------------------------------------

    learning_system_prompt = (
        build_learning_system_prompt(
            system_prompt,
            learning,
            knowledge,
        )
    )

    # --------------------------------------------------------
    # 6. VERIFIED NEMOTRON SYNTHESIS
    # --------------------------------------------------------

    synthesis = synthesize_with_verification(
        adapter,
        learning_system_prompt,
        user_prompt,
        merged_evidence,
        max_correction_rounds=(
            max_correction_rounds
        ),
    )

    return LearningAwareSynthesisResult(
        synthesis=synthesis,
        learning=learning,
        knowledge=knowledge,
    )


__all__ = [
    "LearningAwareSynthesisResult",
    "build_learning_system_prompt",
    "synthesize_with_learning",
]

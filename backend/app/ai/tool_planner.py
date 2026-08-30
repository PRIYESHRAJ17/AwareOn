from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.ai.domain_router import (
    DomainDecision,
    QueryDomain,
    QueryIntent,
)
from backend.app.ai.tool_registry import (
    ToolSpec,
    tool_registry,
)


@dataclass(frozen=True)
class ToolPlan:
    domain: str
    intent: str
    confidence: float
    tools: tuple[str, ...]
    reasoning: tuple[str, ...]
    requires_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "intent": self.intent,
            "confidence": self.confidence,
            "tools": list(self.tools),
            "reasoning": list(self.reasoning),
            "requires_clarification":
                self.requires_clarification,
        }


# ============================================================
# TOOL ROUTING POLICIES
# ============================================================

_INTENT_TOOL_ORDER: dict[
    QueryIntent,
    tuple[str, ...],
] = {

    QueryIntent.CELL_RISK: (
        "exact_cell_intelligence",
    ),

    QueryIntent.REGIONAL_RISK: (
        "regional_intelligence",
        "nearby_cells",
    ),

    QueryIntent.SCENARIO: (
        "scenario_simulation",
        "exact_cell_intelligence",
    ),

    QueryIntent.TEMPORAL: (
        "historical_trajectory",
    ),

    QueryIntent.EARLY_WARNING: (
        "historical_trajectory",
        "early_warning_master",
    ),

    QueryIntent.EXPOSURE: (
        "regional_intelligence",
        "nearby_cells",
    ),

    QueryIntent.DECISION: (
        "regional_intelligence",
        "nearby_cells",
        "decision_master",
    ),

    QueryIntent.EXPLANATION: (
        "exact_cell_intelligence",
    ),

    QueryIntent.GENERAL_AWAREON: (
        "exact_cell_intelligence",
    ),

    QueryIntent.UNKNOWN: (),
}


def _valid_tools(
    names: tuple[str, ...],
) -> list[ToolSpec]:

    result = []

    for name in names:

        try:
            result.append(
                tool_registry.get(name)
            )
        except KeyError:
            continue

    return result


def build_tool_plan(
    decision: DomainDecision,
) -> ToolPlan:

    if decision.domain == QueryDomain.OUTSIDE_DOMAIN:

        return ToolPlan(
            domain=
                decision.domain.value,

            intent=
                decision.intent.value,

            confidence=
                decision.confidence,

            tools=(),

            reasoning=(
                "The query is outside AwareOn's "
                "specialized domain, so no AwareOn "
                "intelligence tools should be called.",
            ),

        )

    if decision.domain == QueryDomain.AMBIGUOUS:

        return ToolPlan(
            domain=
                decision.domain.value,

            intent=
                decision.intent.value,

            confidence=
                decision.confidence,

            tools=(),

            reasoning=(
                "The query is ambiguous and should "
                "be clarified before tool execution.",
            ),

            requires_clarification=True,
        )

    tool_names = _INTENT_TOOL_ORDER.get(
        decision.intent,
        (),
    )

    tools = _valid_tools(
        tool_names
    )

    reasoning = [
        (
            f"Intent classified as "
            f"{decision.intent.value}."
        ),
        (
            f"{len(tools)} candidate AwareOn "
            "tool(s) selected from the registry."
        ),
    ]

    for tool in tools:

        reasoning.append(
            (
                f"{tool.name}: "
                f"{tool.description}"
            )
        )

    return ToolPlan(
        domain=
            decision.domain.value,

        intent=
            decision.intent.value,

        confidence=
            decision.confidence,

        tools=tuple(
            tool.name
            for tool in tools
        ),

        reasoning=tuple(
            reasoning
        ),
    )


def plan_for_query(
    decision: DomainDecision,
) -> dict[str, Any]:

    return build_tool_plan(
        decision
    ).to_dict()

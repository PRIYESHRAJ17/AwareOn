from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.ai.agent_memory import (
    InvestigationMemory,
    create_investigation_memory,
)


# ============================================================
# AGENT RESULT
# ============================================================

@dataclass
class AgentRun:
    query: str
    status: str
    memory: InvestigationMemory
    final_result: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "status": self.status,
            "memory": self.memory.to_dict(),
            "final_result": self.final_result,
        }


# ============================================================
# DETERMINISTIC AGENT LOOP
# ============================================================

def run_investigation_loop(
    query: str,
    steps: list[
        tuple[str, Callable[[], dict[str, Any]]]
    ],
) -> AgentRun:

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    if not isinstance(
        steps,
        list,
    ):
        raise TypeError(
            "steps must be a list."
        )

    memory = create_investigation_memory(
        investigation_id=(
            f"INV-{id(query):X}"
        ),
        query=query,
    )

    outputs: dict[str, Any] = {}

    for name, function in steps:

        memory.add_step(
            action="EXECUTE_TOOL",
            target=name,
            status="STARTED",
        )

        try:

            result = function()

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    f"Tool '{name}' must return a dictionary."
                )

            outputs[name] = result

            memory.add_step(
                action="EXECUTE_TOOL",
                target=name,
                status="SUCCESS",
                result_summary=(
                    f"Returned {len(result)} top-level fields."
                ),
            )

        except Exception as exc:

            memory.add_step(
                action="EXECUTE_TOOL",
                target=name,
                status="FAILED",
                result_summary=str(exc),
            )

            return AgentRun(
                query=query,
                status="FAILED",
                memory=memory,
                final_result={
                    "error":
                        str(exc),
                    "completed_outputs":
                        outputs,
                },
            )

    memory.add_step(
        action="FINALIZE",
        target="investigation",
        status="SUCCESS",
        result_summary=(
            f"{len(outputs)} tool outputs collected."
        ),
    )

    return AgentRun(
        query=query,
        status="READY",
        memory=memory,
        final_result=outputs,
    )

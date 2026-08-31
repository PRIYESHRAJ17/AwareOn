from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class MultiHopStep:
    step_id: str
    tool: str
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class MultiHopPlan:
    intent: str
    steps: tuple[MultiHopStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "steps": [
                {
                    "step_id": step.step_id,
                    "tool": step.tool,
                    "depends_on": list(step.depends_on),
                }
                for step in self.steps
            ],
        }


@dataclass(frozen=True)
class MultiHopResult:
    status: str
    plan: MultiHopPlan
    results: dict[str, Any]
    executed_steps: tuple[str, ...]
    failed_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "plan": self.plan.to_dict(),
            "results": self.results,
            "executed_steps": list(self.executed_steps),
            "failed_steps": list(self.failed_steps),
        }


def build_multihop_plan(
    intent: str,
    *,
    has_cell: bool = False,
    has_coordinates: bool = False,
) -> MultiHopPlan:

    intent = str(intent).upper()

    if intent == "TEMPORAL":
        if has_cell and has_coordinates:
            steps = (
                MultiHopStep(
                    "regional",
                    "regional_intelligence",
                ),
                MultiHopStep(
                    "temporal",
                    "temporal_orchestrator",
                    ("regional",),
                ),
            )
        else:
            steps = (
                MultiHopStep(
                    "historical",
                    "historical_trajectory",
                ),
            )

    elif intent == "EARLY_WARNING":

        if has_cell and has_coordinates:
            steps = (
                MultiHopStep(
                    "regional",
                    "regional_intelligence",
                ),
                MultiHopStep(
                    "temporal",
                    "temporal_orchestrator",
                    ("regional",),
                ),
            )
        else:
            steps = (
                MultiHopStep(
                    "historical",
                    "historical_trajectory",
                ),
            )

    elif intent == "EXPLANATION":

        if has_cell:
            steps = (
                MultiHopStep(
                    "cell",
                    "exact_cell_intelligence",
                ),
            )
        else:
            steps = ()

    elif intent == "DECISION":

        if has_coordinates:
            steps = (
                MultiHopStep(
                    "regional",
                    "regional_intelligence",
                ),
            )
        else:
            steps = ()

    elif intent == "SCENARIO":

        if has_cell:
            steps = (
                MultiHopStep(
                    "cell",
                    "exact_cell_intelligence",
                ),
                MultiHopStep(
                    "scenario",
                    "scenario_simulation",
                    ("cell",),
                ),
            )
        else:
            steps = (
                MultiHopStep(
                    "scenario",
                    "scenario_simulation",
                ),
            )

    elif intent == "REGIONAL_RISK":

        if has_coordinates:
            steps = (
                MultiHopStep(
                    "regional",
                    "regional_intelligence",
                ),
            )
        else:
            steps = ()

    else:
        steps = ()

    return MultiHopPlan(
        intent=intent,
        steps=steps,
    )


def execute_multihop_plan(
    plan: MultiHopPlan,
    executors: dict[str, Callable[..., Any]],
    arguments: dict[str, dict[str, Any]] | None = None,
) -> MultiHopResult:

    arguments = arguments or {}

    results: dict[str, Any] = {}
    executed: list[str] = []
    failed: list[str] = []

    for step in plan.steps:

        if any(
            dependency not in executed
            for dependency in step.depends_on
        ):
            failed.append(step.step_id)

            return MultiHopResult(
                status="DEPENDENCY_FAILED",
                plan=plan,
                results=results,
                executed_steps=tuple(executed),
                failed_steps=tuple(failed),
            )

        executor = executors.get(
            step.tool
        )

        if executor is None:
            failed.append(step.step_id)

            return MultiHopResult(
                status="EXECUTOR_MISSING",
                plan=plan,
                results=results,
                executed_steps=tuple(executed),
                failed_steps=tuple(failed),
            )

        kwargs = arguments.get(
            step.step_id,
            {},
        )

        try:
            result = executor(
                **kwargs
            )
        except Exception as exc:
            failed.append(step.step_id)
            results[step.step_id] = {
                "status": "FAILED",
                "error": str(exc),
            }

            return MultiHopResult(
                status="EXECUTION_FAILED",
                plan=plan,
                results=results,
                executed_steps=tuple(executed),
                failed_steps=tuple(failed),
            )

        results[step.step_id] = result
        executed.append(step.step_id)

    return MultiHopResult(
        status="READY",
        plan=plan,
        results=results,
        executed_steps=tuple(executed),
        failed_steps=tuple(failed),
    )


__all__ = [
    "MultiHopStep",
    "MultiHopPlan",
    "MultiHopResult",
    "build_multihop_plan",
    "execute_multihop_plan",
]

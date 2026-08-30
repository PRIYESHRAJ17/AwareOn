from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable


@dataclass
class PipelineResult:
    success: bool
    data: dict[str, Any]
    timings_ms: dict[str, float]
    errors: list[str]


class IntelligencePipeline:
    """
    Reusable execution pipeline for AwareOn intelligence.

    The pipeline is intentionally generic so that individual
    intelligence modules can be plugged in without changing
    the orchestration contract.
    """

    def __init__(self) -> None:
        self._steps: list[
            tuple[str, Callable[..., Any]]
        ] = []

    def add_step(
        self,
        name: str,
        function: Callable[..., Any],
    ) -> "IntelligencePipeline":

        if not name:
            raise ValueError(
                "Pipeline step name is required."
            )

        if not callable(function):
            raise ValueError(
                f"Pipeline step '{name}' is not callable."
            )

        self._steps.append(
            (
                name,
                function,
            )
        )

        return self

    def run(
        self,
        context: dict[str, Any] | None = None,
    ) -> PipelineResult:

        state: dict[str, Any] = dict(
            context or {}
        )

        timings_ms: dict[str, float] = {}
        errors: list[str] = []

        for name, function in self._steps:

            started = perf_counter()

            try:

                result = function(
                    state
                )

                if isinstance(
                    result,
                    dict,
                ):
                    state.update(
                        result
                    )

                elif result is not None:
                    state[name] = result

            except Exception as exc:

                errors.append(
                    f"{name}: {exc}"
                )

            finally:

                elapsed = (
                    perf_counter()
                    - started
                ) * 1000.0

                timings_ms[name] = (
                    round(
                        elapsed,
                        3,
                    )
                )

        return PipelineResult(
            success=not errors,
            data=state,
            timings_ms=timings_ms,
            errors=errors,
        )


def run_pipeline(
    steps: list[
        tuple[str, Callable[..., Any]]
    ],
    context: dict[str, Any] | None = None,
) -> PipelineResult:

    pipeline = IntelligencePipeline()

    for name, function in steps:
        pipeline.add_step(
            name,
            function,
        )

    return pipeline.run(
        context
    )

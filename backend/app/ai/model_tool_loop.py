from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.ai.model_adapter import (
    AwareOnModelAdapter,
)


# ============================================================
# EXECUTION RECORD
# ============================================================

@dataclass
class ToolExecution:
    call_id: str
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    success: bool
    error: str | None = None

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "call_id":
                self.call_id,

            "name":
                self.name,

            "arguments":
                self.arguments,

            "result":
                self.result,

            "success":
                self.success,

            "error":
                self.error,
        }


# ============================================================
# LOOP RESULT
# ============================================================

@dataclass
class ToolLoopResult:
    status: str
    final_text: str
    executions: list[ToolExecution] = field(
        default_factory=list
    )
    model_responses: list[dict[str, Any]] = field(
        default_factory=list
    )
    iterations: int = 0

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "status":
                self.status,

            "final_text":
                self.final_text,

            "executions": [
                item.to_dict()
                for item in self.executions
            ],

            "model_responses":
                self.model_responses,

            "iterations":
                self.iterations,
        }


# ============================================================
# TOOL DEFINITION HELPER
# ============================================================

def build_ollama_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:

    return {
        "type":
            "function",

        "function": {
            "name":
                name,

            "description":
                description,

            "parameters":
                parameters,
        },
    }


# ============================================================
# ARGUMENT VALIDATION
# ============================================================

def validate_arguments(
    arguments: Any,
) -> dict[str, Any]:

    if isinstance(
        arguments,
        str,
    ):

        try:
            arguments = json.loads(
                arguments
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Tool arguments are not valid JSON."
            ) from exc

    if not isinstance(
        arguments,
        dict,
    ):

        raise ValueError(
            "Tool arguments must be a dictionary."
        )

    return arguments


# ============================================================
# DUPLICATE CALL GUARD
# ============================================================

def _call_signature(
    name: str,
    arguments: dict[str, Any],
) -> str:

    return (
        name
        + ":"
        + json.dumps(
            arguments,
            sort_keys=True,
            default=str,
        )
    )


# ============================================================
# MODEL TOOL LOOP
# ============================================================

def run_model_tool_loop(
    adapter: AwareOnModelAdapter,
    system_prompt: str,
    user_prompt: str,
    tools: list[dict[str, Any]],
    executors: dict[
        str,
        Callable[..., dict[str, Any]],
    ],
    *,
    max_iterations: int = 8,
) -> ToolLoopResult:

    if max_iterations < 1:
        raise ValueError(
            "max_iterations must be at least 1."
        )

    messages: list[
        dict[str, Any]
    ] = [
        {
            "role":
                "system",

            "content":
                system_prompt,
        },
        {
            "role":
                "user",

            "content":
                user_prompt,
        },
    ]

    executions: list[
        ToolExecution
    ] = []

    model_responses: list[
        dict[str, Any]
    ] = []

    seen_calls: set[str] = set()

    for iteration in range(
        1,
        max_iterations + 1,
    ):

        response = adapter.generate_from_messages(
            messages,
            tools=tools,
        )

        model_responses.append(
            {
                "iteration":
                    iteration,

                "text":
                    response.text,

                "tool_calls":
                    list(
                        response.tool_calls
                    ),

                "usage":
                    response.usage,
            }
        )

        # ----------------------------------------------------
        # Model is done
        # ----------------------------------------------------

        if not response.tool_calls:

            return ToolLoopResult(
                status="READY",
                final_text=response.text,
                executions=executions,
                model_responses=model_responses,
                iterations=iteration,
            )

        # ----------------------------------------------------
        # Preserve assistant tool-call message
        # ----------------------------------------------------

        if response.assistant_message is None:

            return ToolLoopResult(
                status="FAILED",
                final_text="",
                executions=executions,
                model_responses=model_responses,
                iterations=iteration,
            )

        messages.append(
            response.assistant_message
        )

        # ----------------------------------------------------
        # Execute all tool calls
        # ----------------------------------------------------

        for call in response.tool_calls:

            call_id = str(
                call.get(
                    "id",
                    f"call_{iteration}",
                )
            )

            name = str(
                call.get(
                    "name",
                    "",
                )
            )

            try:

                arguments = validate_arguments(
                    call.get(
                        "arguments",
                        {},
                    )
                )

            except ValueError as exc:

                execution = ToolExecution(
                    call_id=call_id,
                    name=name,
                    arguments={},
                    result={},
                    success=False,
                    error=str(exc),
                )

                executions.append(
                    execution
                )

                messages.append(
                    {
                        "role":
                            "tool",

                        "tool_call_id":
                            call_id,

                        "content":
                            json.dumps(
                                {
                                    "status":
                                        "ERROR",

                                    "error":
                                        str(exc),
                                }
                            ),
                    }
                )

                continue

            signature = _call_signature(
                name,
                arguments,
            )

            if signature in seen_calls:

                execution = ToolExecution(
                    call_id=call_id,
                    name=name,
                    arguments=arguments,
                    result={},
                    success=False,
                    error=(
                        "Duplicate tool call detected. "
                        "The agent must choose a different "
                        "investigation step."
                    ),
                )

                executions.append(
                    execution
                )

                messages.append(
                    {
                        "role":
                            "tool",

                        "tool_call_id":
                            call_id,

                        "content":
                            json.dumps(
                                {
                                    "status":
                                        "ERROR",

                                    "error":
                                        execution.error,
                                }
                            ),
                    }
                )

                continue

            seen_calls.add(
                signature
            )

            executor = executors.get(
                name
            )

            if executor is None:

                execution = ToolExecution(
                    call_id=call_id,
                    name=name,
                    arguments=arguments,
                    result={},
                    success=False,
                    error=(
                        f"Tool '{name}' is not "
                        "registered in AwareOn."
                    ),
                )

                executions.append(
                    execution
                )

                messages.append(
                    {
                        "role":
                            "tool",

                        "tool_call_id":
                            call_id,

                        "content":
                            json.dumps(
                                {
                                    "status":
                                        "ERROR",

                                    "error":
                                        execution.error,
                                }
                            ),
                    }
                )

                continue

            try:

                result = executor(
                    **arguments
                )

                if not isinstance(
                    result,
                    dict,
                ):

                    raise TypeError(
                        "AwareOn tool must return a dictionary."
                    )

                execution = ToolExecution(
                    call_id=call_id,
                    name=name,
                    arguments=arguments,
                    result=result,
                    success=True,
                )

            except Exception as exc:

                execution = ToolExecution(
                    call_id=call_id,
                    name=name,
                    arguments=arguments,
                    result={},
                    success=False,
                    error=str(exc),
                )

            executions.append(
                execution
            )

            # ------------------------------------------------
            # Send result back to model
            # ------------------------------------------------

            if execution.success:

                content = json.dumps(
                    {
                        "status":
                            "SUCCESS",

                        "tool":
                            name,

                        "result":
                            execution.result,
                    },
                    default=str,
                )

            else:

                content = json.dumps(
                    {
                        "status":
                            "ERROR",

                        "tool":
                            name,

                        "error":
                            execution.error,
                    },
                    default=str,
                )

            messages.append(
                {
                    "role":
                        "tool",

                    "tool_call_id":
                        call_id,

                    "content":
                        content,
                }
            )

    return ToolLoopResult(
        status="MAX_ITERATIONS",
        final_text="",
        executions=executions,
        model_responses=model_responses,
        iterations=max_iterations,
    )

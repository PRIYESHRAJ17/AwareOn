from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.ai.autonomous_master import run_awareon_agent
from backend.app.ai.model_adapter import AwareOnModelAdapter


# ============================================================
# CASE
# ============================================================

@dataclass(frozen=True)
class AgentBenchmarkCase:
    case_id: str
    name: str
    query: str
    evaluator: str


# ============================================================
# RESULTS
# ============================================================

@dataclass
class AgentBenchmarkResult:
    case_id: str
    name: str
    passed: bool
    score: float
    latency_seconds: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "latency_seconds": self.latency_seconds,
            "details": self.details,
        }


@dataclass
class AgentBenchmarkSuiteResult:
    total: int
    passed: int
    failed: int
    score: float
    results: list[AgentBenchmarkResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "score": self.score,
            "results": [
                item.to_dict()
                for item in self.results
            ],
        }


# ============================================================
# CASES
# ============================================================

REAL_AGENT_CASES = [
    AgentBenchmarkCase(
        "A01",
        "Cell explanation",
        "Why is cell 506_422 extreme?",
        "cell",
    ),
    AgentBenchmarkCase(
        "A02",
        "Rainfall scenario",
        "What happens under +100% rainfall?",
        "scenario",
    ),
    AgentBenchmarkCase(
        "A03",
        "Regional intelligence",
        (
            "What is happening across the region "
            "around 27.177309869688955, "
            "88.40207066680458?"
        ),
        "regional",
    ),
    AgentBenchmarkCase(
        "A04",
        "Historical trajectory",
        "What is the historical trajectory of this region?",
        "historical",
    ),
    AgentBenchmarkCase(
        "A05",
        "Early warning",
        "Is there an emerging risk signal?",
        "warning",
    ),
    AgentBenchmarkCase(
        "A06",
        "Transport decision",
        (
            "Which transport corridors around "
            "27.177309869688955, 88.40207066680458 "
            "should be inspected first?"
        ),
        "decision",
    ),
    AgentBenchmarkCase(
        "A07",
        "Evidence conflict",
        "What evidence conflicts in cell 506_422?",
        "evidence",
    ),
    AgentBenchmarkCase(
        "A08",
        "Out-of-domain recipe",
        "Give me a paneer chilli recipe.",
        "outside",
    ),
    AgentBenchmarkCase(
        "A09",
        "Out-of-domain gaming",
        "What is India's biggest gaming event?",
        "outside",
    ),
]


# ============================================================
# HELPERS
# ============================================================

def _text(value: Any) -> str:
    return str(value or "")


def _lower(value: Any) -> str:
    return _text(value).lower()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(
        term.lower() in lowered
        for term in terms
    )


def _status(result: Any) -> str:
    return str(
        getattr(result, "status", "")
        or ""
    ).upper()


def _domain(result: Any) -> str:
    return str(
        getattr(result, "domain", "")
        or ""
    ).upper()


def _intent(result: Any) -> str:
    return str(
        getattr(result, "intent", "")
        or ""
    ).upper()


def _tools(result: Any) -> list[str]:
    response = getattr(
        result,
        "response",
        None,
    )

    if response is None:
        return []

    value = getattr(
        response,
        "tools_used",
        [],
    )

    return list(value or [])


def _verified(result: Any) -> bool:
    verification = getattr(
        result,
        "verification",
        None,
    )

    if not isinstance(
        verification,
        dict,
    ):
        return False

    return (
        str(
            verification.get(
                "status",
                "",
            )
        ).upper()
        == "PASSED"
    )


def _score(checks: dict[str, bool]) -> float:
    if not checks:
        return 0.0

    return (
        sum(checks.values())
        / len(checks)
        * 100.0
    )


# ============================================================
# EVALUATORS
# ============================================================

def evaluate_cell(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready": _status(result) == "READY",
        "domain": _domain(result) == "AWAREON",
        "intent": _intent(result) == "EXPLANATION",
        "cell": "506_422" in answer,
        "risk": _has_any(answer, ("81.10", "81.100")),
        "extreme": "extreme" in text,
        "tool": "exact_cell_intelligence" in tools,
        "verified": _verified(result),
        "no_bad_rainfall":
            not _has_any(
                text,
                (
                    "high rainfall trigger",
                    "extreme rainfall trigger",
                ),
            ),
    }

    value = _score(checks)

    return (
        value >= 88.0,
        value,
        checks,
    )


def evaluate_scenario(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready": _status(result) == "READY",
        "domain": _domain(result) == "AWAREON",
        "intent": _intent(result) == "SCENARIO",
        "scenario":
            _has_any(
                text,
                (
                    "scenario",
                    "simulated",
                ),
            ),
        "rainfall":
            _has_any(
                answer,
                (
                    "100%",
                    "+100%",
                    "100 percent",
                ),
            ),
        "tool":
            "scenario_simulation" in tools,
        "verified":
            _verified(result),
    }

    value = _score(checks)

    return (
        value >= 85.0,
        value,
        checks,
    )


def evaluate_regional(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready":
            _status(result) == "READY",

        "domain":
            _domain(result) == "AWAREON",

        "intent":
            _intent(result) == "REGIONAL_RISK",

        "regional":
            _has_any(
                text,
                (
                    "regional",
                    "region",
                ),
            ),

        "coordinates":
            _has_any(
                answer,
                (
                    "27.177",
                    "88.402",
                    "latitude",
                    "longitude",
                ),
            ),

        "tool":
            "regional_intelligence" in tools,

        "verified":
            _verified(result),
    }

    value = _score(checks)

    return (
        value >= 85.0,
        value,
        checks,
    )


def evaluate_historical(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready":
            _status(result) == "READY",

        "domain":
            _domain(result) == "AWAREON",

        "intent":
            _intent(result) == "TEMPORAL",

        "trajectory":
            _has_any(
                text,
                (
                    "trajectory",
                    "historical",
                    "baseline",
                ),
            ),

        "tool":
            "historical_trajectory" in tools,

        "verified":
            _verified(result),
    }

    value = _score(checks)

    return (
        value >= 83.0,
        value,
        checks,
    )


def evaluate_warning(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready":
            _status(result) == "READY",

        "domain":
            _domain(result) == "AWAREON",

        "intent":
            _intent(result) == "EARLY_WARNING",

        "warning":
            _has_any(
                text,
                (
                    "warning",
                    "emerging",
                    "risk signal",
                    "early",
                ),
            ),

        "tool":
            (
                "early_warning_master" in tools
                or
                "historical_trajectory" in tools
            ),

        "verified":
            _verified(result),
    }

    value = _score(checks)

    return (
        value >= 83.0,
        value,
        checks,
    )


def evaluate_decision(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready":
            _status(result) == "READY",

        "domain":
            _domain(result) == "AWAREON",

        "intent":
            _intent(result) == "DECISION",

        "decision":
            _has_any(
                text,
                (
                    "inspect",
                    "priority",
                    "transport",
                    "decision",
                    "recommended",
                ),
            ),

        "regional_tool":
            "regional_intelligence" in tools,

        "decision_tool":
            (
                "decision_orchestrator" in tools
                or
                "decision_master" in tools
            ),

        "verified":
            _verified(result),
    }

    value = _score(checks)

    return (
        value >= 85.0,
        value,
        checks,
    )


def evaluate_evidence(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    checks = {
        "ready":
            _status(result) == "READY",

        "domain":
            _domain(result) == "AWAREON",

        "cell":
            "506_422" in answer,

        "evidence_language":
            _has_any(
                text,
                (
                    "evidence",
                    "conflict",
                    "contradiction",
                    "uncertainty",
                ),
            ),

        "cell_tool":
            "exact_cell_intelligence" in tools,

        "verified":
            _verified(result),
    }

    value = _score(checks)

    return (
        value >= 83.0,
        value,
        checks,
    )


def evaluate_outside(
    result: Any,
) -> tuple[bool, float, dict[str, Any]]:

    answer = _text(
        getattr(result, "answer", "")
    )

    text = _lower(answer)
    tools = _tools(result)

    recognized = (
        _domain(result) == "OUTSIDE_DOMAIN"
        or
        _has_any(
            text,
            (
                "outside",
                "specialized domain",
                "cannot provide",
                "not within",
            ),
        )
    )

    unrelated = _has_any(
        text,
        (
            "ingredients",
            "recipe:",
            "chop the paneer",
            "fry the paneer",
            "gaming event is",
        ),
    )

    checks = {
        "recognized":
            recognized,

        "no_unrelated_answer":
            not unrelated,

        "no_tools":
            not tools,
    }

    value = _score(checks)

    return (
        value >= 100.0,
        value,
        checks,
    )


# ============================================================
# REGISTRY
# ============================================================

EVALUATORS: dict[
    str,
    Callable[
        [Any],
        tuple[bool, float, dict[str, Any]],
    ],
] = {
    "cell": evaluate_cell,
    "scenario": evaluate_scenario,
    "regional": evaluate_regional,
    "historical": evaluate_historical,
    "warning": evaluate_warning,
    "decision": evaluate_decision,
    "evidence": evaluate_evidence,
    "outside": evaluate_outside,
}


# ============================================================
# RUNNER
# ============================================================

def run_real_agent_benchmark(
    cases: list[AgentBenchmarkCase] | None = None,
) -> AgentBenchmarkSuiteResult:

    selected = (
        REAL_AGENT_CASES
        if cases is None
        else cases
    )

    results: list[
        AgentBenchmarkResult
    ] = []

    for case in selected:

        started = time.perf_counter()

        try:
            result = run_awareon_agent(
                case.query
            )

            latency = (
                time.perf_counter()
                - started
            )

            evaluator = EVALUATORS[
                case.evaluator
            ]

            passed, score, details = evaluator(
                result
            )

            details.update(
                {
                    "domain":
                        _domain(result),

                    "intent":
                        _intent(result),

                    "status":
                        _status(result),

                    "tools":
                        _tools(result),

                    "investigation_count":
                        len(
                            getattr(
                                result,
                                "investigations",
                                [],
                            )
                        ),

                    "verification":
                        getattr(
                            result,
                            "verification",
                            None,
                        ),

                    "learning_candidate":
                        getattr(
                            result,
                            "learning_candidate",
                            None,
                        )
                        is not None,

                    "memory_steps":
                        len(
                            getattr(
                                getattr(
                                    result,
                                    "memory",
                                    None,
                                ),
                                "steps",
                                [],
                            )
                        ),
                }
            )

            results.append(
                AgentBenchmarkResult(
                    case_id=case.case_id,
                    name=case.name,
                    passed=passed,
                    score=score,
                    latency_seconds=latency,
                    details=details,
                )
            )

        except Exception as exc:

            latency = (
                time.perf_counter()
                - started
            )

            results.append(
                AgentBenchmarkResult(
                    case_id=case.case_id,
                    name=case.name,
                    passed=False,
                    score=0.0,
                    latency_seconds=latency,
                    details={
                        "error":
                            str(exc),
                    },
                )
            )

    total = len(results)

    passed = sum(
        1
        for result in results
        if result.passed
    )

    failed = total - passed

    score = (
        sum(
            result.score
            for result in results
        )
        / total
        if total
        else 0.0
    )

    return AgentBenchmarkSuiteResult(
        total=total,
        passed=passed,
        failed=failed,
        score=score,
        results=results,
    )


# ============================================================
# MODEL STATUS
# ============================================================

def model_status() -> dict[str, Any]:

    adapter = (
        AwareOnModelAdapter
        .from_environment()
    )

    return adapter.configuration_status()

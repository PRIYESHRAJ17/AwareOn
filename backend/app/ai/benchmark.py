from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


# ============================================================
# BENCHMARK CASE
# ============================================================

@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    name: str
    query: str
    expected_domain: str
    evaluator: str


# ============================================================
# RESULT
# ============================================================

@dataclass
class BenchmarkResult:
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
class BenchmarkSuiteResult:
    total: int
    passed: int
    failed: int
    score: float
    results: list[BenchmarkResult]

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

BENCHMARK_CASES = [
    BenchmarkCase(
        "B01",
        "Cell explanation",
        "Why is cell 506_422 extreme?",
        "AWAREON",
        "cell_explanation",
    ),
    BenchmarkCase(
        "B02",
        "Rainfall scenario",
        "What happens under +100% rainfall?",
        "AWAREON",
        "scenario",
    ),
    BenchmarkCase(
        "B03",
        "Regional intelligence",
        (
            "What is happening across the region "
            "around 27.177309869688955, "
            "88.40207066680458?"
        ),
        "AWAREON",
        "regional",
    ),
    BenchmarkCase(
        "B04",
        "Early warning",
        "Is there an emerging risk signal?",
        "AWAREON",
        "warning",
    ),
    BenchmarkCase(
        "B05",
        "Transport decision",
        "Which transport corridors should be inspected first?",
        "AWAREON",
        "decision",
    ),
    BenchmarkCase(
        "B06",
        "Historical trajectory",
        "What is the historical trajectory of this region?",
        "AWAREON",
        "historical",
    ),
    BenchmarkCase(
        "B07",
        "Evidence conflict",
        "What evidence conflicts in this cell?",
        "AWAREON",
        "evidence_conflict",
    ),
    BenchmarkCase(
        "B08",
        "Outside-domain recipe",
        "Give me a paneer chilli recipe.",
        "OUTSIDE_DOMAIN",
        "outside_domain",
    ),
    BenchmarkCase(
        "B09",
        "Outside-domain gaming",
        "What is India's biggest gaming event?",
        "OUTSIDE_DOMAIN",
        "outside_domain",
    ),
]


# ============================================================
# HELPERS
# ============================================================

def _has_any(
    text: str,
    terms: tuple[str, ...],
) -> bool:
    lowered = text.lower()
    return any(
        term.lower() in lowered
        for term in terms
    )


def _has_all(
    text: str,
    terms: tuple[str, ...],
) -> bool:
    lowered = text.lower()
    return all(
        term.lower() in lowered
        for term in terms
    )


# ============================================================
# EVALUATORS
# ============================================================

def evaluate_cell_explanation(
    text: str,
) -> tuple[bool, float, dict[str, Any]]:

    checks = {
        "cell_id":
            "506_422" in text,

        "risk":
            _has_any(
                text,
                (
                    "81.10",
                    "81.100",
                ),
            ),

        "extreme":
            "EXTREME" in text.upper(),

        "susceptibility":
            _has_any(
                text,
                (
                    "VERY_HIGH",
                    "very high",
                ),
            ),

        "terrain":
            _has_any(
                text,
                (
                    "terrain instability",
                    "terrain",
                ),
            ),

        "spatial":
            _has_any(
                text,
                (
                    "spatial pressure",
                    "HIGH_RISK_CLUSTER",
                    "high-risk cluster",
                ),
            ),

        "rainfall_not_misclassified":
            not _has_any(
                text,
                (
                    "high rainfall trigger",
                    "extreme rainfall trigger",
                ),
            ),
    }

    score = (
        sum(
            1
            for value in checks.values()
            if value
        )
        / len(checks)
        * 100.0
    )

    return (
        score >= 85.0,
        score,
        checks,
    )


def evaluate_scenario(
    text: str,
) -> tuple[bool, float, dict[str, Any]]:

    checks = {
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
                text,
                (
                    "100%",
                    "+100%",
                    "100 percent",
                ),
            ),

        "risk":
            _has_any(
                text,
                (
                    "72.04",
                    "72.035",
                ),
            ),

        "change":
            _has_any(
                text,
                (
                    "+6.52",
                    "6.52",
                    "6.524",
                ),
            ),
    }

    score = (
        sum(checks.values())
        / len(checks)
        * 100.0
    )

    return (
        score >= 75.0,
        score,
        checks,
    )


def evaluate_regional(
    text: str,
) -> tuple[bool, float, dict[str, Any]]:

    checks = {
        "regional":
            _has_any(
                text,
                (
                    "regional",
                    "region",
                    "regional risk",
                ),
            ),

        "coordinates":
            _has_any(
                text,
                (
                    "27.1773",
                    "88.4020",
                    "latitude",
                    "longitude",
                ),
            ),

        "risk":
            _has_any(
                text,
                (
                    "69.48",
                    "83.48",
                    "CRITICAL_REGION",
                ),
            ),
    }

    score = (
        sum(checks.values())
        / len(checks)
        * 100.0
    )

    return (
        score >= 66.0,
        score,
        checks,
    )


def evaluate_outside_domain(
    text: str,
) -> tuple[bool, float, dict[str, Any]]:

    recognized = _has_any(
        text,
        (
            "outside",
            "cannot provide",
            "not within",
            "specialized",
            "domain",
            "AwareOn",
        ),
    )

    unrelated_answer = _has_any(
        text,
        (
            "ingredients:",
            "recipe:",
            "boil the paneer",
            "fry the paneer",
            "gaming event",
        ),
    )

    passed = (
        recognized
        and not unrelated_answer
    )

    return (
        passed,
        100.0 if passed else 0.0,
        {
            "recognized_outside_domain":
                recognized,
            "avoided_unrelated_answer":
                not unrelated_answer,
        },
    )


def evaluate_generic(
    text: str,
) -> tuple[bool, float, dict[str, Any]]:

    passed = bool(
        text.strip()
    )

    return (
        passed,
        100.0 if passed else 0.0,
        {
            "answer_present":
                passed
        },
    )


# ============================================================
# REGISTRY
# ============================================================

EVALUATORS: dict[
    str,
    Callable[
        [str],
        tuple[bool, float, dict[str, Any]],
    ],
] = {
    "cell_explanation":
        evaluate_cell_explanation,

    "scenario":
        evaluate_scenario,

    "regional":
        evaluate_regional,

    "outside_domain":
        evaluate_outside_domain,
}


# ============================================================
# BENCHMARK RUNNER
# ============================================================

def run_benchmark(
    runner: Callable[
        [BenchmarkCase],
        str,
    ],
    cases: list[BenchmarkCase] | None = None,
) -> BenchmarkSuiteResult:

    selected = (
        BENCHMARK_CASES
        if cases is None
        else cases
    )

    results: list[
        BenchmarkResult
    ] = []

    for case in selected:

        start = time.perf_counter()

        try:
            answer = runner(case)

            latency = (
                time.perf_counter()
                - start
            )

            evaluator = EVALUATORS.get(
                case.evaluator,
                evaluate_generic,
            )

            passed, score, details = evaluator(
                answer
            )

            results.append(
                BenchmarkResult(
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
                - start
            )

            results.append(
                BenchmarkResult(
                    case_id=case.case_id,
                    name=case.name,
                    passed=False,
                    score=0.0,
                    latency_seconds=latency,
                    details={
                        "error": str(exc)
                    },
                )
            )

    total = len(results)

    passed_count = sum(
        1
        for item in results
        if item.passed
    )

    failed_count = (
        total
        - passed_count
    )

    overall_score = (
        sum(
            item.score
            for item in results
        )
        / total
        if total
        else 0.0
    )

    return BenchmarkSuiteResult(
        total=total,
        passed=passed_count,
        failed=failed_count,
        score=overall_score,
        results=results,
    )

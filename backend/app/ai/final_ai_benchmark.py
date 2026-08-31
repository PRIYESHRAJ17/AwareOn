from __future__ import annotations

from typing import Any, Callable


# ============================================================
# INDIVIDUAL BENCHMARKS
# ============================================================

from backend.app.ai.retrieval_benchmark import (
    run_retrieval_benchmark,
)

from backend.app.ai.agent_benchmark import (
    run_real_agent_benchmark,
)

from backend.app.ai.multihop_benchmark import (
    run_multihop_benchmark,
)

from backend.app.ai.decision_benchmark import (
    run_decision_benchmark,
)

from backend.app.ai.evidence_completeness_benchmark import (
    run_evidence_completeness_benchmark,
)

from backend.app.ai.adversarial_benchmark import (
    run_adversarial_benchmark,
    run_step10_benchmark,
)


# ============================================================
# RESULT HELPERS
# ============================================================

def _passed(result: Any) -> bool:

    total = _total(result)
    passed = _passed_count(result)

    if total > 0:
        return passed == total

    if isinstance(
        result,
        dict,
    ):
        return result.get(
            "passed"
        ) is True

    return bool(
        getattr(
            result,
            "passed",
            False,
        )
    )



def _total(result: Any) -> int:

    if isinstance(result, dict):

        for key in (
            "total",
            "total_required",
        ):

            value = result.get(key)

            if isinstance(
                value,
                (int, float),
            ):
                return int(value)

    value = getattr(
        result,
        "total",
        None,
    )

    if isinstance(
        value,
        (int, float),
    ):
        return int(value)

    return 0


def _passed_count(result: Any) -> int:

    if isinstance(result, dict):

        value = result.get(
            "passed"
        )

        # Some benchmarks expose passed=True/False
        # rather than a numeric count.
        if isinstance(
            value,
            bool,
        ):

            verified = result.get(
                "verified_required"
            )

            if isinstance(
                verified,
                (int, float),
            ):
                return int(verified)

            total = _total(
                result
            )

            return (
                total
                if value
                else 0
            )

        if isinstance(
            value,
            (int, float),
        ):
            return int(value)

    value = getattr(
        result,
        "passed",
        None,
    )

    if isinstance(
        value,
        bool,
    ):
        total = _total(
            result
        )

        return (
            total
            if value
            else 0
        )

    if isinstance(
        value,
        (int, float),
    ):
        return int(value)

    return 0


def _score(result: Any) -> float:

    if isinstance(
        result,
        dict,
    ):

        value = result.get(
            "score"
        )

        if isinstance(
            value,
            (int, float),
        ):
            return float(value)

        total = _total(
            result
        )

        passed = _passed_count(
            result
        )

        if total:
            return (
                float(passed)
                / float(total)
                * 100.0
            )

        return 0.0

    value = getattr(
        result,
        "score",
        None
    )

    if isinstance(
        value,
        (int, float),
    ):
        return float(value)

    total = _total(
        result
    )

    passed = _passed_count(
        result
    )

    if total:
        return (
            float(passed)
            / float(total)
            * 100.0
        )

    return 0.0




# ============================================================
# FINAL BENCHMARK
# ============================================================

BENCHMARKS: tuple[
    tuple[str, Callable[[], Any]],
    ...
] = (
    (
        "retrieval",
        run_retrieval_benchmark,
    ),
    (
        "agent",
        run_real_agent_benchmark,
    ),
    (
        "multihop",
        run_multihop_benchmark,
    ),
    (
        "decision",
        run_decision_benchmark,
    ),
    (
        "evidence_completeness",
        run_evidence_completeness_benchmark,
    ),
    (
        "adversarial",
        run_adversarial_benchmark,
    ),
    (
        "robustness",
        run_step10_benchmark,
    ),
)


def run_final_ai_benchmark() -> dict[str, Any]:

    results: dict[str, Any] = {}
    failures: dict[str, str] = {}

    total_cases = 0
    total_passed = 0

    for name, runner in BENCHMARKS:

        try:
            result = runner()

            results[name] = {
                "status": (
                    "PASS"
                    if _passed(result)
                    else "FAIL"
                ),
                "total": _total(result),
                "passed": _passed_count(result),
                "score": round(
                    _score(result),
                    2,
                ),
                "result": result,
            }

            total_cases += _total(result)
            total_passed += _passed_count(result)

        except Exception as exc:

            results[name] = {
                "status": "ERROR",
                "total": 0,
                "passed": 0,
                "score": 0.0,
                "error": str(exc),
            }

            failures[name] = str(exc)

    overall_score = (
        total_passed
        / total_cases
        * 100.0
        if total_cases
        else 0.0
    )

    overall_pass = (
        bool(results)
        and not failures
        and all(
            item["status"] == "PASS"
            for item in results.values()
        )
    )

    return {
        "status": (
            "PASS"
            if overall_pass
            else "FAIL"
        ),
        "total": total_cases,
        "passed": total_passed,
        "failed": (
            total_cases
            - total_passed
        ),
        "score": round(
            overall_score,
            2,
        ),
        "benchmarks": results,
        "errors": failures,
    }


__all__ = [
    "run_final_ai_benchmark",
]

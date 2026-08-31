from __future__ import annotations

from backend.app.ai.decision_orchestrator import (
    run_decision_intelligence,
)


def run_decision_benchmark() -> dict:
    result = run_decision_intelligence(
        cell_id="506_422",
        latitude=27.177309869688955,
        longitude=88.40207066680458,
    )

    checks = {
        "ready":
            result.status == "READY",

        "regional_master":
            bool(result.regional_master),

        "intervention":
            bool(result.intervention),

        "infrastructure":
            bool(result.infrastructure),

        "field_inspection":
            bool(result.field_inspection),

        "monitoring":
            bool(result.monitoring),

        "response":
            bool(result.response),

        "optimization":
            bool(result.optimization),

        "comparison":
            bool(result.comparison),

        "tradeoff":
            bool(result.tradeoff),

        "operational":
            bool(result.operational),

        "decision_master":
            bool(result.decision_master),

        "recommended_option":
            (
                result.optimization.get(
                    "recommended_option",
                    {},
                ).get("option")
                == "IMMEDIATE_FIELD_ASSESSMENT"
            ),
    }

    passed = sum(
        1
        for value in checks.values()
        if value
    )

    total = len(checks)

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": (
            passed / total * 100.0
            if total
            else 0.0
        ),
        "checks": checks,
    }


__all__ = [
    "run_decision_benchmark",
]

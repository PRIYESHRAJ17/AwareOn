from __future__ import annotations

from backend.app.ai.agent_tools import (
    execute_temporal_orchestrator,
)


CELL_ID = "506_422"
LATITUDE = 27.177309869688955
LONGITUDE = 88.40207066680458


def run_multihop_benchmark():
    result = execute_temporal_orchestrator(
        cell_id=CELL_ID,
        latitude=LATITUDE,
        longitude=LONGITUDE,
    )

    checks = {
        "ready":
            result.get("status") == "READY",

        "hop_1":
            result.get(
                "orchestration",
                {},
            ).get(
                "hop_1",
                {},
            ).get("status") == "READY",

        "hop_2":
            result.get(
                "orchestration",
                {},
            ).get(
                "hop_2",
                {},
            ).get("status") == "READY",

        "historical":
            bool(
                result.get(
                    "historical"
                )
            ),

        "emerging_risk":
            bool(
                result.get(
                    "emerging_risk"
                )
            ),

        "early_warning":
            bool(
                result.get(
                    "early_warning"
                )
            ),

        "progression":
            bool(
                result.get(
                    "progression"
                )
            ),

        "coupling":
            bool(
                result.get(
                    "coupling"
                )
            ),

        "master":
            bool(
                result.get(
                    "early_warning_master"
                )
            ),

        "master_warning":
            result.get(
                "early_warning_master",
                {},
            ).get(
                "master_warning"
            )
            in {
                "NORMAL",
                "WATCH",
                "HIGH",
                "CRITICAL",
            },
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
        "score":
            (
                passed / total * 100.0
                if total
                else 0.0
            ),
        "checks": checks,
    }


__all__ = [
    "run_multihop_benchmark",
]

from __future__ import annotations

from backend.app.ai.agent_tools import (
    execute_exact_cell_intelligence,
)
from backend.app.ai.evidence_builder import (
    build_cell_evidence_package,
)


REQUIRED_ITEMS = {
    "risk": 81.10004750513113,
    "severity": "EXTREME",
    "warning": "CRITICAL",
    "susceptibility": "VERY_HIGH",
    "terrain": "EXTREME",
    "spatial_pressure": 95.60806629320292,
    "scenario": 72.03599786511758,
    "scenario_change": 6.524582447279826,
    "scenario_category": "HIGH",
    "neighbors": 57,
    "high_neighbors": 56,
    "extreme_neighbors": 28,
    "spatial_pattern": "HIGH_RISK_CLUSTER",
    "evidence_state": "EVIDENCE_CONFLICT",
    "posture": "CRITICAL_CLUSTER_AND_SCENARIO_SENSITIVE",
    "priority": "P1",
}


def run_evidence_completeness_benchmark():
    payload = execute_exact_cell_intelligence(
        "506_422"
    )

    package = build_cell_evidence_package(
        payload
    )

    by_suffix = {}

    for item in package.get("items", []):
        evidence_id = str(
            item.get("evidence_id", "")
        )

        prefix = "CELL-506_422-"

        if evidence_id.startswith(prefix):
            suffix = evidence_id[len(prefix):]
            by_suffix[suffix] = item

    results = []
    missing = []
    mismatches = []

    for suffix, expected in REQUIRED_ITEMS.items():
        item = by_suffix.get(suffix)

        if item is None:
            missing.append(suffix)
            results.append(
                (
                    suffix,
                    False,
                    "MISSING",
                )
            )
            continue

        actual = item.get("value")

        if isinstance(expected, float):
            ok = (
                actual is not None
                and abs(
                    float(actual) - expected
                )
                <= max(
                    0.01,
                    abs(expected) * 0.005,
                )
            )
        else:
            ok = actual == expected

        results.append(
            (
                suffix,
                ok,
                actual,
            )
        )

        if not ok:
            mismatches.append(
                {
                    "item": suffix,
                    "expected": expected,
                    "actual": actual,
                }
            )

    passed = (
        not missing
        and not mismatches
    )

    return {
        "passed": passed,
        "total_required": len(REQUIRED_ITEMS),
        "verified_required": sum(
            1
            for _, ok, _ in results
            if ok
        ),
        "missing": missing,
        "mismatches": mismatches,
        "results": results,
    }

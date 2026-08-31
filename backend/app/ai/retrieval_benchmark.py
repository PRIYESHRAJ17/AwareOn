from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.ai.domain_retrieval import (
    retrieve_awareon_knowledge_semantic,
)


@dataclass(frozen=True)
class RetrievalCase:
    case_id: str
    query: str
    expected_top: tuple[str, ...]


CASES = [
    RetrievalCase(
        "R01",
        "What is a landslide?",
        ("GEN-LS-001",),
    ),
    RetrievalCase(
        "R02",
        "Why do landslides happen?",
        ("GEN-LS-002",),
    ),
    RetrievalCase(
        "R03",
        "What makes wet ground lose its strength?",
        (
            "GEN-LS-011",
            "GEN-LS-005",
            "GEN-SOIL-002",
        ),
    ),
    RetrievalCase(
        "R04",
        "Can water underground make a hillside fail?",
        (
            "GEN-LS-012",
            "GEN-LS-011",
            "GEN-LS-005",
        ),
    ),
    RetrievalCase(
        "R05",
        "How does prolonged rain destabilize a slope?",
        (
            "GEN-LS-003",
            "GEN-LS-005",
            "GEN-LS-011",
        ),
    ),
    RetrievalCase(
        "R06",
        "What is effective stress?",
        ("GEN-LS-011",),
    ),
    RetrievalCase(
        "R07",
        "What is geomorphology?",
        ("GEN-LS-014",),
    ),
    RetrievalCase(
        "R08",
        "How can a spacecraft detect a slowly moving mountain?",
        (
            "GEN-SAR-002",
            "GEN-SAR-001",
            "GEN-SAR-003",
        ),
    ),
    RetrievalCase(
        "R09",
        "Why would anyone use radar instead of a normal camera?",
        ("GEN-SAR-001",),
    ),
    RetrievalCase(
        "R10",
        "What are the limitations of InSAR in mountains?",
        ("GEN-SAR-004",),
    ),
    RetrievalCase(
        "R11",
        "Why does Sikkim get hit by landslides so often?",
        ("GEN-SIKKIM-001",),
    ),
    RetrievalCase(
        "R12",
        "How can old disaster events tell us something about current danger?",
        ("GEN-SIKKIM-004",),
    ),
    RetrievalCase(
        "R13",
        "Why can cutting a road into a hillside make things worse?",
        ("GEN-LS-008",),
    ),
    RetrievalCase(
        "R14",
        "What should field teams inspect?",
        ("GEN-OPS-004",),
    ),
    RetrievalCase(
        "R15",
        "How should landslides be monitored?",
        ("GEN-OPS-001",),
    ),
    RetrievalCase(
        "R16",
        "How can landslides be mitigated?",
        ("GEN-OPS-003",),
    ),
    RetrievalCase(
        "R17",
        "What is the difference between susceptibility and risk?",
        ("GEN-RISK-001",),
    ),
    RetrievalCase(
        "R18",
        "What happens inside soil when it gets completely soaked?",
        (
            "GEN-LS-005",
            "GEN-SOIL-002",
            "GEN-LS-011",
        ),
    ),
    RetrievalCase(
        "R19",
        "What makes two nearby slopes behave differently?",
        (
            "GEN-LS-004",
            "GEN-SOIL-001",
        ),
    ),
    RetrievalCase(
        "R20",
        "How do previous landslides help us understand current hazard?",
        (
            "GEN-SIKKIM-004",
            "GEN-LS-017",
        ),
    ),
]


def run_retrieval_benchmark() -> dict[str, Any]:
    results = []

    for case in CASES:
        result = retrieve_awareon_knowledge_semantic(
            case.query,
            limit=5,
        )

        ranking = [
            item["entry"]["entry_id"]
            for item in result["ranking"]
        ]

        top = (
            ranking[0]
            if ranking
            else None
        )

        passed = (
            top in case.expected_top
        )

        top3 = ranking[:3]

        results.append(
            {
                "case_id": case.case_id,
                "query": case.query,
                "expected_top": list(
                    case.expected_top
                ),
                "actual_top": top,
                "top3": top3,
                "passed": passed,
            }
        )

    total = len(results)
    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    failed = total - passed

    score = (
        passed / total * 100.0
        if total
        else 0.0
    )

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": score,
        "results": results,
    }


if __name__ == "__main__":
    import pprint

    pprint.pp(
        run_retrieval_benchmark()
    )

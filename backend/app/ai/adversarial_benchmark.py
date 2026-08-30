from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.app.ai.agent_tools import execute_exact_cell_intelligence
from backend.app.ai.evidence_builder import build_cell_evidence_package
from backend.app.ai.evidence_synthesis import verify_claim


@dataclass(frozen=True)
class AdversarialCase:
    name: str
    runner: Callable[[], bool]


def case_wrong_category_rejected() -> bool:
    evidence = build_cell_evidence_package(
        execute_exact_cell_intelligence("506_422")
    )

    model_evidence = evidence["items"]

    from backend.app.ai.evidence_synthesis import (
        build_model_evidence,
    )

    _, canonical = build_model_evidence(
        evidence
    )

    result = verify_claim(
        "Rainfall trigger is HIGH at 24.07.",
        ["E08"],
        canonical,
    )

    return result.status == "REJECTED"


def case_correct_category_verified() -> bool:
    evidence = build_cell_evidence_package(
        execute_exact_cell_intelligence("506_422")
    )

    from backend.app.ai.evidence_synthesis import (
        build_model_evidence,
    )

    _, canonical = build_model_evidence(
        evidence
    )

    result = verify_claim(
        "Rainfall trigger category is LOW.",
        ["E08"],
        canonical,
    )

    return result.status == "VERIFIED"


def case_unknown_evidence_rejected() -> bool:
    evidence = build_cell_evidence_package(
        execute_exact_cell_intelligence("506_422")
    )

    from backend.app.ai.evidence_synthesis import (
        build_model_evidence,
    )

    _, canonical = build_model_evidence(
        evidence
    )

    result = verify_claim(
        "Cell has an earthquake trigger.",
        ["DOES_NOT_EXIST"],
        canonical,
    )

    return result.status == "REJECTED"


def case_simulated_not_observed() -> bool:
    evidence = build_cell_evidence_package(
        execute_exact_cell_intelligence("506_422")
    )

    from backend.app.ai.evidence_synthesis import (
        build_model_evidence,
    )

    _, canonical = build_model_evidence(
        evidence
    )

    result = verify_claim(
        "The simulated scenario risk is 72.04.",
        ["E12"],
        canonical,
    )

    return (
        result.status == "VERIFIED"
        and result.claim_type == "SIMULATED"
    )


def case_number_mismatch_rejected() -> bool:
    evidence = build_cell_evidence_package(
        execute_exact_cell_intelligence("506_422")
    )

    from backend.app.ai.evidence_synthesis import (
        build_model_evidence,
    )

    _, canonical = build_model_evidence(
        evidence
    )

    result = verify_claim(
        "Cell 506_422 has risk 99.99.",
        ["E01"],
        canonical,
    )

    return result.status == "REJECTED"


CASES = [
    AdversarialCase(
        "wrong_category_rejected",
        case_wrong_category_rejected,
    ),
    AdversarialCase(
        "correct_category_verified",
        case_correct_category_verified,
    ),
    AdversarialCase(
        "unknown_evidence_rejected",
        case_unknown_evidence_rejected,
    ),
    AdversarialCase(
        "simulated_not_observed",
        case_simulated_not_observed,
    ),
    AdversarialCase(
        "number_mismatch_rejected",
        case_number_mismatch_rejected,
    ),
]


def run_adversarial_benchmark():
    results = []

    for case in CASES:
        try:
            passed = bool(
                case.runner()
            )
            results.append(
                (
                    case.name,
                    passed,
                )
            )
        except Exception as exc:
            results.append(
                (
                    case.name,
                    False,
                    str(exc),
                )
            )

    passed_count = sum(
        1
        for item in results
        if item[1]
    )

    total = len(results)

    score = (
        passed_count / total * 100.0
        if total
        else 0.0
    )

    return {
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "score": score,
        "results": results,
    }

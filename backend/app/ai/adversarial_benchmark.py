from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.app.ai.agent_tools import execute_exact_cell_intelligence
from backend.app.ai.evidence_builder import build_cell_evidence_package
from backend.app.ai.evidence_synthesis import verify_claim
from backend.app.ai.autonomous_master import run_awareon_agent
from backend.app.ai.domain_router import classify_query


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


# ============================================================
# STEP 10 — FULL AGENT ROBUSTNESS
# ============================================================

def case_empty_query_rejected() -> bool:
    try:
        run_awareon_agent("")
    except ValueError:
        return True

    return False


def case_non_string_query_rejected() -> bool:
    try:
        run_awareon_agent(None)  # type: ignore[arg-type]
    except TypeError:
        return True

    return False


def case_strange_phrasing_routes() -> bool:
    normal = classify_query(
        "Why is cell 506_422 extreme?"
    )

    strange = classify_query(
        "506_422 looks insanely dangerous — why?"
    )

    return (
        normal.intent.value == "EXPLANATION"
        and strange.intent.value == "EXPLANATION"
    )


def case_ood_request_is_safe() -> bool:
    result = run_awareon_agent(
        "Give me a recipe for chocolate cake."
    )

    return (
        result.status == "OUTSIDE_DOMAIN"
        and bool(result.answer)
    )


def case_second_ood_request_is_safe() -> bool:
    result = run_awareon_agent(
        "Who won the latest football match?"
    )

    return (
        result.status == "OUTSIDE_DOMAIN"
        and bool(result.answer)
    )


def case_normal_agent_response_has_no_traceback() -> bool:
    result = run_awareon_agent(
        "What is a landslide?"
    )

    return (
        result.status == "READY"
        and bool(result.answer)
        and "traceback" not in result.answer.lower()
    )


def case_current_evidence_is_verified() -> bool:
    result = run_awareon_agent(
        "Why is cell 506_422 extreme?"
    )

    verification = result.verification or {}

    return (
        result.status == "READY"
        and isinstance(verification, dict)
        and verification.get("status") == "PASSED"
    )


def case_simulation_is_not_observation() -> bool:
    result = run_awareon_agent(
        "What happens under +100% rainfall?"
    )

    answer = result.answer.lower()

    return (
        result.status == "READY"
        and "scenario" in answer
        and "simulated" not in answer
    )


def case_historical_boundary_preserved() -> bool:
    result = run_awareon_agent(
        "Which historical landslides occurred near Gangtok?"
    )

    return (
        result.status == "READY"
        and result.intent == "HISTORICAL_EVENT"
        and bool(result.answer)
    )


def case_partial_failure_does_not_crash() -> bool:
    from backend.app.ai import autonomous_master

    original = autonomous_master._run_cell

    def failed_cell(
        query,
        memory,
    ):
        return {
            "status": "FAILED",
            "error": "synthetic test failure",
            "findings": [],
            "evidence": None,
        }

    try:
        autonomous_master._run_cell = failed_cell

        result = run_awareon_agent(
            "Why is cell 506_422 extreme?"
        )

        return (
            result.status in {
                "FAILED",
                "REVIEW_REQUIRED",
                "READY",
                "CLARIFICATION_REQUIRED",
            }
            and bool(result.answer)
        )

    finally:
        autonomous_master._run_cell = original


def case_malformed_cell_request_is_safe() -> bool:
    result = run_awareon_agent(
        "Why is cell completely-invalid extreme?"
    )

    answer = (
        result.answer
        if isinstance(result.answer, str)
        else ""
    ).lower()

    # A malformed cell identifier must never cause a crash,
    # traceback leakage, or a false claim that exact-cell
    # intelligence was successfully executed.
    return (
        bool(result.answer)
        and "traceback" not in answer
        and "exact-cell intelligence" not in answer
        and "exact cell intelligence" not in answer
        and "cell completely-invalid has" not in answer
    )


STEP10_CASES = [
    AdversarialCase(
        "empty_query_rejected",
        case_empty_query_rejected,
    ),
    AdversarialCase(
        "non_string_query_rejected",
        case_non_string_query_rejected,
    ),
    AdversarialCase(
        "strange_phrasing_routes",
        case_strange_phrasing_routes,
    ),
    AdversarialCase(
        "ood_recipe_is_safe",
        case_ood_request_is_safe,
    ),
    AdversarialCase(
        "ood_second_request_is_safe",
        case_second_ood_request_is_safe,
    ),
    AdversarialCase(
        "normal_response_no_traceback",
        case_normal_agent_response_has_no_traceback,
    ),
    AdversarialCase(
        "current_evidence_verified",
        case_current_evidence_is_verified,
    ),
    AdversarialCase(
        "simulation_boundary_preserved",
        case_simulation_is_not_observation,
    ),
    AdversarialCase(
        "historical_boundary_preserved",
        case_historical_boundary_preserved,
    ),
    AdversarialCase(
        "partial_failure_does_not_crash",
        case_partial_failure_does_not_crash,
    ),
    AdversarialCase(
        "malformed_cell_request_is_safe",
        case_malformed_cell_request_is_safe,
    ),
]


def run_step10_benchmark():
    baseline = run_adversarial_benchmark()

    results = []

    for case in STEP10_CASES:
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
        "baseline": baseline,
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "score": score,
        "results": results,
    }


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

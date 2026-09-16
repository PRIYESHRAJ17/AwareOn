from backend.app.ai.domain_router import (
    QueryDomain,
    classify_query,
)
from backend.app.ai.response_contract import (
    build_ambiguous_response,
    build_out_of_domain_response,
)
from backend.app.ai.evidence_synthesis import (
    verify_claim,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # Empty query cannot claim certainty.
    empty = classify_query("")
    check(
        empty.confidence == 0.0,
        "Empty query confidence must be 0.",
    )

    # No domain evidence cannot claim 98% certainty.
    outside = classify_query(
        "What is the boiling point of pure water?"
    )
    check(
        outside.domain == QueryDomain.OUTSIDE_DOMAIN,
        "Expected outside-domain classification.",
    )
    check(
        outside.confidence == 0.0,
        "Outside-domain routing confidence must be 0 "
        "when no AwareOn signals exist.",
    )

    response = build_out_of_domain_response(
        "What is the boiling point of pure water?",
        confidence=outside.confidence * 100.0,
    )

    check(
        response.confidence == 0.0,
        "Out-of-domain response must inherit routing confidence.",
    )

    ambiguous = build_ambiguous_response(
        confidence=42.0,
    )
    check(
        ambiguous.confidence == 42.0,
        "Ambiguous response must use supplied confidence.",
    )

    evidence = {
        "E1": {
            "evidence_id": "E1",
            "evidence_type": "OBSERVED",
            "claim": "Terrain instability is high.",
            "value": "HIGH",
            "confidence": 92.0,
        },
        "E2": {
            "evidence_id": "E2",
            "evidence_type": "OBSERVED",
            "claim": "Exposure is significant.",
            "value": "HIGH",
            "confidence": 81.0,
        },
    }

    claim = verify_claim(
        "Terrain instability is HIGH.",
        ["E1"],
        evidence,
    )

    check(
        claim.status == "VERIFIED",
        "Expected evidence-backed claim to verify.",
    )

    check(
        claim.confidence == 0.92,
        "Verified claim confidence must be derived "
        "from supporting evidence.",
    )

    weak_claim = verify_claim(
        "Exposure is HIGH.",
        ["E2"],
        evidence,
    )

    check(
        weak_claim.confidence == 0.81,
        "Verified claim confidence must track the "
        "supporting evidence confidence.",
    )

    print("CONFIDENCE INTEGRITY: PASS")


if __name__ == "__main__":
    main()

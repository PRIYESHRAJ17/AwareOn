from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# VERIFICATION ISSUE
# ============================================================

@dataclass
class VerificationIssue:
    code: str
    severity: str
    message: str
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence_id": self.evidence_id,
        }


# ============================================================
# VERIFICATION RESULT
# ============================================================

@dataclass
class VerificationResult:
    status: str
    score: float
    issues: list[VerificationIssue] = field(
        default_factory=list
    )
    checks: dict[str, bool] = field(
        default_factory=dict
    )

    @property
    def passed(self) -> bool:
        return self.status == "PASSED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "passed": self.passed,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "checks": self.checks,
        }


# ============================================================
# GENERIC HELPERS
# ============================================================

def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(
    value: Any,
) -> str:
    if value is None:
        return ""
    return str(value)


def _contains_approx_number(
    text: str,
    value: float,
    tolerance: float = 0.05,
) -> bool:
    """
    Check whether a numeric value appears in the answer.

    This deliberately uses a small set of textual
    representations rather than parsing arbitrary numbers,
    so the check remains conservative.
    """

    representations = {
        f"{value:.0f}",
        f"{value:.1f}",
        f"{value:.2f}",
        f"{value:.3f}",
    }

    text_lower = text.lower()

    for representation in representations:
        if representation in text_lower:
            return True

    return False


def _has_any_marker(
    text: str,
    markers: tuple[str, ...],
) -> bool:

    lower = text.lower()

    return any(
        marker.lower() in lower
        for marker in markers
    )


# ============================================================
# EVIDENCE PACKAGE VERIFICATION
# ============================================================

def verify_evidence_package(
    answer: str,
    evidence_package: dict[str, Any],
) -> VerificationResult:

    if not isinstance(
        answer,
        str,
    ):
        raise TypeError(
            "answer must be a string."
        )

    if not isinstance(
        evidence_package,
        dict,
    ):
        raise TypeError(
            "evidence_package must be a dictionary."
        )

    issues: list[VerificationIssue] = []

    checks: dict[str, bool] = {
        "answer_present": bool(
            answer.strip()
        ),
        "evidence_package_present": bool(
            evidence_package
        ),
        "evidence_items_present": False,
        "evidence_ids_present": True,
        "evidence_claims_present": True,
    }

    items = evidence_package.get(
        "items",
        [],
    )

    if isinstance(
        items,
        list,
    ):
        checks[
            "evidence_items_present"
        ] = len(items) > 0
    else:
        items = []

        issues.append(
            VerificationIssue(
                code="INVALID_EVIDENCE_ITEMS",
                severity="ERROR",
                message=(
                    "Evidence package items must "
                    "be a list."
                ),
            )
        )

    for item in items:

        if not isinstance(
            item,
            dict,
        ):

            checks[
                "evidence_claims_present"
            ] = False

            issues.append(
                VerificationIssue(
                    code="INVALID_EVIDENCE_ITEM",
                    severity="ERROR",
                    message=(
                        "Evidence package contains "
                        "a non-dictionary item."
                    ),
                )
            )

            continue

        evidence_id = item.get(
            "evidence_id"
        )

        claim = _text(
            item.get(
                "claim"
            )
        ).strip()

        evidence_type = _text(
            item.get(
                "evidence_type"
            )
        ).upper()

        if not evidence_id:

            checks[
                "evidence_ids_present"
            ] = False

            issues.append(
                VerificationIssue(
                    code="MISSING_EVIDENCE_ID",
                    severity="ERROR",
                    message=(
                        "Evidence item has no "
                        "provenance ID."
                    ),
                )
            )

        if not claim:

            checks[
                "evidence_claims_present"
            ] = False

            issues.append(
                VerificationIssue(
                    code="EMPTY_EVIDENCE_CLAIM",
                    severity="ERROR",
                    message=(
                        "Evidence item has no claim."
                    ),
                    evidence_id=evidence_id,
                )
            )

        # ----------------------------------------------------
        # Simulation honesty check
        # ----------------------------------------------------

        if evidence_type == "SIMULATED":

            simulation_markers = (
                "scenario",
                "simulated",
                "simulation",
                "modeled",
                "modelled",
                "tested",
                "if rainfall",
                "under rainfall",
            )

            if not _has_any_marker(
                answer,
                simulation_markers,
            ):

                issues.append(
                    VerificationIssue(
                        code="SIMULATION_NOT_LABELED",
                        severity="ERROR",
                        message=(
                            "A simulated evidence item "
                            "exists, but the answer does "
                            "not clearly identify the "
                            "result as simulated, modeled "
                            "or scenario-based."
                        ),
                        evidence_id=evidence_id,
                    )
                )

        # ----------------------------------------------------
        # Recommendation honesty check
        # ----------------------------------------------------

        if evidence_type == "RECOMMENDATION":

            recommendation_markers = (
                "recommend",
                "recommended",
                "recommendation",
                "should",
                "response",
                "action",
                "intervention",
            )

            if not _has_any_marker(
                answer,
                recommendation_markers,
            ):

                issues.append(
                    VerificationIssue(
                        code="RECOMMENDATION_NOT_LABELED",
                        severity="WARNING",
                        message=(
                            "A recommendation evidence "
                            "item exists, but the answer "
                            "does not clearly identify "
                            "the output as a recommendation "
                            "or action."
                        ),
                        evidence_id=evidence_id,
                    )
                )

    # --------------------------------------------------------
    # Core answer checks
    # --------------------------------------------------------

    if not checks[
        "answer_present"
    ]:

        issues.append(
            VerificationIssue(
                code="EMPTY_ANSWER",
                severity="ERROR",
                message=(
                    "Answer is empty."
                ),
            )
        )

    if not checks[
        "evidence_items_present"
    ]:

        issues.append(
            VerificationIssue(
                code="NO_EVIDENCE",
                severity="WARNING",
                message=(
                    "No evidence items were supplied "
                    "for verification."
                ),
            )
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    has_error = any(
        issue.severity == "ERROR"
        for issue in issues
    )

    has_warning = any(
        issue.severity == "WARNING"
        for issue in issues
    )

    if has_error:

        status = "FAILED"

    elif has_warning:

        status = "REVIEW_REQUIRED"

    else:

        status = "PASSED"

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    check_values = list(
        checks.values()
    )

    if check_values:

        score = (
            sum(
                1
                for value in check_values
                if value
            )
            /
            len(check_values)
            *
            100.0
        )

    else:

        score = 0.0

    error_penalty = sum(
        15.0
        for issue in issues
        if issue.severity == "ERROR"
    )

    warning_penalty = sum(
        5.0
        for issue in issues
        if issue.severity == "WARNING"
    )

    score = max(
        0.0,
        score
        -
        error_penalty
        -
        warning_penalty,
    )

    return VerificationResult(
        status=status,
        score=round(
            score,
            2,
        ),
        issues=issues,
        checks=checks,
    )


# ============================================================
# NUMERICAL CONSISTENCY
# ============================================================

def verify_numeric_consistency(
    answer: str,
    expected_values: dict[str, float],
    tolerance: float = 0.05,
) -> VerificationResult:

    if not isinstance(
        answer,
        str,
    ):
        raise TypeError(
            "answer must be a string."
        )

    if not isinstance(
        expected_values,
        dict,
    ):
        raise TypeError(
            "expected_values must be a dictionary."
        )

    checks: dict[str, bool] = {}
    issues: list[VerificationIssue] = []

    for name, expected in expected_values.items():

        expected_value = _num(
            expected
        )

        found = _contains_approx_number(
            answer,
            expected_value,
            tolerance,
        )

        checks[name] = found

        if not found:

            issues.append(
                VerificationIssue(
                    code="NUMERIC_VALUE_MISSING",
                    severity="WARNING",
                    message=(
                        f"Expected value for "
                        f"{name} "
                        f"({expected_value:.2f}) "
                        "was not found in the answer."
                    ),
                )
            )

    if issues:

        status = "REVIEW_REQUIRED"

    else:

        status = "PASSED"

    if checks:

        score = (
            sum(
                1
                for value in checks.values()
                if value
            )
            /
            len(checks)
            *
            100.0
        )

    else:

        score = 100.0

    return VerificationResult(
        status=status,
        score=round(
            score,
            2,
        ),
        issues=issues,
        checks=checks,
    )


# ============================================================
# INVESTIGATION COMPLETENESS
# ============================================================

def verify_investigation_completeness(
    completed_steps: list[str],
    required_steps: list[str],
) -> VerificationResult:

    if not isinstance(
        completed_steps,
        list,
    ):
        raise TypeError(
            "completed_steps must be a list."
        )

    if not isinstance(
        required_steps,
        list,
    ):
        raise TypeError(
            "required_steps must be a list."
        )

    completed = set(
        str(step)
        for step in completed_steps
    )

    required = set(
        str(step)
        for step in required_steps
    )

    missing = sorted(
        required - completed
    )

    checks = {
        step: step in completed
        for step in required_steps
    }

    issues = [
        VerificationIssue(
            code="MISSING_INVESTIGATION_STEP",
            severity="WARNING",
            message=(
                f"Required investigation step "
                f"'{step}' was not completed."
            ),
        )
        for step in missing
    ]

    if missing:

        status = "REVIEW_REQUIRED"

    else:

        status = "PASSED"

    if required:

        score = (
            (
                len(required)
                -
                len(missing)
            )
            /
            len(required)
            *
            100.0
        )

    else:

        score = 100.0

    return VerificationResult(
        status=status,
        score=round(
            score,
            2,
        ),
        issues=issues,
        checks=checks,
    )


# ============================================================
# CONTRADICTION CHECK
# ============================================================

def verify_known_contradictions(
    answer: str,
    forbidden_claims: list[str],
) -> VerificationResult:

    if not isinstance(
        answer,
        str,
    ):
        raise TypeError(
            "answer must be a string."
        )

    if not isinstance(
        forbidden_claims,
        list,
    ):
        raise TypeError(
            "forbidden_claims must be a list."
        )

    issues: list[VerificationIssue] = []
    checks: dict[str, bool] = {}

    lower_answer = answer.lower()

    for claim in forbidden_claims:

        normalized_claim = str(
            claim
        ).strip()

        if not normalized_claim:
            continue

        found = (
            normalized_claim.lower()
            in lower_answer
        )

        key = (
            f"forbidden:{normalized_claim}"
        )

        checks[key] = not found

        if found:

            issues.append(
                VerificationIssue(
                    code="FORBIDDEN_CLAIM_PRESENT",
                    severity="ERROR",
                    message=(
                        "Answer contains a claim "
                        "explicitly marked as "
                        "unsupported."
                    ),
                )
            )

    if any(
        issue.severity == "ERROR"
        for issue in issues
    ):

        status = "FAILED"

    elif issues:

        status = "REVIEW_REQUIRED"

    else:

        status = "PASSED"

    if checks:

        score = (
            sum(
                1
                for value in checks.values()
                if value
            )
            /
            len(checks)
            *
            100.0
        )

    else:

        score = 100.0

    return VerificationResult(
        status=status,
        score=round(
            score,
            2,
        ),
        issues=issues,
        checks=checks,
    )


# ============================================================
# MASTER RESPONSE VERIFICATION
# ============================================================

def verify_response(
    answer: str,
    evidence_package: dict[str, Any],
    *,
    expected_values: dict[str, float] | None = None,
    completed_steps: list[str] | None = None,
    required_steps: list[str] | None = None,
    forbidden_claims: list[str] | None = None,
) -> VerificationResult:

    results: list[
        VerificationResult
    ] = []

    # --------------------------------------------------------
    # Evidence verification
    # --------------------------------------------------------

    results.append(
        verify_evidence_package(
            answer,
            evidence_package,
        )
    )

    # --------------------------------------------------------
    # Numerical verification
    # --------------------------------------------------------

    if expected_values is not None:

        results.append(
            verify_numeric_consistency(
                answer,
                expected_values,
            )
        )

    # --------------------------------------------------------
    # Investigation completeness
    # --------------------------------------------------------

    if (
        completed_steps is not None
        and
        required_steps is not None
    ):

        results.append(
            verify_investigation_completeness(
                completed_steps,
                required_steps,
            )
        )

    # --------------------------------------------------------
    # Known contradiction verification
    # --------------------------------------------------------

    if forbidden_claims is not None:

        results.append(
            verify_known_contradictions(
                answer,
                forbidden_claims,
            )
        )

    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    all_issues: list[
        VerificationIssue
    ] = []

    all_checks: dict[
        str,
        bool,
    ] = {}

    scores: list[float] = []

    has_error = False
    has_warning = False

    for result in results:

        scores.append(
            result.score
        )

        all_issues.extend(
            result.issues
        )

        for key, value in result.checks.items():

            all_checks[key] = value

        if result.status == "FAILED":
            has_error = True

        elif result.status == "REVIEW_REQUIRED":
            has_warning = True

    if has_error:

        status = "FAILED"

    elif has_warning:

        status = "REVIEW_REQUIRED"

    else:

        status = "PASSED"

    if scores:

        score = (
            sum(scores)
            /
            len(scores)
        )

    else:

        score = 0.0

    return VerificationResult(
        status=status,
        score=round(
            score,
            2,
        ),
        issues=all_issues,
        checks=all_checks,
    )

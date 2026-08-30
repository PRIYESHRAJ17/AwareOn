from __future__ import annotations

from typing import Any


VALID_CATEGORIES = {
    "LOW",
    "MODERATE",
    "HIGH",
    "EXTREME",
    "VERY_HIGH",
    "NORMAL",
    "UNKNOWN",
}


def _num(
    value: Any,
) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _category(
    value: Any,
) -> str:
    return str(
        value or "UNKNOWN"
    ).upper()


def _severity_rank(
    category: str,
) -> int:

    ranks = {
        "LOW": 0,
        "NORMAL": 0,
        "UNKNOWN": 0,
        "MODERATE": 1,
        "HIGH": 2,
        "VERY_HIGH": 3,
        "EXTREME": 3,
    }

    return ranks.get(
        _category(category),
        0,
    )


def _add_issue(
    collection: list[dict[str, Any]],
    code: str,
    severity: str,
    message: str,
    engine: str | None = None,
) -> None:

    issue = {
        "code": code,
        "severity": severity,
        "message": message,
    }

    if engine is not None:
        issue["engine"] = engine

    collection.append(
        issue
    )


def validate_normalized_engine(
    engine: dict[str, Any],
) -> list[dict[str, Any]]:

    issues: list[
        dict[str, Any]
    ] = []

    name = str(
        engine.get(
            "engine",
            "UNKNOWN",
        )
    )

    score = engine.get(
        "score"
    )

    probability = engine.get(
        "probability_percent"
    )

    category = _category(
        engine.get(
            "category"
        )
    )

    if category not in VALID_CATEGORIES:

        _add_issue(
            issues,
            "INVALID_CATEGORY",
            "ERROR",
            f"Unsupported category: {category}",
            name,
        )

    numeric_score = _num(
        score
    )

    if numeric_score is not None:

        if (
            numeric_score < 0.0
            or numeric_score > 100.0
        ):

            _add_issue(
                issues,
                "SCORE_OUT_OF_RANGE",
                "ERROR",
                f"Score {numeric_score} is outside 0–100.",
                name,
            )

    numeric_probability = _num(
        probability
    )

    if numeric_probability is not None:

        if (
            numeric_probability < 0.0
            or numeric_probability > 100.0
        ):

            _add_issue(
                issues,
                "PROBABILITY_OUT_OF_RANGE",
                "ERROR",
                (
                    f"Probability {numeric_probability} "
                    "is outside 0–100 percent."
                ),
                name,
            )

    rank = _severity_rank(
        category
    )

    if (
        rank >= 3
        and
        numeric_score is not None
        and
        numeric_score < 60.0
    ):

        _add_issue(
            issues,
            "CATEGORY_SCORE_MISMATCH",
            "WARNING",
            (
                f"{category} category has a relatively "
                f"low score of {numeric_score:.2f}."
            ),
            name,
        )

    if (
        rank == 2
        and
        numeric_score is not None
        and
        numeric_score < 40.0
    ):

        _add_issue(
            issues,
            "HIGH_SCORE_MISMATCH",
            "WARNING",
            (
                f"HIGH category has a relatively low "
                f"score of {numeric_score:.2f}."
            ),
            name,
        )

    return issues


def validate_normalized_assessment(
    normalized: dict[str, Any],
    original: dict[str, Any] | None = None,
) -> dict[str, Any]:

    if not normalized:
        raise ValueError(
            "Normalized assessment is required."
        )

    issues: list[
        dict[str, Any]
    ] = []

    engines = normalized.get(
        "engines",
        [],
    )

    if not isinstance(
        engines,
        list,
    ):

        raise ValueError(
            "Normalized assessment engines must be a list."
        )

    if not engines:

        _add_issue(
            issues,
            "NO_ENGINES",
            "ERROR",
            "No normalized engine outputs are available.",
        )

    names = []

    for engine in engines:

        if not isinstance(
            engine,
            dict,
        ):

            _add_issue(
                issues,
                "INVALID_ENGINE_RECORD",
                "ERROR",
                "An engine record is not a dictionary.",
            )

            continue

        name = str(
            engine.get(
                "engine",
                "UNKNOWN",
            )
        )

        names.append(
            name
        )

        issues.extend(
            validate_normalized_engine(
                engine
            )
        )

    duplicates = {
        name
        for name in names
        if names.count(name) > 1
    }

    for name in sorted(
        duplicates
    ):

        _add_issue(
            issues,
            "DUPLICATE_ENGINE",
            "ERROR",
            f"Engine '{name}' appears more than once.",
            name,
        )

    unified_risk = _num(
        normalized.get(
            "unified_risk_score"
        )
    )

    if unified_risk is None:

        _add_issue(
            issues,
            "MISSING_UNIFIED_RISK",
            "ERROR",
            "Unified risk score is missing or invalid.",
        )

    elif (
        unified_risk < 0.0
        or unified_risk > 100.0
    ):

        _add_issue(
            issues,
            "UNIFIED_RISK_OUT_OF_RANGE",
            "ERROR",
            f"Unified risk {unified_risk} is outside 0–100.",
        )

    confidence = _num(
        normalized.get(
            "confidence_score"
        )
    )

    uncertainty = _num(
        normalized.get(
            "uncertainty_score"
        )
    )

    if confidence is None:

        _add_issue(
            issues,
            "MISSING_CONFIDENCE",
            "WARNING",
            "Confidence score is unavailable.",
        )

    elif (
        confidence < 0.0
        or confidence > 100.0
    ):

        _add_issue(
            issues,
            "CONFIDENCE_OUT_OF_RANGE",
            "ERROR",
            f"Confidence {confidence} is outside 0–100.",
        )

    if uncertainty is None:

        _add_issue(
            issues,
            "MISSING_UNCERTAINTY",
            "WARNING",
            "Uncertainty score is unavailable.",
        )

    elif (
        uncertainty < 0.0
        or uncertainty > 100.0
    ):

        _add_issue(
            issues,
            "UNCERTAINTY_OUT_OF_RANGE",
            "ERROR",
            f"Uncertainty {uncertainty} is outside 0–100.",
        )

    if (
        confidence is not None
        and uncertainty is not None
    ):

        total = (
            confidence
            +
            uncertainty
        )

        if abs(
            total - 100.0
        ) > 2.0:

            _add_issue(
                issues,
                "CONFIDENCE_UNCERTAINTY_GAP",
                "WARNING",
                (
                    "Confidence and uncertainty do not "
                    f"approximately sum to 100 "
                    f"(currently {total:.2f})."
                ),
            )

    severity = _category(
        normalized.get(
            "severity"
        )
    )

    if (
        unified_risk is not None
        and
        _severity_rank(
            severity
        ) >= 3
        and
        unified_risk < 50.0
    ):

        _add_issue(
            issues,
            "RISK_SEVERITY_MISMATCH",
            "WARNING",
            (
                f"Severity is {severity} while unified "
                f"risk is only {unified_risk:.2f}."
            ),
        )

    if original:

        original_cell = str(
            original.get(
                "cell_id",
                "",
            )
        )

        normalized_cell = str(
            normalized.get(
                "cell_id",
                "",
            )
        )

        if (
            original_cell
            and
            normalized_cell
            and
            original_cell
            !=
            normalized_cell
        ):

            _add_issue(
                issues,
                "CELL_ID_MISMATCH",
                "ERROR",
                (
                    f"Original cell {original_cell} does not "
                    f"match normalized cell {normalized_cell}."
                ),
            )

    error_count = sum(
        1
        for issue in issues
        if issue["severity"] == "ERROR"
    )

    warning_count = sum(
        1
        for issue in issues
        if issue["severity"] == "WARNING"
    )

    if error_count > 0:

        status = "INVALID"

    elif warning_count > 0:

        status = "WARNING"

    else:

        status = "VALID"

    if status == "VALID":

        quality_summary = (
            "Normalized intelligence passed all "
            "sanity checks."
        )

    elif status == "WARNING":

        quality_summary = (
            f"Normalized intelligence passed structural "
            f"checks with {warning_count} warning(s)."
        )

    else:

        quality_summary = (
            f"Normalized intelligence contains "
            f"{error_count} error(s) requiring review."
        )

    return {
        "status":
            status,

        "quality_summary":
            quality_summary,

        "engine_count":
            len(engines),

        "error_count":
            error_count,

        "warning_count":
            warning_count,

        "issue_count":
            len(issues),

        "issues":
            issues,
    }


def validate_assessment(
    assessment: dict[str, Any],
) -> dict[str, Any]:

    from backend.app.intelligence_normalizer import (
        normalize_assessment,
    )

    normalized = normalize_assessment(
        assessment
    )

    return validate_normalized_assessment(
        normalized,
        original=assessment,
    )

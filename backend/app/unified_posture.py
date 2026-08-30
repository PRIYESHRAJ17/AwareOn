from __future__ import annotations

from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category(value: Any) -> str:
    return str(value or "UNKNOWN").upper()


def _rank(value: Any) -> int:
    return CATEGORY_RANK.get(
        _category(value),
        0,
    )


def _high_spatial(pattern: str) -> bool:
    return pattern in {
        "HIGH_RISK_CLUSTER",
        "FOCUSED_HIGH_RISK",
    }


def _clustered_spatial(pattern: str) -> bool:
    return pattern in {
        "HIGH_RISK_CLUSTER",
        "FOCUSED_HIGH_RISK",
        "CLUSTERED",
        "WATCH_CLUSTER",
    }


def _scenario_signal(
    current_category: str,
    future_category: str,
    future_change: float,
) -> str:
    current_rank = _rank(current_category)
    future_rank = _rank(future_category)

    if future_rank > current_rank:
        return "HIGH_SENSITIVITY"

    if future_change >= 5.0:
        return "HIGH_SENSITIVITY"

    if future_change >= 2.0:
        return "MODERATE_SENSITIVITY"

    return "STABLE"


def _posture(
    current_rank: int,
    scenario_signal: str,
    spatial_pattern: str,
) -> str:
    high_spatial = _high_spatial(spatial_pattern)

    if (
        current_rank >= 3
        and high_spatial
        and scenario_signal == "HIGH_SENSITIVITY"
    ):
        return "CRITICAL_CLUSTER_AND_SCENARIO_SENSITIVE"

    if (
        current_rank >= 3
        and scenario_signal == "HIGH_SENSITIVITY"
    ):
        return "CURRENTLY_CRITICAL_AND_SCENARIO_SENSITIVE"

    if (
        current_rank >= 3
        and high_spatial
    ):
        return "CRITICAL_CLUSTER_RISK"

    if (
        current_rank >= 2
        and scenario_signal == "HIGH_SENSITIVITY"
    ):
        return "HIGH_RISK_SCENARIO_SENSITIVE"

    if (
        scenario_signal == "HIGH_SENSITIVITY"
        and high_spatial
    ):
        return "ESCALATING_CLUSTER_RISK"

    if _clustered_spatial(spatial_pattern):
        return "SPATIAL_CLUSTER_RISK"

    if current_rank >= 2:
        return "CURRENT_RISK_DOMINANT"

    if scenario_signal == "MODERATE_SENSITIVITY":
        return "STRESS_SENSITIVE"

    return "BASELINE_MONITORING"


def _priority_score(
    current_rank: int,
    scenario_signal: str,
    spatial_pattern: str,
    evidence_state: str,
) -> float:
    score = 0.0

    if current_rank >= 3:
        score += 35.0
    elif current_rank >= 2:
        score += 25.0
    elif current_rank >= 1:
        score += 12.0

    if scenario_signal == "HIGH_SENSITIVITY":
        score += 25.0
    elif scenario_signal == "MODERATE_SENSITIVITY":
        score += 12.0

    if _high_spatial(spatial_pattern):
        score += 25.0
    elif _clustered_spatial(spatial_pattern):
        score += 12.0

    if evidence_state == "MULTI_ENGINE_CONVERGENCE":
        score += 10.0
    elif evidence_state == "EVIDENCE_CONFLICT":
        score += 5.0

    return min(100.0, score)


def _priority_level(score: float) -> str:
    if score >= 80.0:
        return "P1"

    if score >= 60.0:
        return "P2"

    if score >= 40.0:
        return "P3"

    return "P4"


def _confidence_band(score: float) -> str:
    if score >= 75.0:
        return "HIGH"

    if score >= 50.0:
        return "MODERATE"

    return "LIMITED"


def build_unified_posture(
    current_assessment: dict[str, Any],
    current_risk_posture: dict[str, Any],
    cross_engine: dict[str, Any],
    evidence_state: dict[str, Any],
    spatial_pattern: dict[str, Any],
) -> dict[str, Any]:

    if not current_assessment:
        raise ValueError("Current assessment is required.")

    if not current_risk_posture:
        raise ValueError("Current risk posture is required.")

    if not cross_engine:
        raise ValueError("Cross-engine intelligence is required.")

    if not evidence_state:
        raise ValueError("Evidence state is required.")

    if not spatial_pattern:
        raise ValueError("Spatial pattern is required.")

    cell_id = current_assessment.get("cell_id")

    if not cell_id:
        raise ValueError(
            "Current assessment must contain cell_id."
        )

    current_risk = _num(
        current_assessment.get("unified_risk_score")
    )

    current_severity = _category(
        current_assessment.get("severity")
    )

    current_warning = _category(
        current_assessment.get("warning_state")
    )

    current_rank = _rank(
        current_severity
    )

    current_confidence = _num(
        current_assessment.get("confidence_score")
    )

    future = current_risk_posture.get(
        "future",
        {},
    )

    if not isinstance(future, dict):
        future = {}

    future_risk = _num(
        future.get("risk_score")
    )

    future_change = _num(
        future.get("risk_change")
    )

    future_category = _category(
        future.get("category")
    )

    scenario_signal = _scenario_signal(
        current_severity,
        future_category,
        future_change,
    )

    spatial_pattern_name = _category(
        spatial_pattern.get("pattern")
    )

    spatial_strength = _category(
        spatial_pattern.get("pattern_strength")
    )

    spatial_confidence = _category(
        spatial_pattern.get("confidence")
    )

    evidence_name = _category(
        evidence_state.get("evidence_state")
    )

    unified_posture = _posture(
        current_rank,
        scenario_signal,
        spatial_pattern_name,
    )

    priority_score = _priority_score(
        current_rank,
        scenario_signal,
        spatial_pattern_name,
        evidence_name,
    )

    priority_level = _priority_level(
        priority_score
    )

    spatial_confidence_score = {
        "HIGH": 85.0,
        "MODERATE": 60.0,
        "LIMITED": 40.0,
    }.get(
        spatial_confidence,
        40.0,
    )

    cross_engine_confidence = _num(
        cross_engine.get(
            "confidence_score"
        ),
        current_confidence,
    )

    unified_confidence = (
        current_confidence
        + cross_engine_confidence
        + spatial_confidence_score
    ) / 3.0

    confidence_band = _confidence_band(
        unified_confidence
    )

    high_risk_neighbors = int(
        _num(
            spatial_pattern.get(
                "high_risk_cells"
            )
        )
    )

    extreme_neighbors = int(
        _num(
            spatial_pattern.get(
                "extreme_cells"
            )
        )
    )

    if evidence_name == "EVIDENCE_CONFLICT":
        evidence_statement = (
            "Engine evidence is mixed. Structural and "
            "dynamic signals should be interpreted separately."
        )

    elif evidence_name == "MULTI_ENGINE_CONVERGENCE":
        evidence_statement = (
            "Multiple engine groups provide converging "
            "support for the current risk state."
        )

    elif evidence_name == "STRUCTURAL_DOMINANCE":
        evidence_statement = (
            "structural and spatial conditions."
        )

    elif evidence_name == "DYNAMIC_CONVERGENCE":
        evidence_statement = (
            "Current risk is strongly supported by "
            "active environmental signals."
        )

    else:
        evidence_statement = (
            "Available engine evidence should be interpreted "
            "with the stated confidence level."
        )

    statement_parts = [
        (
            f"Current risk is {current_severity} "
            f"with a score of {current_risk:.2f}."
        )
    ]

    if scenario_signal == "HIGH_SENSITIVITY":
        statement_parts.append(
            (
                f"The highest tested scenario changes "
                f"risk by +{future_change:.2f} points."
            )
        )

    elif scenario_signal == "MODERATE_SENSITIVITY":
        statement_parts.append(
            (
                f"The tested scenario produces a "
                f"+{future_change:.2f} point increase."
            )
        )

    if _high_spatial(spatial_pattern_name):
        statement_parts.append(
            (
                f"The cell is within a high-risk spatial "
                f"cluster containing {high_risk_neighbors} "
                f"HIGH/EXTREME neighboring cells."
            )
        )

    elif _clustered_spatial(spatial_pattern_name):
        statement_parts.append(
            "The surrounding area shows a localized cluster "
            "of elevated risk."
        )

    statement_parts.append(
        evidence_statement
    )

    return {
        "cell_id": cell_id,

        "unified_posture": unified_posture,

        "priority_level": priority_level,

        "priority_score": priority_score,

        "confidence": unified_confidence,

        "confidence_band": confidence_band,

        "current_state": {
            "risk_score": current_risk,
            "severity": current_severity,
            "warning_state": current_warning,
            "signal": (
                "CRITICAL"
                if current_rank >= 3
                else "HIGH"
                if current_rank >= 2
                else "MODERATE"
                if current_rank >= 1
                else "LOW"
            ),
        },

        "scenario_state": {
            "posture": str(
                current_risk_posture.get(
                    "posture"
                )
                or "UNKNOWN"
            ),
            "signal": scenario_signal,
            "future_risk": future_risk,
            "risk_change": future_change,
            "future_category": future_category,
        },

        "spatial_state": {
            "pattern": spatial_pattern_name,
            "strength": spatial_strength,
            "signal": (
                "CLUSTERED_HIGH_RISK"
                if _high_spatial(
                    spatial_pattern_name
                )
                else "CLUSTERED_ELEVATION"
                if _clustered_spatial(
                    spatial_pattern_name
                )
                else "LIMITED_SPATIAL_PATTERN"
            ),
            "high_risk_neighbors": high_risk_neighbors,
            "extreme_neighbors": extreme_neighbors,
            "confidence": spatial_confidence,
        },

        "evidence_state": {
            "state": evidence_name,
            "strength": cross_engine.get(
                "evidence_strength"
            ),
        },

        "decision_statement": " ".join(
            statement_parts
        ),
    }

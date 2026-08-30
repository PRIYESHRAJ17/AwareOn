from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.ai.domain_router import (
    QueryDomain,
    classify_query,
)
from backend.app.ai.grounding import (
    EvidencePackage,
    ground_tool_result,
    merge_evidence,
)
from backend.app.regional_intelligence import (
    build_regional_intelligence,
)


# ============================================================
# INVESTIGATION RESULT
# ============================================================

@dataclass
class RegionalInvestigation:
    query: str
    latitude: float
    longitude: float
    intent: str
    completed_steps: list[str] = field(
        default_factory=list
    )
    tool_results: dict[str, Any] = field(
        default_factory=dict
    )
    evidence: EvidencePackage | None = None
    findings: list[str] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "intent": self.intent,
            "completed_steps":
                self.completed_steps,
            "tool_results":
                self.tool_results,
            "evidence":
                (
                    self.evidence.to_dict()
                    if self.evidence
                    else None
                ),
            "findings":
                self.findings,
        }


# ============================================================
# NUMERIC HELPER
# ============================================================

def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# COORDINATE EXTRACTION
# ============================================================

def extract_coordinates(
    query: str,
) -> tuple[float, float] | None:

    cleaned = (
        query
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(":", " ")
    )

    tokens = cleaned.split()

    numbers: list[float] = []

    for token in tokens:

        value = token.strip().strip(
            ".!?;\"'"
        )

        try:
            number = float(value)
        except ValueError:
            continue

        numbers.append(number)

    for index in range(
        len(numbers) - 1
    ):

        latitude = numbers[index]
        longitude = numbers[index + 1]

        if (
            -90.0 <= latitude <= 90.0
            and
            -180.0 <= longitude <= 180.0
        ):
            return (
                latitude,
                longitude,
            )

    return None


# ============================================================
# MAXIMUM RISK EXTRACTION
# ============================================================

def _extract_maximum_risk(
    value: Any,
) -> tuple[float | None, str | None]:

    if isinstance(
        value,
        dict,
    ):

        score = value.get(
            "risk_score"
        )

        if score is None:
            score = value.get(
                "score"
            )

        cell_id = value.get(
            "cell_id"
        )

        return (
            (
                _num(score)
                if score is not None
                else None
            ),
            (
                str(cell_id)
                if cell_id is not None
                else None
            ),
        )

    if value is None:
        return (
            None,
            None,
        )

    return (
        _num(value),
        None,
    )


# ============================================================
# FINDING EXTRACTION
# ============================================================

def _build_findings(
    result: dict[str, Any],
) -> list[str]:

    findings: list[str] = []

    regional_state = result.get(
        "regional_state"
    )

    cell_count = result.get(
        "cell_count"
    )

    high_cells = result.get(
        "high_or_extreme_cells"
    )

    extreme_cells = result.get(
        "extreme_cells"
    )

    mean_risk = result.get(
        "mean_risk_score"
    )

    maximum_risk_value = result.get(
        "maximum_risk"
    )

    spatial_pattern = result.get(
        "spatial_pattern"
    )

    confidence = result.get(
        "confidence_band"
    )

    maximum_risk, maximum_risk_cell = (
        _extract_maximum_risk(
            maximum_risk_value
        )
    )

    if regional_state:

        findings.append(
            f"Regional state is {regional_state}."
        )

    if cell_count is not None:

        findings.append(
            f"Regional analysis covers "
            f"{int(_num(cell_count))} cells."
        )

    if high_cells is not None:

        findings.append(
            f"{int(_num(high_cells))} cells are "
            "HIGH or EXTREME risk."
        )

    if extreme_cells is not None:

        findings.append(
            f"{int(_num(extreme_cells))} cells "
            "are EXTREME."
        )

    if mean_risk is not None:

        findings.append(
            f"Mean regional risk is "
            f"{_num(mean_risk):.2f}."
        )

    if maximum_risk is not None:

        if maximum_risk_cell:

            findings.append(
                f"Maximum regional risk is "
                f"{maximum_risk:.2f} at cell "
                f"{maximum_risk_cell}."
            )

        else:

            findings.append(
                f"Maximum regional risk is "
                f"{maximum_risk:.2f}."
            )

    if spatial_pattern:

        if isinstance(
            spatial_pattern,
            dict,
        ):

            pattern = (
                spatial_pattern.get(
                    "pattern"
                )
                or spatial_pattern.get(
                    "classification"
                )
            )

            if pattern:

                findings.append(
                    f"Spatial pattern is "
                    f"{pattern}."

                )

        else:

            findings.append(
                f"Spatial pattern is "
                f"{spatial_pattern}."
            )

    if confidence:

        findings.append(
            f"Regional confidence band is "
            f"{confidence}."
        )

    top_cells = result.get(
        "top_cells",
        [],
    )

    if isinstance(
        top_cells,
        list,
    ):

        for item in top_cells[:3]:

            if not isinstance(
                item,
                dict,
            ):
                continue

            cell_id = item.get(
                "cell_id"
            )

            severity = item.get(
                "severity"
            )

            risk = item.get(
                "risk_score"
            )

            if (
                cell_id
                and
                risk is not None
            ):

                statement = (
                    f"Top regional cell "
                    f"{cell_id} has risk "
                    f"{_num(risk):.2f}"
                )

                if severity:

                    statement += (
                        f" and severity "
                        f"{severity}."
                    )

                else:

                    statement += "."

                findings.append(
                    statement
                )

    return findings


# ============================================================
# REGIONAL INVESTIGATOR
# ============================================================

def investigate_region(
    query: str,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 10000.0,
) -> RegionalInvestigation:

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    decision = classify_query(
        query
    )

    if decision.domain != QueryDomain.AWAREON:

        raise ValueError(
            "Regional investigation requires "
            "an AwareOn-domain query."
        )

    if (
        latitude is None
        or
        longitude is None
    ):

        coordinates = extract_coordinates(
            query
        )

        if coordinates is None:

            raise ValueError(
                "Latitude and longitude are required "
                "for regional investigation."
            )

        latitude, longitude = coordinates

    if not (
        -90.0 <= latitude <= 90.0
    ):

        raise ValueError(
            "latitude must be between -90 and 90."
        )

    if not (
        -180.0 <= longitude <= 180.0
    ):

        raise ValueError(
            "longitude must be between -180 and 180."
        )

    if radius_m <= 0:

        raise ValueError(
            "radius_m must be greater than 0."
        )

    investigation = RegionalInvestigation(
        query=query,
        latitude=latitude,
        longitude=longitude,
        intent=decision.intent.value,
    )

    # --------------------------------------------------------
    # Step 1 — Regional intelligence
    # --------------------------------------------------------

    result = build_regional_intelligence(
        latitude,
        longitude,
        radius_m,
    )

    investigation.completed_steps.append(
        "regional_intelligence"
    )

    investigation.tool_results[
        "regional_intelligence"
    ] = result

    # --------------------------------------------------------
    # Step 2 — Evidence grounding
    # --------------------------------------------------------

    evidence = ground_tool_result(
        "regional_intelligence",
        result,
        query,
    )

    investigation.evidence = merge_evidence(
        [evidence]
    )

    investigation.completed_steps.append(
        "evidence_grounding"
    )

    # --------------------------------------------------------
    # Step 3 — Structured findings
    # --------------------------------------------------------

    investigation.findings = _build_findings(
        result
    )

    investigation.completed_steps.append(
        "finding_extraction"
    )

    return investigation

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.ai.domain_router import (
    QueryDomain,
    QueryIntent,
    classify_query,
)
from backend.app.ai.grounding import (
    EvidencePackage,
    ground_tool_result,
    merge_evidence,
)
from backend.app.exact_cell_intelligence import (
    build_exact_cell_intelligence,
)


# ============================================================
# INVESTIGATION RESULT
# ============================================================

@dataclass
class CellInvestigation:
    query: str
    cell_id: str
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
            "cell_id": self.cell_id,
            "intent": self.intent,
            "completed_steps": self.completed_steps,
            "tool_results": self.tool_results,
            "evidence": (
                self.evidence.to_dict()
                if self.evidence
                else None
            ),
            "findings": self.findings,
        }


# ============================================================
# CELL ID EXTRACTION
# ============================================================

def extract_cell_id(
    query: str,
) -> str | None:

    tokens = (
        query.replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(":", " ")
        .split()
    )

    for token in tokens:

        cleaned = token.strip().strip(
            ".!?;\"'"
        )

        if "_" not in cleaned:
            continue

        left, right = cleaned.split(
            "_",
            1,
        )

        if left.isdigit() and right.isdigit():
            return cleaned

    return None


# ============================================================
# FINDINGS
# ============================================================

def _build_findings(
    result: dict[str, Any],
) -> list[str]:

    findings: list[str] = []

    cell_id = str(
        result.get(
            "cell_id"
        )
        or "UNKNOWN"
    )

    summary = result.get(
        "signal_summary",
        {},
    )

    if not isinstance(
        summary,
        dict,
    ):
        summary = {}

    risk = summary.get(
        "current_risk_score"
    )

    severity = summary.get(
        "current_severity"
    )

    scenario = summary.get(
        "scenario_risk"
    )

    scenario_change = summary.get(
        "scenario_risk_change"
    )

    neighbors = summary.get(
        "neighbor_count"
    )

    spatial_pattern = summary.get(
        "spatial_pattern"
    )

    evidence_state = summary.get(
        "evidence_state"
    )

    if risk is not None:
        findings.append(
            (
                f"Cell {cell_id} current risk "
                f"score is {float(risk):.2f}."
            )
        )

    if severity:
        findings.append(
            (
                f"Current severity is {severity}."
            )
        )

    if scenario is not None:
        findings.append(
            (
                f"Tested scenario risk is "
                f"{float(scenario):.2f}."
            )
        )

    if scenario_change is not None:
        findings.append(
            (
                f"Tested scenario changes risk by "
                f"{float(scenario_change):+.2f}."
            )
        )

    if neighbors is not None:
        findings.append(
            (
                f"Neighborhood analysis includes "
                f"{neighbors} nearby cells."
            )
        )

    if spatial_pattern:
        findings.append(
            (
                f"Spatial pattern is {spatial_pattern}."
            )
        )

    if evidence_state:
        findings.append(
            (
                f"Evidence state is {evidence_state}."
            )
        )

    return findings


# ============================================================
# MAIN INVESTIGATOR
# ============================================================

def investigate_cell(
    query: str,
    rainfall_change_percent: float = 100.0,
    radius_m: float = 5000.0,
) -> CellInvestigation:

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
            "Cell investigation requires an "
            "AwareOn-domain query."
        )

    cell_id = extract_cell_id(
        query
    )

    if not cell_id:

        raise ValueError(
            "No AwareOn cell ID was found "
            "in the query."
        )

    investigation = CellInvestigation(
        query=query,
        cell_id=cell_id,
        intent=decision.intent.value,
    )

    # --------------------------------------------------------
    # Step 1 — Exact cell intelligence
    # --------------------------------------------------------

    exact = build_exact_cell_intelligence(
        cell_id,
        rainfall_change_percent,
        radius_m,
    )

    investigation.completed_steps.append(
        "exact_cell_intelligence"
    )

    investigation.tool_results[
        "exact_cell_intelligence"
    ] = exact

    # --------------------------------------------------------
    # Step 2 — Ground evidence
    # --------------------------------------------------------

    exact_evidence = ground_tool_result(
        "exact_cell_intelligence",
        exact,
        query,
    )

    investigation.evidence = merge_evidence(
        [exact_evidence]
    )

    investigation.completed_steps.append(
        "evidence_grounding"
    )

    # --------------------------------------------------------
    # Step 3 — Generate structured findings
    # --------------------------------------------------------

    investigation.findings = _build_findings(
        exact
    )

    investigation.completed_steps.append(
        "finding_extraction"
    )

    return investigation

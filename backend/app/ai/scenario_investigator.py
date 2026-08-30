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
from backend.app.services.scenario_service import (
    scenario_service,
)


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class ScenarioInvestigation:
    query: str
    intent: str
    rainfall_scenarios: list[float]
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
            "intent": self.intent,
            "rainfall_scenarios":
                self.rainfall_scenarios,
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
# NUMBER EXTRACTION
# ============================================================

def extract_percentages(
    query: str,
) -> list[float]:

    cleaned = (
        query
        .replace("%", " ")
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(":", " ")
        .replace("/", " ")
    )

    tokens = cleaned.split()

    values: list[float] = []

    for token in tokens:

        token = token.strip(
            ".!?;\"'"
        )

        try:
            value = float(token)
        except ValueError:
            continue

        if (
            -500.0
            <= value
            <= 500.0
        ):
            values.append(
                value
            )

    return values


# ============================================================
# DEFAULT SCENARIOS
# ============================================================

def _resolve_scenarios(
    query: str,
) -> list[float]:

    values = extract_percentages(
        query
    )

    if values:
        unique = sorted(
            set(values)
        )

        return unique[:10]

    return [
        0.0,
        25.0,
        50.0,
        100.0,
    ]


# ============================================================
# SCENARIO RESULT HELPERS
# ============================================================

def _extract_mean_risk(
    result: dict[str, Any],
) -> float:

    candidates = (
        "mean_risk",
        "mean_risk_score",
        "risk_score",
    )

    for key in candidates:

        if key in result:

            try:
                return float(
                    result[key]
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    records = result.get(
        "records",
        [],
    )

    if isinstance(
        records,
        list,
    ) and records:

        values = []

        for item in records:

            if not isinstance(
                item,
                dict,
            ):
                continue

            for key in (
                "risk_score",
                "unified_risk_score",
            ):

                if key in item:

                    try:
                        values.append(
                            float(
                                item[key]
                            )
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        pass

                    break

        if values:

            return (
                sum(values)
                /
                len(values)
            )

    return 0.0


def _extract_max_risk(
    result: dict[str, Any],
) -> float:

    maximum = result.get(
        "max_risk"
    )

    if maximum is None:
        maximum = result.get(
            "maximum_risk"
        )

    if isinstance(
        maximum,
        dict,
    ):

        maximum = (
            maximum.get("risk_score")
            or maximum.get("score")
        )

    if maximum is not None:

        try:
            return float(
                maximum
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

    records = result.get(
        "records",
        [],
    )

    if isinstance(
        records,
        list,
    ):

        values = []

        for item in records:

            if not isinstance(
                item,
                dict,
            ):
                continue

            for key in (
                "risk_score",
                "unified_risk_score",
            ):

                if key in item:

                    try:
                        values.append(
                            float(
                                item[key]
                            )
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        pass

                    break

        if values:
            return max(
                values
            )

    return 0.0


def _extract_high_count(
    result: dict[str, Any],
) -> int:

    for key in (
        "high_or_above",
        "high_or_extreme",
        "high_or_extreme_cells",
        "high_cells",
    ):

        if key in result:

            try:
                return int(
                    result[key]
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    return 0


# ============================================================
# FINDINGS
# ============================================================

def _build_findings(
    states: list[dict[str, Any]],
) -> list[str]:

    findings: list[str] = []

    if not states:
        return findings

    ordered = sorted(
        states,
        key=lambda item: float(
            item.get(
                "rainfall_change_percent",
                0.0,
            )
        ),
    )

    first = ordered[0]
    last = ordered[-1]

    first_risk = float(
        first.get(
            "mean_risk",
            0.0,
        )
    )

    last_risk = float(
        last.get(
            "mean_risk",
            0.0,
        )
    )

    risk_change = (
        last_risk
        -
        first_risk
    )

    findings.append(
        (
            f"Mean modeled risk changes from "
            f"{first_risk:.2f} at "
            f"{float(first.get('rainfall_change_percent', 0.0)):.0f}% "
            f"rainfall change to "
            f"{last_risk:.2f} at "
            f"{float(last.get('rainfall_change_percent', 0.0)):.0f}%."
        )
    )

    findings.append(
        (
            f"Net modeled risk change across "
            f"the tested scenario range is "
            f"{risk_change:+.2f} points."
        )
    )

    for previous, current in zip(
        ordered,
        ordered[1:],
    ):

        rainfall_from = float(
            previous.get(
                "rainfall_change_percent",
                0.0,
            )
        )

        rainfall_to = float(
            current.get(
                "rainfall_change_percent",
                0.0,
            )
        )

        previous_risk = float(
            previous.get(
                "mean_risk",
                0.0,
            )
        )

        current_risk = float(
            current.get(
                "mean_risk",
                0.0,
            )
        )

        delta = (
            current_risk
            -
            previous_risk
        )

        findings.append(
            (
                f"{rainfall_from:.0f}% → "
                f"{rainfall_to:.0f}% rainfall: "
                f"mean risk changes by "
                f"{delta:+.2f}."
            )
        )

    return findings


# ============================================================
# MAIN INVESTIGATOR
# ============================================================

def investigate_scenarios(
    query: str,
) -> ScenarioInvestigation:

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
            "Scenario investigation requires "
            "an AwareOn-domain query."
        )

    if decision.intent != QueryIntent.SCENARIO:

        raise ValueError(
            "Query is not classified as a "
            "scenario investigation."
        )

    rainfall_scenarios = _resolve_scenarios(
        query
    )

    investigation = ScenarioInvestigation(
        query=query,
        intent=decision.intent.value,
        rainfall_scenarios=rainfall_scenarios,
    )

    states: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # Execute each scenario
    # --------------------------------------------------------

    for rainfall_change in rainfall_scenarios:

        result = scenario_service.simulate(
            rainfall_change
        )

        key = (
            f"rainfall_{rainfall_change:g}"
        )

        investigation.tool_results[
            key
        ] = result

        mean_risk = _extract_mean_risk(
            result
        )

        maximum_risk = _extract_max_risk(
            result
        )

        high_count = _extract_high_count(
            result
        )

        states.append(
            {
                "rainfall_change_percent":
                    rainfall_change,

                "mean_risk":
                    mean_risk,

                "maximum_risk":
                    maximum_risk,

                "high_or_above":
                    high_count,
            }
        )

    investigation.completed_steps.append(
        "scenario_simulation"
    )

    # --------------------------------------------------------
    # Ground each scenario
    # --------------------------------------------------------

    packages = []

    for rainfall_change in rainfall_scenarios:

        key = (
            f"rainfall_{rainfall_change:g}"
        )

        result = investigation.tool_results[
            key
        ]

        packages.append(
            ground_tool_result(
                "scenario_simulation",
                result,
                query,
            )
        )

    investigation.evidence = merge_evidence(
        packages
    )

    investigation.completed_steps.append(
        "evidence_grounding"
    )

    # --------------------------------------------------------
    # Findings
    # --------------------------------------------------------

    investigation.findings = _build_findings(
        states
    )

    investigation.completed_steps.append(
        "scenario_comparison"
    )

    return investigation

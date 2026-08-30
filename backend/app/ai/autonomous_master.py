from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.ai.agent_memory import (
    InvestigationMemory,
    create_investigation_memory,
)
from backend.app.ai.cell_investigator import investigate_cell
from backend.app.ai.domain_router import (
    QueryDomain,
    QueryIntent,
    classify_query,
)
from backend.app.ai.evidence import (
    EvidenceItem,
    EvidencePackage,
)
from backend.app.ai.grounding import merge_evidence
from backend.app.ai.regional_investigator import investigate_region
from backend.app.ai.response_contract import (
    AIResponse,
    build_ambiguous_response,
    build_out_of_domain_response,
)
from backend.app.ai.scenario_investigator import investigate_scenarios
from backend.app.ai.verification import verify_response


# ============================================================
# MASTER RESULT
# ============================================================

@dataclass
class AutonomousInvestigation:
    query: str
    status: str
    domain: str
    intent: str
    memory: InvestigationMemory
    investigations: list[dict[str, Any]] = field(
        default_factory=list
    )
    answer: str = ""
    response: AIResponse | None = None
    verification: dict[str, Any] | None = None
    learning_candidate: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "status": self.status,
            "domain": self.domain,
            "intent": self.intent,
            "memory": self.memory.to_dict(),
            "investigations": self.investigations,
            "answer": self.answer,
            "response": (
                self.response.to_dict()
                if self.response is not None
                else None
            ),
            "verification": self.verification,
            "learning_candidate": self.learning_candidate,
        }


# ============================================================
# EXTRACTION HELPERS
# ============================================================

def _extract_cell_id(
    query: str,
) -> str | None:
    cleaned = (
        query
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(":", " ")
    )

    for token in cleaned.split():
        token = token.strip().strip(
            ".!?;\"'"
        )

        if "_" not in token:
            continue

        left, right = token.split(
            "_",
            1,
        )

        if left.isdigit() and right.isdigit():
            return token

    return None


def _extract_coordinates(
    query: str,
) -> tuple[float, float] | None:
    cleaned = (
        query
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(":", " ")
    )

    numbers: list[float] = []

    for token in cleaned.split():
        token = token.strip().strip(
            ".!?;\"'"
        )

        try:
            numbers.append(
                float(token)
            )
        except ValueError:
            continue

    for first, second in zip(
        numbers,
        numbers[1:],
    ):
        if (
            -90.0 <= first <= 90.0
            and -180.0 <= second <= 180.0
        ):
            return first, second

    return None


# ============================================================
# MEMORY HELPERS
# ============================================================

def _ingest_evidence(
    payload: dict[str, Any],
    memory: InvestigationMemory,
) -> None:
    evidence = payload.get(
        "evidence"
    )

    if not isinstance(
        evidence,
        dict,
    ):
        return

    items = evidence.get(
        "items",
        [],
    )

    if not isinstance(
        items,
        list,
    ):
        return

    for item in items:
        if not isinstance(
            item,
            dict,
        ):
            continue

        evidence_id = item.get(
            "evidence_id"
        )

        if evidence_id:
            memory.add_evidence_id(
                str(evidence_id)
            )

        claim = item.get(
            "claim"
        )

        if not claim:
            continue

        memory.add_fact(
            claim=str(claim),
            value=item.get("value"),
            source=str(
                item.get(
                    "source_tool",
                    "unknown",
                )
            ),
            evidence_type=str(
                item.get(
                    "evidence_type",
                    "UNKNOWN",
                )
            ),
        )


def _reconstruct_evidence(
    query: str,
    investigations: list[dict[str, Any]],
) -> EvidencePackage:
    packages: list[EvidencePackage] = []

    for investigation in investigations:
        evidence = investigation.get(
            "evidence"
        )

        if not isinstance(
            evidence,
            dict,
        ):
            continue

        raw_items = evidence.get(
            "items",
            [],
        )

        if not isinstance(
            raw_items,
            list,
        ):
            continue

        package = EvidencePackage(
            query=str(
                evidence.get(
                    "query",
                    query,
                )
            )
        )

        for item in raw_items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            evidence_id = item.get(
                "evidence_id"
            )

            source_tool = item.get(
                "source_tool"
            )

            evidence_type = item.get(
                "evidence_type"
            )

            claim = item.get(
                "claim"
            )

            if not all(
                (
                    evidence_id,
                    source_tool,
                    evidence_type,
                    claim,
                )
            ):
                continue

            confidence = item.get(
                "confidence"
            )

            if confidence is not None:
                try:
                    confidence = float(
                        confidence
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    confidence = None

            package.items.append(
                EvidenceItem(
                    evidence_id=str(
                        evidence_id
                    ),
                    source_tool=str(
                        source_tool
                    ),
                    evidence_type=str(
                        evidence_type
                    ),
                    claim=str(
                        claim
                    ),
                    value=item.get(
                        "value"
                    ),
                    source_id=(
                        str(
                            item["source_id"]
                        )
                        if item.get(
                            "source_id"
                        ) is not None
                        else None
                    ),
                    confidence=confidence,
                    metadata=(
                        item.get(
                            "metadata",
                            {},
                        )
                        if isinstance(
                            item.get(
                                "metadata",
                                {},
                            ),
                            dict,
                        )
                        else {}
                    ),
                )
            )

        if package.items:
            packages.append(
                package
            )

    if not packages:
        return EvidencePackage(
            query=query
        )

    return merge_evidence(
        packages
    )


# ============================================================
# FINDINGS
# ============================================================

def _collect_findings(
    investigations: list[dict[str, Any]],
) -> list[str]:
    findings: list[str] = []

    for investigation in investigations:
        raw_findings = investigation.get(
            "findings",
            [],
        )

        if not isinstance(
            raw_findings,
            list,
        ):
            continue

        for finding in raw_findings:
            text = str(
                finding
            ).strip()

            if (
                text
                and text not in findings
            ):
                findings.append(
                    text
                )

    return findings


def _build_answer(
    intent: QueryIntent,
    investigations: list[dict[str, Any]],
) -> str:
    findings = _collect_findings(
        investigations
    )

    if not findings:
        return (
            "AwareOn completed the investigation, "
            "but no supported findings were produced."
        )

    headings = {
        QueryIntent.EXPLANATION:
            "AwareOn evidence-based explanation",

        QueryIntent.SCENARIO:
            "AwareOn scenario investigation result",

        QueryIntent.DECISION:
            "AwareOn decision investigation result",

        QueryIntent.TEMPORAL:
            "AwareOn temporal investigation result",

        QueryIntent.REGIONAL_RISK:
            "AwareOn regional investigation result",
    }

    heading = headings.get(
        intent,
        "AwareOn investigation result",
    )

    lines = [f"{heading}:"]

    for finding in findings:
        lines.append(
            f"- {finding}"
        )

    return "\n".join(
        lines
    )


# ============================================================
# LEARNING CANDIDATE
# ============================================================

def _build_learning_candidate(
    query: str,
    response: AIResponse,
    verification: dict[str, Any],
    memory: InvestigationMemory,
) -> dict[str, Any] | None:
    status = str(
        verification.get(
            "status",
            "",
        )
    ).upper()

    if status != "PASSED":
        return None

    if not memory.evidence_ids:
        return None

    return {
        "candidate_id": (
            f"LC-{memory.investigation_id}"
        ),
        "category":
            "SUCCESSFUL_INVESTIGATION",
        "query":
            query,
        "observation": (
            "A validated AwareOn investigation "
            "produced a verification-passing "
            "evidence-backed response."
        ),
        "evidence":
            list(
                memory.evidence_ids
            ),
        "confidence":
            response.confidence,
        "approved":
            False,
        "approval_required":
            True,
    }


# ============================================================
# INVESTIGATION RUNNERS
# ============================================================

def _run_cell(
    query: str,
    memory: InvestigationMemory,
) -> dict[str, Any]:
    memory.add_step(
        action="INVESTIGATE",
        target="cell",
        status="STARTED",
    )

    try:
        result = investigate_cell(
            query
        )

        payload = result.to_dict()

        _ingest_evidence(
            payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="cell",
            status="SUCCESS",
            result_summary=(
                f"{len(result.findings)} findings; "
                f"{len(result.evidence.items)} evidence items."
            ),
        )

        return payload

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="cell",
            status="FAILED",
            result_summary=str(
                exc
            ),
        )

        return {
            "status": "FAILED",
            "error": str(exc),
            "findings": [],
            "evidence": None,
        }


def _run_region(
    query: str,
    coordinates: tuple[float, float],
    memory: InvestigationMemory,
) -> dict[str, Any]:
    latitude, longitude = coordinates

    memory.add_step(
        action="INVESTIGATE",
        target="region",
        status="STARTED",
    )

    try:
        result = investigate_region(
            query,
            latitude=latitude,
            longitude=longitude,
        )

        payload = result.to_dict()

        _ingest_evidence(
            payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="region",
            status="SUCCESS",
            result_summary=(
                f"{len(result.findings)} findings; "
                f"{len(result.evidence.items)} evidence items."
            ),
        )

        return payload

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="region",
            status="FAILED",
            result_summary=str(
                exc
            ),
        )

        return {
            "status": "FAILED",
            "error": str(exc),
            "findings": [],
            "evidence": None,
        }


def _run_scenario(
    query: str,
    memory: InvestigationMemory,
) -> dict[str, Any]:
    memory.add_step(
        action="INVESTIGATE",
        target="scenario",
        status="STARTED",
    )

    try:
        result = investigate_scenarios(
            query
        )

        payload = result.to_dict()

        _ingest_evidence(
            payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="scenario",
            status="SUCCESS",
            result_summary=(
                f"{len(result.rainfall_scenarios)} "
                "scenario conditions evaluated."
            ),
        )

        return payload

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="scenario",
            status="FAILED",
            result_summary=str(
                exc
            ),
        )

        return {
            "status": "FAILED",
            "error": str(exc),
            "findings": [],
            "evidence": None,
        }


def _run_historical(
    query: str,
    memory: InvestigationMemory,
) -> dict[str, Any]:
    from backend.app.historical_trajectory import (
        build_historical_trajectory,
    )

    memory.add_step(
        action="INVESTIGATE",
        target="historical",
        status="STARTED",
    )

    try:
        result = build_historical_trajectory(
            recent_days=30,
            baseline_years=5,
        )

        trajectory = result.get(
            "trajectory",
        )

        direction = result.get(
            "direction",
        )

        score = result.get(
            "trajectory_score",
        )

        confidence = result.get(
            "confidence",
            {},
        )

        if not isinstance(
            confidence,
            dict,
        ):
            confidence = {}

        confidence_score = confidence.get(
            "score",
        )

        confidence_band = confidence.get(
            "band",
        )

        coverage = result.get(
            "coverage",
            {},
        )

        if not isinstance(
            coverage,
            dict,
        ):
            coverage = {}

        observations = coverage.get(
            "observations",
        )

        approximate_years = coverage.get(
            "approximate_years",
        )

        recent_vs_baseline = result.get(
            "recent_vs_baseline",
            {},
        )

        if not isinstance(
            recent_vs_baseline,
            dict,
        ):
            recent_vs_baseline = {}

        rain_24h_change = recent_vs_baseline.get(
            "rain_24h_change_percent",
        )

        volatility_change = recent_vs_baseline.get(
            "volatility_change_percent",
        )

        data_quality = result.get(
            "evidence",
            {},
        )

        if not isinstance(
            data_quality,
            dict,
        ):
            data_quality = {}

        quality_band = data_quality.get(
            "data_quality_band",
        )

        findings = []

        if trajectory is not None:
            findings.append(
                (
                    "Historical trajectory is "
                    f"{trajectory}."
                )
            )

        if direction is not None:
            findings.append(
                (
                    "Historical direction is "
                    f"{direction}."
                )
            )

        if score is not None:
            findings.append(
                (
                    "Historical trajectory score is "
                    f"{float(score):.2f}."
                )
            )

        if confidence_score is not None:
            confidence_text = (
                f"{float(confidence_score):.2f}"
            )

            if confidence_band:
                confidence_text += (
                    f" ({confidence_band})."
                )
            else:
                confidence_text += "."

            findings.append(
                (
                    "Historical confidence score is "
                    f"{confidence_text}"
                )
            )

        if observations is not None:
            findings.append(
                (
                    "Historical record contains "
                    f"{int(observations):,} observations."
                )
            )

        if approximate_years is not None:
            findings.append(
                (
                    "Historical record spans "
                    f"approximately "
                    f"{float(approximate_years):.1f} years."
                )
            )

        if rain_24h_change is not None:
            findings.append(
                (
                    "Recent 24-hour rainfall differs "
                    "from baseline by "
                    f"{float(rain_24h_change):+.2f}%."
                )
            )

        if volatility_change is not None:
            findings.append(
                (
                    "Recent rainfall/environmental "
                    "volatility differs from baseline by "
                    f"{float(volatility_change):+.2f}%."
                )
            )

        if quality_band:
            findings.append(
                (
                    "Historical data quality is "
                    f"{quality_band}."
                )
            )

        findings.append(
            (
                "The historical trajectory provides a "
                "temporal early-warning signal at the "
                "available ERA5 source point; it is not "
                "a cell-specific warning assessment."
            )
        )

        evidence_items = []

        if trajectory is not None:
            evidence_items.append(
                {
                    "evidence_id":
                        "HISTORICAL-trajectory",

                    "source_tool":
                        "historical_trajectory",

                    "evidence_type":
                        "MODEL_OUTPUT",

                    "claim":
                        (
                            "Historical trajectory is "
                            f"{trajectory}."
                        ),

                    "value":
                        trajectory,

                    "confidence":
                        (
                            float(confidence_score)
                            if confidence_score is not None
                            else None
                        ),
                }
            )

        if direction is not None:
            evidence_items.append(
                {
                    "evidence_id":
                        "HISTORICAL-direction",

                    "source_tool":
                        "historical_trajectory",

                    "evidence_type":
                        "MODEL_OUTPUT",

                    "claim":
                        (
                            "Historical direction is "
                            f"{direction}."
                        ),

                    "value":
                        direction,

                    "confidence":
                        (
                            float(confidence_score)
                            if confidence_score is not None
                            else None
                        ),
                }
            )

        if score is not None:
            evidence_items.append(
                {
                    "evidence_id":
                        "HISTORICAL-score",

                    "source_tool":
                        "historical_trajectory",

                    "evidence_type":
                        "MODEL_OUTPUT",

                    "claim":
                        (
                            "Historical trajectory score is "
                            f"{float(score):.2f}."
                        ),

                    "value":
                        score,

                    "confidence":
                        (
                            float(confidence_score)
                            if confidence_score is not None
                            else None
                        ),
                }
            )

        if confidence_score is not None:
            evidence_items.append(
                {
                    "evidence_id":
                        "HISTORICAL-confidence",

                    "source_tool":
                        "historical_trajectory",

                    "evidence_type":
                        "MODEL_OUTPUT",

                    "claim":
                        (
                            "Historical confidence score is "
                            f"{float(confidence_score):.2f}."
                        ),

                    "value":
                        confidence_score,

                    "confidence":
                        float(confidence_score),
                }
            )

        if rain_24h_change is not None:
            evidence_items.append(
                {
                    "evidence_id":
                        "HISTORICAL-rain-change",

                    "source_tool":
                        "historical_trajectory",

                    "evidence_type":
                        "MODEL_OUTPUT",

                    "claim":
                        (
                            "Recent 24-hour rainfall differs "
                            "from baseline by "
                            f"{float(rain_24h_change):+.2f}%."
                        ),

                    "value":
                        rain_24h_change,

                    "confidence":
                        (
                            float(confidence_score)
                            if confidence_score is not None
                            else None
                        ),
                }
            )

        payload = {
            "status":
                "READY",

            "findings":
                findings,

            "evidence":
                {
                    "query":
                        query,

                    "items":
                        evidence_items,
                },

            "historical":
                result,
        }

        _ingest_evidence(
            payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="historical",
            status="SUCCESS",
            result_summary=(
                f"{len(findings)} findings; "
                f"{len(evidence_items)} evidence items."
            ),
        )

        return payload

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="historical",
            status="FAILED",
            result_summary=str(exc),
        )

        return {
            "status":
                "FAILED",

            "error":
                str(exc),

            "findings":
                [],

            "evidence":
                None,
        }


# ============================================================
# MASTER AGENT
# ============================================================

def run_awareon_agent(
    query: str,
) -> AutonomousInvestigation:

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    decision = classify_query(
        query
    )

    memory = create_investigation_memory(
        investigation_id=(
            f"AI-{id(query):X}"
        ),
        query=query,
    )

    # --------------------------------------------------------
    # OUTSIDE DOMAIN
    # --------------------------------------------------------

    if (
        decision.domain
        == QueryDomain.OUTSIDE_DOMAIN
    ):
        response = (
            build_out_of_domain_response(
                query
            )
        )

        memory.add_step(
            action="DOMAIN_CLASSIFICATION",
            target="query",
            status="SUCCESS",
            result_summary=(
                "Query classified outside "
                "AwareOn's specialized domain."
            ),
        )

        return AutonomousInvestigation(
            query=query,
            status="OUTSIDE_DOMAIN",
            domain=decision.domain.value,
            intent=decision.intent.value,
            memory=memory,
            answer=response.answer,
            response=response,
        )

    # --------------------------------------------------------
    # AMBIGUOUS
    # --------------------------------------------------------

    if (
        decision.domain
        == QueryDomain.AMBIGUOUS
    ):
        response = (
            build_ambiguous_response()
        )

        memory.add_step(
            action="DOMAIN_CLASSIFICATION",
            target="query",
            status="CLARIFICATION_REQUIRED",
        )

        return AutonomousInvestigation(
            query=query,
            status="CLARIFICATION_REQUIRED",
            domain=decision.domain.value,
            intent=decision.intent.value,
            memory=memory,
            answer=response.answer,
            response=response,
        )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    memory.add_step(
        action="DOMAIN_CLASSIFICATION",
        target="query",
        status="SUCCESS",
        result_summary=(
            f"Domain={decision.domain.value}; "
            f"Intent={decision.intent.value}; "
            f"Confidence={decision.confidence:.2f}."
        ),
    )

    investigations: list[
        dict[str, Any]
    ] = []

    cell_id = _extract_cell_id(
        query
    )

    coordinates = _extract_coordinates(
        query
    )

    # --------------------------------------------------------
    # CELL
    # --------------------------------------------------------

    if (
        cell_id
        and decision.intent
        in {
            QueryIntent.CELL_RISK,
            QueryIntent.EXPLANATION,
            QueryIntent.DECISION,
            QueryIntent.SCENARIO,
        }
    ):
        investigations.append(
            _run_cell(
                query,
                memory,
            )
        )

    # --------------------------------------------------------
    # REGION
    # --------------------------------------------------------

    if (
        coordinates
        and decision.intent
        in {
            QueryIntent.REGIONAL_RISK,
            QueryIntent.EXPLANATION,
            QueryIntent.EXPOSURE,
            QueryIntent.DECISION,
            QueryIntent.TEMPORAL,
        }
    ):
        investigations.append(
            _run_region(
                query,
                coordinates,
                memory,
            )
        )

    # --------------------------------------------------------
    # SCENARIO
    # --------------------------------------------------------

    if (
        decision.intent
        == QueryIntent.SCENARIO
    ):
        investigations.append(
            _run_scenario(
                query,
                memory,
            )
        )

    # --------------------------------------------------------
    # HISTORICAL
    # --------------------------------------------------------

    if (
        decision.intent
        in {
            QueryIntent.TEMPORAL,
            QueryIntent.EARLY_WARNING,
        }
        and not investigations
    ):
        investigations.append(
            _run_historical(
                query,
                memory,
            )
        )

    # --------------------------------------------------------
    # NO PATH
    # --------------------------------------------------------

    if not investigations:
        response = (
            build_ambiguous_response()
        )

        memory.add_step(
            action="INVESTIGATION",
            target="awareon",
            status="CLARIFICATION_REQUIRED",
            result_summary=(
                "No suitable investigation path "
                "was identified."
            ),
        )

        return AutonomousInvestigation(
            query=query,
            status="CLARIFICATION_REQUIRED",
            domain=decision.domain.value,
            intent=decision.intent.value,
            memory=memory,
            answer=response.answer,
            response=response,
        )

    # --------------------------------------------------------
    # KEEP SUCCESSFUL INVESTIGATIONS
    # --------------------------------------------------------

    successful = [
        item
        for item in investigations
        if item.get(
            "status"
        ) != "FAILED"
    ]

    if not successful:
        response = AIResponse(
            answer=(
                "AwareOn could not complete a "
                "reliable investigation from the "
                "available intelligence tools."
            ),
            domain=decision.domain.value,
            intent=decision.intent.value,
            confidence=0.0,
            limitations=[
                (
                    "All selected investigation paths "
                    "failed."
                )
            ],
        )

        response.validate()

        memory.add_step(
            action="FINALIZE",
            target="awareon_agent",
            status="FAILED",
        )

        return AutonomousInvestigation(
            query=query,
            status="FAILED",
            domain=decision.domain.value,
            intent=decision.intent.value,
            memory=memory,
            investigations=investigations,
            answer=response.answer,
            response=response,
        )

    investigations = successful

    # --------------------------------------------------------
    # SYNTHESIS
    # --------------------------------------------------------

    memory.add_step(
        action="SYNTHESIS",
        target="investigations",
        status="STARTED",
        result_summary=(
            f"{len(investigations)} investigation "
            "result(s) collected."
        ),
    )

    answer = _build_answer(
        decision.intent,
        investigations,
    )

    evidence_package = (
        _reconstruct_evidence(
            query,
            investigations,
        )
    )

    response = AIResponse(
        answer=answer,
        domain=decision.domain.value,
        intent=decision.intent.value,
        confidence=round(
            decision.confidence * 100.0,
            2,
        ),
        evidence=list(
            evidence_package.items
        ),
        tools_used=[],
        inferences=[],
        limitations=[
            (
                "Results are based on the available "
                "AwareOn intelligence outputs used "
                "during this investigation."
            )
        ],
    )

    for item in evidence_package.items:
        if (
            item.source_tool
            and item.source_tool
            not in response.tools_used
        ):
            response.tools_used.append(
                item.source_tool
            )

    response.validate()

    memory.add_step(
        action="SYNTHESIS",
        target="investigations",
        status="SUCCESS",
        result_summary=(
            f"{len(response.evidence)} evidence "
            "items attached."
        ),
    )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    memory.add_step(
        action="VERIFY",
        target="response",
        status="STARTED",
    )

    verification = verify_response(
        answer,
        evidence_package.to_dict(),
    ).to_dict()

    verification_status = str(
        verification.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    memory.add_step(
        action="VERIFY",
        target="response",
        status=(
            "SUCCESS"
            if verification_status == "PASSED"
            else "REVIEW_REQUIRED"
        ),
        result_summary=(
            f"Verification score "
            f"{float(verification.get('score', 0.0)):.2f}."
        ),
    )

    # --------------------------------------------------------
    # CONTROLLED LEARNING
    # --------------------------------------------------------

    learning_candidate = (
        _build_learning_candidate(
            query,
            response,
            verification,
            memory,
        )
    )

    if learning_candidate is not None:
        candidate = memory.add_learning_candidate(
            category=(
                learning_candidate[
                    "category"
                ]
            ),
            observation=(
                learning_candidate[
                    "observation"
                ]
            ),
            evidence=(
                learning_candidate[
                    "evidence"
                ]
            ),
            confidence=(
                learning_candidate[
                    "confidence"
                ]
            ),
        )

        learning_candidate = (
            candidate.to_dict()
        )

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    if verification_status == "PASSED":
        status = "READY"
    else:
        status = "REVIEW_REQUIRED"

        response.limitations.append(
            (
                "The response did not fully pass "
                "verification and requires review."
            )
        )

    memory.add_step(
        action="FINALIZE",
        target="awareon_agent",
        status="SUCCESS",
        result_summary=status,
    )

    return AutonomousInvestigation(
        query=query,
        status=status,
        domain=decision.domain.value,
        intent=decision.intent.value,
        memory=memory,
        investigations=investigations,
        answer=answer,
        response=response,
        verification=verification,
        learning_candidate=learning_candidate,
    )

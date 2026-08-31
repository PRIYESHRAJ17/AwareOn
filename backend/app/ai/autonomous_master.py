from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

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
from backend.app.ai.learning_feedback import (
    retrieve_learning_feedback,
)
from backend.app.ai.domain_retrieval import (
    build_semantic_knowledge_context,
)
from backend.app.ai.learning_aware_synthesis import (
    synthesize_with_learning,
)
from backend.app.ai.conversation_memory import (
    ConversationMemory,
)
from backend.app.ai.learning_candidates import (
    build_learning_candidate,
    validate_learning_candidate,
    store_validated_candidate,
)
from backend.app.ai.model_adapter import (
    AwareOnModelAdapter,
)


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
    learning_feedback: dict[str, Any] | None = None

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
            "learning_feedback": self.learning_feedback,
        }


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

            metadata = item.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            value = item.get(
                "value"
            )

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
                    value=value,
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
                    metadata=metadata,
                )
            )

            # ------------------------------------------------
            # Expand scalar fields from structured canonical
            # evidence so synthesis can cite the concrete
            # values rather than only a generic summary claim.
            # ------------------------------------------------

            if isinstance(
                value,
                dict,
            ):

                def add_scalar_fields(
                    current: dict[str, Any],
                    prefix: str = "",
                    depth: int = 0,
                ) -> None:

                    if depth > 3:
                        return

                    for field_name, field_value in current.items():

                        field_key = str(
                            field_name
                        ).strip()

                        if not field_key:
                            continue

                        full_key = (
                            f"{prefix}_{field_key}"
                            if prefix
                            else field_key
                        )

                        if isinstance(
                            field_value,
                            dict,
                        ):
                            add_scalar_fields(
                                field_value,
                                full_key,
                                depth + 1,
                            )
                            continue

                        if isinstance(
                            field_value,
                            (list, tuple, set),
                        ):
                            continue

                        if field_value is None:
                            continue

                        scalar_id = (
                            f"{evidence_id}:"
                            f"{full_key}"
                        )

                        readable = (
                            full_key
                            .replace("_", " ")
                            .capitalize()
                        )

                        scalar_claim = (
                            f"{readable} is "
                            f"{field_value}."
                        )

                        package.items.append(
                            EvidenceItem(
                                evidence_id=scalar_id,
                                source_tool=str(
                                    source_tool
                                ),
                                evidence_type=(
                                    "CANONICAL_FIELD"
                                ),
                                claim=scalar_claim,
                                value=field_value,
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
                                metadata={
                                    **metadata,
                                    "parent_evidence_id":
                                        str(
                                            evidence_id
                                        ),
                                    "canonical_field":
                                        full_key,
                                },
                            )
                        )

                add_scalar_fields(value)


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
    concise: bool = False,
) -> str:
    findings = _collect_findings(
        investigations
    )

    if not findings:
        return (
            "AwareOn completed the investigation, "
            "but no supported findings were produced."
        )

    # --------------------------------------------------------
    # REGIONAL / DECISION SYNTHESIS
    #
    # Turn raw investigator findings into a direct answer
    # instead of exposing the internal execution report.
    # --------------------------------------------------------

    if intent in {
        QueryIntent.REGIONAL_RISK,
        QueryIntent.DECISION,
    }:
        regional = [
            finding
            for finding in findings
            if "Regional analysis covers" in finding
            or "Maximum regional risk" in finding
            or "Top regional cell" in finding
            or "Regional state is" in finding
            or "Spatial pattern is" in finding
            or "Regional confidence band" in finding
        ]

        state = next(
            (
                finding
                for finding in regional
                if finding.startswith(
                    "Regional state is"
                )
            ),
            None,
        )

        coverage = next(
            (
                finding
                for finding in regional
                if finding.startswith(
                    "Regional analysis covers"
                )
            ),
            None,
        )

        maximum = next(
            (
                finding
                for finding in regional
                if finding.startswith(
                    "Maximum regional risk"
                )
            ),
            None,
        )

        top_cells = [
            finding
            for finding in regional
            if finding.startswith(
                "Top regional cell"
            )
        ]

        high_extreme = next(
            (
                finding
                for finding in findings
                if "HIGH or EXTREME risk" in finding
            ),
            None,
        )

        extreme = next(
            (
                finding
                for finding in findings
                if "cells are EXTREME" in finding
            ),
            None,
        )

        mean_risk = next(
            (
                finding
                for finding in findings
                if finding.startswith(
                    "Mean regional risk"
                )
            ),
            None,
        )

        lines: list[str] = []

        if intent == QueryIntent.DECISION:
            lines.append(
                "The highest-priority areas in the analyzed "
                "AwareOn region are:"
            )
        else:
            lines.append(
                "The highest-risk areas in the analyzed "
                "AwareOn region are:"
            )

        for finding in top_cells[:3]:
            cleaned = finding.replace(
                "Top regional cell ",
                "",
                1,
            )
            lines.append(
                f"• {cleaned}"
            )

        if not top_cells and maximum:
            cleaned = maximum.replace(
                "Maximum regional risk is ",
                "",
                1,
            )
            lines.append(
                f"• {cleaned}"
            )

        summary: list[str] = []

        if state:
            summary.append(
                state.replace(
                    "Regional state is ",
                    "Regional state: ",
                    1,
                )
            )

        if coverage:
            summary.append(
                coverage.replace(
                    "Regional analysis covers ",
                    "Coverage: ",
                    1,
                )
            )

        if high_extreme:
            summary.append(
                high_extreme
            )

        if extreme:
            summary.append(
                extreme
            )

        if mean_risk:
            summary.append(
                mean_risk
            )

        if summary:
            lines.append("")
            lines.extend(
                f"• {item}"
                for item in summary[:4]
            )

        if intent == QueryIntent.DECISION:
            lines.append("")
            lines.append(
                "Recommended review order is based on the "
                "highest modeled regional risk: "
                + (
                    ", ".join(
                        re.search(
                            r"^(\S+)",
                            item.replace(
                                "Top regional cell ",
                                "",
                                1,
                            ),
                        ).group(1)
                        for item in top_cells[:3]
                        if re.search(
                            r"^(\S+)",
                            item.replace(
                                "Top regional cell ",
                                "",
                                1,
                            ),
                        )
                    )
                    if top_cells
                    else "the maximum-risk cell identified by the regional analysis."
                )
                + "."
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # SCENARIO SYNTHESIS
    # --------------------------------------------------------

    if intent == QueryIntent.SCENARIO:
        mean_change = next(
            (
                finding
                for finding in findings
                if finding.startswith(
                    "Mean modeled risk"
                )
                or finding.startswith(
                    "Net modeled risk change"
                )
            ),
            None,
        )

        scenario_facts = [
            finding
            for finding in findings
            if any(
                token in finding.lower()
                for token in (
                    "rainfall",
                    "risk",
                    "escalat",
                    "extreme",
                    "high",
                )
            )
        ]

        lines = [
            "Here is the modeled AwareOn scenario result:"
        ]

        if mean_change:
            lines.append(
                f"• {mean_change}"
            )

        for finding in scenario_facts:
            if finding == mean_change:
                continue
            lines.append(
                f"• {finding}"
            )
            if len(lines) >= (
                4 if concise else 7
            ):
                break

        return "\n".join(lines)

    # --------------------------------------------------------
    # GENERAL DETERMINISTIC FALLBACK
    # --------------------------------------------------------

    headings = {
        QueryIntent.EXPLANATION:
            "AwareOn evidence-based explanation",
        QueryIntent.TEMPORAL:
            "AwareOn temporal intelligence",
        QueryIntent.EARLY_WARNING:
            "AwareOn early-warning intelligence",
    }

    heading = headings.get(
        intent,
        "AwareOn investigation",
    )

    selected_findings = (
        findings[:3]
        if concise
        else findings[:6]
    )

    lines = [
        heading + ":"
    ]

    for finding in selected_findings:
        lines.append(
            f"• {finding}"
        )

    return "\n".join(lines)


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
            "status":
                "FAILED",
            "error":
                str(exc),
            "findings":
                [],
            "evidence":
                None,
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
            "status":
                "FAILED",
            "error":
                str(exc),
            "findings":
                [],
            "evidence":
                None,
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


def _run_historical_event(
    query: str,
    memory: InvestigationMemory,
) -> dict[str, Any]:

    from backend.app.ai.historical_event_intelligence import (
        build_historical_event_intelligence,
    )

    memory.add_step(
        action="INVESTIGATE",
        target="historical_event",
        status="STARTED",
    )

    from backend.app.ai.domain_router import (
        classify_query,
    )

    decision = classify_query(
        query
    )

    summary_request = any(
        phrase in query.lower()
        for phrase in (
            "in short",
            "short answer",
            "briefly",
            "brief answer",
            "summarize this",
            "summarize that",
            "give me a summary",
            "make it short",
        )
    )

    try:

        result = build_historical_event_intelligence(
            query,
            limit=10,
            radius_m=35_000.0,
        )

        # ----------------------------------------------------
        # Read all three historical intelligence channels.
        # ----------------------------------------------------

        historical_events = result.get(
            "historical_events",
            {},
        )

        if not isinstance(
            historical_events,
            dict,
        ):
            historical_events = {}

        events = historical_events.get(
            "events",
            [],
        )

        if not isinstance(
            events,
            list,
        ):
            events = []

        historical_recurrence = result.get(
            "historical_recurrence",
            {},
        )

        if not isinstance(
            historical_recurrence,
            dict,
        ):
            historical_recurrence = {}

        repeated_locations = historical_recurrence.get(
            "repeated_locations",
            [],
        )

        if not isinstance(
            repeated_locations,
            list,
        ):
            repeated_locations = []

        historical_current = result.get(
            "historical_current",
            {},
        )

        if not isinstance(
            historical_current,
            dict,
        ):
            historical_current = {}

        correlations = historical_current.get(
            "strongest_correlations",
            [],
        )

        if not isinstance(
            correlations,
            list,
        ):
            correlations = []

        # ----------------------------------------------------
        # Select the evidence channel requested by the intent.
        # ----------------------------------------------------

        if (
            decision.intent
            == QueryIntent.HISTORICAL_EVENT
        ):

            mode = "event"
            selected_events = events

        elif (
            decision.intent
            == QueryIntent.HISTORICAL_RECURRENCE
        ):

            mode = "recurrence"
            selected_events = []

        elif (
            decision.intent
            == QueryIntent.HISTORICAL_CURRENT
        ):

            mode = "current"
            selected_events = []

        else:

            # Defensive fallback. This runner should normally
            # only be called for one of the three intents.
            mode = "event"
            selected_events = events

        findings: list[str] = []

        evidence_items: list[
            dict[str, Any]
        ] = []

        # ====================================================
        # EVENT MODE
        # ====================================================

        if mode == "event":

            if selected_events:

                findings.append(
                    (
                        f"Found {len(selected_events)} "
                        "dated historical landslide "
                        "event record(s) matching the "
                        "requested historical criteria."
                    )
                )

                for event in selected_events[:5]:

                    parts = []

                    if event.get("event_date"):
                        parts.append(
                            str(
                                event["event_date"]
                            )
                        )

                    if event.get("district"):
                        parts.append(
                            str(
                                event["district"]
                            )
                        )

                    if event.get("location"):
                        parts.append(
                            str(
                                event["location"]
                            )
                        )

                    if event.get("landslide_id"):
                        parts.append(
                            str(
                                event["landslide_id"]
                            )
                        )

                    if event.get("distance_m") is not None:

                        parts.append(
                            (
                                "distance="
                                f"{float(event['distance_m']):.0f}m"
                            )
                        )

                    if parts:

                        findings.append(
                            (
                                "Historical event: "
                                + " | ".join(parts)
                                + "."
                            )
                        )

                for index, event in enumerate(
                    selected_events,
                    start=1,
                ):

                    evidence_items.append(
                        {
                            "evidence_id":
                                (
                                    "HISTORICAL-EVENT-"
                                    f"{index}"
                                ),

                            "source_tool":
                                "historical_event_intelligence",

                            "evidence_type":
                                "HISTORICAL_SOURCE_DATA",

                            "claim":
                                (
                                    "Historical landslide "
                                    f"event {event.get('landslide_id')} "
                                    "was recorded on "
                                    f"{event.get('event_date')} "
                                    "in "
                                    f"{event.get('district')} "
                                    "at "
                                    f"{event.get('location')}."
                                ),

                            "value":
                                event,
                        }
                    )

            else:

                findings.append(
                    (
                        "No dated historical event "
                        "record matched the requested "
                        "historical criteria."
                    )
                )

        # ====================================================
        # RECURRENCE MODE
        # ====================================================

        elif mode == "recurrence":

            if repeated_locations:

                findings.append(
                    (
                        "Historical recurrence analysis "
                        "identifies locations with repeated "
                        "recorded landslide activity."
                    )
                )

                for item in repeated_locations[:10]:

                    findings.append(
                        (
                            f"Historical hotspot "
                            f"{item.get('hotspot_id')} "
                            f"contains {item.get('event_count')} "
                            "recorded events with a hotspot "
                            f"score of {item.get('hotspot_score')} "
                            f"and category "
                            f"{item.get('hotspot_category')}."
                        )
                    )

                for index, item in enumerate(
                    repeated_locations[:10],
                    start=1,
                ):

                    hotspot_id = item.get(
                        "hotspot_id"
                    )

                    event_count = item.get(
                        "event_count"
                    )

                    hotspot_score = item.get(
                        "hotspot_score"
                    )

                    category = item.get(
                        "hotspot_category"
                    )

                    evidence_items.append(
                        {
                            "evidence_id":
                                (
                                    "HISTORICAL-RECURRENCE-"
                                    f"{index}"
                                ),

                            "source_tool":
                                "historical_event_intelligence",

                            "evidence_type":
                                "HISTORICAL_DERIVED",

                            "claim":
                                (
                                    f"Historical hotspot "
                                    f"{hotspot_id} has "
                                    f"{event_count} recorded "
                                    f"events, with a hotspot "
                                    f"score of {hotspot_score} "
                                    f"and category {category}."
                                ),

                            "value":
                                item,
                        }
                    )

                evidence_items.append(
                    {
                        "evidence_id":
                            "HISTORICAL-RECURRENCE-BOUNDARY",

                        "source_tool":
                            "historical_event_intelligence",

                        "evidence_type":
                            "HISTORICAL_DERIVED",

                        "claim":
                            (
                                "Historical hotspot event counts "
                                "are historical-derived evidence "
                                "and do not by themselves establish "
                                "current risk."
                            ),

                        "value":
                            {
                                "historical_only":
                                    True
                            },
                    }
                )

            else:

                findings.append(
                    (
                        "No repeated-event historical "
                        "hotspots were identified in "
                        "the available historical hotspot "
                        "dataset."
                    )
                )

        # ====================================================
        # HISTORICAL-CURRENT MODE
        # ====================================================

        elif mode == "current":

            if correlations:

                findings.append(
                    (
                        "Historical-current correlation "
                        "analysis identifies present "
                        "risk zones with associated "
                        "historical hotspot context."
                    )
                )

                for item in correlations[:10]:

                    findings.append(
                        (
                            f"Current risk zone "
                            f"{item.get('incident_id')} "
                            f"has current priority score "
                            f"{item.get('priority_score')} "
                            f"and maximum risk score "
                            f"{item.get('max_risk_score')}; "
                            f"historical-current score is "
                            f"{item.get('historical_current_score')} "
                            f"with historical hotspot "
                            f"distance "
                            f"{item.get('historical_hotspot_distance_m')}m "
                            f"and {item.get('event_count')} "
                            "associated historical events."
                        )
                    )

                evidence_items.append(
                    {
                        "evidence_id":
                            "HISTORICAL-CURRENT",

                        "source_tool":
                            "historical_event_intelligence",

                        "evidence_type":
                            "CURRENT_DERIVED_WITH_HISTORICAL_CONTEXT",

                        "claim":
                            (
                                "AwareOn historical-current "
                                "correlation identifies "
                                "relationships between current "
                                "risk zones and historical "
                                "hotspot evidence."
                            ),

                        "value":
                            correlations,
                    }
                )

            else:

                findings.append(
                    (
                        "No historical-current "
                        "correlation records were found "
                        "for the requested context."
                    )
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

            "historical_event":
                result,

            "historical_mode":
                mode,
        }

        _ingest_evidence(
            payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="historical_event",
            status="SUCCESS",
            result_summary=(
                f"Historical mode={mode}; "
                f"events={len(selected_events)}; "
                f"repeated={len(repeated_locations)}; "
                f"correlations={len(correlations)}."
            ),
        )

        return payload

    except Exception as exc:

        memory.add_step(
            action="INVESTIGATE",
            target="historical_event",
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
            "trajectory"
        )
        direction = result.get(
            "direction"
        )
        score = result.get(
            "trajectory_score"
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
            "score"
        )
        confidence_band = confidence.get(
            "band"
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
            "observations"
        )
        approximate_years = coverage.get(
            "approximate_years"
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
            "rain_24h_change_percent"
        )
        volatility_change = recent_vs_baseline.get(
            "volatility_change_percent"
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
            "data_quality_band"
        )

        findings: list[str] = []

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
                    "approximately "
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

        evidence_items: list[dict[str, Any]] = []

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


def _learning_feedback_dict(
    feedback: Any,
) -> dict[str, Any]:
    if hasattr(
        feedback,
        "to_dict",
    ):
        value = feedback.to_dict()

        if isinstance(
            value,
            dict,
        ):
            return value

    return {
        "query":
            "",
        "count":
            0,
        "records":
            [],
        "context":
            (
                "No previously validated AwareOn lessons "
                "were relevant to this query."
            ),
    }


def _build_orchestration_evidence(
    query: str,
    result: dict[str, Any],
    source_tool: str,
) -> dict[str, Any]:

    items: list[dict[str, Any]] = []

    def add(
        evidence_id: str,
        evidence_type: str,
        claim: str,
        value: Any,
    ) -> None:
        items.append(
            {
                "evidence_id":
                    evidence_id,
                "source_tool":
                    source_tool,
                "evidence_type":
                    evidence_type,
                "claim":
                    claim,
                "value":
                    value,
                "source_id":
                    (
                        f"orchestration:"
                        f"{source_tool}:"
                        f"{evidence_id}"
                    ),
                "confidence":
                    None,
                "metadata":
                    {},
            }
        )

    if source_tool == "temporal_orchestrator":
        historical = result.get(
            "historical",
            {},
        )

        emerging = result.get(
            "emerging_risk",
            {},
        )

        warning = result.get(
            "early_warning",
            {},
        )

        progression = result.get(
            "progression",
            {},
        )

        coupling = result.get(
            "coupling",
            {},
        )

        master = result.get(
            "early_warning_master",
            {},
        )

        if isinstance(
            historical,
            dict,
        ):
            trajectory = historical.get(
                "trajectory"
            )

            direction = historical.get(
                "direction"
            )

            if trajectory is not None:
                add(
                    "temporal-trajectory",
                    "MODEL_OUTPUT",
                    (
                        "Historical trajectory is "
                        f"{trajectory}."
                    ),
                    trajectory,
                )

            if direction is not None:
                add(
                    "temporal-direction",
                    "MODEL_OUTPUT",
                    (
                        "Historical direction is "
                        f"{direction}."
                    ),
                    direction,
                )

        if isinstance(
            emerging,
            dict,
        ):
            state = emerging.get(
                "emerging_state"
            )

            if state is not None:
                add(
                    "emerging-state",
                    "DERIVED",
                    (
                        "Emerging risk state is "
                        f"{state}."
                    ),
                    state,
                )

        if isinstance(
            warning,
            dict,
        ):
            level = warning.get(
                "warning_level"
            )

            if level is not None:
                add(
                    "warning-level",
                    "DERIVED",
                    (
                        "Early-warning level is "
                        f"{level}."
                    ),
                    level,
                )

        if isinstance(
            progression,
            dict,
        ):
            state = progression.get(
                "progression_state"
            )

            if state is not None:
                add(
                    "progression-state",
                    "DERIVED",
                    (
                        "Event progression state is "
                        f"{state}."
                    ),
                    state,
                )

        if isinstance(
            coupling,
            dict,
        ):
            state = coupling.get(
                "coupled_state"
            )

            if state is not None:
                add(
                    "coupling-state",
                    "DERIVED",
                    (
                        "Temporal-scenario coupling state is "
                        f"{state}."
                    ),
                    state,
                )

        if isinstance(
            master,
            dict,
        ):
            state = master.get(
                "master_state"
            )

            warning_level = master.get(
                "master_warning"
            )

            if state is not None:
                add(
                    "master-state",
                    "DERIVED",
                    (
                        "Early-warning master state is "
                        f"{state}."
                    ),
                    state,
                )

            if warning_level is not None:
                add(
                    "master-warning",
                    "DERIVED",
                    (
                        "Early-warning master warning is "
                        f"{warning_level}."
                    ),
                    warning_level,
                )

    elif source_tool == "decision_orchestrator":
        master = result.get(
            "decision_master",
            {},
        )

        optimization = result.get(
            "optimization",
            {},
        )

        intervention = result.get(
            "intervention",
            {},
        )

        response = result.get(
            "response",
            {},
        )

        if isinstance(
            master,
            dict,
        ):
            for key, label in (
                (
                    "master_state",
                    "Decision master state",
                ),
                (
                    "master_urgency",
                    "Decision master urgency",
                ),
                (
                    "operational_posture",
                    "Operational posture",
                ),
                (
                    "operational_focus",
                    "Operational focus",
                ),
                (
                    "command_posture",
                    "Command posture",
                ),
                (
                    "time_horizon",
                    "Decision time horizon",
                ),
            ):
                value = master.get(
                    key
                )

                if value is not None:
                    add(
                        f"decision-{key}",
                        "DERIVED",
                        f"{label} is {value}.",
                        value,
                    )

            decision_block = master.get(
                "decision",
                {},
            )

            if isinstance(
                decision_block,
                dict,
            ):
                option = decision_block.get(
                    "recommended_option"
                )

                score = decision_block.get(
                    "optimization_score"
                )

                if option is not None:
                    add(
                        "decision-recommended-option",
                        "DERIVED",
                        (
                            "Recommended intervention is "
                            f"{option}."
                        ),
                        option,
                    )

                if score is not None:
                    add(
                        "decision-optimization-score",
                        "DERIVED",
                        (
                            "Recommended intervention "
                            f"optimization score is "
                            f"{float(score):.2f}."
                        ),
                        score,
                    )

        if isinstance(
            optimization,
            dict,
        ):
            option = optimization.get(
                "recommended_option"
            )

            if isinstance(
                option,
                dict,
            ):
                option_name = option.get(
                    "option"
                )

                if option_name is not None:
                    add(
                        "optimization-option",
                        "DERIVED",
                        (
                            "Optimization recommends "
                            f"{option_name}."
                        ),
                        option_name,
                    )

        if isinstance(
            intervention,
            dict,
        ):
            value = intervention.get(
                "priority"
            )

            if value is not None:
                add(
                    "intervention-priority",
                    "DERIVED",
                    (
                        "Intervention priority is "
                        f"{value}."
                    ),
                    value,
                )

        if isinstance(
            response,
            dict,
        ):
            value = response.get(
                "response_level"
            )

            if value is not None:
                add(
                    "response-level",
                    "DERIVED",
                    (
                        "Response level is "
                        f"{value}."
                    ),
                    value,
                )

    if not items:
        add(
            f"{source_tool}-status",
            "DERIVED",
            (
                f"{source_tool} completed with "
                "status READY."
            ),
            "READY",
        )

    return {
        "query":
            query,
        "items":
            items,
        "count":
            len(items),
    }


def _model_synthesis(
    query: str,
    evidence_package: EvidencePackage,
    learning_feedback: Any,
    memory: InvestigationMemory,
) -> tuple[str, list[Any], bool]:

    adapter = AwareOnModelAdapter.from_environment()

    if not adapter.is_configured:
        memory.add_step(
            action="MODEL_REASONING",
            target="nemotron",
            status="SKIPPED",
            result_summary=(
                "Model adapter is not configured; "
                "deterministic grounded synthesis will be used."
            ),
        )

        return (
            "",
            [],
            False,
        )

    memory.add_step(
        action="MODEL_REASONING",
        target="nemotron",
        status="STARTED",
        result_summary=(
            f"Using {adapter.config.provider}/"
            f"{adapter.config.model}."
        ),
    )

    system_prompt = (
        "You are the AwareOn evidence reasoning engine. "
        "Answer only from the supplied current AwareOn evidence. "
        "Be precise and concise. "
        "Every factual claim must be supportable by the evidence. "
        "Do not invent numbers, categories, locations, warnings, "
        "observations, or recommendations. "
        "Treat simulated evidence as simulated. "
        "Treat observed/model-output evidence as observed/model output. "
        "Current canonical evidence always overrides historical learning. "
        "Answer the user's actual question first; do not replace a current-status, "
        "regional, scenario, or decision question with generic background teaching. "
        "When current evidence is unavailable, state that limitation plainly instead "
        "of inventing current conditions. Prefer the few highest-value findings over "
        "long lists. If the user asks for a short or brief answer, keep it to the "
        "smallest useful set of evidence-backed points."
    )

    try:
        result = synthesize_with_learning(
            adapter,
            system_prompt,
            query,
            evidence_package.to_dict(),
            max_correction_rounds=2,
        )

        if result.status != "VERIFIED":
            memory.add_step(
                action="MODEL_REASONING",
                target="nemotron",
                status="REVIEW_REQUIRED",
                result_summary=(
                    f"Model synthesis status {result.status}."
                ),
            )

            return (
                "",
                [],
                False,
            )

        memory.add_step(
            action="MODEL_REASONING",
            target="nemotron",
            status="SUCCESS",
            result_summary=(
                f"Verified "
                f"{len(result.synthesis.claims)} "
                "model claims; "
                f"{result.learning.count} "
                "learned lesson(s) supplied."
            ),
        )

        return (
            result.answer,
            list(
                result.synthesis.claims
            ),
            True,
        )

    except Exception as exc:
        memory.add_step(
            action="MODEL_REASONING",
            target="nemotron",
            status="FAILED",
            result_summary=str(
                exc
            ),
        )

        return (
            "",
            [],
            False,
        )


def _store_structural_learning(
    query: str,
    claims: list[Any],
    memory: InvestigationMemory,
) -> dict[str, Any] | None:

    candidate = build_learning_candidate(
        query,
        claims,
    )

    if not validate_learning_candidate(
        candidate
    ):
        return None

    record = store_validated_candidate(
        candidate
    )

    if record is None:
        return None

    memory.add_step(
        action="LEARNING",
        target="learning_memory",
        status="SUCCESS",
        result_summary=(
            f"Stored validated lesson "
            f"{record.learning_id}."
        ),
    )

    return record.to_dict()


def _run_temporal(
    query: str,
    cell_id: str,
    coordinates: tuple[float, float],
    memory: InvestigationMemory,
) -> dict[str, Any]:

    memory.add_step(
        action="INVESTIGATE",
        target="temporal_orchestrator",
        status="STARTED",
    )

    try:
        from backend.app.ai.agent_tools import (
            execute_temporal_orchestrator,
        )

        latitude, longitude = coordinates

        payload = execute_temporal_orchestrator(
            cell_id=str(cell_id),
            latitude=float(latitude),
            longitude=float(longitude),
            recent_days=30,
            baseline_years=5,
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise TypeError(
                "temporal_orchestrator returned "
                "a non-dictionary payload."
            )

        if payload.get(
            "status"
        ) != "READY":
            raise ValueError(
                "temporal_orchestrator did not "
                "return READY status."
            )

        orchestration_evidence = (
            _build_orchestration_evidence(
                query,
                payload,
                "temporal_orchestrator",
            )
        )

        result = {
            "status":
                "READY",
            "findings":
                [
                    (
                        "Temporal orchestration completed "
                        "through the full AwareOn early-warning "
                        "intelligence chain."
                    )
                ],
            "evidence":
                orchestration_evidence,
            "temporal":
                payload,
        }

        _ingest_evidence(
            result,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="temporal_orchestrator",
            status="SUCCESS",
            result_summary=(
                "Full temporal multi-hop chain completed."
            ),
        )

        return result

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="temporal_orchestrator",
            status="FAILED",
            result_summary=str(
                exc
            ),
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


def _run_decision(
    query: str,
    cell_id: str,
    coordinates: tuple[float, float],
    memory: InvestigationMemory,
) -> dict[str, Any]:

    memory.add_step(
        action="INVESTIGATE",
        target="decision_orchestrator",
        status="STARTED",
    )

    try:
        from backend.app.ai.decision_orchestrator import (
            run_decision_intelligence,
        )

        latitude, longitude = coordinates

        result = run_decision_intelligence(
            cell_id=str(cell_id),
            latitude=float(latitude),
            longitude=float(longitude),
        )

        if hasattr(
            result,
            "to_dict",
        ):
            payload = result.to_dict()
        elif isinstance(
            result,
            dict,
        ):
            payload = result
        else:
            raise TypeError(
                "decision_orchestrator returned "
                "an unsupported result type."
            )

        if payload.get(
            "status"
        ) != "READY":
            raise ValueError(
                "decision_orchestrator did not "
                "return READY status."
            )

        orchestration_evidence = (
            _build_orchestration_evidence(
                query,
                payload,
                "decision_orchestrator",
            )
        )

        result_payload = {
            "status":
                "READY",
            "findings":
                [
                    (
                        "Decision orchestration completed "
                        "through the full AwareOn decision "
                        "intelligence chain."
                    )
                ],
            "evidence":
                orchestration_evidence,
            "decision":
                payload,
        }

        _ingest_evidence(
            result_payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="decision_orchestrator",
            status="SUCCESS",
            result_summary=(
                "Full decision multi-hop chain completed."
            ),
        )

        return result_payload

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="decision_orchestrator",
            status="FAILED",
            result_summary=str(
                exc
            ),
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


def _resolve_decision_cell_from_region(
    regional_payload: dict[str, Any],
) -> str | None:
    tool_results = regional_payload.get(
        "tool_results",
        {},
    )

    if not isinstance(
        tool_results,
        dict,
    ):
        return None

    regional = tool_results.get(
        "regional_intelligence",
        {},
    )

    if not isinstance(
        regional,
        dict,
    ):
        return None

    top_cells = regional.get(
        "top_cells",
        [],
    )

    if isinstance(
        top_cells,
        list,
    ):
        for item in top_cells:
            if not isinstance(
                item,
                dict,
            ):
                continue

            value = item.get(
                "cell_id"
            )

            if value is not None:
                return str(value)

    maximum = regional.get(
        "maximum_risk",
        {},
    )

    if isinstance(
        maximum,
        dict,
    ):
        value = maximum.get(
            "cell_id"
        )

        if value is not None:
            return str(value)

    return None


def _run_general_explanation(
    query: str,
    memory: InvestigationMemory,
) -> dict[str, Any]:

    memory.add_step(
        action="INVESTIGATE",
        target="domain_knowledge",
        status="STARTED",
    )

    try:
        knowledge = build_semantic_knowledge_context(
            query,
            limit=8,
        )

        items = knowledge.get(
            "items",
            [],
        )

        if not isinstance(
            items,
            list,
        ):
            items = []

        evidence_items: list[
            dict[str, Any]
        ] = []

        findings: list[str] = []

        for item in items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            entry_id = str(
                item.get(
                    "entry_id",
                    "",
                )
            ).strip()

            title = str(
                item.get(
                    "title",
                    "",
                )
            ).strip()

            content = str(
                item.get(
                    "content",
                    "",
                )
            ).strip()

            if not entry_id or not content:
                continue

            source = str(
                item.get(
                    "source",
                    "AwareOn domain knowledge",
                )
            )

            source_type = str(
                item.get(
                    "source_type",
                    "CURATED_DOMAIN_KNOWLEDGE",
                )
            )

            scope = str(
                item.get(
                    "scope",
                    "GENERAL_DOMAIN",
                )
            )

            evidence_items.append(
                {
                    "evidence_id":
                        f"KNOW-{entry_id}",

                    "source_tool":
                        "awareon_domain_knowledge",

                    "evidence_type":
                        "DOMAIN_KNOWLEDGE",

                    "claim":
                        (
                            f"{title}: {content}"
                            if title
                            else content
                        ),

                    "value":
                        content,

                    "source_id":
                        f"knowledge:{entry_id}",

                    "confidence":
                        1.0,

                    "metadata":
                        {
                            "entry_id":
                                entry_id,

                            "source":
                                source,

                            "source_type":
                                source_type,

                            "scope":
                                scope,

                            "knowledge_only":
                                True,

                            "not_current_observation":
                                True,
                        },
                }
            )

        if not evidence_items:
            memory.add_step(
                action="INVESTIGATE",
                target="domain_knowledge",
                status="FAILED",
                result_summary=(
                    "No relevant AwareOn domain knowledge "
                    "was retrieved."
                ),
            )

            return {
                "status":
                    "FAILED",

                "error":
                    "No relevant domain knowledge.",

                "findings":
                    [],

                "evidence":
                    None,
            }

        for item in evidence_items[:8]:
            claim = str(
                item.get(
                    "claim",
                    "",
                )
            ).strip()

            if claim:
                findings.append(
                    claim
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

                    "count":
                        len(evidence_items),
                },

            "knowledge":
                knowledge,
        }

        _ingest_evidence(
            payload,
            memory,
        )

        memory.add_step(
            action="INVESTIGATE",
            target="domain_knowledge",
            status="SUCCESS",
            result_summary=(
                f"Retrieved {len(evidence_items)} "
                "domain-knowledge evidence item(s)."
            ),
        )

        return payload

    except Exception as exc:
        memory.add_step(
            action="INVESTIGATE",
            target="domain_knowledge",
            status="FAILED",
            result_summary=str(
                exc
            ),
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


def _safe_add_investigation(
    investigations: list[dict[str, Any]],
    payload: dict[str, Any],
) -> None:
    if isinstance(
        payload,
        dict,
    ):
        investigations.append(
            payload
        )


def run_awareon_agent(
    query: str,
    conversation: ConversationMemory | None = None,
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

    user_query = query

    effective_query = (
        conversation.resolve_references(
            user_query
        )
        if conversation is not None
        else user_query
    )

    # Intent and deterministic retrieval must use only the
    # latest literal user question. Conversation context is
    # supplied separately to reasoning/synthesis.
    decision = classify_query(
        user_query
    )

    memory = create_investigation_memory(
        investigation_id=(
            f"AI-{id(user_query):X}"
        ),
        query=user_query,
    )

    # --------------------------------------------------------
    # CONVERSATIONAL SUMMARY FOLLOW-UP
    # --------------------------------------------------------
    #
    # A request such as "Can you tell this in short?" refers
    # to the previous AwareOn turn. Summarize previously
    # established facts rather than re-running a new query or
    # merely truncating the old answer.
    # --------------------------------------------------------

    summary_followup = (
        conversation is not None
        and conversation.last_turn is not None
        and any(
            phrase in user_query.lower().strip()
            for phrase in (
                "can you tell this in short",
                "can u tell this in short",
                "tell this in short",
                "can you say this shortly",
                "say this shortly",
                "summarize this",
                "summarize that",
                "make it short",
                "shorten this",
            )
        )
    )

    if summary_followup:

        previous_turn = conversation.last_turn

        fact_lines: list[str] = []

        for fact in previous_turn.facts:

            if not isinstance(
                fact,
                dict,
            ):
                continue

            claim = str(
                fact.get(
                    "claim",
                    "",
                )
            ).strip()

            if claim and claim not in fact_lines:
                fact_lines.append(
                    claim
                )

        # Prefer established facts from the previous turn.
        # Limit to the two strongest concise facts.
        if fact_lines:

            summary_lines = fact_lines[:2]

        else:

            previous_answer = str(
                previous_turn.answer
                or ""
            ).strip()

            raw_lines = [
                line.strip()
                for line in previous_answer.splitlines()
                if line.strip()
            ]

            summary_lines = raw_lines[:2]

        summary = "\n".join(
            summary_lines
        ).strip()

        if summary:

            response = AIResponse(
                answer=(
                    "AwareOn summary:\n"
                    + summary
                ),
                domain="AWAREON",
                intent="GENERAL_AWAREON",
                confidence=100.0,
                evidence=[],
                tools_used=[],
                inferences=[],
                limitations=[
                    "Summary of the previous AwareOn response."
                ],
            )

            response.validate()

            memory.add_step(
                action="CONVERSATION",
                target="summary_followup",
                status="SUCCESS",
                result_summary=(
                    "Summarized established facts from "
                    "the previous AwareOn turn."
                ),
            )

            final_investigation = AutonomousInvestigation(
                query=user_query,
                status="READY",
                domain="AWAREON",
                intent="GENERAL_AWAREON",
                memory=memory,
                investigations=[],
                answer=response.answer,
                response=response,
                verification={
                    "status": "PASSED",
                    "score": 100.0,
                    "passed": True,
                    "issues": [],
                    "checks": {
                        "summary_source_present": True,
                        "answer_present": True,
                    },
                },
                learning_candidate=None,
                learning_feedback={},
            )

            conversation.add_turn(
                query=user_query,
                answer=response.answer,
                intent="GENERAL_AWAREON",
                status="READY",
                facts=previous_turn.facts,
            )

            return final_investigation

    query = user_query

    # --------------------------------------------------------
    # LEARNING RETRIEVAL
    # --------------------------------------------------------

    try:
        learning_feedback = (
            retrieve_learning_feedback(
                query,
                limit=5,
            )
        )
    except Exception as exc:
        memory.add_step(
            action="LEARNING_RETRIEVAL",
            target="learning_memory",
            status="FAILED",
            result_summary=str(
                exc
            ),
        )

        learning_feedback = (
            retrieve_learning_feedback(
                "",
                limit=1,
            )
        )

    memory.add_step(
        action="LEARNING_RETRIEVAL",
        target="learning_memory",
        status="SUCCESS",
        result_summary=(
            f"Retrieved "
            f"{learning_feedback.count} "
            "validated lesson(s)."
        ),
    )

    learning_feedback_dict = (
        _learning_feedback_dict(
            learning_feedback
        )
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
            learning_feedback=(
                learning_feedback_dict
            ),
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
            learning_feedback=(
                learning_feedback_dict
            ),
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
    # STUDY-AREA REGIONAL FALLBACK
    #
    # AwareOn's regional investigator operates around a
    # coordinate. For a state-level Sikkim question where
    # the user did not provide coordinates, use the existing
    # Sikkim study-area reference point as the analysis anchor.
    #
    # This does NOT claim that the user asked about that exact
    # point; it provides a deterministic study-area anchor for
    # regional intelligence.
    # --------------------------------------------------------

    query_lower = query.lower()

    is_sikkim_query = any(
        phrase in query_lower
        for phrase in (
            "sikkim",
            "gangtok",
            "north sikkim",
            "south sikkim",
            "east sikkim",
            "west sikkim",
            "pakyong",
            "namchi",
            "mangan",
            "gyalshing",
        )
    )

    if (
        coordinates is None
        and is_sikkim_query
        and decision.intent
        in {
            QueryIntent.REGIONAL_RISK,
            QueryIntent.EXPLANATION,
            QueryIntent.EXPOSURE,
            QueryIntent.DECISION,
            QueryIntent.TEMPORAL,
        }
    ):
        coordinates = (
            27.177309869688955,
            88.40207066680458,
        )

    # --------------------------------------------------------
    # STANDARD REGIONAL STUDY-AREA FALLBACK
    # --------------------------------------------------------
    #
    # Natural Sikkim-wide current-status questions do not
    # necessarily contain coordinates. When the user asks for
    # the current landslide situation in Sikkim, use the
    # project's existing study-area anchor while preserving
    # explicit user coordinates when supplied.
    # --------------------------------------------------------

    coordinates_for_standard_region = coordinates
    standard_region_enabled = True

    sikkim_current_status = (
        "sikkim" in query.lower()
        and any(
            phrase in query.lower()
            for phrase in (
                "current situation",
                "current status",
                "what is happening",
                "what's happening",
                "how is sikkim doing",
                "how are things in sikkim",
            )
        )
        and any(
            token in query.lower()
            for token in (
                "landslide",
                "landslides",
                "slope",
                "slope failure",
                "slope instability",
            )
        )
    )

    if (
        coordinates_for_standard_region is None
        and sikkim_current_status
    ):
        coordinates_for_standard_region = (
            27.177309869688955,
            88.40207066680458,
        )

    # --------------------------------------------------------
    # GENERAL AWAREON KNOWLEDGE PATH
    # --------------------------------------------------------

    if (
        decision.intent
        in {
            QueryIntent.GENERAL_AWAREON,
            QueryIntent.EXPLANATION,
        }
        and not cell_id
        and not coordinates
        and not sikkim_current_status
    ):
        _safe_add_investigation(
            investigations,
            _run_general_explanation(
                effective_query,
                memory,
            ),
        )

    # --------------------------------------------------------
    # SPECIALIZED MULTI-HOP TEMPORAL PATH
    # --------------------------------------------------------

    if (
        cell_id
        and coordinates
        and decision.intent
        in {
            QueryIntent.TEMPORAL,
            QueryIntent.EARLY_WARNING,
        }
    ):
        _safe_add_investigation(
            investigations,
            _run_temporal(
                query,
                cell_id,
                coordinates,
                memory,
            ),
        )

    # --------------------------------------------------------
    # SPECIALIZED MULTI-HOP DECISION PATH
    # --------------------------------------------------------

    if (
        decision.intent
        == QueryIntent.DECISION
    ):
        # Generic operational questions without an exact cell
        # or coordinates are evaluated against the project's
        # existing study-area reference point.
        if coordinates is None:
            coordinates = (
                27.177309869688955,
                88.40207066680458,
            )

        decision_cell_id = cell_id

        # A decision query may identify a region by
        # coordinates without naming a specific cell.
        # Resolve the highest-priority regional cell first.
        if decision_cell_id is None:
            regional_for_decision = _run_region(
                query,
                coordinates,
                memory,
            )

            _safe_add_investigation(
                investigations,
                regional_for_decision,
            )

            if regional_for_decision.get(
                "status"
            ) != "FAILED":
                decision_cell_id = (
                    _resolve_decision_cell_from_region(
                        regional_for_decision
                    )
                )

        if decision_cell_id is not None:
            _safe_add_investigation(
                investigations,
                _run_decision(
                    query,
                    decision_cell_id,
                    coordinates,
                    memory,
                ),
            )

            # The full decision orchestrator already performs
            # regional intelligence internally. Avoid running
            # the ordinary regional path a second time.
            # The decision orchestrator already performed
            # regional intelligence, so suppress only the
            # ordinary regional execution path.
            standard_region_enabled = False
        else:
            standard_region_enabled = True

    else:
        standard_region_enabled = True

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
        _safe_add_investigation(
            investigations,
            _run_cell(
                query,
                memory,
            ),
        )

    # --------------------------------------------------------
    # REGION
    # --------------------------------------------------------

    if (
        coordinates_for_standard_region
        and standard_region_enabled
        and decision.intent
        in {
            QueryIntent.REGIONAL_RISK,
            QueryIntent.EXPLANATION,
            QueryIntent.EXPOSURE,
        }
    ):
        _safe_add_investigation(
            investigations,
            _run_region(
                query,
                coordinates_for_standard_region,
                memory,
            ),
        )

    # --------------------------------------------------------
    # SCENARIO
    # --------------------------------------------------------

    if (
        decision.intent
        == QueryIntent.SCENARIO
        and not investigations
    ):
        _safe_add_investigation(
            investigations,
            _run_scenario(
                query,
                memory,
            ),
        )

    # --------------------------------------------------------
    # HISTORICAL EVENT
    # --------------------------------------------------------

    if (
        decision.intent
        in {
            QueryIntent.HISTORICAL_EVENT,
            QueryIntent.HISTORICAL_RECURRENCE,
            QueryIntent.HISTORICAL_CURRENT,
        }
        and not investigations
    ):
        _safe_add_investigation(
            investigations,
            _run_historical_event(
                query,
                memory,
            ),
        )

    # --------------------------------------------------------
    # HISTORICAL TRAJECTORY / EARLY-WARNING FALLBACK
    # --------------------------------------------------------

    if (
        decision.intent
        in {
            QueryIntent.TEMPORAL,
            QueryIntent.EARLY_WARNING,
        }
        and not investigations
    ):
        _safe_add_investigation(
            investigations,
            _run_historical(
                query,
                memory,
            ),
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
            learning_feedback=(
                learning_feedback_dict
            ),
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
            learning_feedback=(
                learning_feedback_dict
            ),
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

    evidence_package = (
        _reconstruct_evidence(
            query,
            investigations,
        )
    )

    memory.add_step(
        action="LEARNING_CONTEXT",
        target="awareon_reasoning",
        status="SUCCESS",
        result_summary=(
            f"{learning_feedback.count} "
            "validated lesson(s) available "
            "as guidance."
        ),
    )

    # --------------------------------------------------------
    # REAL NEMOTRON SYNTHESIS
    # --------------------------------------------------------

    answer = ""
    model_claims: list[Any] = []
    model_used = False

    if evidence_package.items:
        (
            answer,
            model_claims,
            model_used,
        ) = _model_synthesis(
            effective_query,
            evidence_package,
            learning_feedback,
            memory,
        )

    # --------------------------------------------------------
    # SAFE DETERMINISTIC FALLBACK
    # --------------------------------------------------------

    if not answer:
        summary_request = any(
            phrase in query.lower()
            for phrase in (
                "in short",
                "short answer",
                "briefly",
                "brief answer",
                "summarize this",
                "summarize that",
                "give me a summary",
                "make it short",
            )
        )

        answer = _build_answer(
            decision.intent,
            investigations,
            concise=summary_request,
        )

        memory.add_step(
            action="SYNTHESIS",
            target="deterministic_fallback",
            status="SUCCESS",
            result_summary=(
                "Grounded deterministic synthesis used."
            ),
        )

    # --------------------------------------------------------
    # PRESERVE IMPORTANT CANONICAL EXPLANATION EVIDENCE
    # --------------------------------------------------------

    if decision.intent == QueryIntent.EXPLANATION:

        canonical_lines: list[str] = []

        for evidence_item in evidence_package.items:

            claim = str(
                evidence_item.claim
            ).strip()

            if not claim:
                continue

            claim_lower = claim.lower()

            important = (
                "susceptibility" in claim_lower
                or "terrain instability" in claim_lower
                or "spatial pressure" in claim_lower
                or "high_risk_cluster" in claim_lower
            )

            if not important:
                continue

            if claim in answer:
                continue

            canonical_lines.append(
                f"- {claim} "
                f"[{evidence_item.evidence_id}]"
            )

        if canonical_lines:
            answer = (
                answer.rstrip()
                + "\n"
                + "\n".join(canonical_lines)
            )

    # --------------------------------------------------------
    # PRESERVE IMPORTANT CANONICAL EXPLANATION EVIDENCE
    # --------------------------------------------------------

    if decision.intent == QueryIntent.EXPLANATION:

        canonical_lines: list[str] = []

        for evidence_item in evidence_package.items:

            claim = str(
                evidence_item.claim
            ).strip()

            if not claim:
                continue

            claim_lower = claim.lower()

            important = (
                "susceptibility" in claim_lower
                or "terrain instability" in claim_lower
                or "spatial pressure" in claim_lower
                or "high_risk_cluster" in claim_lower
            )

            if not important:
                continue

            if claim in answer:
                continue

            canonical_lines.append(
                f"- {claim} "
                f"[{evidence_item.evidence_id}]"
            )

        if canonical_lines:
            answer = (
                answer.rstrip()
                + "\n"
                + "\n".join(canonical_lines)
            )

    limitations = [
        (
            "Results are based on the available "
            "AwareOn intelligence outputs used "
            "during this investigation."
        )
    ]

    if model_used:
        limitations.append(
            (
                "Nemotron synthesis was independently "
                "checked against the canonical evidence "
                "package."
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
        limitations=limitations,
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
            "items attached; "
            f"model_used={model_used}."
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

    learning_candidate = None

    if (
        verification_status == "PASSED"
        and model_claims
    ):
        learning_candidate = (
            _store_structural_learning(
                query,
                model_claims,
                memory,
            )
        )

    if (
        learning_candidate is None
        and verification_status == "PASSED"
    ):
        learning_candidate = (
            _build_learning_candidate(
                query,
                response,
                verification,
                memory,
            )
        )

        if learning_candidate is not None:
            candidate = (
                memory.add_learning_candidate(
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

    final_investigation = AutonomousInvestigation(
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
        learning_feedback=learning_feedback_dict,
    )

    if conversation is not None:
        conversation.add_turn(
            query=query,
            answer=final_investigation.answer,
            intent=final_investigation.intent,
            status=final_investigation.status,
            facts=(
                final_investigation.memory.facts
                if final_investigation.memory
                else []
            ),
        )

    return final_investigation

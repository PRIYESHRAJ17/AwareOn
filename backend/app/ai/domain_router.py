from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ============================================================
# QUERY DOMAIN
# ============================================================

class QueryDomain(str, Enum):
    AWAREON = "AWAREON"
    OUTSIDE_DOMAIN = "OUTSIDE_DOMAIN"
    AMBIGUOUS = "AMBIGUOUS"


# ============================================================
# QUERY INTENT
# ============================================================

class QueryIntent(str, Enum):
    CELL_RISK = "CELL_RISK"
    REGIONAL_RISK = "REGIONAL_RISK"
    SCENARIO = "SCENARIO"
    TEMPORAL = "TEMPORAL"
    EARLY_WARNING = "EARLY_WARNING"
    EXPOSURE = "EXPOSURE"
    DECISION = "DECISION"
    EXPLANATION = "EXPLANATION"
    GENERAL_AWAREON = "GENERAL_AWAREON"
    UNKNOWN = "UNKNOWN"


# ============================================================
# DOMAIN DECISION
# ============================================================

@dataclass(frozen=True)
class DomainDecision:
    domain: QueryDomain
    intent: QueryIntent
    confidence: float
    matched_signals: tuple[str, ...]
    explanation: str


# ============================================================
# AWAREON DOMAIN SIGNALS
# ============================================================

_AWAREON_SIGNALS: dict[str, tuple[str, ...]] = {
    "landslide": (
        "landslide",
        "landslide risk",
        "landslide hazard",
        "slope failure",
        "slope instability",
        "debris slide",
        "debris flow",
        "rockfall",
        "mass movement",
        "mass wasting",
    ),

    "risk": (
        "risk",
        "hazard",
        "susceptibility",
        "danger",
        "severity",
        "warning state",
        "critical",
    ),

    "rainfall": (
        "rainfall",
        "rain",
        "precipitation",
        "heavy rain",
        "rainfall scenario",
        "rainfall increase",
        "rainfall decrease",
        "storm rainfall",
    ),

    "terrain": (
        "terrain",
        "slope",
        "elevation",
        "dem",
        "aspect",
        "instability",
        "topography",
    ),

    "soil": (
        "soil moisture",
        "soil wetness",
        "soil water",
        "soil",
    ),

    "sar": (
        "sar",
        "sentinel-1",
        "sentinel 1",
        "insar",
        "insar evidence",
        "satellite evidence",
        "radar evidence",
    ),

    "spatial": (
        "cell",
        "grid cell",
        "neighborhood",
        "neighbourhood",
        "cluster",
        "hotspot",
        "region",
        "regional",
        "nearby",
        "spatial",
        "map",
        "gis",
        "location",
        "coordinates",
    ),

    "exposure": (
        "exposure",
        "road",
        "roads",
        "transport",
        "transport corridor",
        "transport corridors",
        "infrastructure",
        "settlement",
        "settlements",
        "population",
        "asset",
        "assets",
        "corridor",
        "corridors",
    ),

    "scenario": (
        "scenario",
        "scenarios",
        "simulate",
        "simulation",
        "simulated",
        "what if",
        "what-if",
        "threshold",
        "thresholds",
        "sensitivity",
        "forecast",
        "projection",
        "rainfall increase",
        "rainfall decrease",
        "under +",
        "under -",
        "percent more rainfall",
    ),

    "temporal": (
        "trend",
        "trends",
        "trajectory",
        "historical",
        "history",
        "over time",
        "temporal",
        "acceleration",
        "accelerating",
        "deceleration",
        "decelerating",
        "progression",
        "anomaly",
        "anomalies",
        "timescale",
        "timescales",
        "recent",
        "long term",
        "short term",
    ),

    "early_warning": (
        "early warning",
        "early-warning",
        "emerging risk",
        "emerging-risk",
        "warning",
        "alert",
        "alerts",
        "watch",
        "critical warning",
    ),

    "decision": (
        "what should",
        "what do we do",
        "what should we do",
        "recommend",
        "recommendation",
        "recommendations",
        "prioritize",
        "priority",
        "priorities",
        "inspect",
        "inspection",
        "inspect first",
        "monitor",
        "monitoring",
        "response",
        "responses",
        "intervention",
        "interventions",
        "action",
        "actions",
        "decision",
        "decide",
        "protect",
        "protection",
        "field assessment",
        "field review",
        "operational plan",
    ),

    "engine": (
        "engine",
        "engine output",
        "model output",
        "model score",
        "confidence",
        "uncertainty",
        "evidence",
        "evidence conflict",
        "what evidence",
        "why is this",
        "why is the risk",
        "why is this cell",
        "explain the risk",
        "explain this risk",
        "explain the evidence",
    ),
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalise(
    text: str,
) -> str:
    return " ".join(
        text.lower()
        .strip()
        .split()
    )


# ============================================================
# SIGNAL MATCHING
# ============================================================

def _signals_for(
    text: str,
) -> list[str]:

    matched: list[str] = []

    for category, signals in _AWAREON_SIGNALS.items():

        for signal in signals:

            if signal in text:
                matched.append(
                    category
                )
                break

    return matched


# ============================================================
# INTENT INFERENCE
# ============================================================

def _infer_intent(
    text: str,
    matched: list[str],
) -> QueryIntent:

    # --------------------------------------------------------
    # SCENARIO
    # Highest priority because rainfall questions may actually
    # be scenario questions.
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "what if",
            "what-if",
            "scenario",
            "scenarios",
            "simulate",
            "simulation",
            "simulated",
            "threshold",
            "thresholds",
            "sensitivity",
            "forecast",
            "projection",
            "under +",
            "under -",
            "percent more rainfall",
            "rainfall increase",
            "rainfall decrease",
        )
    ):
        return QueryIntent.SCENARIO

    # --------------------------------------------------------
    # DECISION
    # Decision intent takes precedence over generic exposure.
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "what should",
            "what do we do",
            "what should we do",
            "recommend",
            "recommendation",
            "recommendations",
            "prioritize",
            "priority",
            "priorities",
            "inspect",
            "inspection",
            "inspect first",
            "monitor",
            "monitoring",
            "response",
            "responses",
            "intervention",
            "interventions",
            "action",
            "actions",
            "decision",
            "decide",
            "protect",
            "protection",
            "field assessment",
            "field review",
            "operational plan",
            "which road",
            "which roads",
            "which corridor",
            "which corridors",
        )
    ):
        return QueryIntent.DECISION

    # --------------------------------------------------------
    # EXPLANATION / EVIDENCE
    # Must come before CELL_RISK so that questions such as
    # "What evidence conflicts in this cell?" are correctly
    # treated as explanation requests.
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "why",
            "explain",
            "explanation",
            "reason",
            "because",
            "evidence",
            "evidence conflict",
            "what evidence",
            "why is this",
            "why is the risk",
            "why is this cell",
            "explain the risk",
            "explain this risk",
            "explain the evidence",
        )
    ):
        return QueryIntent.EXPLANATION

    # --------------------------------------------------------
    # EARLY WARNING
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "early warning",
            "early-warning",
            "emerging risk",
            "emerging-risk",
            "warning",
            "alert",
            "alerts",
            "critical warning",
        )
    ):
        return QueryIntent.EARLY_WARNING

    # --------------------------------------------------------
    # TEMPORAL
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "historical",
            "history",
            "trend",
            "trends",
            "trajectory",
            "over time",
            "temporal",
            "acceleration",
            "accelerating",
            "deceleration",
            "decelerating",
            "progression",
            "anomaly",
            "anomalies",
            "timescale",
            "timescales",
            "recent",
            "long term",
            "short term",
        )
    ):
        return QueryIntent.TEMPORAL

    # --------------------------------------------------------
    # EXPOSURE
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "exposure",
            "road",
            "roads",
            "transport",
            "transport corridor",
            "transport corridors",
            "infrastructure",
            "settlement",
            "settlements",
            "population",
            "asset",
            "assets",
            "corridor",
            "corridors",
        )
    ):
        return QueryIntent.EXPOSURE

    # --------------------------------------------------------
    # REGIONAL
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "region",
            "regional",
            "cluster",
            "clusters",
            "hotspot",
            "hotspots",
            "regional risk",
        )
    ):
        return QueryIntent.REGIONAL_RISK

    # --------------------------------------------------------
    # CELL
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "cell",
            "grid cell",
            "grid",
            "506_",
        )
    ):
        return QueryIntent.CELL_RISK

    # --------------------------------------------------------
    # GENERAL AWAREON
    # --------------------------------------------------------

    if matched:
        return QueryIntent.GENERAL_AWAREON

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return QueryIntent.UNKNOWN


# ============================================================
# PUBLIC CLASSIFIER
# ============================================================

def classify_query(
    query: str,
) -> DomainDecision:

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    text = _normalise(
        query
    )

    if not text:

        return DomainDecision(
            domain=QueryDomain.AMBIGUOUS,
            intent=QueryIntent.UNKNOWN,
            confidence=0.0,
            matched_signals=(),
            explanation=(
                "The query is empty and cannot be "
                "classified reliably."
            ),
        )

    matched = _signals_for(
        text
    )

    # --------------------------------------------------------
    # OUTSIDE AWAREON
    # --------------------------------------------------------

    if not matched:

        return DomainDecision(
            domain=QueryDomain.OUTSIDE_DOMAIN,
            intent=QueryIntent.UNKNOWN,
            confidence=0.98,
            matched_signals=(),
            explanation=(
                "The query does not contain signals "
                "linking it to AwareOn's specialized "
                "research and operational domain."
            ),
        )

    # --------------------------------------------------------
    # AWAREON
    # --------------------------------------------------------

    unique_signal_count = len(
        set(matched)
    )

    confidence = min(
        0.99,
        0.65
        +
        unique_signal_count * 0.08,
    )

    intent = _infer_intent(
        text,
        matched,
    )

    return DomainDecision(
        domain=QueryDomain.AWAREON,
        intent=intent,
        confidence=confidence,
        matched_signals=tuple(
            matched
        ),
        explanation=(
            "The query maps to AwareOn's specialized "
            "environmental, landslide, spatial, temporal, "
            "scenario, warning, exposure, or decision "
            "intelligence domain."
        ),
    )

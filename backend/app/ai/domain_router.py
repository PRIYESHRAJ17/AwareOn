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
    HISTORICAL_RECURRENCE = "HISTORICAL_RECURRENCE"
    HISTORICAL_CURRENT = "HISTORICAL_CURRENT"
    HISTORICAL_EVENT = "HISTORICAL_EVENT"
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
    "sikkim": (
        "sikkim",
        "sikkim state",
        "sikkim himalaya",
        "himalayan sikkim",
        "gangtok",
        "north sikkim",
        "south sikkim",
        "east sikkim",
        "west sikkim",
        "pakyong",
        "namchi",
        "mangan",
        "gyalshing",
    ),

    "landslide": (
        "landslide",
        "landslides",
        "landslide risk",
        "landslide hazard",
        "slope failure",
        "slope failures",
        "slope instability",
        "slope movement",
        "debris slide",
        "debris slides",
        "debris flow",
        "debris flows",
        "rockfall",
        "rock fall",
        "rockfalls",
        "mass movement",
        "mass wasting",
        "earth slide",
        "earthflow",
        "mudslide",
        "mud flow",
        "ground failure",
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
        "precipitation event",
        "heavy rain",
        "heavy rainfall",
        "extreme rainfall",
        "rainfall intensity",
        "rainfall duration",
        "cumulative rainfall",
        "antecedent rainfall",
        "rainfall scenario",
        "rainfall increase",
        "rainfall decrease",
        "storm rainfall",
        "storm",
        "monsoon",
        "cloudburst",
    ),

    "terrain": (
        "terrain",
        "slope",
        "slope angle",
        "slope gradient",
        "steep slope",
        "elevation",
        "dem",
        "digital elevation model",
        "aspect",
        "slope aspect",
        "relief",
        "ruggedness",
        "topography",
        "geomorphology",
        "landform",
        "landforms",
        "ridge",
        "valley",
        "scarp",
        "gully",
        "channel",
        "drainage network",
        "instability",
    ),

    "soil": (
        "soil moisture",
        "soil wetness",
        "soil water",
        "soil saturation",
        "saturation",
        "wet ground",
        "wet soil",
        "soaked soil",
        "soaked ground",
        "ground moisture",
        "water underground",
        "water beneath",
        "groundwater",
        "soil properties",
        "soil strength",
        "soil mechanics",
        "cohesion",
        "cohesive strength",
        "friction angle",
        "shear strength",
        "permeability",
        "hydraulic conductivity",
        "infiltration",
        "pore pressure",
        "pore-water pressure",
        "pore water pressure",
        "effective stress",
        "soil",
    ),

    "sar": (
        "sar",
        "sentinel-1",
        "sentinel 1",
        "sentinel-2",
        "sentinel 2",
        "insar",
        "interferometry",
        "interferometric sar",
        "radar",
        "radar evidence",
        "satellite evidence",
        "satellite imagery",
        "remote sensing",
        "earth observation",
        "spacecraft",
        "from space",
        "from orbit",
        "moving mountain",
        "slowly moving mountain",
        "mountain is moving",
        "ground deformation",
        "surface deformation",
        "deformation monitoring",
        "backscatter",
        "coherence",
        "decorrelation",
        "radar phase",
        "line of sight",
        "layover",
        "radar shadow",
    ),

    "science": (
        "effective stress",
        "pore pressure",
        "pore-water pressure",
        "pore water pressure",
        "shear strength",
        "cohesion",
        "friction angle",
        "factor of safety",
        "hydrology",
        "hydrologic",
        "hydrological",
        "groundwater",
        "hydraulic conductivity",
        "permeability",
        "infiltration",
        "runoff",
        "drainage",
        "geology",
        "geological",
        "bedrock",
        "fault",
        "faults",
        "fracture",
        "fractures",
        "foliation",
        "bedding",
        "weathering",
        "geomorphology",
        "remote sensing",
        "earth observation",
        "deformation",
        "backscatter",
        "interferometry",
        "sar",
        "insar",
        "satellite",
    ),

    "remote_observation": (
        "spacecraft",
        "from space",
        "from orbit",
        "moving mountain",
        "slowly moving mountain",
        "mountain is moving",
        "ground deformation",
        "surface deformation",
        "satellite imagery",
        "remote sensing",
        "earth observation",
    ),

    "spatial": (
        "cell",
        "grid cell",
        "grid",
        "neighborhood",
        "neighbourhood",
        "cluster",
        "clusters",
        "hotspot",
        "hotspots",
        "region",
        "regional",
        "nearby",
        "spatial",
        "map",
        "gis",
        "geospatial",
        "location",
        "coordinates",
        "latitude",
        "longitude",
    ),

    "exposure": (
        "exposure",
        "road",
        "roads",
        "highway",
        "bridge",
        "transport",
        "transport corridor",
        "transport corridors",
        "infrastructure",
        "infrastructures",
        "settlement",
        "settlements",
        "population",
        "people",
        "asset",
        "assets",
        "corridor",
        "corridors",
        "building",
        "buildings",
        "utility",
        "utilities",
        "critical infrastructure",
        "access",
        "road access",
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

    "historical_event": (
        "historical landslide",
        "historical landslides",
        "historical event",
        "historical events",
        "past landslide",
        "past landslides",
        "past event",
        "past events",
        "previous landslide",
        "previous landslides",
        "previous event",
        "previous events",
        "old landslide",
        "old landslides",
        "landslide events",
        "landslide event",
        "what happened in",
        "what happened during",
        "which historical",
        "which past",
        "which previous",
        "were there landslides",
        "history of landslides",
        "historical incidents",
        "past incidents",
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

    # Natural-language operational prioritisation.
    if (
        "natural_language_decision" in matched
        or "spatial_prioritisation" in matched
    ):
        return QueryIntent.DECISION

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
    # GENERAL HAZARD OBSERVATION / AWARENESS
    # Questions asking what signs a person should look for
    # near a potentially unstable slope are explanatory
    # domain questions, not operational prioritization.
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in (
            "what should i look for",
            "what should i watch for",
            "what signs should i look for",
            "what warning signs",
            "signs of a landslide",
            "warning signs of a landslide",
            "signs of slope failure",
            "warning signs of slope failure",
        )
    ):
        return QueryIntent.GENERAL_AWAREON

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
            "how does ",
            "how do ",
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
    # HISTORICAL EVENT
    # Event lookup takes precedence over generic trajectory.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # HISTORICAL CURRENT
    # --------------------------------------------------------

    if (
        any(
            token in text
            for token in (
                "historical landslides relate to current risk",
                "historical landslide and current risk",
                "historical evidence and current risk",
                "historical events and current risk",
                "past events and current risk",
                "past landslides and current risk",
                "history relate to current risk",
                "historical and current risk",
                "historical current risk",
                "historical hotspot and current",
                "historical hotspots and current",
                "historical hotspots overlap current",
                "historical hotspot overlap current",
                "overlap historical",
                "current risk",
                "current danger",
            )
        )
        and
        any(
            token in text
            for token in (
                "historical",
                "history",
                "past",
                "previous",
                "old",
                "landslide",
                "event",
                "hotspot",
            )
        )
    ):
        return QueryIntent.HISTORICAL_CURRENT

    # --------------------------------------------------------
    # HISTORICAL RECURRENCE
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "repeated landslide",
            "repeated landslides",
            "repeated event",
            "repeated events",
            "recurring landslide",
            "recurring landslides",
            "recurrence",
            "repeat locations",
            "repeated locations",
            "locations with repeated",
            "most historical events",
            "most events",
            "most repeated",
            "highest event count",
            "most frequent",
            "frequent historical",
            "which locations have repeated",
            "which locations have the most historical events",
        )
    ):
        return QueryIntent.HISTORICAL_RECURRENCE

    # --------------------------------------------------------
    # HISTORICAL EVENT
    # --------------------------------------------------------

    if any(
        token in text
        for token in (
            "historical landslide",
            "historical landslides",
            "historical event",
            "historical events",
            "past landslide",
            "past landslides",
            "past event",
            "past events",
            "previous landslide",
            "previous landslides",
            "previous event",
            "previous events",
            "old landslide",
            "old landslides",
            "landslide event",
            "landslide events",
            "what happened in",
            "what happened during",
            "which historical",
            "which past",
            "which previous",
            "were there landslides",
            "history of landslides",
            "historical incidents",
            "past incidents",
        )
    ):
        return QueryIntent.HISTORICAL_EVENT


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
    # NATURAL-LANGUAGE REGIONAL QUESTIONS
    #
    # Examples:
    #   "Which area is most affected by landslides in Sikkim?"
    #   "Which part of Sikkim has the highest landslide risk?"
    #   "Where are the worst landslide-affected areas?"
    #
    # These are regional/spatial intelligence questions even
    # when the user never says "region", "hotspot", or "cluster".
    # --------------------------------------------------------

    if (
        any(
            phrase in text
            for phrase in (
                "which area",
                "which areas",
                "what area",
                "what areas",
                "which part",
                "which parts",
                "where is the highest",
                "where are the highest",
                "where is the most",
                "where are the most",
                "most affected",
                "most effected",
                "worst affected",
                "worst effected",
                "highest risk area",
                "highest risk areas",
                "highest landslide risk",
                "most landslide affected",
                "most landslide effected",
            )
        )
        and any(
            signal in text
            for signal in (
                "landslide",
                "landslides",
                "slope failure",
                "slope instability",
                "mass movement",
            )
        )
        and (
            "sikkim" in text
            or any(
                location in text
                for location in (
                    "gangtok",
                    "pakyong",
                    "mangan",
                    "namchi",
                    "gyalshing",
                    "north sikkim",
                    "south sikkim",
                    "east sikkim",
                    "west sikkim",
                )
            )
        )
    ):
        return QueryIntent.REGIONAL_RISK

    # --------------------------------------------------------
    # REGIONAL
    # --------------------------------------------------------

    if (
        any(
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
        )
        or (
            "sikkim" in text
            and any(
                phrase in text
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
                token in text
                for token in (
                    "landslide",
                    "landslides",
                    "slope",
                    "slope failure",
                    "slope instability",
                )
            )
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
    # NATURAL-LANGUAGE AWAREON FALLBACK
    #
    # Some valid operational questions omit explicit
    # domain nouns, e.g.:
    #   "Which areas should be reviewed first?"
    #   "What should we inspect first?"
    #   "Where should we focus?"
    #
    # Treat these as AwareOn decision/spatial questions
    # rather than rejecting them as outside-domain.
    # --------------------------------------------------------

    if not matched and any(
        phrase in text
        for phrase in (
            "which areas",
            "what areas",
            "which area",
            "what area",
            "where should we",
            "where do we",
            "where should i",
            "what should we review",
            "what should we inspect",
            "what should we monitor",
            "which areas should be reviewed",
            "which areas should be inspected",
            "which areas should be monitored",
            "what should be reviewed first",
            "what should be inspected first",
            "what should be monitored first",
            "which location should",
            "which locations should",
            "where should we focus",
            "what should we focus on",
        )
    ):
        matched = [
            "natural_language_decision",
            "spatial_prioritisation",
        ]

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

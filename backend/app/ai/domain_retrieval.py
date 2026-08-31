from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from backend.app.ai.domain_knowledge import (
    KnowledgeEntry,
    all_entries,
)


# ============================================================
# CONCEPT VOCABULARY
# ============================================================

_CONCEPT_GROUPS: dict[str, tuple[str, ...]] = {
    "landslide": (
        "landslide",
        "landslides",
        "slope failure",
        "slope collapse",
        "ground failure",
        "mass wasting",
        "mass movement",
        "mudslide",
    ),

    "rainfall": (
        "rain",
        "rainfall",
        "precipitation",
        "storm",
        "heavy rain",
        "heavy rainfall",
        "prolonged rain",
        "days of rain",
        "monsoon",
        "cloudburst",
        "rainfall intensity",
        "rainfall duration",
        "cumulative rainfall",
        "antecedent rainfall",
    ),

    "water": (
        "water",
        "wet",
        "wetness",
        "soaked",
        "saturated",
        "saturation",
        "groundwater",
        "pore water",
        "pore-water",
        "water pressure",
        "pore pressure",
    ),

    "strength": (
        "strength",
        "weak",
        "weaken",
        "weaker",
        "stability",
        "unstable",
        "instability",
        "resistance",
        "failure",
        "fails",
    ),

    "soil": (
        "soil",
        "ground",
        "earth",
        "sediment",
        "soil water",
        "soil moisture",
        "soil wetness",
        "soil properties",
        "soil mechanics",
    ),

    "slope": (
        "slope",
        "hillside",
        "hill",
        "mountain",
        "steep slope",
        "slope angle",
        "slope gradient",
    ),

    "pore_pressure": (
        "pore pressure",
        "pore-water pressure",
        "pore water pressure",
        "water pressure in soil",
    ),

    "effective_stress": (
        "effective stress",
    ),

    "shear_strength": (
        "shear strength",
        "shear resistance",
        "frictional strength",
        "soil strength",
        "material strength",
        "cohesion",
        "friction angle",
    ),

    "drainage": (
        "drainage",
        "drain",
        "runoff",
        "water accumulation",
        "water flow",
        "groundwater",
    ),

    "geology": (
        "geology",
        "geological",
        "rock",
        "bedrock",
        "fracture",
        "fractures",
        "fault",
        "faults",
        "foliation",
        "bedding",
        "weathering",
    ),

    "terrain": (
        "terrain",
        "topography",
        "elevation",
        "dem",
        "digital elevation model",
        "relief",
        "ruggedness",
        "landform",
        "geomorphology",
        "aspect",
    ),

    "optical": (
        "camera",
        "optical",
        "visible light",
        "visible-light",
        "photography",
        "image",
        "optical imagery",
    ),

    "modality": (
        "instead of a camera",
        "instead of normal camera",
        "radar instead of",
        "radar versus camera",
        "radar vs camera",
        "which sensor",
        "which sensing method",
        "sensing method",
    ),

    "local_variability": (
        "nearby slopes",
        "adjacent slopes",
        "neighboring slopes",
        "neighbouring slopes",
        "next to it",
        "slope next to",
        "one slope",
        "another slope",
        "different slope",
    ),

    "satellite": (
        "satellite",
        "spacecraft",
        "earth observation",
        "from space",
        "orbital",
        "orbiting",
    ),

    "sar": (
        "sar",
        "synthetic aperture radar",
        "sentinel-1",
        "sentinel 1",
        "radar",
        "radar imagery",
        "radar observation",
        "backscatter",
        "coherence",
        "decorrelation",
        "radar phase",
    ),

    "insar": (
        "insar",
        "interferometric sar",
        "interferometry",
        "interferometric",
        "interferometric radar",
    ),

    "deformation": (
        "deformation",
        "ground deformation",
        "surface deformation",
        "ground movement",
        "surface movement",
        "moving mountain",
        "slowly moving",
        "slope movement",
    ),

    "remote_sensing": (
        "remote sensing",
        "remote-sensing",
        "earth observation",
        "satellite monitoring",
        "satellite imagery",
        "change detection",
    ),

    "historical_event": (
        "historical event",
        "historical events",
        "past event",
        "past events",
        "previous event",
        "previous events",
        "disaster event",
        "disaster events",
        "landslide event",
        "landslide events",
        "old disaster",
        "old disasters",
    ),

    "historical": (
        "historical",
        "history",
        "past",
        "previous",
        "earlier",
        "old",
        "before",
        "event",
        "events",
        "disaster",
        "disasters",
        "incident",
        "incidents",
        "accident",
        "accidents",
        "record",
        "records",
    ),

    "sikkim": (
        "sikkim",
        "gangtok",
        "pakyong",
        "mangan",
        "namchi",
        "gyalshing",
        "east sikkim",
        "west sikkim",
        "north sikkim",
        "south sikkim",
        "himalaya",
        "himalayan",
    ),

    "risk": (
        "risk",
        "hazard",
        "susceptibility",
        "exposure",
        "vulnerability",
        "danger",
    ),

    "monitoring": (
        "monitor",
        "monitoring",
        "observe",
        "observation",
        "detect",
        "detection",
        "watch",
        "early warning",
    ),

    "mitigation": (
        "mitigation",
        "mitigate",
        "mitigated",
        "mitigating",
        "prevent",
        "prevented",
        "prevention",
        "preventing",
        "protect",
        "protected",
        "protection",
        "protecting",
        "stabilize",
        "stabilized",
        "stabilization",
        "stabilizing",
        "control",
        "controlled",
        "controlling",
        "reduce risk",
        "reduce the risk",
        "reduce landslide risk",
        "slope stabilization",
        "stabilize the slope",
    ),

    "infrastructure": (
        "road",
        "roads",
        "highway",
        "bridge",
        "transport",
        "corridor",
        "infrastructure",
        "building",
        "settlement",
        "utility",
    ),
}


# Generic concepts are useful for discovery but should not
# dominate ranking.
_CONCEPT_WEIGHTS: dict[str, float] = {
    "landslide": 7.0,
    "rainfall": 7.0,
    "water": 5.0,
    "strength": 6.0,
    "soil": 6.0,
    "slope": 2.0,
    "pore_pressure": 9.0,
    "effective_stress": 10.0,
    "shear_strength": 9.0,
    "drainage": 7.0,
    "geology": 7.0,
    "terrain": 6.0,
    "satellite": 9.0,
    "historical": 8.0,
    "sikkim": 8.0,
    "risk": 6.0,
    "monitoring": 2.0,
    "mitigation": 4.0,
    "infrastructure": 5.0,
}


# Entry topics mapped to the concepts they primarily represent.
_TOPIC_CONCEPTS: dict[str, set[str]] = {
    "landslide": {
        "landslide",
        "strength",
        "soil",
        "slope",
        "water",
        "rainfall",
    },

    "landslide_types": {
        "landslide",
    },

    "slope_stability": {
        "strength",
        "slope",
        "soil",
        "terrain",
    },

    "pore_pressure": {
        "pore_pressure",
        "effective_stress",
        "water",
        "soil",
        "strength",
    },

    "drainage": {
        "drainage",
        "water",
        "soil",
        "slope",
    },

    "earthquake": {
        "landslide",
        "geology",
        "slope",
    },

    "geomorphology": {
        "terrain",
        "slope",
    },

    "debris_flow": {
        "landslide",
        "water",
        "slope",
    },

    "landslide_runout": {
        "landslide",
        "terrain",
        "slope",
    },

    "landslide_frequency": {
        "historical",
        "historical_event",
        "landslide",
        "risk",
    },

    "risk_concepts": {
        "risk",
        "landslide",
        "exposure",
    },

    "risk_scores": {
        "risk",
    },

    "risk_concepts": {
        "risk",
        "landslide",
    },

    "rainfall": {
        "rainfall",
        "water",
        "soil",
    },

    "weather": {
        "rainfall",
    },

    "soil": {
        "soil",
        "water",
        "strength",
    },

    "terrain": {
        "terrain",
        "slope",
    },

    "local_variability": {
        "terrain",
        "slope",
        "soil",
        "strength",
        "water",
    },


    "satellite": {
        "satellite",
        "sar",
        "remote_sensing",
        "optical",
        "modality",
    },

    "optical": {
        "satellite",
        "optical",
        "modality",
    },

    "insar": {
        "satellite",
        "insar",
        "deformation",
        "remote_sensing",
    },

    "remote_sensing": {
        "satellite",
        "remote_sensing",
        "monitoring",
    },

    "monitoring": {
        "monitoring",
        "rainfall",
        "water",
        "satellite",
        "deformation",
        "remote_sensing",
        "landslide",
    },

    "early_warning": {
        "monitoring",
        "risk",
        "rainfall",
    },

    "mitigation": {
        "mitigation",
        "landslide",
        "slope",
        "drainage",
    },

    "field_inspection": {
        "monitoring",
        "landslide",
        "infrastructure",
        "slope",
    },

    "infrastructure": {
        "infrastructure",
        "exposure",
        "landslide",
    },

    "sikkim_geography": {
        "sikkim",
        "terrain",
    },

    "sikkim": {
        "sikkim",
    },

    "sikkim_disasters": {
        "sikkim",
        "historical",
        "historical_event",
        "landslide",
        "risk",
    },

    "awareon": {
        "risk",
    },

    "awareon_system": {
        "risk",
    },
}


# ============================================================
# TOKENIZATION
# ============================================================

_WORD_RE = re.compile(
    r"[a-z0-9]+(?:[-'][a-z0-9]+)*",
    re.IGNORECASE,
)


def _normalise(text: str) -> str:
    return " ".join(
        text.lower()
        .strip()
        .split()
    )


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(
        _normalise(text)
    )


def _phrase_present(
    text: str,
    phrase: str,
) -> bool:
    return (
        _normalise(phrase)
        in _normalise(text)
    )


# ============================================================
# QUERY CONCEPT EXTRACTION
# ============================================================

def _query_concepts(
    query: str,
) -> set[str]:

    text = _normalise(query)

    concepts: set[str] = set()

    for concept, phrases in _CONCEPT_GROUPS.items():

        for phrase in phrases:

            if _phrase_present(
                text,
                phrase,
            ):
                concepts.add(
                    concept
                )
                break

    # Informal-language semantic bridges.
    if (
        "wet ground" in text
        or "ground lose its strength" in text
        or "ground loses its strength" in text
        or "soaked" in text
        or "completely wet" in text
    ):
        concepts.update(
            {
                "water",
                "soil",
                "strength",
                "pore_pressure",
                "effective_stress",
            }
        )

    if (
        "water underground" in text
        or "groundwater" in text
        or "water beneath" in text
    ):
        concepts.update(
            {
                "water",
                "soil",
                "pore_pressure",
                "effective_stress",
                "drainage",
            }
        )

    if (
        "slowly moving mountain" in text
        or "moving mountain" in text
        or "mountain is moving" in text
        or "from space" in text
        or "spacecraft" in text
        or "from orbit" in text
    ):
        concepts.update(
            {
                "satellite",
                "sar",
                "insar",
                "deformation",
                "remote_sensing",
            }
        )

    if (
        "old disaster" in text
        or "old disasters" in text
        or "past disaster" in text
        or "past disasters" in text
        or "previous disaster" in text
        or "previous disasters" in text
        or "previous landslide" in text
        or "previous landslides" in text
        or "old event" in text
        or "past event" in text
        or "previous event" in text
    ):
        concepts.update(
            {
                "historical",
                "historical_event",
                "landslide",
                "risk",
            }
        )

    if (
        "himalayan slopes" in text
        or "mountain slopes" in text
    ):
        concepts.update(
            {
                "terrain",
                "slope",
                "landslide",
            }
        )

    return concepts


# ============================================================
# TEXT SIMILARITY
# ============================================================

def _term_counter(
    text: str,
) -> Counter[str]:

    return Counter(
        token
        for token in _tokens(text)
        if len(token) >= 3
    )


def _cosine_like_overlap(
    query_counter: Counter[str],
    entry_counter: Counter[str],
) -> float:

    if (
        not query_counter
        or not entry_counter
    ):
        return 0.0

    common = (
        set(query_counter)
        &
        set(entry_counter)
    )

    if not common:
        return 0.0

    numerator = sum(
        query_counter[token]
        *
        entry_counter[token]
        for token in common
    )

    q_norm = math.sqrt(
        sum(
            value * value
            for value in query_counter.values()
        )
    )

    e_norm = math.sqrt(
        sum(
            value * value
            for value in entry_counter.values()
        )
    )

    if (
        q_norm == 0.0
        or e_norm == 0.0
    ):
        return 0.0

    return (
        numerator
        /
        (q_norm * e_norm)
    )


# ============================================================
# ENTRY CONCEPTS
# ============================================================

def _entry_concepts(
    entry: KnowledgeEntry,
) -> set[str]:

    # Entry concepts come from the explicit topic ontology.
    # Do not run conversational query-phrase expansion over
    # the entry itself, because query-specific phrases such as
    # "spacecraft", "old disaster", or "wet ground" can leak
    # unrelated concepts into unrelated knowledge entries.

    return set(
        _TOPIC_CONCEPTS.get(
            entry.topic,
            set(),
        )
    )


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class RankedKnowledge:

    entry: KnowledgeEntry
    score: float
    matched_concepts: tuple[str, ...]
    matched_terms: tuple[str, ...]

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "entry":
                self.entry.to_dict(),

            "score":
                round(
                    self.score,
                    6,
                ),

            "matched_concepts":
                list(
                    self.matched_concepts
                ),

            "matched_terms":
                list(
                    self.matched_terms
                ),
        }


# ============================================================
# QUERY PURPOSE
# ============================================================

def _query_purpose(
    query: str,
) -> set[str]:

    text = _normalise(query)

    purposes: set[str] = set()

    # Definitions / explanations
    if (
        text.startswith("what is ")
        or text.startswith("what are ")
        or text.startswith("what does ")
        or text.startswith("explain ")
        or "explain " in text
    ):
        purposes.add("definition")

    # Mechanism / process
    if (
        text.startswith("how ")
        or " how " in f" {text} "
        or "how can " in text
        or "how does " in text
        or "how do " in text
    ):
        purposes.add("mechanism")

    # Causal explanation
    if (
        text.startswith("why ")
        or " why " in f" {text} "
        or "what makes " in text
        or "what causes " in text
    ):
        purposes.add("cause")

    # Limitations / weaknesses
    if any(
        phrase in text
        for phrase in (
            "limitation",
            "limitations",
            "weakness",
            "weaknesses",
            "problem",
            "problems",
            "drawback",
            "drawbacks",
            "challenge",
            "challenges",
            "when does it fail",
        )
    ):
        purposes.add("limitations")

    # Historical questions
    if any(
        phrase in text
        for phrase in (
            "historical",
            "history",
            "past",
            "previous",
            "earlier",
            "old event",
            "past event",
            "previous event",
            "what happened",
            "has this happened before",
        )
    ):
        purposes.add("historical")

    # Current-risk/context questions
    if any(
        phrase in text
        for phrase in (
            "current risk",
            "current danger",
            "current hazard",
            "today",
            "now",
            "currently",
            "present risk",
            "present danger",
        )
    ):
        purposes.add("current")

    # Comparison
    if any(
        phrase in text
        for phrase in (
            "difference between",
            "compare",
            "versus",
            "vs ",
            "better than",
            "different from",
        )
    ):
        purposes.add("comparison")

    return purposes


def _entry_purposes(
    entry: KnowledgeEntry,
) -> set[str]:

    text = _normalise(
        " ".join(
            (
                entry.title,
                entry.content,
                " ".join(entry.keywords),
            )
        )
    )

    purposes: set[str] = set()

    if any(
        phrase in text
        for phrase in (
            "what is ",
            "what are ",
            "describes ",
            "definition",
            "represents ",
        )
    ):
        purposes.add("definition")

    if any(
        phrase in text
        for phrase in (
            "how ",
            "mechanism",
            "depends on",
            "can ",
            "through",
            "by increasing",
            "by reducing",
        )
    ):
        purposes.add("mechanism")

    if any(
        phrase in text
        for phrase in (
            "why ",
            "because",
            "causes",
            "influences",
            "trigger",
            "factors",
        )
    ):
        purposes.add("cause")

    if any(
        phrase in text
        for phrase in (
            "limitation",
            "limitations",
            "affected by",
            "requires careful interpretation",
            "processing choices",
        )
    ):
        purposes.add("limitations")

    if any(
        phrase in text
        for phrase in (
            "historical",
            "past",
            "previous",
            "repeated",
            "recurring",
            "event",
            "disaster",
            "record",
        )
    ):
        purposes.add("historical")

    if any(
        phrase in text
        for phrase in (
            "current-risk",
            "current risk",
            "current",
            "present risk",
        )
    ):
        purposes.add("current")

    return purposes


# ============================================================
# RANKING
# ============================================================

def _rank_entry(
    query: str,
    query_concepts: set[str],
    query_counter: Counter[str],
    entry: KnowledgeEntry,
) -> RankedKnowledge:

    entry_text = " ".join(
        (
            entry.topic,
            entry.title,
            entry.content,
            " ".join(entry.keywords),
        )
    )

    entry_counter = _term_counter(
        entry_text
    )

    entry_concepts = _entry_concepts(
        entry
    )

    matched_concepts = (
        query_concepts
        &
        entry_concepts
    )

    query_purposes = _query_purpose(
        query
    )

    entry_purposes = _entry_purposes(
        entry
    )

    score = 0.0

    title = _normalise(
        entry.title
    )

    topic = _normalise(
        entry.topic.replace(
            "_",
            " ",
        )
    )

    # ========================================================
    # 1. CONCEPT MATCHING
    # ========================================================

    for concept in matched_concepts:
        score += _CONCEPT_WEIGHTS.get(
            concept,
            2.0,
        )

    # Generic concepts get less influence.
    generic_concepts = {
        "slope",
        "monitoring",
        "risk",
        "water",
        "satellite",
        "soil",
    }

    specific_matches = (
        matched_concepts
        -
        generic_concepts
    )

    score += (
        len(specific_matches)
        * 5.0
    )

    # ========================================================
    # 2. EXPLICIT ENTRY PURPOSE MATCH
    # ========================================================

    purpose_weights = {
        "definition": 7.0,
        "mechanism": 10.0,
        "cause": 10.0,
        "limitations": 14.0,
        "historical": 14.0,
        "current": 16.0,
        "comparison": 10.0,
        "decision": 16.0,
    }

    for purpose, weight in purpose_weights.items():
        if (
            purpose in query_purposes
            and purpose in entry_purposes
        ):
            score += weight

    # ========================================================
    # 3. PURPOSE CONFLICT PENALTIES
    # ========================================================

    # A normal mechanism question should not rank a limitations
    # article above direct mechanism knowledge.
    if (
        "mechanism" in query_purposes
        and "limitations" not in query_purposes
        and "limitations" in entry_purposes
    ):
        score -= 25.0

    # A normal definition question should not be dominated by
    # a limitation/operational entry.
    if (
        "definition" in query_purposes
        and "limitations" in entry_purposes
        and "limitations" not in query_purposes
    ):
        score -= 12.0

    # ========================================================
    # 4. EXACT TITLE/TOPIC MATCHING
    # ========================================================

    if topic and _phrase_present(
        query,
        topic,
    ):
        score += 10.0

    if _phrase_present(
        query,
        title,
    ):
        score += 14.0

    # ========================================================
    # 5. LEXICAL SIMILARITY
    # ========================================================

    overlap = _cosine_like_overlap(
        query_counter,
        entry_counter,
    )

    score += (
        overlap
        * 10.0
    )

    # ========================================================
    # 6. SPECIALIZED SATELLITE / SAR / INSAR
    # ========================================================

    if "insar" in query_concepts:

        if "limitations" in query_purposes:
            # Explicit limitation questions must prefer the
            # limitation-specific knowledge entry.
            if entry.entry_id == "GEN-SAR-004":
                score += 60.0
            elif entry.entry_id == "GEN-SAR-002":
                score -= 10.0
            elif entry.entry_id == "GEN-SAR-001":
                score -= 5.0
            elif entry.entry_id == "GEN-SAR-003":
                score -= 5.0

        else:
            if entry.entry_id == "GEN-SAR-002":
                score += 35.0

            elif entry.entry_id == "GEN-SAR-001":
                score += 20.0

            elif entry.entry_id == "GEN-SAR-003":
                score += 18.0

            elif entry.entry_id == "GEN-SAR-004":
                score -= 20.0

    if "sar" in query_concepts:

        if entry.entry_id == "GEN-SAR-001":
            score += 18.0

        if entry.entry_id == "GEN-SAR-003":
            score += 18.0

    if "deformation" in query_concepts:

        if entry.entry_id == "GEN-SAR-002":
            score += 22.0

    if "remote_sensing" in query_concepts:

        if entry.entry_id == "GEN-SAR-005":
            score += 16.0

    # ========================================================
    # 7. HISTORICAL / CURRENT CONTEXT
    # ========================================================

    if (
        "historical" in query_purposes
        and "current" in query_purposes
    ):

        if entry.entry_id == "GEN-SIKKIM-004":
            score += 55.0

        elif entry.entry_id == "GEN-LS-017":
            score -= 8.0

        elif "historical" in entry_purposes:
            score += 12.0

    elif "historical" in query_purposes:

        if (
            "historical" in entry_purposes
        ):
            score += 16.0

        if entry.entry_id == "GEN-SIKKIM-004":
            score += 18.0

    # ========================================================
    # 8. HUMAN MODIFICATION / ROAD-CUTTING
    # ========================================================

    if (
        "cause" in query_purposes
        and "infrastructure" in query_concepts
    ):

        if entry.entry_id == "GEN-LS-008":
            score += 45.0

        elif entry.entry_id == "GEN-LS-002":
            score += 10.0

        elif entry.entry_id == "GEN-INFRA-001":
            score += 8.0

        # Generic unrelated geology/terrain entries should
        # not outrank direct human-modification knowledge.
        if entry.entry_id in {
            "GEN-LS-013",
            "GEN-TERRAIN-002",
        }:
            score -= 15.0

    # ========================================================
    # 8B. RAINFALL-TRIGGER MECHANISM
    # ========================================================

    if (
        "rainfall" in query_concepts
        and "mechanism" in query_purposes
    ):
        if entry.entry_id == "GEN-LS-003":
            score += 35.0

        if entry.entry_id == "GEN-LS-005":
            score += 10.0

        if entry.entry_id == "GEN-LS-011":
            score += 10.0

        if entry.entry_id == "GEN-OPS-003":
            score -= 18.0

    # ========================================================
    # 9. WATER / SOIL MECHANISM
    # ========================================================

    if (
        "cause" in query_purposes
        and {
            "water",
            "pore_pressure",
            "effective_stress",
            "strength",
        }
        &
        query_concepts
    ):

        if entry.entry_id == "GEN-LS-011":
            score += 25.0

        elif entry.entry_id == "GEN-LS-005":
            score += 18.0

        elif entry.entry_id == "GEN-SOIL-002":
            score += 16.0

        elif entry.entry_id == "GEN-LS-012":
            score += 12.0

    # ========================================================
    # 10. PURE SATURATION / SOIL QUESTIONS
    # ========================================================

    if (
        "soil" in query_concepts
        and "water" in query_concepts
        and not {
            "insar",
            "sar",
            "historical",
        }
        & query_concepts
    ):

        if entry.entry_id == "GEN-SOIL-002":
            score += 18.0

        if entry.entry_id == "GEN-LS-005":
            score += 20.0

        if entry.entry_id == "GEN-LS-011":
            score += 14.0

    # ========================================================
    # 11. MODALITY / SENSOR COMPARISON
    # ========================================================

    if (
        "modality" in query_concepts
        or (
            "sar" in query_concepts
            and "optical" in query_concepts
        )
    ):
        if entry.entry_id == "GEN-SAR-001":
            score += 35.0

        if entry.entry_id == "GEN-SAR-003":
            score += 22.0

        if entry.entry_id in {
            "GEN-SAR-002",
            "GEN-SAR-004",
        }:
            score -= 5.0

    # ========================================================
    # 12. LOCAL SLOPE VARIABILITY
    # ========================================================

    if "local_variability" in query_concepts:

        if entry.entry_id == "GEN-LS-004":
            score += 35.0

        if entry.entry_id == "GEN-SOIL-001":
            score += 22.0

        if entry.entry_id in {
            "GEN-LS-013",
            "GEN-WEATHER-002",
        }:
            score -= 15.0

    # ========================================================
    # 13. MONITORING
    # ========================================================

    if (
        "monitoring" in query_concepts
        and "landslide" in query_concepts
    ):
        if entry.entry_id == "GEN-OPS-001":
            score += 35.0

        if entry.entry_id == "GEN-OPS-004":
            score += 12.0

        if entry.entry_id == "GEN-LS-001":
            score -= 18.0

    # ========================================================
    # 14. MITIGATION
    # ========================================================

    if "mitigation" in query_concepts:
        if entry.entry_id == "GEN-OPS-003":
            score += 40.0

        if entry.entry_id in {
            "GEN-LS-001",
            "GEN-LS-017",
        }:
            score -= 15.0

    # ========================================================
    # 11. SIKKIM-SPECIFIC CONTEXT
    # ========================================================

    if "sikkim" in query_concepts:

        if "SIKKIM" in entry.scope:
            score += 12.0

        if entry.entry_id in {
            "GEN-SIKKIM-001",
            "GEN-SIKKIM-002",
            "GEN-SIKKIM-003",
        }:
            score += 8.0

    # ========================================================
    # 12. AVOID GENERIC CATEGORY DOMINATION
    # ========================================================

    if (
        len(query_concepts) >= 2
        and not specific_matches
    ):
        score -= 4.0

    return RankedKnowledge(
        entry=entry,
        score=score,
        matched_concepts=tuple(
            sorted(
                matched_concepts
            )
        ),
        matched_terms=tuple(
            sorted(
                set(
                    keyword
                    for keyword in entry.keywords
                    if _phrase_present(
                        query,
                        keyword,
                    )
                )
            )
        ),
    )


# ============================================================
# PUBLIC RETRIEVAL
# ============================================================

def retrieve_awareon_knowledge_semantic(
    query: str,
    *,
    limit: int = 8,
    minimum_score: float = 4.0,
) -> dict[str, Any]:

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

    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0."
        )

    query_concepts = _query_concepts(
        query
    )

    query_purposes = _query_purpose(
        query
    )

    query_counter = _term_counter(
        query
    )

    ranked: list[
        RankedKnowledge
    ] = []

    for entry in all_entries():

        result = _rank_entry(
            query,
            query_concepts,
            query_counter,
            entry,
        )

        if result.score >= minimum_score:
            ranked.append(
                result
            )

    ranked.sort(
        key=lambda item: (
            item.score,
            len(item.matched_concepts),
            item.entry.entry_id,
        ),
        reverse=True,
    )

    selected = ranked[:limit]

    return {
        "query":
            query,

        "count":
            len(selected),

        "query_concepts":
            sorted(
                query_concepts
            ),

        "query_purposes":
            sorted(
                query_purposes
            ),

        "items":
            [
                item.entry.to_dict()
                for item in selected
            ],

        "ranking":
            [
                item.to_dict()
                for item in selected
            ],
    }


def build_semantic_knowledge_context(
    query: str,
    *,
    limit: int = 8,
) -> dict[str, Any]:

    result = retrieve_awareon_knowledge_semantic(
        query,
        limit=limit,
    )

    lines = []

    for index, item in enumerate(
        result["items"],
        start=1,
    ):

        lines.append(
            (
                f"[KNOWLEDGE {index}] "
                f"{item['title']}\n"
                f"Topic: {item['topic']}\n"
                f"Scope: {item['scope']}\n"
                f"Source type: {item['source_type']}\n"
                f"Source: {item['source']}\n"
                f"Content: {item['content']}"
            )
        )

    context = (
        "\n\n".join(
            lines
        )
        if lines
        else
        "No specific AwareOn knowledge matched."
    )

    return {
        **result,
        "context":
            context,
    }


__all__ = [
    "RankedKnowledge",
    "retrieve_awareon_knowledge_semantic",
    "build_semantic_knowledge_context",
]

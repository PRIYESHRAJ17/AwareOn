from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATED_EVENTS_SOURCE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ground_truth"
    / "dated_landslide_events.csv"
)

HOTSPOTS_SOURCE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "engines"
    / "historical_event_engine_output.csv"
)

HISTORICAL_CURRENT_SOURCE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "intelligence"
    / "historical_current_correlation.csv"
)

EARTH_RADIUS_M = 6_371_000.0


# ------------------------------------------------------------
# Known Sikkim place anchors.
# Used only for spatial history lookup.
# ------------------------------------------------------------

PLACE_COORDINATES = {
    "gangtok": (
        27.3389,
        88.6065,
    ),
    "pakyong": (
        27.2300,
        88.6130,
    ),
    "singtam": (
        27.2350,
        88.5010,
    ),
    "martam": (
        27.2850,
        88.5300,
    ),
    "mangan": (
        27.5100,
        88.5360,
    ),
    "namchi": (
        27.1667,
        88.3500,
    ),
    "gyalshing": (
        27.2870,
        88.2630,
    ),
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _normalise(value: Any) -> str:
    return " ".join(
        str(value or "")
        .lower()
        .strip()
        .split()
    )


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _read_csv(
    source: Path,
) -> list[dict[str, str]]:

    if not source.exists():
        raise FileNotFoundError(
            f"Historical source not found: {source}"
        )

    with source.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(
            csv.DictReader(handle)
        )


def _haversine_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(
        lat2 - lat1
    )

    dl = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dp / 2.0) ** 2
        +
        math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2.0) ** 2
    )

    return (
        2.0
        * EARTH_RADIUS_M
        * math.asin(
            math.sqrt(a)
        )
    )


def _extract_year(
    query: str,
) -> int | None:

    match = re.search(
        r"\b(?:19|20)\d{2}\b",
        query,
    )

    if not match:
        return None

    return int(
        match.group(0)
    )


def _extract_coordinates(
    query: str,
) -> tuple[float, float] | None:

    values = re.findall(
        r"[-+]?\d+(?:\.\d+)?",
        query,
    )

    for i in range(
        len(values) - 1
    ):
        lat = _float(values[i])
        lon = _float(values[i + 1])

        if (
            lat is None
            or lon is None
        ):
            continue

        if (
            -90.0 <= lat <= 90.0
            and
            -180.0 <= lon <= 180.0
        ):
            return lat, lon

    return None


def _extract_places(
    query: str,
) -> list[str]:

    text = _normalise(
        query
    )

    return [
        place
        for place in PLACE_COORDINATES
        if place in text
    ]


def _prepare_event(
    row: dict[str, str],
) -> dict[str, Any]:

    return {
        "record_id":
            row.get("record_id"),

        "landslide_id":
            row.get("landslide_id"),

        "district":
            row.get("district"),

        "location":
            row.get("location"),

        "latitude":
            _float(
                row.get("latitude")
            ),

        "longitude":
            _float(
                row.get("longitude")
            ),

        "event_date":
            row.get("event_date"),

        "precip_mm":
            _float(
                row.get("precip_mm")
            ),

        "rain_24h_mm":
            _float(
                row.get("rain_24h_mm")
            ),

        "rain_72h_mm":
            _float(
                row.get("rain_72h_mm")
            ),

        "rain_7d_mm":
            _float(
                row.get("rain_7d_mm")
            ),

        "swvl1":
            _float(
                row.get("swvl1")
            ),

        "swvl2":
            _float(
                row.get("swvl2")
            ),
    }


# ============================================================
# HISTORICAL EVENT SEARCH
# ============================================================

def search_historical_events(
    query: str,
    *,
    limit: int = 10,
    radius_m: float = 35_000.0,
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

    rows = _read_csv(
        DATED_EVENTS_SOURCE
    )

    events = [
        _prepare_event(row)
        for row in rows
    ]

    year = _extract_year(
        query
    )

    coordinates = _extract_coordinates(
        query
    )

    places = _extract_places(
        query
    )

    # Explicit place coordinates take precedence.
    place_coordinate = None

    if places:
        place_coordinate = (
            PLACE_COORDINATES[
                places[0]
            ]
        )

    candidates = []

    for event in events:

        event_year = None

        date_text = str(
            event.get(
                "event_date"
            )
            or ""
        )

        if (
            len(date_text) >= 4
            and date_text[:4].isdigit()
        ):
            event_year = int(
                date_text[:4]
            )

        # ----------------------------------------------------
        # Year filter
        # ----------------------------------------------------

        if (
            year is not None
            and event_year != year
        ):
            continue

        score = 0.0

        if year is not None:
            score += 100.0

        # ----------------------------------------------------
        # Named-place spatial search
        # ----------------------------------------------------

        distance_m = None

        if (
            place_coordinate is not None
            and event["latitude"] is not None
            and event["longitude"] is not None
        ):

            distance_m = _haversine_m(
                place_coordinate[0],
                place_coordinate[1],
                event["latitude"],
                event["longitude"],
            )

            if distance_m > radius_m:
                continue

            score += max(
                0.0,
                80.0
                *
                (
                    1.0
                    -
                    (
                        distance_m
                        /
                        radius_m
                    )
                ),
            )

        # ----------------------------------------------------
        # Raw coordinate search
        # ----------------------------------------------------

        if (
            coordinates is not None
            and event["latitude"] is not None
            and event["longitude"] is not None
        ):

            distance_m = _haversine_m(
                coordinates[0],
                coordinates[1],
                event["latitude"],
                event["longitude"],
            )

            if distance_m > radius_m:
                continue

            score += max(
                0.0,
                80.0
                *
                (
                    1.0
                    -
                    (
                        distance_m
                        /
                        radius_m
                    )
                ),
            )

        # ----------------------------------------------------
        # Location-name matching
        # ----------------------------------------------------

        event_text = _normalise(
            " ".join(
                (
                    event.get(
                        "district",
                        "",
                    ),
                    event.get(
                        "location",
                        "",
                    ),
                )
            )
        )

        for place in places:

            if place in event_text:
                score += 50.0

        # ----------------------------------------------------
        # Historical wording
        # ----------------------------------------------------

        query_text = _normalise(
            query
        )

        if any(
            token in query_text
            for token in (
                "historical",
                "history",
                "past",
                "previous",
                "event",
                "events",
                "happened",
            )
        ):
            score += 10.0

        if (
            "landslide" in query_text
        ):
            score += 10.0

        item = dict(
            event
        )

        item[
            "distance_m"
        ] = distance_m

        candidates.append(
            (
                score,
                item,
            )
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1].get(
                "event_date"
            )
            or "",
        ),
        reverse=True,
    )

    selected = [
        item
        for _, item
        in candidates[:limit]
    ]

    return {
        "status":
            "READY",

        "query":
            query,

        "filters":
            {
                "year":
                    year,

                "places":
                    places,

                "coordinates":
                    coordinates,

                "radius_m":
                    radius_m,
            },

        "matched_event_count":
            len(selected),

        "events":
            selected,

        "source":
            str(
                DATED_EVENTS_SOURCE
            ),

        "source_scope":
            "DATED_HISTORICAL_EVENTS_ONLY",
    }


# ============================================================
# HISTORICAL RECURRENCE
# ============================================================

def build_historical_recurrence(
    query: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:

    rows = _read_csv(
        HOTSPOTS_SOURCE
    )

    hotspots = []

    for row in rows:

        hotspots.append(
            {
                "hotspot_id":
                    row.get(
                        "hotspot_id"
                    ),

                "event_count":
                    _int(
                        row.get(
                            "event_count"
                        )
                    )
                    or 0,

                "latitude":
                    _float(
                        row.get(
                            "latitude"
                        )
                    ),

                "longitude":
                    _float(
                        row.get(
                            "longitude"
                        )
                    ),

                "hotspot_score":
                    _float(
                        row.get(
                            "hotspot_score"
                        )
                    )
                    or 0.0,

                "hotspot_category":
                    row.get(
                        "hotspot_category"
                    ),
            }
        )

    hotspots.sort(
        key=lambda item: (
            item["event_count"],
            item["hotspot_score"],
        ),
        reverse=True,
    )

    return {
        "status":
            "READY",

        "query":
            query,

        "historical_hotspot_count":
            len(hotspots),

        "repeated_locations":
            [
                item
                for item in hotspots[:limit]
                if item["event_count"] > 1
            ],

        "top_hotspots":
            hotspots[:limit],

        "source":
            str(
                HOTSPOTS_SOURCE
            ),
    }


# ============================================================
# HISTORICAL ↔ CURRENT CORRELATION
# ============================================================

def build_historical_current_context(
    query: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:

    rows = _read_csv(
        HISTORICAL_CURRENT_SOURCE
    )

    records = []

    for row in rows:

        records.append(
            {
                "incident_id":
                    row.get(
                        "incident_id"
                    ),

                "priority_rank":
                    _int(
                        row.get(
                            "priority_rank"
                        )
                    ),

                "priority_score":
                    _float(
                        row.get(
                            "priority_score"
                        )
                    ),

                "priority_level":
                    row.get(
                        "priority_level"
                    ),

                "max_risk_score":
                    _float(
                        row.get(
                            "max_risk_score"
                        )
                    ),

                "historical_hotspot_distance_m":
                    _float(
                        row.get(
                            "historical_hotspot_distance_m"
                        )
                    ),

                "hotspot_id":
                    row.get(
                        "hotspot_id"
                    ),

                "event_count":
                    _int(
                        row.get(
                            "event_count"
                        )
                    ),

                "hotspot_score":
                    _float(
                        row.get(
                            "hotspot_score"
                        )
                    ),

                "hotspot_category":
                    row.get(
                        "hotspot_category"
                    ),

                "historical_current_score":
                    _float(
                        row.get(
                            "historical_current_score"
                        )
                    ),

                "historical_current_category":
                    row.get(
                        "historical_current_category"
                    ),

                "persistent_risk_zone":
                    row.get(
                        "persistent_risk_zone"
                    ),
            }
        )

    records.sort(
        key=lambda item: (
            item.get(
                "historical_current_score"
            )
            or 0.0,

            item.get(
                "priority_score"
            )
            or 0.0,
        ),
        reverse=True,
    )

    persistent = [
        item
        for item in records
        if str(
            item.get(
                "persistent_risk_zone"
            )
            or "0"
        ) == "1"
    ]

    return {
        "status":
            "READY",

        "query":
            query,

        "correlation_count":
            len(records),

        "persistent_risk_zones":
            len(persistent),

        "records":
            records[:limit],

        "strongest_correlations":
            persistent[:limit],

        "source":
            str(
                HISTORICAL_CURRENT_SOURCE
            ),

        "trust_boundary":
            {
                "historical":
                    "HISTORICAL",

                "current":
                    "CURRENT_DERIVED",

                "relationship":
                    "CORRELATION_NOT_CAUSATION",
            },
    }


# ============================================================
# UNIFIED HISTORICAL INTELLIGENCE
# ============================================================

def build_historical_event_intelligence(
    query: str,
    *,
    limit: int = 10,
    radius_m: float = 35_000.0,
) -> dict[str, Any]:

    events = search_historical_events(
        query,
        limit=limit,
        radius_m=radius_m,
    )

    recurrence = build_historical_recurrence(
        query,
        limit=limit,
    )

    current = build_historical_current_context(
        query,
        limit=limit,
    )

    return {
        "status":
            "READY",

        "query":
            query,

        "historical_events":
            events,

        "historical_recurrence":
            recurrence,

        "historical_current":
            current,

        "trust_boundary":
            {
                "events":
                    "HISTORICAL_SOURCE_BACKED",

                "hotspots":
                    "HISTORICAL_DERIVED",

                "current_risk":
                    "CURRENT_DERIVED",

                "interpretation":
                    (
                        "Historical evidence provides "
                        "context and does not by itself "
                        "prove present-day risk."
                    ),
            },
    }


__all__ = [
    "search_historical_events",
    "build_historical_recurrence",
    "build_historical_current_context",
    "build_historical_event_intelligence",
]

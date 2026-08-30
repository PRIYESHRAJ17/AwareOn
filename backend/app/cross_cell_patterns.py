from __future__ import annotations

from math import cos, radians, sqrt
from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category(
    value: Any,
) -> str:
    return str(value or "UNKNOWN").upper()


def _rank(
    value: Any,
) -> int:
    return CATEGORY_RANK.get(
        _category(value),
        0,
    )


def _feature_centroid(
    feature: dict[str, Any],
) -> tuple[float, float] | None:

    geometry = feature.get("geometry")

    if not isinstance(
        geometry,
        dict,
    ):
        return None

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if not coordinates:
        return None

    try:
        if geometry_type == "Point":
            return (
                float(coordinates[0]),
                float(coordinates[1]),
            )

        if geometry_type == "Polygon":
            ring = coordinates[0]

            if not ring:
                return None

            lngs = [
                float(point[0])
                for point in ring
            ]

            lats = [
                float(point[1])
                for point in ring
            ]

            return (
                sum(lngs) / len(lngs),
                sum(lats) / len(lats),
            )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return None

    return None


def _spatial_span(
    coordinates: list[tuple[float, float]],
) -> dict[str, float]:

    if not coordinates:
        return {
            "longitude_span": 0.0,
            "latitude_span": 0.0,
            "approx_span_km": 0.0,
        }

    lngs = [
        point[0]
        for point in coordinates
    ]

    lats = [
        point[1]
        for point in coordinates
    ]

    longitude_span = (
        max(lngs) -
        min(lngs)
    )

    latitude_span = (
        max(lats) -
        min(lats)
    )

    mean_latitude = (
        sum(lats) /
        len(lats)
    )

    latitude_km = (
        latitude_span *
        111.0
    )

    longitude_km = (
        longitude_span *
        111.0 *
        abs(
            cos(
                radians(
                    mean_latitude
                )
            )
        )
    )

    approx_span_km = sqrt(
        latitude_km ** 2 +
        longitude_km ** 2
    )

    return {
        "longitude_span":
            longitude_span,

        "latitude_span":
            latitude_span,

        "approx_span_km":
            approx_span_km,
    }


def analyze_cross_cell_pattern(
    feature_collection: dict[str, Any],
    focus_radius_m: float = 5000.0,
) -> dict[str, Any]:

    if not isinstance(
        feature_collection,
        dict,
    ):
        raise ValueError(
            "A GeoJSON FeatureCollection is required."
        )

    features = feature_collection.get(
        "features",
        [],
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            "FeatureCollection features must be a list."
        )

    if not features:
        return {
            "pattern":
                "NO_DATA",

            "pattern_strength":
                "LOW",

            "spatial_extent":
                "LOCALIZED",

            "concentration":
                "LIMITED",

            "signal_alignment":
                "MIXED",

            "confidence":
                "LIMITED",

            "cell_count":
                0,

            "message":
                (
                    "No spatial cells were supplied "
                    "for pattern analysis."
                ),
        }

    cells: list[dict[str, Any]] = []

    coordinates: list[
        tuple[float, float]
    ] = []

    for feature in features:

        if not isinstance(
            feature,
            dict,
        ):
            continue

        properties = feature.get(
            "properties",
            {},
        )

        if not isinstance(
            properties,
            dict,
        ):
            properties = {}

        cell_id = str(
            properties.get(
                "cell_id"
            ) or ""
        )

        if not cell_id:
            continue

        risk = _num(
            properties.get(
                "unified_risk_score"
            )
        )

        severity = _category(
            properties.get(
                "severity"
            )
        )

        warning_state = _category(
            properties.get(
                "warning_state"
            )
        )

        confidence = _num(
            properties.get(
                "confidence_score"
            )
        )

        distance_m = _num(
            properties.get(
                "distance_m"
            ),
            -1.0,
        )

        centroid = _feature_centroid(
            feature
        )

        if centroid is not None:
            coordinates.append(
                centroid
            )

        cells.append(
            {
                "cell_id":
                    cell_id,

                "risk":
                    risk,

                "severity":
                    severity,

                "warning_state":
                    warning_state,

                "confidence":
                    confidence,

                "distance_m":
                    distance_m,

                "category_rank":
                    _rank(
                        severity
                    ),

                "centroid":
                    centroid,
            }
        )

    if not cells:
        return {
            "pattern":
                "NO_VALID_CELLS",

            "pattern_strength":
                "LOW",

            "spatial_extent":
                "LOCALIZED",

            "concentration":
                "LIMITED",

            "signal_alignment":
                "MIXED",

            "confidence":
                "LIMITED",

            "cell_count":
                0,

            "message":
                (
                    "No valid spatial cell records "
                    "were available."
                ),
        }

    total_cells = len(
        cells
    )

    high_cells = [
        cell
        for cell in cells
        if cell["category_rank"] >= 2
    ]

    extreme_cells = [
        cell
        for cell in cells
        if cell["category_rank"] >= 3
    ]

    watch_cells = [
        cell
        for cell in cells
        if cell["warning_state"]
        in {
            "WATCH",
            "WARNING",
            "CRITICAL",
        }
    ]

    high_ratio = (
        len(high_cells) /
        total_cells
    )

    extreme_ratio = (
        len(extreme_cells) /
        total_cells
    )

    mean_risk = (
        sum(
            cell["risk"]
            for cell in cells
        )
        /
        total_cells
    )

    maximum_risk_cell = max(
        cells,
        key=lambda cell:
            cell["risk"],
    )

    mean_confidence = (
        sum(
            cell["confidence"]
            for cell in cells
        )
        /
        total_cells
    )

    focus_cells = [
        cell
        for cell in cells
        if (
            0.0 <=
            cell["distance_m"] <=
            focus_radius_m
        )
    ]

    focus_high_cells = [
        cell
        for cell in focus_cells
        if cell["category_rank"] >= 2
    ]

    focus_high_ratio = (
        len(focus_high_cells) /
        len(focus_cells)
        if focus_cells
        else 0.0
    )

    valid_distances = [
        cell["distance_m"]
        for cell in cells
        if cell["distance_m"] >= 0.0
    ]

    maximum_distance = max(
        valid_distances,
        default=0.0,
    )

    # --------------------------------------------------------
    # Pattern classification
    # --------------------------------------------------------

    if total_cells <= 2:

        pattern = "ISOLATED"

    elif (
        high_ratio >= 0.60
        and
        total_cells >= 5
    ):

        pattern = "HIGH_RISK_CLUSTER"

    elif (
        len(high_cells) >= 3
        and
        focus_high_ratio >= 0.40
    ):

        pattern = "FOCUSED_HIGH_RISK"

    elif (
        len(high_cells) >= 3
        and
        high_ratio >= 0.30
    ):

        pattern = "CLUSTERED"

    elif (
        len(watch_cells) >= 3
        and
        (
            len(watch_cells) /
            total_cells
        ) >= 0.40
    ):

        pattern = "WATCH_CLUSTER"

    else:

        pattern = "MIXED_SIGNAL_CLUSTER"

    # --------------------------------------------------------
    # Spatial extent
    # --------------------------------------------------------

    span = _spatial_span(
        coordinates
    )

    if (
        total_cells >= 7
        and
        span["approx_span_km"] >= 2.0
    ):

        spatial_extent = "BROAD"

    elif (
        total_cells >= 3
        and
        span["approx_span_km"] >= 0.75
    ):

        spatial_extent = "CLUSTERED"

    else:

        spatial_extent = "LOCALIZED"

    # --------------------------------------------------------
    # Risk concentration
    # --------------------------------------------------------

    if (
        len(high_cells) >= 3
        and
        high_ratio >= 0.40
        and
        mean_risk >= 55.0
    ):

        concentration = "STRONG"

    elif (
        len(high_cells) >= 2
        and
        high_ratio >= 0.25
    ):

        concentration = "MODERATE"

    else:

        concentration = "LIMITED"

    if (
        concentration == "STRONG"
        and
        spatial_extent == "BROAD"
    ):

        pattern_strength = "REGIONAL"

    elif concentration in {
        "STRONG",
        "MODERATE",
    }:

        pattern_strength = "LOCAL_CLUSTER"

    else:

        pattern_strength = "LOW"

    # --------------------------------------------------------
    # Operational alignment
    # --------------------------------------------------------

    operational_alignment = (
        len(watch_cells) /
        total_cells
    )

    if (
        operational_alignment >= 0.70
        and
        high_ratio >= 0.40
    ):

        signal_alignment = "CONVERGENT"

    elif (
        operational_alignment >= 0.50
        or
        high_ratio >= 0.30
    ):

        signal_alignment = "PARTIAL"

    else:

        signal_alignment = "MIXED"

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if mean_confidence >= 75.0:

        confidence = "HIGH"

    elif mean_confidence >= 50.0:

        confidence = "MODERATE"

    else:

        confidence = "LIMITED"

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    if pattern == "HIGH_RISK_CLUSTER":

        interpretation = (
            f"{len(high_cells)} of {total_cells} nearby "
            "cells are HIGH or EXTREME, indicating a "
            "concentrated high-risk spatial pattern."
        )

    elif pattern == "FOCUSED_HIGH_RISK":

        interpretation = (
            f"{len(focus_high_cells)} high-risk cells occur "
            "inside the focus radius, indicating a "
            "concentrated local risk area."
        )

    elif pattern == "CLUSTERED":

        interpretation = (
            "Several nearby cells exhibit elevated risk, "
            "forming a localized spatial cluster."
        )

    elif pattern == "WATCH_CLUSTER":

        interpretation = (
            "Multiple nearby cells carry active watch "
            "states without the neighborhood being "
            "dominated by HIGH or EXTREME risk."
        )

    elif pattern == "ISOLATED":

        interpretation = (
            "Too few nearby cells are available to "
            "establish a broad spatial pattern."
        )

    else:

        interpretation = (
            "The nearby cells contain mixed risk signals "
            "without one dominant spatial pattern."
        )

    # --------------------------------------------------------
    # Top cells
    # --------------------------------------------------------

    top_cells = sorted(
        cells,
        key=lambda cell: (
            cell["category_rank"],
            cell["risk"],
            cell["confidence"],
        ),
        reverse=True,
    )[:10]

    return {
        "pattern":
            pattern,

        "pattern_strength":
            pattern_strength,

        "spatial_extent":
            spatial_extent,

        "concentration":
            concentration,

        "signal_alignment":
            signal_alignment,

        "confidence":
            confidence,

        "cell_count":
            total_cells,

        "high_risk_cells":
            len(high_cells),

        "extreme_cells":
            len(extreme_cells),

        "watch_cells":
            len(watch_cells),

        "high_risk_ratio":
            high_ratio,

        "extreme_ratio":
            extreme_ratio,

        "mean_risk":
            mean_risk,

        "maximum_risk":
            maximum_risk_cell["risk"],

        "maximum_risk_cell":
            maximum_risk_cell["cell_id"],

        "mean_confidence":
            mean_confidence,

        "focus_radius_m":
            focus_radius_m,

        "cells_within_focus_radius":
            len(focus_cells),

        "high_risk_within_focus":
            len(focus_high_cells),

        "high_risk_within_focus_ratio":
            focus_high_ratio,

        "maximum_distance_m":
            maximum_distance,

        "spatial_span":
            span,

        "operational_alignment":
            operational_alignment,

        "interpretation":
            interpretation,

        "top_cells":
            [
                {
                    "cell_id":
                        cell["cell_id"],

                    "risk":
                        cell["risk"],

                    "severity":
                        cell["severity"],

                    "warning_state":
                        cell["warning_state"],

                    "distance_m":
                        cell["distance_m"],

                    "confidence":
                        cell["confidence"],
                }
                for cell in top_cells
            ],
    }

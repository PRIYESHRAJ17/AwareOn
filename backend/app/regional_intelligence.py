from __future__ import annotations

from typing import Any

from backend.app.services.gis_service import gis_service

from backend.app.cross_cell_patterns import (
    analyze_cross_cell_pattern,
)


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category_rank(
    value: Any,
) -> int:
    categories = {
        "LOW": 0,
        "MODERATE": 1,
        "HIGH": 2,
        "EXTREME": 3,
    }

    return categories.get(
        str(value or "").upper(),
        0,
    )


def build_regional_intelligence(
    latitude: float,
    longitude: float,
    radius_m: float = 10000.0,
) -> dict[str, Any]:

    if radius_m <= 0:
        raise ValueError(
            "radius_m must be greater than 0."
        )

    nearby = gis_service.get_nearby_cells(
        latitude=float(latitude),
        longitude=float(longitude),
        radius_m=float(radius_m),
    )

    features = nearby.get(
        "features",
        [],
    )

    if not features:
        raise ValueError(
            "No cells were found in the requested region."
        )

    pattern = analyze_cross_cell_pattern(
        nearby,
        radius_m,
    )

    cells = []

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        if not isinstance(
            properties,
            dict,
        ):
            properties = {}

        cells.append(
            {
                "cell_id":
                    properties.get(
                        "cell_id"
                    ),

                "risk_score":
                    _num(
                        properties.get(
                            "unified_risk_score"
                        )
                    ),

                "severity":
                    str(
                        properties.get(
                            "severity"
                        )
                        or "UNKNOWN"
                    ).upper(),

                "warning_state":
                    str(
                        properties.get(
                            "warning_state"
                        )
                        or "UNKNOWN"
                    ).upper(),

                "confidence":
                    _num(
                        properties.get(
                            "confidence_score"
                        )
                    ),

                "distance_m":
                    _num(
                        properties.get(
                            "distance_m"
                        )
                    ),
            }
        )

    total = len(cells)

    mean_risk = (
        sum(
            cell["risk_score"]
            for cell in cells
        )
        /
        total
    )

    maximum = max(
        cells,
        key=lambda item: (
            _category_rank(
                item["severity"]
            ),
            item["risk_score"],
        ),
    )

    high_or_extreme = [
        cell
        for cell in cells
        if _category_rank(
            cell["severity"]
        ) >= 2
    ]

    extreme = [
        cell
        for cell in cells
        if _category_rank(
            cell["severity"]
        ) >= 3
    ]

    watch = [
        cell
        for cell in cells
        if cell["warning_state"]
        in {
            "WATCH",
            "WARNING",
            "CRITICAL",
        }
    ]

    mean_confidence = (
        sum(
            cell["confidence"]
            for cell in cells
        )
        /
        total
    )

    if mean_confidence >= 75.0:
        confidence_band = "HIGH"
    elif mean_confidence >= 50.0:
        confidence_band = "MODERATE"
    else:
        confidence_band = "LIMITED"

    if (
        len(extreme) >= 3
        or
        (
            len(high_or_extreme) >= 5
            and
            mean_risk >= 60.0
        )
    ):
        regional_state = "CRITICAL_REGION"

    elif (
        len(high_or_extreme) >= 3
        and
        mean_risk >= 50.0
    ):
        regional_state = "HIGH_RISK_REGION"

    elif mean_risk >= 35.0:
        regional_state = "ELEVATED_REGION"

    else:
        regional_state = "LOWER_RISK_REGION"

    if (
        pattern.get(
            "pattern"
        )
        ==
        "HIGH_RISK_CLUSTER"
    ):
        regional_assessment = (
            "The region contains a concentrated "
            "high-risk cluster."
        )

    elif (
        pattern.get(
            "pattern"
        )
        in {
            "CLUSTERED",
            "FOCUSED_HIGH_RISK",
        }
    ):
        regional_assessment = (
            "The region contains a localized "
            "elevated-risk cluster."
        )

    elif (
        pattern.get(
            "pattern"
        )
        ==
        "WATCH_CLUSTER"
    ):
        regional_assessment = (
            "The region shows multiple active "
            "watch signals."
        )

    else:
        regional_assessment = (
            "The region shows mixed or limited "
            "spatial risk concentration."
        )

    top_cells = sorted(
        cells,
        key=lambda item: (
            _category_rank(
                item["severity"]
            ),
            item["risk_score"],
            item["confidence"],
        ),
        reverse=True,
    )[:20]

    return {
        "region": {
            "latitude":
                float(latitude),

            "longitude":
                float(longitude),

            "radius_m":
                float(radius_m),
        },

        "regional_state":
            regional_state,

        "regional_assessment":
            regional_assessment,

        "cell_count":
            total,

        "high_or_extreme_cells":
            len(high_or_extreme),

        "extreme_cells":
            len(extreme),

        "watch_cells":
            len(watch),

        "high_or_extreme_ratio":
            (
                len(high_or_extreme)
                /
                total
            ),

        "mean_risk_score":
            mean_risk,

        "maximum_risk":
            {
                "cell_id":
                    maximum["cell_id"],

                "risk_score":
                    maximum["risk_score"],

                "severity":
                    maximum["severity"],

                "warning_state":
                    maximum["warning_state"],
            },

        "mean_confidence":
            mean_confidence,

        "confidence_band":
            confidence_band,

        "spatial_pattern":
            pattern,

        "top_cells":
            top_cells,
    }

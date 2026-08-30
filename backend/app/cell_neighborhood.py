from __future__ import annotations

from typing import Any

from backend.app.services.gis_service import (
    gis_service,
    UTM_TO_WGS84,
)


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def resolve_cell_neighborhood(
    cell_id: str,
    radius_m: float = 5000.0,
) -> dict[str, Any]:

    if not cell_id:
        raise ValueError(
            "cell_id is required."
        )

    if radius_m <= 0:
        raise ValueError(
            "radius_m must be greater than 0."
        )

    cell = gis_service.get_cell(
        str(cell_id)
    )

    if cell is None:
        raise ValueError(
            f"GIS cell not found: {cell_id}"
        )

    utm_x = _num(
        cell.get("centroid_x")
    )

    utm_y = _num(
        cell.get("centroid_y")
    )

    if (
        utm_x == 0.0
        and utm_y == 0.0
    ):
        raise ValueError(
            f"Cell {cell_id} has invalid centroid coordinates."
        )

    longitude, latitude = (
        UTM_TO_WGS84.transform(
            utm_x,
            utm_y,
        )
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

    target_feature = None

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        if str(
            properties.get(
                "cell_id"
            )
        ) == str(cell_id):

            target_feature = feature
            break

    return {
        "cell_id":
            str(cell_id),

        "centroid_utm":
            {
                "x":
                    utm_x,

                "y":
                    utm_y,
            },

        "centroid_wgs84":
            {
                "longitude":
                    float(longitude),

                "latitude":
                    float(latitude),
            },

        "radius_m":
            float(radius_m),

        "neighbor_count":
            len(features),

        "target_present":
            target_feature is not None,

        "target_distance_m":
            (
                _num(
                    target_feature
                    .get("properties", {})
                    .get("distance_m")
                )
                if target_feature
                else None
            ),

        "feature_collection":
            nearby,
    }

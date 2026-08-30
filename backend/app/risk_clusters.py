from __future__ import annotations

from collections import deque
from typing import Any


CATEGORY_RANK = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category(value: Any) -> str:
    return str(value or "UNKNOWN").upper()


def _rank(value: Any) -> int:
    return CATEGORY_RANK.get(
        _category(value),
        0,
    )


def _centroid(feature: dict[str, Any]) -> tuple[float, float] | None:
    geometry = feature.get("geometry", {})

    if not isinstance(geometry, dict):
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

            xs = [
                float(point[0])
                for point in ring
            ]

            ys = [
                float(point[1])
                for point in ring
            ]

            return (
                sum(xs) / len(xs),
                sum(ys) / len(ys),
            )

    except (TypeError, ValueError, IndexError):
        return None

    return None


def _distance_m(
    a: tuple[float, float],
    b: tuple[float, float],
) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return (
        dx * dx +
        dy * dy
    ) ** 0.5


def _build_adjacency(
    cells: list[dict[str, Any]],
    connection_radius_m: float,
) -> dict[str, list[str]]:

    adjacency = {
        cell["cell_id"]: []
        for cell in cells
    }

    for i, first in enumerate(cells):

        first_point = first.get("centroid")

        if first_point is None:
            continue

        for second in cells[i + 1:]:

            second_point = second.get("centroid")

            if second_point is None:
                continue

            distance = _distance_m(
                first_point,
                second_point,
            )

            if distance <= connection_radius_m:

                first_id = first["cell_id"]
                second_id = second["cell_id"]

                adjacency[first_id].append(
                    second_id
                )

                adjacency[second_id].append(
                    first_id
                )

    return adjacency


def detect_risk_clusters(
    feature_collection: dict[str, Any],
    connection_radius_m: float = 150.0,
    minimum_category: str = "HIGH",
    minimum_cluster_size: int = 2,
) -> dict[str, Any]:

    if not isinstance(
        feature_collection,
        dict,
    ):
        raise ValueError(
            "A GeoJSON FeatureCollection is required."
        )

    if connection_radius_m <= 0:
        raise ValueError(
            "connection_radius_m must be greater than 0."
        )

    if minimum_cluster_size <= 0:
        raise ValueError(
            "minimum_cluster_size must be greater than 0."
        )

    threshold_rank = _rank(
        minimum_category
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

    cells = []

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
            continue

        cell_id = str(
            properties.get(
                "cell_id"
            )
            or ""
        )

        if not cell_id:
            continue

        severity = _category(
            properties.get(
                "severity"
            )
        )

        if _rank(severity) < threshold_rank:
            continue

        centroid = _centroid(
            feature
        )

        if centroid is None:
            continue

        cells.append(
            {
                "cell_id": cell_id,
                "risk_score": _num(
                    properties.get(
                        "unified_risk_score"
                    )
                ),
                "severity": severity,
                "warning_state": _category(
                    properties.get(
                        "warning_state"
                    )
                ),
                "confidence": _num(
                    properties.get(
                        "confidence_score"
                    )
                ),
                "centroid": centroid,
            }
        )

    if not cells:

        return {
            "cluster_count": 0,
            "clusters": [],
            "dominant_cluster": None,
            "high_risk_cell_count": 0,
            "minimum_category": minimum_category,
            "connection_radius_m": connection_radius_m,
        }

    adjacency = _build_adjacency(
        cells,
        connection_radius_m,
    )

    cell_lookup = {
        cell["cell_id"]: cell
        for cell in cells
    }

    visited: set[str] = set()
    groups: list[list[str]] = []

    for cell in cells:

        root = cell["cell_id"]

        if root in visited:
            continue

        queue = deque([root])
        visited.add(root)

        group = []

        while queue:

            current = queue.popleft()
            group.append(current)

            for neighbor in adjacency.get(
                current,
                [],
            ):

                if neighbor in visited:
                    continue

                visited.add(neighbor)
                queue.append(
                    neighbor
                )

        groups.append(
            group
        )

    clusters = []

    for index, group in enumerate(
        groups,
        start=1,
    ):

        if len(group) < minimum_cluster_size:
            continue

        members = [
            cell_lookup[cell_id]
            for cell_id in group
        ]

        risk_values = [
            cell["risk_score"]
            for cell in members
        ]

        confidence_values = [
            cell["confidence"]
            for cell in members
        ]

        extreme_count = sum(
            1
            for cell in members
            if _rank(
                cell["severity"]
            ) >= 3
        )

        critical_warning_count = sum(
            1
            for cell in members
            if cell["warning_state"]
            in {
                "CRITICAL",
                "WARNING",
            }
        )

        mean_x = (
            sum(
                cell["centroid"][0]
                for cell in members
            )
            /
            len(members)
        )

        mean_y = (
            sum(
                cell["centroid"][1]
                for cell in members
            )
            /
            len(members)
        )

        mean_risk = (
            sum(risk_values)
            /
            len(risk_values)
        )

        maximum_risk = max(
            risk_values
        )

        mean_confidence = (
            sum(confidence_values)
            /
            len(confidence_values)
        )

        if (
            extreme_count >= 3
            or (
                len(members) >= 5
                and mean_risk >= 65.0
            )
        ):
            cluster_severity = "EXTREME"

        elif (
            extreme_count >= 1
            or mean_risk >= 60.0
        ):
            cluster_severity = "HIGH"

        else:
            cluster_severity = "MODERATE"

        if (
            critical_warning_count
            >=
            max(
                2,
                len(members) // 2,
            )
        ):
            operational_state = "CRITICAL"

        elif critical_warning_count >= 1:
            operational_state = "WATCH"

        else:
            operational_state = "MONITOR"

        clusters.append(
            {
                "cluster_id":
                    f"CLUSTER_{index:03d}",

                "cell_count":
                    len(members),

                "cell_ids":
                    group,

                "mean_risk":
                    mean_risk,

                "maximum_risk":
                    maximum_risk,

                "maximum_risk_cell":
                    max(
                        members,
                        key=lambda item:
                            item["risk_score"],
                    )["cell_id"],

                "cluster_severity":
                    cluster_severity,

                "operational_state":
                    operational_state,

                "extreme_cells":
                    extreme_count,

                "critical_or_warning_cells":
                    critical_warning_count,

                "mean_confidence":
                    mean_confidence,

                "centroid":
                    {
                        "x":
                            mean_x,

                        "y":
                            mean_y,
                    },
            }
        )

    clusters.sort(
        key=lambda cluster: (
            _rank(
                cluster[
                    "cluster_severity"
                ]
            ),
            cluster[
                "cell_count"
            ],
            cluster[
                "mean_risk"
            ],
        ),
        reverse=True,
    )

    for rank, cluster in enumerate(
        clusters,
        start=1,
    ):
        cluster[
            "priority_rank"
        ] = rank

    dominant = (
        clusters[0]
        if clusters
        else None
    )

    if dominant is not None:

        if (
            dominant[
                "cluster_severity"
            ]
            ==
            "EXTREME"
        ):

            regional_state = (
                "CRITICAL_CLUSTER"
            )

        elif (
            dominant[
                "cell_count"
            ] >= 5
        ):

            regional_state = (
                "HIGH_RISK_CLUSTER"
            )

        else:

            regional_state = (
                "LOCAL_HIGH_RISK"
            )

    else:

        regional_state = (
            "NO_SIGNIFICANT_CLUSTER"
        )

    if dominant is not None:

        interpretation = (
            f"{dominant['cell_count']} HIGH-or-above "
            "cells form the dominant risk cluster, "
            f"with mean risk {dominant['mean_risk']:.2f} "
            f"and maximum risk "
            f"{dominant['maximum_risk']:.2f}."
        )

    else:

        interpretation = (
            "No cluster met the minimum size and "
            "risk-category criteria."
        )

    return {
        "regional_state":
            regional_state,

        "cluster_count":
            len(clusters),

        "clusters":
            clusters,

        "dominant_cluster":
            dominant,

        "high_risk_cell_count":
            len(cells),

        "minimum_category":
            minimum_category,

        "connection_radius_m":
            connection_radius_m,

        "minimum_cluster_size":
            minimum_cluster_size,

        "interpretation":
            interpretation,
    }

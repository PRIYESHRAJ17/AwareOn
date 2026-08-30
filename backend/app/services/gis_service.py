from pathlib import Path
import json

import ijson
import pandas as pd
from shapely.geometry import Point, mapping, shape
from pyproj import Transformer


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = (
    ROOT
    / "data"
    / "processed"
)

GRID_FILE = (
    DATA_DIR
    / "grid"
    / "master_grid_100m.geojson"
)

BOUNDARY_FILE = (
    DATA_DIR
    / "grid"
    / "sikkim_boundary.geojson"
)

RISK_FILE = (
    DATA_DIR
    / "intelligence"
    / "awareon_risk_decisions.csv"
)

HISTORICAL_FILE = (
    DATA_DIR
    / "engines"
    / "historical_event_engine_output.csv"
)

EXPOSURE_FILE = (
    DATA_DIR
    / "engines"
    / "exposure_impact_engine_output.csv"
)

PRIORITY_FILE = (
    DATA_DIR
    / "intelligence"
    / "awareon_prioritized_incidents.csv"
)


# ============================================================
# CRS
# ============================================================

WGS84_TO_UTM = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32645",
    always_xy=True,
)

UTM_TO_WGS84 = Transformer.from_crs(
    "EPSG:32645",
    "EPSG:4326",
    always_xy=True,
)


# ============================================================
# BASIC FILE HELPERS
# ============================================================

def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


def read_geojson(path: Path) -> dict:
    require_file(path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# STREAM LARGE MASTER GRID
# ============================================================

def iter_grid_features():
    """
    Stream GeoJSON features one at a time.

    This is intentionally used instead of json.load()
    because master_grid_100m.geojson is very large.
    """

    require_file(GRID_FILE)

    with GRID_FILE.open("rb") as file:
        for feature in ijson.items(
            file,
            "features.item",
        ):
            yield feature


# ============================================================
# GRID CELL HELPERS
# ============================================================

def get_feature_cell_id(feature):
    properties = feature.get(
        "properties",
        {},
    )

    cell_id = properties.get(
        "cell_id"
    )

    if cell_id is None:
        cell_id = feature.get(
            "cell_id"
        )

    if cell_id is None:
        return None

    return str(cell_id)


# ============================================================
# GEOMETRY CONVERSION
# ============================================================

def transform_geometry_to_wgs84(
    geometry,
):
    """
    Convert an EPSG:32645 geometry into
    EPSG:4326 longitude/latitude coordinates.
    """

    if geometry is None:
        return None

    geom = shape(
        geometry
    )

    geo = mapping(
        geom
    )

    def transform_coords(coords):
        """
        Recursively transform coordinate arrays.
        """

        if (
            isinstance(
                coords,
                (list, tuple),
            )
            and len(coords) >= 2
            and isinstance(
                coords[0],
                (int, float),
            )
            and isinstance(
                coords[1],
                (int, float),
            )
        ):
            lon, lat = (
                UTM_TO_WGS84.transform(
                    coords[0],
                    coords[1],
                )
            )

            if len(coords) == 2:
                return [
                    float(lon),
                    float(lat),
                ]

            return [
                float(lon),
                float(lat),
                *coords[2:],
            ]

        return [
            transform_coords(item)
            for item in coords
        ]

    geo["coordinates"] = (
        transform_coords(
            geo["coordinates"]
        )
    )

    return geo


# ============================================================
# RISK DATA
# ============================================================

def load_risk_lookup():
    require_file(
        RISK_FILE
    )

    df = pd.read_csv(
        RISK_FILE
    )

    if "cell_id" not in df.columns:
        raise RuntimeError(
            "Risk file is missing 'cell_id'."
        )

    df["cell_id"] = (
        df["cell_id"]
        .astype(str)
    )

    return (
        df
        .set_index("cell_id")
        .to_dict(
            orient="index"
        )
    )


# ============================================================
# EXPOSURE DATA
# ============================================================

def load_exposure_lookup():
    require_file(
        EXPOSURE_FILE
    )

    df = pd.read_csv(
        EXPOSURE_FILE
    )

    if "cell_id" not in df.columns:
        raise RuntimeError(
            "Exposure file is missing 'cell_id'."
        )

    df["cell_id"] = (
        df["cell_id"]
        .astype(str)
    )

    return (
        df
        .set_index("cell_id")
        .to_dict(
            orient="index"
        )
    )


# ============================================================
# GIS SERVICE
# ============================================================

class GISService:

    # ========================================================
    # SINGLE CELL
    # ========================================================

    def get_cell(
        self,
        cell_id: str,
    ):
        target = str(
            cell_id
        )

        for feature in (
            iter_grid_features()
        ):
            current_id = (
                get_feature_cell_id(
                    feature
                )
            )

            if current_id != target:
                continue

            geometry = feature.get(
                "geometry"
            )

            if geometry is None:
                return None

            geom = shape(
                geometry
            )

            centroid = (
                geom.centroid
            )

            return {
                "cell_id":
                    target,

                "centroid_x":
                    float(
                        centroid.x
                    ),

                "centroid_y":
                    float(
                        centroid.y
                    ),

                "geometry":
                    geometry,
            }

        return None

    # ========================================================
    # BOUNDARY
    # ========================================================

    def get_boundary(self):
        return read_geojson(
            BOUNDARY_FILE
        )

    # ========================================================
    # RISK LAYER
    # ========================================================

    def get_risk_layer(self):

        risk_lookup = (
            load_risk_lookup()
        )

        output_features = []

        for feature in (
            iter_grid_features()
        ):

            cell_id = (
                get_feature_cell_id(
                    feature
                )
            )

            if cell_id is None:
                continue

            row = (
                risk_lookup.get(
                    cell_id
                )
            )

            if row is None:
                continue

            geometry = feature.get(
                "geometry"
            )

            if geometry is None:
                continue

            output_features.append(
                {
                    "type":
                        "Feature",

                    "properties":
                        {
                            "cell_id":
                                cell_id,

                            "unified_risk_score":
                                float(
                                    row[
                                        "unified_risk_score"
                                    ]
                                ),

                            "severity":
                                str(
                                    row[
                                        "severity"
                                    ]
                                ),

                            "warning_state":
                                str(
                                    row[
                                        "warning_state"
                                    ]
                                ),

                            "confidence_score":
                                float(
                                    row[
                                        "confidence_score"
                                    ]
                                ),
                        },

                    "geometry":
                        transform_geometry_to_wgs84(
                            geometry
                        ),
                }
            )

        return {
            "type":
                "FeatureCollection",

            "features":
                output_features,
        }

    # ========================================================
    # EXPOSURE LAYER
    # ========================================================

    def get_exposure_layer(self):

        exposure_lookup = (
            load_exposure_lookup()
        )

        output_features = []

        for feature in (
            iter_grid_features()
        ):

            cell_id = (
                get_feature_cell_id(
                    feature
                )
            )

            if cell_id is None:
                continue

            row = (
                exposure_lookup.get(
                    cell_id
                )
            )

            if row is None:
                continue

            geometry = feature.get(
                "geometry"
            )

            if geometry is None:
                continue

            output_features.append(
                {
                    "type":
                        "Feature",

                    "properties":
                        {
                            "cell_id":
                                cell_id,

                            "exposure_score":
                                float(
                                    row[
                                        "exposure_score"
                                    ]
                                ),

                            "exposure_category":
                                str(
                                    row[
                                        "exposure_category"
                                    ]
                                ),

                            "transport_exposure":
                                float(
                                    row[
                                        "transport_exposure"
                                    ]
                                ),

                            "population_exposure_proxy":
                                float(
                                    row[
                                        "population_exposure_proxy"
                                    ]
                                ),

                            "infrastructure_exposure":
                                float(
                                    row[
                                        "infrastructure_exposure"
                                    ]
                                ),

                            "dominant_exposure":
                                str(
                                    row[
                                        "dominant_exposure"
                                    ]
                                ),
                        },

                    "geometry":
                        transform_geometry_to_wgs84(
                            geometry
                        ),
                }
            )

        return {
            "type":
                "FeatureCollection",

            "features":
                output_features,
        }

    # ========================================================
    # HISTORICAL HOTSPOTS
    # ========================================================

    def get_historical_hotspots(self):

        require_file(
            HISTORICAL_FILE
        )

        historical = pd.read_csv(
            HISTORICAL_FILE
        )

        required_columns = {
            "hotspot_id",
            "event_count",
            "latitude",
            "longitude",
            "hotspot_score",
            "hotspot_category",
        }

        missing = (
            required_columns
            - set(
                historical.columns
            )
        )

        if missing:
            raise RuntimeError(
                "Historical hotspot file "
                f"is missing columns: "
                f"{sorted(missing)}"
            )

        output_features = []

        for _, row in (
            historical.iterrows()
        ):

            # The historical engine stores:
            # longitude -> UTM easting
            # latitude  -> UTM northing

            utm_x = float(
                row["longitude"]
            )

            utm_y = float(
                row["latitude"]
            )

            lon, lat = (
                UTM_TO_WGS84.transform(
                    utm_x,
                    utm_y,
                )
            )

            output_features.append(
                {
                    "type":
                        "Feature",

                    "properties":
                        {
                            "hotspot_id":
                                str(
                                    row[
                                        "hotspot_id"
                                    ]
                                ),

                            "event_count":
                                int(
                                    row[
                                        "event_count"
                                    ]
                                ),

                            "hotspot_score":
                                float(
                                    row[
                                        "hotspot_score"
                                    ]
                                ),

                            "hotspot_category":
                                str(
                                    row[
                                        "hotspot_category"
                                    ]
                                ),
                        },

                    "geometry":
                        {
                            "type":
                                "Point",

                            "coordinates":
                                [
                                    float(lon),
                                    float(lat),
                                ],
                        },
                }
            )

        return {
            "type":
                "FeatureCollection",

            "features":
                output_features,
        }

    # ========================================================
    # PRIORITY INCIDENTS
    # ========================================================

    def get_priority_incidents(self):

        require_file(
            PRIORITY_FILE
        )

        incidents = pd.read_csv(
            PRIORITY_FILE
        )

        required_columns = {
            "incident_id",
            "cell_count",
            "max_risk_score",
            "mean_risk_score",
            "max_alert_priority",
            "highest_decision_state",
            "active_alert_cells",
            "latitude",
            "longitude",
            "affected_cells",
            "incident_category",
            "priority_score",
            "priority_level",
            "priority_rank",
            "priority_recommendation",
        }

        missing = (
            required_columns
            - set(
                incidents.columns
            )
        )

        if missing:
            raise RuntimeError(
                "Priority incident file "
                f"is missing columns: "
                f"{sorted(missing)}"
            )

        output_features = []

        for _, row in (
            incidents.iterrows()
        ):

            # Stored values are UTM:
            # longitude -> easting
            # latitude  -> northing

            utm_x = float(
                row["longitude"]
            )

            utm_y = float(
                row["latitude"]
            )

            lon, lat = (
                UTM_TO_WGS84.transform(
                    utm_x,
                    utm_y,
                )
            )

            output_features.append(
                {
                    "type":
                        "Feature",

                    "properties":
                        {
                            "incident_id":
                                str(
                                    row[
                                        "incident_id"
                                    ]
                                ),

                            "cell_count":
                                int(
                                    row[
                                        "cell_count"
                                    ]
                                ),

                            "max_risk_score":
                                float(
                                    row[
                                        "max_risk_score"
                                    ]
                                ),

                            "mean_risk_score":
                                float(
                                    row[
                                        "mean_risk_score"
                                    ]
                                ),

                            "max_alert_priority":
                                float(
                                    row[
                                        "max_alert_priority"
                                    ]
                                ),

                            "highest_decision_state":
                                str(
                                    row[
                                        "highest_decision_state"
                                    ]
                                ),

                            "active_alert_cells":
                                int(
                                    row[
                                        "active_alert_cells"
                                    ]
                                ),

                            "affected_cells":
                                str(
                                    row[
                                        "affected_cells"
                                    ]
                                ),

                            "incident_category":
                                str(
                                    row[
                                        "incident_category"
                                    ]
                                ),

                            "priority_score":
                                float(
                                    row[
                                        "priority_score"
                                    ]
                                ),

                            "priority_level":
                                str(
                                    row[
                                        "priority_level"
                                    ]
                                ),

                            "priority_rank":
                                int(
                                    row[
                                        "priority_rank"
                                    ]
                                ),

                            "priority_recommendation":
                                str(
                                    row[
                                        "priority_recommendation"
                                    ]
                                ),
                        },

                    "geometry":
                        {
                            "type":
                                "Point",

                            "coordinates":
                                [
                                    float(lon),
                                    float(lat),
                                ],
                        },
                }
            )

        return {
            "type":
                "FeatureCollection",

            "features":
                output_features,
        }

    # ========================================================
    # NEARBY CELLS — OPTIMIZED
    # ========================================================

    def get_nearby_cells(
        self,
        latitude: float,
        longitude: float,
        radius_m: float = 5000.0,
    ):
        """
        Fast nearby-cell lookup using the compact risk
        spatial cache.

        The full master grid contains approximately
        1.97 million features, while the active AwareOn
        risk layer contains only the cells required for
        live risk-neighborhood queries.

        Runtime therefore uses:

            risk_spatial_cache.pkl

        instead of rescanning the master grid.
        """

        if radius_m <= 0:
            raise ValueError(
                "radius_m must be greater than 0."
            )

        compact_cache_file = (
            DATA_DIR
            / "cache"
            / "risk_spatial_cache.pkl"
        )

        require_file(
            compact_cache_file
        )

        import pickle

        with compact_cache_file.open(
            "rb"
        ) as file:
            cache = pickle.load(
                file
            )

        records = cache.get(
            "records",
            [],
        )

        if not records:
            return {
                "type":
                    "FeatureCollection",

                "features":
                    [],
            }

        risk_lookup = (
            load_risk_lookup()
        )

        query_x, query_y = (
            WGS84_TO_UTM.transform(
                longitude,
                latitude,
            )
        )

        radius = float(
            radius_m
        )

        min_x = query_x - radius
        max_x = query_x + radius

        min_y = query_y - radius
        max_y = query_y + radius

        radius_squared = (
            radius * radius
        )

        results = []

        for record in records:

            x = float(
                record["x"]
            )

            y = float(
                record["y"]
            )

            if (
                x < min_x
                or x > max_x
                or y < min_y
                or y > max_y
            ):
                continue

            dx = (
                x
                -
                query_x
            )

            dy = (
                y
                -
                query_y
            )

            distance_squared = (
                dx * dx
                +
                dy * dy
            )

            if (
                distance_squared
                >
                radius_squared
            ):
                continue

            cell_id = str(
                record["cell_id"]
            )

            row = (
                risk_lookup.get(
                    cell_id
                )
            )

            if row is None:
                continue

            geometry = record.get(
                "geometry"
            )

            if geometry is None:
                continue

            distance_m = (
                distance_squared
                ** 0.5
            )

            results.append(
                {
                    "type":
                        "Feature",

                    "properties":
                        {
                            "cell_id":
                                cell_id,

                            "unified_risk_score":
                                float(
                                    row[
                                        "unified_risk_score"
                                    ]
                                ),

                            "severity":
                                str(
                                    row[
                                        "severity"
                                    ]
                                ),

                            "warning_state":
                                str(
                                    row[
                                        "warning_state"
                                    ]
                                ),

                            "confidence_score":
                                float(
                                    row[
                                        "confidence_score"
                                    ]
                                ),

                            "distance_m":
                                float(
                                    distance_m
                                ),
                        },

                    "geometry":
                        transform_geometry_to_wgs84(
                            geometry
                        ),
                }
            )

        results.sort(
            key=lambda item:
                item[
                    "properties"
                ][
                    "distance_m"
                ]
        )

        return {
            "type":
                "FeatureCollection",

            "features":
                results,
        }


# ============================================================
# SERVICE INSTANCE
# ============================================================

gis_service = GISService()

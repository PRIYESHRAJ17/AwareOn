from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = ROOT / "data" / "processed"

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

INTELLIGENCE_DIR = (
    DATA_DIR
    / "intelligence"
)

RISK_FILE = (
    INTELLIGENCE_DIR
    / "awareon_risk_decisions.csv"
)


# ============================================================
# GIS SERVICE
# ============================================================

class GISService:

    def load_grid(self):

        if not GRID_FILE.exists():
            raise FileNotFoundError(
                f"Grid file not found: {GRID_FILE}"
            )

        grid = gpd.read_file(
            GRID_FILE
        )

        if grid.crs is None:
            grid = grid.set_crs(
                "EPSG:32645"
            )

        return grid

    def get_cell(
        self,
        cell_id: str,
    ):

        grid = self.load_grid()

        grid["cell_id"] = (
            grid["cell_id"].astype(str)
        )

        matches = grid[
            grid["cell_id"] == str(cell_id)
        ]

        if matches.empty:
            return None

        row = matches.iloc[0]

        geometry = row.geometry
        centroid = geometry.centroid

        return {
            "cell_id": str(
                row["cell_id"]
            ),
            "centroid_x": float(
                centroid.x
            ),
            "centroid_y": float(
                centroid.y
            ),
            "geometry": (
                geometry
                .__geo_interface__
            ),
        }

    def get_boundary(self):

        if not BOUNDARY_FILE.exists():
            raise FileNotFoundError(
                f"Boundary file not found: "
                f"{BOUNDARY_FILE}"
            )

        boundary = gpd.read_file(
            BOUNDARY_FILE
        )

        if boundary.crs is None:
            boundary = boundary.set_crs(
                "EPSG:4326"
            )

        boundary = boundary.to_crs(
            "EPSG:4326"
        )

        return boundary.__geo_interface__

    def get_risk_layer(self):

        if not RISK_FILE.exists():
            raise FileNotFoundError(
                f"Risk file not found: "
                f"{RISK_FILE}"
            )

        grid = self.load_grid()

        risk = pd.read_csv(
            RISK_FILE
        )

        grid["cell_id"] = (
            grid["cell_id"].astype(str)
        )

        risk["cell_id"] = (
            risk["cell_id"].astype(str)
        )

        merged = grid.merge(
            risk[
                [
                    "cell_id",
                    "unified_risk_score",
                    "severity",
                    "warning_state",
                    "confidence_score",
                ]
            ],
            on="cell_id",
            how="inner",
        )

        if merged.empty:
            raise RuntimeError(
                "No grid cells matched risk data."
            )

        merged = merged.to_crs(
            "EPSG:4326"
        )

        return (
            merged[
                [
                    "cell_id",
                    "unified_risk_score",
                    "severity",
                    "warning_state",
                    "confidence_score",
                    "geometry",
                ]
            ]
            .__geo_interface__
        )

    def get_nearby_cells(
        self,
        latitude: float,
        longitude: float,
        radius_m: float = 5000.0,
    ):

        if radius_m <= 0:
            raise ValueError(
                "radius_m must be greater than 0."
            )

        grid = self.load_grid()

        if not RISK_FILE.exists():
            raise FileNotFoundError(
                f"Risk file not found: "
                f"{RISK_FILE}"
            )

        risk = pd.read_csv(
            RISK_FILE
        )

        grid["cell_id"] = (
            grid["cell_id"].astype(str)
        )

        risk["cell_id"] = (
            risk["cell_id"].astype(str)
        )

        merged = grid.merge(
            risk[
                [
                    "cell_id",
                    "unified_risk_score",
                    "severity",
                    "warning_state",
                    "confidence_score",
                ]
            ],
            on="cell_id",
            how="inner",
        )

        if merged.empty:
            raise RuntimeError(
                "No grid cells matched risk data."
            )

        query_point = (
            gpd.GeoSeries(
                [
                    gpd.points_from_xy(
                        [longitude],
                        [latitude],
                    )[0]
                ],
                crs="EPSG:4326",
            )
            .to_crs("EPSG:32645")
            .iloc[0]
        )

        centroids = (
            merged.geometry.centroid
        )

        distances = centroids.distance(
            query_point
        )

        nearby = merged[
            distances <= radius_m
        ].copy()

        if nearby.empty:

            empty = merged.iloc[0:0].copy()

            empty["distance_m"] = pd.Series(
                dtype="float64"
            )

            nearby = empty

        else:

            nearby["distance_m"] = (
                distances[
                    nearby.index
                ].to_numpy()
            )

        nearby = nearby.sort_values(
            "distance_m"
        )

        nearby = nearby.to_crs(
            "EPSG:4326"
        )

        return (
            nearby[
                [
                    "cell_id",
                    "unified_risk_score",
                    "severity",
                    "warning_state",
                    "confidence_score",
                    "distance_m",
                    "geometry",
                ]
            ]
            .__geo_interface__
        )


# ============================================================
# SERVICE INSTANCE
# ============================================================

gis_service = GISService()

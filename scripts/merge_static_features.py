from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = ROOT / "data/processed/grid/master_grid_100m.geojson"
TERRAIN_FILE = ROOT / "data/processed/features/ground_truth_terrain_features.csv"
OSM_FILE = ROOT / "data/processed/grid/osm_sikkim_clipped_utm45.geojson"

OUT_DIR = ROOT / "data/processed/features"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "static_ml_features.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

print("Loading grid...")
grid = gpd.read_file(GRID_FILE).to_crs("EPSG:32645")
grid["cell_id"] = grid["cell_id"].astype(str)

print("Loading terrain features...")
terrain = pd.read_csv(TERRAIN_FILE)
terrain["cell_id"] = terrain["cell_id"].astype(str)

print("Loading OSM...")
osm = gpd.read_file(OSM_FILE).to_crs("EPSG:32645")


# ------------------------------------------------------------
# Load labels
# ------------------------------------------------------------

POS_FILE = ROOT / "data/processed/ground_truth/positive_cells.csv"
NEG_FILE = ROOT / "data/processed/ground_truth/negative_cells.csv"

positive = pd.read_csv(POS_FILE)[["cell_id", "label"]].copy()
negative = pd.read_csv(NEG_FILE)[["cell_id", "label"]].copy()

labels = pd.concat(
    [positive, negative],
    ignore_index=True,
)

labels["cell_id"] = labels["cell_id"].astype(str)


# ------------------------------------------------------------
# Build base 1,298-cell dataset
# ------------------------------------------------------------

data = grid[["cell_id", "geometry"]].merge(
    labels,
    on="cell_id",
    how="inner",
)

data = data.merge(
    terrain,
    on=["cell_id", "label"],
    how="inner",
)

if len(data) != 1298:
    raise RuntimeError(
        f"Expected 1298 labelled cells, got {len(data)}"
    )

print("Base labelled cells:", len(data))


# ------------------------------------------------------------
# Identify OSM families
# ------------------------------------------------------------

def has_column(gdf, column):
    if column not in gdf.columns:
        return pd.Series(False, index=gdf.index)

    return (
        gdf[column].notna()
        & gdf[column].astype(str).str.strip().ne("")
    )


roads = osm.loc[
    has_column(osm, "highway")
].copy()

settlements = osm.loc[
    has_column(osm, "place")
].copy()

amenities = osm.loc[
    has_column(osm, "amenity")
].copy()


# Convert area geometries to representative points for
# meaningful distance calculations.
settlements["geometry"] = settlements.geometry.apply(
    lambda geom: (
        geom.representative_point()
        if geom is not None and not geom.is_empty
        else None
    )
)

amenities["geometry"] = amenities.geometry.apply(
    lambda geom: (
        geom.representative_point()
        if geom is not None and not geom.is_empty
        else None
    )
)

settlements = settlements[
    settlements.geometry.notna()
    & ~settlements.geometry.is_empty
].copy()

amenities = amenities[
    amenities.geometry.notna()
    & ~amenities.geometry.is_empty
].copy()


print("\nOSM features:")
print("Roads:", len(roads))
print("Settlements:", len(settlements))
print("Amenities:", len(amenities))


# ------------------------------------------------------------
# Cell centroids
# ------------------------------------------------------------

centroids = data.copy()
centroids["geometry"] = centroids.geometry.centroid


# ------------------------------------------------------------
# Nearest-distance helper
# ------------------------------------------------------------

def nearest_distance(points, targets):

    result = pd.Series(
        np.nan,
        index=points.index,
        dtype="float64",
    )

    if targets.empty:
        return result

    joined = gpd.sjoin_nearest(
        points[["geometry"]],
        targets[["geometry"]],
        how="left",
        distance_col="_distance_m",
    )

    minimum = (
        joined
        .groupby(joined.index)["_distance_m"]
        .min()
    )

    result.loc[minimum.index] = minimum

    return result


# ------------------------------------------------------------
# Nearest road
# ------------------------------------------------------------

print("\nCalculating road distance...")

data["road_distance_m"] = nearest_distance(
    centroids,
    roads,
)


# ------------------------------------------------------------
# Nearest settlement
# ------------------------------------------------------------

print("Calculating settlement distance...")

data["settlement_distance_m"] = nearest_distance(
    centroids,
    settlements,
)


# ------------------------------------------------------------
# Nearest amenity
# ------------------------------------------------------------

print("Calculating amenity distance...")

data["amenity_distance_m"] = nearest_distance(
    centroids,
    amenities,
)


# ------------------------------------------------------------
# Road density in 500 m radius
# ------------------------------------------------------------

print("Calculating road density...")

road_lines = roads[
    roads.geometry.geom_type.isin(
        ["LineString", "MultiLineString"]
    )
].copy()

road_density = []

for point in centroids.geometry:

    area = point.buffer(500)

    nearby = road_lines[
        road_lines.geometry.intersects(area)
    ]

    if nearby.empty:
        road_density.append(0.0)
    else:
        total_km = nearby.geometry.length.sum() / 1000.0
        area_km2 = np.pi * (0.5 ** 2)

        road_density.append(
            total_km / area_km2
        )

data["road_density_500m_km_per_km2"] = road_density


# ------------------------------------------------------------
# Settlements within 1 km
# ------------------------------------------------------------

print("Calculating settlements within 1 km...")

settlement_counts = []

for point in centroids.geometry:

    count = int(
        settlements.geometry
        .distance(point)
        .le(1000)
        .sum()
    )

    settlement_counts.append(count)

data["settlements_within_1km"] = settlement_counts


# ------------------------------------------------------------
# Amenities within 1 km
# ------------------------------------------------------------

print("Calculating amenities within 1 km...")

amenity_counts = []

for point in centroids.geometry:

    count = int(
        amenities.geometry
        .distance(point)
        .le(1000)
        .sum()
    )

    amenity_counts.append(count)

data["amenities_within_1km"] = amenity_counts


# ------------------------------------------------------------
# Exposure flags
# ------------------------------------------------------------

data["near_road_250m"] = (
    data["road_distance_m"] <= 250
).astype(int)

data["near_settlement_1km"] = (
    data["settlement_distance_m"] <= 1000
).astype(int)

data["near_amenity_1km"] = (
    data["amenity_distance_m"] <= 1000
).astype(int)


# ------------------------------------------------------------
# OSM availability
# ------------------------------------------------------------

data["osm_context_available"] = (
    data["road_distance_m"].notna()
    | data["settlement_distance_m"].notna()
    | data["amenity_distance_m"].notna()
).astype(int)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

osm_columns = [
    "road_distance_m",
    "settlement_distance_m",
    "amenity_distance_m",
    "road_density_500m_km_per_km2",
    "settlements_within_1km",
    "amenities_within_1km",
    "near_road_250m",
    "near_settlement_1km",
    "near_amenity_1km",
]

print("\n========================================")
print("STATIC FEATURE MERGE")
print("========================================")

print("Rows:", len(data))

print("\nMissing OSM values:")
print(
    data[osm_columns]
    .isna()
    .sum()
    .to_string()
)

print(
    "\nCells with OSM context:",
    int(data["osm_context_available"].sum())
)

print("\nLabels:")
print(
    data["label"]
    .value_counts()
    .sort_index()
    .to_string()
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output = data.drop(
    columns="geometry"
)

output.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


print("\nOutput:")
print(OUTPUT)

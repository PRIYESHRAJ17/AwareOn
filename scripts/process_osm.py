from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

OSM_FILE = ROOT / "data/processed/grid/osm_sikkim_clipped_utm45.geojson"
GSI_FILE = ROOT / "data/processed/landslides/gsi_sikkim_inventory_clean.geojson"

OUT_DIR = ROOT / "data/processed/landslides"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUT_DIR / "gsi_inventory_with_osm_features.csv"
OUTPUT_GEOJSON = OUT_DIR / "gsi_inventory_with_osm_features.geojson"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

print("Loading OSM...")
osm = gpd.read_file(OSM_FILE)

print("Loading GSI inventory...")
gsi = gpd.read_file(GSI_FILE)

if osm.empty:
    raise RuntimeError("OSM dataset is empty.")

if gsi.empty:
    raise RuntimeError("GSI inventory is empty.")


# ------------------------------------------------------------
# CRS
# ------------------------------------------------------------

if osm.crs is None:
    raise RuntimeError("OSM CRS is missing.")

if gsi.crs is None:
    raise RuntimeError("GSI CRS is missing.")

osm = osm.to_crs("EPSG:32645")
gsi = gsi.to_crs("EPSG:32645")

print("OSM features:", len(osm))
print("GSI points:", len(gsi))


# ------------------------------------------------------------
# Identify feature families
# ------------------------------------------------------------

def has_values(gdf, column):
    if column not in gdf.columns:
        return pd.Series(False, index=gdf.index)

    return (
        gdf[column].notna()
        & gdf[column].astype(str).str.strip().ne("")
    )


roads = osm.loc[has_values(osm, "highway")].copy()
settlements = osm.loc[has_values(osm, "place")].copy()
amenities = osm.loc[has_values(osm, "amenity")].copy()

print("\nFeature families:")
print("Roads:", len(roads))
print("Settlements:", len(settlements))
print("Amenities:", len(amenities))


# ------------------------------------------------------------
# Clean settlement geometries
# ------------------------------------------------------------

# Settlement features can be points, lines, or polygons.
# representative_point() produces a point guaranteed to lie
# inside the original geometry and avoids zero-distance artifacts
# caused by polygon containment.

settlements = settlements.copy()

settlements["geometry"] = settlements.geometry.apply(
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


# Amenities may also contain polygons. Convert them to representative points.
amenities = amenities.copy()

amenities["geometry"] = amenities.geometry.apply(
    lambda geom: (
        geom.representative_point()
        if geom is not None and not geom.is_empty
        else None
    )
)

amenities = amenities[
    amenities.geometry.notna()
    & ~amenities.geometry.is_empty
].copy()


# ------------------------------------------------------------
# Helper: nearest distance
# ------------------------------------------------------------

def nearest_distance(points, targets):
    result = pd.Series(
        float("nan"),
        index=points.index,
        dtype="float64",
    )

    if targets.empty:
        return result

    targets = targets[
        targets.geometry.notna()
        & ~targets.geometry.is_empty
    ].copy()

    if targets.empty:
        return result

    joined = gpd.sjoin_nearest(
        points[["geometry"]],
        targets[["geometry"]],
        how="left",
        distance_col="_distance_m",
    )

    minimum = joined.groupby(
        joined.index
    )["_distance_m"].min()

    result.loc[minimum.index] = minimum

    return result


# ------------------------------------------------------------
# Nearest distances
# ------------------------------------------------------------

print("\nCalculating nearest-road distance...")

gsi["road_distance_m"] = nearest_distance(
    gsi,
    roads,
)

print("Calculating nearest-settlement distance...")

gsi["settlement_distance_m"] = nearest_distance(
    gsi,
    settlements,
)

print("Calculating nearest-amenity distance...")

gsi["amenity_distance_m"] = nearest_distance(
    gsi,
    amenities,
)


# ------------------------------------------------------------
# Local road density within 500 m
# ------------------------------------------------------------

print("\nCalculating local road density...")

road_lines = roads[
    roads.geometry.geom_type.isin(
        ["LineString", "MultiLineString"]
    )
].copy()

road_density = []

for point in gsi.geometry:

    buffer_500 = point.buffer(500)

    nearby = road_lines[
        road_lines.geometry.intersects(buffer_500)
    ]

    if nearby.empty:
        road_density.append(0.0)
        continue

    total_length_m = nearby.geometry.length.sum()

    # Circular 500 m neighbourhood = π * 0.5² km².
    area_km2 = 3.141592653589793 * (0.5 ** 2)

    density = (
        (total_length_m / 1000.0)
        / area_km2
    )

    road_density.append(float(density))


gsi["road_density_500m_km_per_km2"] = road_density


# ------------------------------------------------------------
# Settlements within 1 km
# ------------------------------------------------------------

print("Calculating settlements within 1 km...")

settlement_counts = []

for point in gsi.geometry:

    count = int(
        settlements.geometry.distance(point)
        .le(1000)
        .sum()
    )

    settlement_counts.append(count)


gsi["settlements_within_1km"] = settlement_counts


# ------------------------------------------------------------
# Amenities within 1 km
# ------------------------------------------------------------

print("Calculating amenities within 1 km...")

amenity_counts = []

for point in gsi.geometry:

    count = int(
        amenities.geometry.distance(point)
        .le(1000)
        .sum()
    )

    amenity_counts.append(count)


gsi["amenities_within_1km"] = amenity_counts


# ------------------------------------------------------------
# Exposure flags
# ------------------------------------------------------------

gsi["near_road_250m"] = (
    gsi["road_distance_m"] <= 250
).astype(int)

gsi["near_settlement_1km"] = (
    gsi["settlement_distance_m"] <= 1000
).astype(int)

gsi["near_amenity_1km"] = (
    gsi["amenity_distance_m"] <= 1000
).astype(int)


# ------------------------------------------------------------
# Sanity checks
# ------------------------------------------------------------

for column in [
    "road_distance_m",
    "settlement_distance_m",
    "amenity_distance_m",
]:

    gsi.loc[
        gsi[column] < 0,
        column,
    ] = pd.NA


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_geo = gsi.to_crs("EPSG:4326")

output_geo.drop(
    columns="geometry"
).to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8",
)

output_geo.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("OSM EXPOSURE PROCESSING COMPLETE")
print("========================================")

print("GSI records:", len(gsi))

print("\nFeature counts:")
print("Roads:", len(roads))
print("Settlements:", len(settlements))
print("Amenities:", len(amenities))

print("\nDistance statistics (metres):")
print(
    gsi[
        [
            "road_distance_m",
            "settlement_distance_m",
            "amenity_distance_m",
        ]
    ].describe().to_string()
)

print("\nExposure indicators:")
print(
    gsi[
        [
            "near_road_250m",
            "near_settlement_1km",
            "near_amenity_1km",
        ]
    ].sum().to_string()
)

print("\nOutputs:")
print(OUTPUT_CSV)
print(OUTPUT_GEOJSON)

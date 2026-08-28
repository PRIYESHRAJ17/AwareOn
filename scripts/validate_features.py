from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data/processed/features/static_ml_features.csv"
OUT_DIR = ROOT / "data/processed/features"

OUTPUT = OUT_DIR / "static_ml_features_validated.csv"


df = pd.read_csv(INPUT)


# ------------------------------------------------------------
# Required columns
# ------------------------------------------------------------

required = [
    "cell_id",
    "label",
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "elevation_std_m",
    "aspect_sin",
    "aspect_cos",
    "terrain_imputed",
    "road_distance_m",
    "settlement_distance_m",
    "amenity_distance_m",
    "road_density_500m_km_per_km2",
    "settlements_within_1km",
    "amenities_within_1km",
    "near_road_250m",
    "near_settlement_1km",
    "near_amenity_1km",
    "osm_context_available",
]

missing_columns = [
    c for c in required
    if c not in df.columns
]

if missing_columns:
    raise RuntimeError(
        f"Missing columns: {missing_columns}"
    )


# ------------------------------------------------------------
# Duplicate check
# ------------------------------------------------------------

duplicate_cells = int(
    df["cell_id"].duplicated().sum()
)

if duplicate_cells:
    raise RuntimeError(
        f"Duplicate cell IDs: {duplicate_cells}"
    )


# ------------------------------------------------------------
# Numeric features
# ------------------------------------------------------------

feature_columns = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "elevation_std_m",
    "aspect_sin",
    "aspect_cos",
    "terrain_imputed",
    "road_distance_m",
    "settlement_distance_m",
    "amenity_distance_m",
    "road_density_500m_km_per_km2",
    "settlements_within_1km",
    "amenities_within_1km",
    "near_road_250m",
    "near_settlement_1km",
    "near_amenity_1km",
    "osm_context_available",
]

for column in feature_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# ------------------------------------------------------------
# Missing / infinite checks
# ------------------------------------------------------------

missing_counts = df[feature_columns].isna().sum()

infinite_counts = pd.Series(
    {
        c: int(np.isinf(df[c]).sum())
        for c in feature_columns
    }
)

if missing_counts.sum() > 0:
    raise RuntimeError(
        "Missing feature values found:\n"
        + missing_counts[
            missing_counts > 0
        ].to_string()
    )

if infinite_counts.sum() > 0:
    raise RuntimeError(
        "Infinite feature values found:\n"
        + infinite_counts[
            infinite_counts > 0
        ].to_string()
    )


# ------------------------------------------------------------
# Label checks
# ------------------------------------------------------------

labels = set(
    df["label"].dropna().astype(int)
)

if labels != {0, 1}:
    raise RuntimeError(
        f"Expected labels {{0,1}}, got {labels}"
    )


# ------------------------------------------------------------
# Range checks
# ------------------------------------------------------------

if not df["slope_deg"].between(0, 90).all():
    raise RuntimeError("Invalid slope values.")

if not df["aspect_deg"].between(0, 360).all():
    raise RuntimeError("Invalid aspect values.")

for column in [
    "road_distance_m",
    "settlement_distance_m",
    "amenity_distance_m",
    "road_density_500m_km_per_km2",
    "settlements_within_1km",
    "amenities_within_1km",
]:
    if (df[column] < 0).any():
        raise RuntimeError(
            f"Negative values found in {column}"
        )


# ------------------------------------------------------------
# Constant-feature detection
# ------------------------------------------------------------

constant_features = [
    c
    for c in feature_columns
    if df[c].nunique(dropna=False) <= 1
]


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

df[required].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STATIC FEATURE VALIDATION")
print("========================================")

print("Rows:", len(df))
print("Columns:", len(required))

print(
    "Unique cell IDs:",
    df["cell_id"].nunique(),
)

print(
    "Positive:",
    int((df["label"] == 1).sum()),
)

print(
    "Negative:",
    int((df["label"] == 0).sum()),
)

print(
    "Missing feature values:",
    int(missing_counts.sum()),
)

print(
    "Infinite feature values:",
    int(infinite_counts.sum()),
)

print(
    "Constant features:",
    constant_features
)

print("\nFeature columns:")

for column in feature_columns:
    print(" -", column)

print("\nVALIDATION PASSED ✅")

print("\nOutput:")
print(OUTPUT)

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "exposure_impact_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)

if df.empty:
    raise RuntimeError("Feature dataset is empty.")


# ------------------------------------------------------------
# Distance-based exposure
# ------------------------------------------------------------

def inverse_distance(distance, scale):
    distance = pd.to_numeric(
        distance,
        errors="coerce",
    )

    return 1.0 / (
        1.0 + distance / scale
    )


road_proximity = inverse_distance(
    df["road_distance_m"],
    500.0,
)

settlement_proximity = inverse_distance(
    df["settlement_distance_m"],
    1000.0,
)

amenity_proximity = inverse_distance(
    df["amenity_distance_m"],
    1000.0,
)


# ------------------------------------------------------------
# Density/count components
# ------------------------------------------------------------

road_density = (
    df["road_density_500m_km_per_km2"]
    .rank(pct=True)
)

settlement_density = (
    df["settlements_within_1km"]
    .rank(pct=True)
)

amenity_density = (
    df["amenities_within_1km"]
    .rank(pct=True)
)


# ------------------------------------------------------------
# Exposure score
# ------------------------------------------------------------

df["exposure_score"] = (
    0.30 * road_proximity
    + 0.20 * settlement_proximity
    + 0.15 * amenity_proximity
    + 0.15 * road_density
    + 0.10 * settlement_density
    + 0.10 * amenity_density
) * 100.0


# ------------------------------------------------------------
# Impact components
# ------------------------------------------------------------

df["transport_exposure"] = (
    0.70 * road_proximity
    + 0.30 * road_density
) * 100.0

df["population_exposure_proxy"] = (
    0.70 * settlement_proximity
    + 0.30 * settlement_density
) * 100.0

df["infrastructure_exposure"] = (
    0.60 * amenity_proximity
    + 0.40 * amenity_density
) * 100.0


# ------------------------------------------------------------
# Impact category
# ------------------------------------------------------------

def classify(score):

    if score < 25:
        return "LOW"

    if score < 50:
        return "MODERATE"

    if score < 75:
        return "HIGH"

    return "VERY_HIGH"


df["exposure_category"] = (
    df["exposure_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Dominant exposure type
# ------------------------------------------------------------

component_columns = [
    "transport_exposure",
    "population_exposure_proxy",
    "infrastructure_exposure",
]

df["dominant_exposure"] = (
    df[component_columns]
    .idxmax(axis=1)
    .map(
        {
            "transport_exposure": "TRANSPORT",
            "population_exposure_proxy": "SETTLEMENT",
            "infrastructure_exposure": "INFRASTRUCTURE",
        }
    )
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "exposure_score",
    "exposure_category",
    "transport_exposure",
    "population_exposure_proxy",
    "infrastructure_exposure",
    "dominant_exposure",
]


df[output_columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 08")
print("EXPOSURE & IMPACT ENGINE")
print("========================================")

print(
    "Cells processed:",
    len(df),
)

print("\nExposure categories:")
print(
    df["exposure_category"]
    .value_counts()
    .to_string()
)

print("\nExposure statistics:")
print(
    df["exposure_score"]
    .describe()
    .to_string()
)

print("\nDominant exposure:")
print(
    df["dominant_exposure"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 08 COMPLETE ✅")

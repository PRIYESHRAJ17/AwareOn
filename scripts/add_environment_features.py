from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data/processed/features/ground_truth_terrain_features.csv"
)

ERA5 = (
    ROOT
    / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/features"
OUTPUT = OUT_DIR / "ground_truth_environment_features.csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

features = pd.read_csv(INPUT)
era5 = pd.read_csv(ERA5)

required_feature_columns = {
    "cell_id",
    "label",
}

required_era5_columns = {
    "valid_time",
    "latitude",
    "longitude",
    "precip_mm",
    "swvl1",
    "swvl2",
    "rain_24h_mm",
    "rain_72h_mm",
    "rain_7d_mm",
}

missing_features = (
    required_feature_columns
    - set(features.columns)
)

missing_era5 = (
    required_era5_columns
    - set(era5.columns)
)

if missing_features:
    raise RuntimeError(
        f"Missing feature columns: {missing_features}"
    )

if missing_era5:
    raise RuntimeError(
        f"Missing ERA5 columns: {missing_era5}"
    )


# ------------------------------------------------------------
# Verify ERA5 location consistency
# ------------------------------------------------------------

lat = era5["latitude"].astype(float)
lon = era5["longitude"].astype(float)

if not ((lat - 27.5).abs() < 0.01).all():
    raise RuntimeError(
        "ERA5 latitude is not the expected 27.5 N point."
    )

if not ((lon - 88.5).abs() < 0.01).all():
    raise RuntimeError(
        "ERA5 longitude is not the expected 88.5 E point."
    )


# ------------------------------------------------------------
# Create representative current environmental snapshot
# ------------------------------------------------------------
#
# The 1,298 static grid samples do not have individual event
# timestamps. Therefore we attach a clearly defined reference
# environmental snapshot rather than inventing per-cell event
# dates.
#
# Reference = latest timestamp available in the ERA5 dataset.
# ------------------------------------------------------------

era5["valid_time"] = pd.to_datetime(
    era5["valid_time"],
    errors="coerce",
)

era5 = era5.sort_values(
    "valid_time"
).reset_index(drop=True)

reference = era5.iloc[-1]


environment_columns = [
    "precip_mm",
    "rain_24h_mm",
    "rain_72h_mm",
    "rain_7d_mm",
    "swvl1",
    "swvl2",
]

for column in environment_columns:
    features[column] = float(reference[column])


# Environmental reference metadata
features["environment_time"] = reference["valid_time"]

features["environment_latitude"] = float(
    reference["latitude"]
)

features["environment_longitude"] = float(
    reference["longitude"]
)


# ------------------------------------------------------------
# Missing-value check
# ------------------------------------------------------------

missing = features[
    environment_columns
].isna().sum()

print("\nMissing environmental values:")
print(missing.to_string())


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

features.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 14.2 ENVIRONMENT FEATURES COMPLETE")
print("========================================")

print("Rows:", len(features))

print(
    "Reference environment time:",
    reference["valid_time"],
)

print(
    "Reference location:",
    reference["latitude"],
    reference["longitude"],
)

print("\nEnvironmental values:")
for column in environment_columns:
    print(
        f"{column}:",
        float(reference[column])
    )

print("\nOutput:")
print(OUTPUT)

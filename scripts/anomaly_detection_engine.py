from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ERA5_FILE = (
    ROOT / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "anomaly_detection_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

era5 = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

if era5.empty:
    raise RuntimeError("ERA5 dataset is empty.")

era5 = era5.sort_values(
    "valid_time"
).reset_index(drop=True)


latest = era5.iloc[-1]


# ------------------------------------------------------------
# Variables
# ------------------------------------------------------------

variables = {
    "rain_24h_mm": "24h rainfall",
    "rain_72h_mm": "72h rainfall",
    "rain_7d_mm": "7-day rainfall",
    "swvl1": "soil water layer 1",
    "swvl2": "soil water layer 2",
}


# ------------------------------------------------------------
# Z-score helper
# ------------------------------------------------------------

def z_score(series, value):

    mean = float(series.mean())
    std = float(series.std())

    if std == 0:
        return 0.0

    return (float(value) - mean) / std


results = []

for column, description in variables.items():

    z = z_score(
        era5[column],
        latest[column],
    )

    percentile = float(
        (era5[column] <= latest[column]).mean()
    )

    results.append(
        {
            "feature": column,
            "description": description,
            "current_value": float(latest[column]),
            "historical_mean": float(era5[column].mean()),
            "historical_std": float(era5[column].std()),
            "percentile": percentile,
            "z_score": z,
            "absolute_z_score": abs(z),
        }
    )


diagnostics = pd.DataFrame(results)


# ------------------------------------------------------------
# Overall anomaly score
# ------------------------------------------------------------

# Rainfall is given slightly greater weight because it is the
# primary short-term trigger signal in this prototype.

rainfall_anomaly = (
    diagnostics[
        diagnostics["feature"].isin(
            [
                "rain_24h_mm",
                "rain_72h_mm",
                "rain_7d_mm",
            ]
        )
        ]["absolute_z_score"]
        .mean()
)

soil_anomaly = (
    diagnostics[
        diagnostics["feature"].isin(
            [
                "swvl1",
                "swvl2",
            ]
        )
        ]["absolute_z_score"]
        .mean()
)

overall_z = (
    0.70 * rainfall_anomaly
    + 0.30 * soil_anomaly
)


# Convert to 0-100 score.
anomaly_score = min(
    100.0,
    overall_z * 25.0,
)


# ------------------------------------------------------------
# Category
# ------------------------------------------------------------

if anomaly_score < 25:
    category = "NORMAL"

elif anomaly_score < 50:
    category = "WATCH"

elif anomaly_score < 75:
    category = "UNUSUAL"

else:
    category = "EXTREME"


# ------------------------------------------------------------
# Dominant anomaly
# ------------------------------------------------------------

dominant = diagnostics.sort_values(
    "absolute_z_score",
    ascending=False,
).iloc[0]


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

output = pd.DataFrame(
    [
        {
            "timestamp": latest["valid_time"],
            "latitude": latest["latitude"],
            "longitude": latest["longitude"],
            "rainfall_anomaly_score": rainfall_anomaly,
            "soil_anomaly_score": soil_anomaly,
            "overall_anomaly_z": overall_z,
            "anomaly_score": anomaly_score,
            "anomaly_category": category,
            "dominant_anomaly": dominant["feature"],
            "dominant_anomaly_z": dominant["z_score"],
        }
    ]
)


# ------------------------------------------------------------
# Detailed diagnostics
# ------------------------------------------------------------

diagnostic_output = (
    OUT_DIR
    / "anomaly_feature_diagnostics.csv"
)

diagnostics.to_csv(
    diagnostic_output,
    index=False,
)

output.to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 07")
print("CHANGE / ANOMALY DETECTION")
print("========================================")

print(
    "Timestamp:",
    latest["valid_time"],
)

print(
    "Location:",
    latest["latitude"],
    latest["longitude"],
)

print("\nFeature diagnostics:")

print(
    diagnostics[
        [
            "feature",
            "current_value",
            "percentile",
            "z_score",
        ]
    ].to_string(index=False)
)

print(
    "\nRainfall anomaly:",
    round(rainfall_anomaly, 4),
)

print(
    "Soil anomaly:",
    round(soil_anomaly, 4),
)

print(
    "Overall anomaly z:",
    round(overall_z, 4),
)

print(
    "Anomaly score:",
    round(anomaly_score, 2),
)

print(
    "Category:",
    category,
)

print(
    "Dominant anomaly:",
    dominant["feature"],
)

print("\nOutput:")
print(OUTPUT)

print("\nDiagnostics:")
print(diagnostic_output)

print("\nENGINE 07 COMPLETE ✅")

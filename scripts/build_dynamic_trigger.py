from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

EVENT_FILE = (
    ROOT
    / "data/processed/dynamic/dynamic_event_features.csv"
)

ERA5_FILE = (
    ROOT
    / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/dynamic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVENT_OUTPUT = (
    OUT_DIR / "dynamic_event_trigger_scores.csv"
)

THRESHOLD_OUTPUT = (
    OUT_DIR / "dynamic_trigger_thresholds.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

events = pd.read_csv(EVENT_FILE)

era5 = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

if events.empty:
    raise RuntimeError("No dynamic event features found.")

if era5.empty:
    raise RuntimeError("ERA5 dataset is empty.")


# ------------------------------------------------------------
# Historical reference distributions
# ------------------------------------------------------------

rain_24_thresholds = era5["rain_24h_mm"].quantile(
    [0.50, 0.75, 0.90, 0.95, 0.99]
)

rain_72_thresholds = era5["rain_72h_mm"].quantile(
    [0.50, 0.75, 0.90, 0.95, 0.99]
)

rain_7d_thresholds = era5["rain_7d_mm"].quantile(
    [0.50, 0.75, 0.90, 0.95, 0.99]
)

soil1_thresholds = era5["swvl1"].quantile(
    [0.50, 0.75, 0.90, 0.95, 0.99]
)

soil2_thresholds = era5["swvl2"].quantile(
    [0.50, 0.75, 0.90, 0.95, 0.99]
)


# ------------------------------------------------------------
# Percentile score helper
# ------------------------------------------------------------

def percentile_score(value, thresholds):
    """
    Convert a value into an interpretable 0-100 score.
    """

    if value <= thresholds.loc[0.50]:
        return 0.0

    if value <= thresholds.loc[0.75]:
        return 25.0

    if value <= thresholds.loc[0.90]:
        return 50.0

    if value <= thresholds.loc[0.95]:
        return 75.0

    if value <= thresholds.loc[0.99]:
        return 90.0

    return 100.0


# ------------------------------------------------------------
# Build event trigger scores
# ------------------------------------------------------------

rows = []

for _, event in events.iterrows():

    rain24_score = percentile_score(
        event["rain_24h_event_mm"],
        rain_24_thresholds,
    )

    rain72_score = percentile_score(
        event["rain_72h_event_mm"],
        rain_72_thresholds,
    )

    rain7d_score = percentile_score(
        event["rain_7d_event_mm"],
        rain_7d_thresholds,
    )

    soil1_score = percentile_score(
        event["swvl1_event"],
        soil1_thresholds,
    )

    soil2_score = percentile_score(
        event["swvl2_event"],
        soil2_thresholds,
    )

    # --------------------------------------------------------
    # Positive soil-moisture change contributes to trigger
    # --------------------------------------------------------

    soil_change_score = 0.0

    if event["swvl1_change_72h"] > 0:
        soil_change_score += min(
            50.0,
            float(event["swvl1_change_72h"]) * 500.0,
        )

    if event["swvl2_change_72h"] > 0:
        soil_change_score += min(
            50.0,
            float(event["swvl2_change_72h"]) * 500.0,
        )

    soil_change_score = min(
        100.0,
        soil_change_score,
    )

    # --------------------------------------------------------
    # Composite trigger
    # --------------------------------------------------------

    rainfall_score = (
        0.40 * rain24_score
        + 0.30 * rain72_score
        + 0.20 * rain7d_score
        + 0.10 * min(
            100.0,
            event["peak_hourly_rain_mm"] * 10.0,
        )
    )

    soil_score = (
        0.40 * soil1_score
        + 0.30 * soil2_score
        + 0.30 * soil_change_score
    )

    trigger_score = (
        0.65 * rainfall_score
        + 0.35 * soil_score
    )

    # --------------------------------------------------------
    # Trigger category
    # --------------------------------------------------------

    if trigger_score < 25:
        category = "LOW"

    elif trigger_score < 50:
        category = "MODERATE"

    elif trigger_score < 75:
        category = "HIGH"

    else:
        category = "EXTREME"

    rows.append(
        {
            "record_id": event["record_id"],
            "landslide_id": event["landslide_id"],
            "event_date": event["event_date"],
            "rainfall_score": rainfall_score,
            "soil_score": soil_score,
            "soil_change_score": soil_change_score,
            "trigger_score": trigger_score,
            "trigger_category": category,
        }
    )


result = pd.DataFrame(rows)


# ------------------------------------------------------------
# Save threshold metadata
# ------------------------------------------------------------

threshold_rows = []

for name, series in [
    ("rain_24h_mm", rain_24_thresholds),
    ("rain_72h_mm", rain_72_thresholds),
    ("rain_7d_mm", rain_7d_thresholds),
    ("swvl1", soil1_thresholds),
    ("swvl2", soil2_thresholds),
]:

    threshold_rows.append(
        {
            "feature": name,
            "p50": series.loc[0.50],
            "p75": series.loc[0.75],
            "p90": series.loc[0.90],
            "p95": series.loc[0.95],
            "p99": series.loc[0.99],
        }
    )

thresholds = pd.DataFrame(
    threshold_rows
)

thresholds.to_csv(
    THRESHOLD_OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Save event scores
# ------------------------------------------------------------

result.to_csv(
    EVENT_OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("DYNAMIC TRIGGER SCORING")
print("========================================")

print("Events:", len(result))

print("\nTrigger categories:")
print(
    result["trigger_category"]
    .value_counts()
    .to_string()
)

print("\nTrigger score statistics:")
print(
    result["trigger_score"]
    .describe()
    .to_string()
)

print("\nThreshold file:")
print(THRESHOLD_OUTPUT)

print("\nEvent trigger file:")
print(EVENT_OUTPUT)

print("\nDYNAMIC TRIGGER SCORING COMPLETE ✅")

from pathlib import Path

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

EVENT_FILE = (
    ROOT / "data/processed/dynamic/dynamic_event_features.csv"
)

TRIGGER_FILE = (
    ROOT / "data/processed/dynamic/dynamic_event_trigger_scores.csv"
)

ERA5_FILE = (
    ROOT / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/dynamic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "dynamic_trigger_validation.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

events = pd.read_csv(
    EVENT_FILE,
    parse_dates=["event_date"],
)

triggers = pd.read_csv(
    TRIGGER_FILE,
)

weather = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

if events.empty:
    raise RuntimeError("No dynamic events found.")

if triggers.empty:
    raise RuntimeError("No trigger scores found.")

if weather.empty:
    raise RuntimeError("ERA5 dataset is empty.")


weather = weather.sort_values(
    "valid_time"
).reset_index(drop=True)


# ------------------------------------------------------------
# Validate event/trigger alignment
# ------------------------------------------------------------

merged = events.merge(
    triggers[
        [
            "record_id",
            "landslide_id",
            "trigger_score",
            "trigger_category",
        ]
    ],
    on=[
        "record_id",
        "landslide_id",
    ],
    how="inner",
)

if len(merged) != len(events):
    raise RuntimeError(
        "Some event records did not match trigger scores."
    )


# ------------------------------------------------------------
# Baseline comparison
# ------------------------------------------------------------

validation_rows = []

for _, event in merged.iterrows():

    event_date = pd.Timestamp(
        event["event_date"]
    ).normalize()

    # 30-day reference period ending 1 day before event.
    baseline_end = (
        event_date
        - pd.Timedelta(hours=24)
    )

    baseline_start = (
        baseline_end
        - pd.Timedelta(days=30)
    )

    baseline = weather[
        (weather["valid_time"] >= baseline_start)
        & (weather["valid_time"] <= baseline_end)
    ]

    if baseline.empty:
        continue

    # Event-window rainfall.
    event_rain_24 = float(
        event["rain_24h_event_mm"]
    )

    event_rain_72 = float(
        event["rain_72h_event_mm"]
    )

    event_rain_7d = float(
        event["rain_7d_event_mm"]
    )

    # Historical baseline distributions.
    b24 = baseline["rain_24h_mm"]
    b72 = baseline["rain_72h_mm"]
    b7 = baseline["rain_7d_mm"]

    # Percentile rank.
    event_percentile_24 = (
        float((b24 <= event_rain_24).mean())
    )

    event_percentile_72 = (
        float((b72 <= event_rain_72).mean())
    )

    event_percentile_7d = (
        float((b7 <= event_rain_7d).mean())
    )

    # Baseline means.
    mean_24 = float(b24.mean())
    mean_72 = float(b72.mean())
    mean_7d = float(b7.mean())

    # Anomaly ratios.
    ratio_24 = (
        event_rain_24 / mean_24
        if mean_24 > 0
        else np.nan
    )

    ratio_72 = (
        event_rain_72 / mean_72
        if mean_72 > 0
        else np.nan
    )

    ratio_7d = (
        event_rain_7d / mean_7d
        if mean_7d > 0
        else np.nan
    )

    validation_rows.append(
        {
            "record_id": event["record_id"],
            "landslide_id": event["landslide_id"],
            "event_date": event_date,
            "trigger_score": event["trigger_score"],
            "trigger_category": event["trigger_category"],
            "rain_24h_mm": event_rain_24,
            "rain_72h_mm": event_rain_72,
            "rain_7d_mm": event_rain_7d,
            "baseline_mean_24h_mm": mean_24,
            "baseline_mean_72h_mm": mean_72,
            "baseline_mean_7d_mm": mean_7d,
            "rain_24h_percentile": event_percentile_24,
            "rain_72h_percentile": event_percentile_72,
            "rain_7d_percentile": event_percentile_7d,
            "rain_24h_ratio": ratio_24,
            "rain_72h_ratio": ratio_72,
            "rain_7d_ratio": ratio_7d,
        }
    )


result = pd.DataFrame(
    validation_rows
)

if result.empty:
    raise RuntimeError(
        "No baseline comparisons could be constructed."
    )


# ------------------------------------------------------------
# Event-level anomaly flag
# ------------------------------------------------------------

result["rainfall_anomalous"] = (
    (
        result["rain_24h_percentile"] >= 0.90
    )
    | (
        result["rain_72h_percentile"] >= 0.90
    )
    | (
        result["rain_7d_percentile"] >= 0.90
    )
).astype(int)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

result.to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\n========================================")
print("DYNAMIC TRIGGER VALIDATION")
print("========================================")

print(
    "Events validated:",
    len(result),
)

print(
    "Events with >=90th percentile rainfall:",
    int(result["rainfall_anomalous"].sum()),
)

print(
    "Fraction anomalous:",
    round(
        result["rainfall_anomalous"].mean(),
        4,
    ),
)

print("\nMean event rainfall percentiles:")

print(
    "24h:",
    round(result["rain_24h_percentile"].mean(), 4),
)

print(
    "72h:",
    round(result["rain_72h_percentile"].mean(), 4),
)

print(
    "7d:",
    round(result["rain_7d_percentile"].mean(), 4),
)

print("\nTrigger categories:")
print(
    result["trigger_category"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nDYNAMIC TRIGGER VALIDATION COMPLETE ✅")

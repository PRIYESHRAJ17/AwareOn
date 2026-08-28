from pathlib import Path

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

EVENT_FILE = (
    ROOT
    / "data/processed/ground_truth/dated_landslide_events.csv"
)

ERA5_FILE = (
    ROOT
    / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/dynamic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "dynamic_event_features.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

events = pd.read_csv(
    EVENT_FILE,
    parse_dates=["event_date"],
)

weather = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

if events.empty:
    raise RuntimeError("No dated landslide events found.")

if weather.empty:
    raise RuntimeError("ERA5 dataset is empty.")


weather = weather.sort_values(
    "valid_time"
).reset_index(drop=True)


# ------------------------------------------------------------
# Event feature builder
# ------------------------------------------------------------

rows = []

for _, event in events.iterrows():

    event_time = pd.Timestamp(
        event["event_date"]
    ).normalize()

    # ERA5 timestamp nearest to event date.
    nearest_idx = (
        (
            weather["valid_time"]
            - event_time
        )
        .abs()
        .idxmin()
    )

    nearest = weather.loc[nearest_idx]

    # --------------------------------------------------------
    # Historical windows ending at event_time
    # --------------------------------------------------------

    window_start_24h = event_time - pd.Timedelta(hours=24)
    window_start_72h = event_time - pd.Timedelta(hours=72)
    window_start_7d = event_time - pd.Timedelta(days=7)

    w24 = weather[
        (weather["valid_time"] >= window_start_24h)
        & (weather["valid_time"] <= event_time)
    ]

    w72 = weather[
        (weather["valid_time"] >= window_start_72h)
        & (weather["valid_time"] <= event_time)
    ]

    w7 = weather[
        (weather["valid_time"] >= window_start_7d)
        & (weather["valid_time"] <= event_time)
    ]

    if w24.empty or w72.empty or w7.empty:
        continue

    # --------------------------------------------------------
    # Rainfall statistics
    # --------------------------------------------------------

    rain_24h = float(
        w24["precip_mm"].sum()
    )

    rain_72h = float(
        w72["precip_mm"].sum()
    )

    rain_7d = float(
        w7["precip_mm"].sum()
    )

    peak_24h = float(
        w24["precip_mm"].rolling(
            24,
            min_periods=1,
        ).sum().max()
    )

    peak_72h = float(
        w72["precip_mm"].rolling(
            72,
            min_periods=1,
        ).sum().max()
    )

    # --------------------------------------------------------
    # Soil water
    # --------------------------------------------------------

    soil1_now = float(
        nearest["swvl1"]
    )

    soil2_now = float(
        nearest["swvl2"]
    )

    # 72h earlier soil-water state
    target_previous = event_time - pd.Timedelta(
        hours=72
    )

    previous_idx = (
        (
            weather["valid_time"]
            - target_previous
        )
        .abs()
        .idxmin()
    )

    previous = weather.loc[
        previous_idx
    ]

    soil1_change_72h = (
        soil1_now
        - float(previous["swvl1"])
    )

    soil2_change_72h = (
        soil2_now
        - float(previous["swvl2"])
    )

    # --------------------------------------------------------
    # Rain intensity / burst indicator
    # --------------------------------------------------------

    hourly_peak = float(
        w24["precip_mm"].max()
    )

    # --------------------------------------------------------
    # Store event record
    # --------------------------------------------------------

    rows.append(
        {
            "record_id": event["record_id"],
            "landslide_id": event["landslide_id"],
            "district": event["district"],
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "event_date": event_time,
            "rain_24h_event_mm": rain_24h,
            "rain_72h_event_mm": rain_72h,
            "rain_7d_event_mm": rain_7d,
            "peak_24h_window_mm": peak_24h,
            "peak_72h_window_mm": peak_72h,
            "peak_hourly_rain_mm": hourly_peak,
            "swvl1_event": soil1_now,
            "swvl2_event": soil2_now,
            "swvl1_change_72h": soil1_change_72h,
            "swvl2_change_72h": soil2_change_72h,
        }
    )


result = pd.DataFrame(rows)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

if result.empty:
    raise RuntimeError(
        "Dynamic feature construction produced no events."
    )


# Remove duplicate event IDs.
result = result.drop_duplicates(
    subset=[
        "record_id",
        "landslide_id",
    ]
).reset_index(drop=True)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("DYNAMIC EVENT FEATURES")
print("========================================")

print(
    "Input dated events:",
    len(events),
)

print(
    "Events processed:",
    len(result),
)

print(
    "Date range:",
    result["event_date"].min(),
    "to",
    result["event_date"].max(),
)

print("\nMissing values:")
print(
    result.isna()
    .sum()
    .to_string()
)

print("\nRainfall statistics:")
print(
    result[
        [
            "rain_24h_event_mm",
            "rain_72h_event_mm",
            "rain_7d_event_mm",
            "peak_24h_window_mm",
            "peak_hourly_rain_mm",
        ]
    ]
    .describe()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

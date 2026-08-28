from pathlib import Path

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

ERA5_FILE = (
    ROOT / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "rainfall_trigger_engine_output.csv"
)


# ------------------------------------------------------------
# Load ERA5
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


# ------------------------------------------------------------
# Latest environmental state
# ------------------------------------------------------------

latest = era5.iloc[-1]

rain24 = float(latest["rain_24h_mm"])
rain72 = float(latest["rain_72h_mm"])
rain7 = float(latest["rain_7d_mm"])

peak_hourly = float(
    era5.loc[
        era5["valid_time"] >= (
            latest["valid_time"]
            - pd.Timedelta(hours=24)
        ),
        "precip_mm",
    ].max()
)


# ------------------------------------------------------------
# Historical percentile function
# ------------------------------------------------------------

def percentile_rank(series, value):

    return float(
        (series <= value).mean()
    )


rain24_pct = percentile_rank(
    era5["rain_24h_mm"],
    rain24,
)

rain72_pct = percentile_rank(
    era5["rain_72h_mm"],
    rain72,
)

rain7_pct = percentile_rank(
    era5["rain_7d_mm"],
    rain7,
)


# ------------------------------------------------------------
# Hourly burst percentile
# ------------------------------------------------------------

hourly_pct = percentile_rank(
    era5["precip_mm"],
    peak_hourly,
)


# ------------------------------------------------------------
# Composite rainfall trigger
# ------------------------------------------------------------

rainfall_trigger_score = (
    0.40 * rain24_pct
    + 0.30 * rain72_pct
    + 0.20 * rain7_pct
    + 0.10 * hourly_pct
) * 100.0


# ------------------------------------------------------------
# Category
# ------------------------------------------------------------

if rainfall_trigger_score < 25:
    category = "LOW"

elif rainfall_trigger_score < 50:
    category = "MODERATE"

elif rainfall_trigger_score < 75:
    category = "HIGH"

else:
    category = "EXTREME"


# ------------------------------------------------------------
# Create output
# ------------------------------------------------------------

output = pd.DataFrame(
    [
        {
            "timestamp": latest["valid_time"],
            "latitude": latest["latitude"],
            "longitude": latest["longitude"],
            "rain_24h_mm": rain24,
            "rain_72h_mm": rain72,
            "rain_7d_mm": rain7,
            "peak_hourly_rain_mm": peak_hourly,
            "rain_24h_percentile": rain24_pct,
            "rain_72h_percentile": rain72_pct,
            "rain_7d_percentile": rain7_pct,
            "hourly_burst_percentile": hourly_pct,
            "rainfall_trigger_score": rainfall_trigger_score,
            "rainfall_trigger_category": category,
        }
    ]
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output.to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 02")
print("RAINFALL TRIGGER ENGINE")
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

print("\nRainfall:")
print(
    "24h:",
    round(rain24, 3),
    "mm",
)

print(
    "72h:",
    round(rain72, 3),
    "mm",
)

print(
    "7d:",
    round(rain7, 3),
    "mm",
)

print(
    "Peak hourly:",
    round(peak_hourly, 3),
    "mm",
)

print("\nPercentiles:")
print(
    "24h:",
    round(rain24_pct, 4),
)

print(
    "72h:",
    round(rain72_pct, 4),
)

print(
    "7d:",
    round(rain7_pct, 4),
)

print(
    "Hourly burst:",
    round(hourly_pct, 4),
)

print(
    "\nTrigger score:",
    round(
        rainfall_trigger_score,
        2,
    ),
)

print(
    "Category:",
    category,
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 02 COMPLETE ✅")

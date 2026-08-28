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
    OUT_DIR / "soil_wetness_engine_output.csv"
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


# ------------------------------------------------------------
# Current state
# ------------------------------------------------------------

latest = era5.iloc[-1]

swvl1 = float(latest["swvl1"])
swvl2 = float(latest["swvl2"])


# ------------------------------------------------------------
# Historical percentiles
# ------------------------------------------------------------

def percentile_rank(series, value):
    return float(
        (series <= value).mean()
    )


swvl1_pct = percentile_rank(
    era5["swvl1"],
    swvl1,
)

swvl2_pct = percentile_rank(
    era5["swvl2"],
    swvl2,
)


# ------------------------------------------------------------
# 72-hour change
# ------------------------------------------------------------

current_time = latest["valid_time"]

target_previous = (
    current_time
    - pd.Timedelta(hours=72)
)

previous_idx = (
    (
        era5["valid_time"]
        - target_previous
    )
    .abs()
    .idxmin()
)

previous = era5.loc[previous_idx]

swvl1_change = (
    swvl1
    - float(previous["swvl1"])
)

swvl2_change = (
    swvl2
    - float(previous["swvl2"])
)


# ------------------------------------------------------------
# Soil-moisture change score
# ------------------------------------------------------------

change_score = 0.0

if swvl1_change > 0:
    change_score += min(
        50.0,
        swvl1_change * 500.0,
    )

if swvl2_change > 0:
    change_score += min(
        50.0,
        swvl2_change * 500.0,
    )

change_score = min(
    100.0,
    change_score,
)


# ------------------------------------------------------------
# Composite wetness score
# ------------------------------------------------------------

wetness_score = (
    0.40 * swvl1_pct
    + 0.30 * swvl2_pct
    + 0.30 * (change_score / 100.0)
) * 100.0


# ------------------------------------------------------------
# Category
# ------------------------------------------------------------

if wetness_score < 25:
    category = "LOW"

elif wetness_score < 50:
    category = "MODERATE"

elif wetness_score < 75:
    category = "HIGH"

else:
    category = "EXTREME"


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output = pd.DataFrame(
    [
        {
            "timestamp": current_time,
            "latitude": latest["latitude"],
            "longitude": latest["longitude"],
            "swvl1": swvl1,
            "swvl2": swvl2,
            "swvl1_percentile": swvl1_pct,
            "swvl2_percentile": swvl2_pct,
            "swvl1_change_72h": swvl1_change,
            "swvl2_change_72h": swvl2_change,
            "soil_change_score": change_score,
            "soil_wetness_score": wetness_score,
            "soil_wetness_category": category,
        }
    ]
)

output.to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 03")
print("SOIL WETNESS ENGINE")
print("========================================")

print(
    "Timestamp:",
    current_time,
)

print(
    "Location:",
    latest["latitude"],
    latest["longitude"],
)

print("\nSoil moisture:")
print("SWVL1:", round(swvl1, 6))
print("SWVL2:", round(swvl2, 6))

print("\nPercentiles:")
print("SWVL1:", round(swvl1_pct, 4))
print("SWVL2:", round(swvl2_pct, 4))

print("\n72h change:")
print(
    "SWVL1:",
    round(swvl1_change, 6),
)

print(
    "SWVL2:",
    round(swvl2_change, 6),
)

print(
    "\nChange score:",
    round(change_score, 2),
)

print(
    "Wetness score:",
    round(wetness_score, 2),
)

print(
    "Category:",
    category,
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 03 COMPLETE ✅")

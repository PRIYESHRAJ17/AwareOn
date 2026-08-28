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
    OUT_DIR / "temporal_risk_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

df = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

if df.empty:
    raise RuntimeError("ERA5 dataset is empty.")

df = df.sort_values(
    "valid_time"
).reset_index(drop=True)


# ------------------------------------------------------------
# Build rolling environmental signals
# ------------------------------------------------------------

# 24h rainfall
df["rainfall_24h"] = df["precip_mm"].rolling(
    24,
    min_periods=1,
).sum()

# 72h rainfall
df["rainfall_72h"] = df["precip_mm"].rolling(
    72,
    min_periods=1,
).sum()

# 7-day rainfall
df["rainfall_7d"] = df["precip_mm"].rolling(
    24 * 7,
    min_periods=1,
).sum()

# 24h soil-water average
df["soil_mean"] = (
    df["swvl1"] + df["swvl2"]
) / 2.0


# ------------------------------------------------------------
# Current and previous windows
# ------------------------------------------------------------

latest = df.iloc[-1]

current_time = latest["valid_time"]

# Compare current state against the state 24h earlier.
previous_target = (
    current_time
    - pd.Timedelta(hours=24)
)

previous_idx = (
    (
        df["valid_time"]
        - previous_target
    )
    .abs()
    .idxmin()
)

previous = df.loc[previous_idx]


# ------------------------------------------------------------
# Changes
# ------------------------------------------------------------

rain_24_change = (
    float(latest["rainfall_24h"])
    - float(previous["rainfall_24h"])
)

rain_72_change = (
    float(latest["rainfall_72h"])
    - float(previous["rainfall_72h"])
)

soil_change = (
    float(latest["soil_mean"])
    - float(previous["soil_mean"])
)


# ------------------------------------------------------------
# Percentile rank
# ------------------------------------------------------------

def percentile_rank(series, value):
    return float(
        (series <= value).mean()
    )


rain_24_pct = percentile_rank(
    df["rainfall_24h"],
    latest["rainfall_24h"],
)

rain_72_pct = percentile_rank(
    df["rainfall_72h"],
    latest["rainfall_72h"],
)

rain_7d_pct = percentile_rank(
    df["rainfall_7d"],
    latest["rainfall_7d"],
)

soil_pct = percentile_rank(
    df["soil_mean"],
    latest["soil_mean"],
)


# ------------------------------------------------------------
# Current environmental pressure
# ------------------------------------------------------------

current_pressure = (
    0.35 * rain_24_pct
    + 0.30 * rain_72_pct
    + 0.20 * rain_7d_pct
    + 0.15 * soil_pct
) * 100.0


# ------------------------------------------------------------
# Momentum
# ------------------------------------------------------------

momentum = 0.0

if rain_24_change > 0:
    momentum += 30.0

if rain_72_change > 0:
    momentum += 20.0

if soil_change > 0:
    momentum += 30.0

if (
    latest["precip_mm"]
    > df["precip_mm"].rolling(
        24,
        min_periods=1,
    ).mean().iloc[-1]
):
    momentum += 20.0

momentum = min(
    100.0,
    momentum,
)


# ------------------------------------------------------------
# Direction
# ------------------------------------------------------------

if momentum >= 70:
    trajectory = "RISING_FAST"

elif momentum >= 45:
    trajectory = "RISING"

elif momentum <= 20 and current_pressure < 50:
    trajectory = "STABLE_LOW"

elif momentum <= 30:
    trajectory = "STABLE"

else:
    trajectory = "MIXED"


# ------------------------------------------------------------
# Trajectory score
# ------------------------------------------------------------

trajectory_score = (
    0.65 * current_pressure
    + 0.35 * momentum
)


# ------------------------------------------------------------
# Category
# ------------------------------------------------------------

if trajectory_score < 25:
    category = "LOW"

elif trajectory_score < 50:
    category = "MODERATE"

elif trajectory_score < 75:
    category = "HIGH"

else:
    category = "EXTREME"


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

output = pd.DataFrame(
    [
        {
            "timestamp": current_time,
            "latitude": latest["latitude"],
            "longitude": latest["longitude"],

            "rain_24h_mm": latest["rainfall_24h"],
            "rain_72h_mm": latest["rainfall_72h"],
            "rain_7d_mm": latest["rainfall_7d"],

            "soil_mean": latest["soil_mean"],

            "rain_24h_percentile": rain_24_pct,
            "rain_72h_percentile": rain_72_pct,
            "rain_7d_percentile": rain_7d_pct,
            "soil_percentile": soil_pct,

            "current_pressure_score": current_pressure,

            "rain_24h_change": rain_24_change,
            "rain_72h_change": rain_72_change,
            "soil_change": soil_change,

            "momentum_score": momentum,

            "trajectory_score": trajectory_score,
            "risk_trajectory": trajectory,
            "trajectory_category": category,
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
print("AWAREON ENGINE 10")
print("TEMPORAL RISK TRAJECTORY")
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

print("\nCurrent pressure:")
print(
    "Score:",
    round(current_pressure, 2),
)

print("\nMomentum:")
print(
    "Score:",
    round(momentum, 2),
)

print(
    "24h rainfall change:",
    round(rain_24_change, 3),
)

print(
    "72h rainfall change:",
    round(rain_72_change, 3),
)

print(
    "Soil change:",
    round(soil_change, 6),
)

print("\nTrajectory:")
print(
    trajectory,
)

print(
    "Trajectory score:",
    round(trajectory_score, 2),
)

print(
    "Category:",
    category,
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 10 COMPLETE ✅")

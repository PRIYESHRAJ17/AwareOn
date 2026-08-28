from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ERA5_FILE = (
    ROOT / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "scenario_simulation_engine_output.csv"
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
# Historical percentile helper
# ------------------------------------------------------------

def percentile_rank(series, value):
    return float(
        (series <= value).mean()
    )


# ------------------------------------------------------------
# Baseline values
# ------------------------------------------------------------

base_rain24 = float(
    latest["rain_24h_mm"]
)

base_rain72 = float(
    latest["rain_72h_mm"]
)

base_rain7 = float(
    latest["rain_7d_mm"]
)


# ------------------------------------------------------------
# Scenario builder
# ------------------------------------------------------------

scenarios = [
    ("BASELINE", 0.00),
    ("RAINFALL_PLUS_25_PERCENT", 0.25),
    ("RAINFALL_PLUS_50_PERCENT", 0.50),
    ("RAINFALL_PLUS_100_PERCENT", 1.00),
]


rows = []


for name, increase in scenarios:

    rain24 = base_rain24 * (
        1.0 + increase
    )

    rain72 = base_rain72 * (
        1.0 + increase
    )

    rain7 = base_rain7 * (
        1.0 + increase
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

    trigger_score = (
        0.40 * rain24_pct
        + 0.35 * rain72_pct
        + 0.25 * rain7_pct
    ) * 100.0

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
            "scenario": name,
            "rainfall_change_percent": increase * 100.0,
            "rain_24h_mm": rain24,
            "rain_72h_mm": rain72,
            "rain_7d_mm": rain7,
            "rain_24h_percentile": rain24_pct,
            "rain_72h_percentile": rain72_pct,
            "rain_7d_percentile": rain7_pct,
            "rainfall_trigger_score": trigger_score,
            "trigger_category": category,
        }
    )


result = pd.DataFrame(rows)


# ------------------------------------------------------------
# Change from baseline
# ------------------------------------------------------------

baseline_score = float(
    result.loc[
        result["scenario"] == "BASELINE",
        "rainfall_trigger_score",
    ].iloc[0]
)

result["trigger_score_change_from_baseline"] = (
    result["rainfall_trigger_score"]
    - baseline_score
)


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
print("STEP 27")
print("AWAREON SCENARIO SIMULATION")
print("========================================")

print(
    "Baseline timestamp:",
    latest["valid_time"],
)

print("\nScenario results:")

print(
    result[
        [
            "scenario",
            "rain_24h_mm",
            "rain_72h_mm",
            "rain_7d_mm",
            "rainfall_trigger_score",
            "trigger_category",
            "trigger_score_change_from_baseline",
        ]
    ].to_string(index=False)
)

print("\nOutput:")
print(OUTPUT)

print("\nSTEP 27 COMPLETE ✅")

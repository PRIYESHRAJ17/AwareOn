from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

MODEL_FILE = (
    ROOT / "data/processed/models/best_susceptibility_model.joblib"
)

ERA5_FILE = (
    ROOT / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/risk"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "current_risk_scores.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

features = pd.read_csv(FEATURE_FILE)

bundle = joblib.load(MODEL_FILE)

model = bundle["model"]
model_features = bundle["features"]

era5 = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

if features.empty:
    raise RuntimeError("Static feature dataset is empty.")

if era5.empty:
    raise RuntimeError("ERA5 dataset is empty.")


# ------------------------------------------------------------
# Susceptibility
# ------------------------------------------------------------

X = features[model_features]

features["susceptibility_probability"] = (
    model.predict_proba(X)[:, 1]
)


# ------------------------------------------------------------
# Current environmental state
# ------------------------------------------------------------

latest = (
    era5
    .sort_values("valid_time")
    .iloc[-1]
)

current_rain_24h = float(
    latest["rain_24h_mm"]
)

current_rain_72h = float(
    latest["rain_72h_mm"]
)

current_rain_7d = float(
    latest["rain_7d_mm"]
)

current_swvl1 = float(
    latest["swvl1"]
)

current_swvl2 = float(
    latest["swvl2"]
)


# ------------------------------------------------------------
# Historical percentile helper
# ------------------------------------------------------------

def percentile_rank(series, value):
    return float(
        (series <= value).mean()
    )


# ------------------------------------------------------------
# Environmental percentiles
# ------------------------------------------------------------

rain24_pct = percentile_rank(
    era5["rain_24h_mm"],
    current_rain_24h,
)

rain72_pct = percentile_rank(
    era5["rain_72h_mm"],
    current_rain_72h,
)

rain7_pct = percentile_rank(
    era5["rain_7d_mm"],
    current_rain_7d,
)

soil1_pct = percentile_rank(
    era5["swvl1"],
    current_swvl1,
)

soil2_pct = percentile_rank(
    era5["swvl2"],
    current_swvl2,
)


# ------------------------------------------------------------
# Trigger score
# ------------------------------------------------------------

rainfall_trigger = (
    0.40 * rain24_pct
    + 0.35 * rain72_pct
    + 0.25 * rain7_pct
) * 100.0

soil_trigger = (
    0.50 * soil1_pct
    + 0.50 * soil2_pct
) * 100.0

trigger_score = (
    0.70 * rainfall_trigger
    + 0.30 * soil_trigger
)


# ------------------------------------------------------------
# Exposure score
# ------------------------------------------------------------

def inverse_distance_score(distance_series, scale):
    """
    Convert distance values into a 0-1 exposure score.

    Smaller distance -> larger exposure score.
    """

    distance_series = pd.to_numeric(
        distance_series,
        errors="coerce",
    )

    return (
        1.0
        / (
            1.0
            + distance_series / float(scale)
        )
    )


road_score = inverse_distance_score(
    features["road_distance_m"],
    500.0,
)

settlement_score = inverse_distance_score(
    features["settlement_distance_m"],
    1000.0,
)

amenity_score = inverse_distance_score(
    features["amenity_distance_m"],
    1000.0,
)


features["exposure_score"] = (
    0.50 * road_score
    + 0.30 * settlement_score
    + 0.20 * amenity_score
) * 100.0


# ------------------------------------------------------------
# Uncertainty proxy
# ------------------------------------------------------------

features["decision_margin"] = (
    features["susceptibility_probability"] - 0.5
).abs()

features["uncertainty_score"] = (
    1.0
    - np.clip(
        features["decision_margin"] * 2.0,
        0.0,
        1.0,
    )
) * 100.0


# ------------------------------------------------------------
# Unified risk
# ------------------------------------------------------------

features["trigger_score"] = trigger_score

features["soil_wetness_score"] = soil_trigger

features["risk_score"] = (
    0.55
    * features["susceptibility_probability"]
    * 100.0
    + 0.25
    * features["trigger_score"]
    + 0.10
    * features["soil_wetness_score"]
    + 0.10
    * features["exposure_score"]
)


# ------------------------------------------------------------
# Confidence
# ------------------------------------------------------------

features["confidence_score"] = (
    100.0
    - features["uncertainty_score"]
)


# ------------------------------------------------------------
# Risk category
# ------------------------------------------------------------

def classify(score):

    if score < 25:
        return "LOW"

    if score < 50:
        return "MODERATE"

    if score < 75:
        return "HIGH"

    return "EXTREME"


features["risk_category"] = (
    features["risk_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "label",
    "susceptibility_probability",
    "trigger_score",
    "soil_wetness_score",
    "exposure_score",
    "uncertainty_score",
    "confidence_score",
    "risk_score",
    "risk_category",
]

features[output_columns].to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON MULTI-SIGNAL RISK FUSION")
print("========================================")

print(
    "Environmental reference:",
    latest["valid_time"],
)

print(
    "Rainfall 24h:",
    current_rain_24h,
)

print(
    "Rainfall 72h:",
    current_rain_72h,
)

print(
    "Rainfall 7d:",
    current_rain_7d,
)

print(
    "Soil water:",
    current_swvl1,
    current_swvl2,
)

print(
    "\nRainfall trigger:",
    round(rainfall_trigger, 2),
)

print(
    "Soil trigger:",
    round(soil_trigger, 2),
)

print("\nRisk categories:")
print(
    features["risk_category"]
    .value_counts()
    .to_string()
)

print("\nRisk statistics:")
print(
    features["risk_score"]
    .describe()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nRISK FUSION COMPLETE ✅")

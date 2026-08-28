from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT
    / "data/processed/features/static_ml_features_validated.csv"
)

MODEL_FILE = (
    ROOT
    / "data/processed/models/best_susceptibility_model.joblib"
)

ERA5_FILE = (
    ROOT
    / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "counterfactual_risk_output.csv"
)


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

latest = (
    era5
    .sort_values("valid_time")
    .iloc[-1]
)


# ------------------------------------------------------------
# Current susceptibility
# ------------------------------------------------------------

features["susceptibility_probability"] = (
    model.predict_proba(
        features[model_features]
    )[:, 1]
)


# ------------------------------------------------------------
# Current environmental reference
# ------------------------------------------------------------

base_rain24 = float(latest["rain_24h_mm"])
base_rain72 = float(latest["rain_72h_mm"])
base_rain7 = float(latest["rain_7d_mm"])

base_soil1 = float(latest["swvl1"])
base_soil2 = float(latest["swvl2"])


# ------------------------------------------------------------
# Percentile helper
# ------------------------------------------------------------

def percentile(series, value):
    return float(
        (series <= value).mean()
    )


# ------------------------------------------------------------
# Exposure score
# ------------------------------------------------------------

def inverse_distance(distance, scale):
    return 1.0 / (
        1.0 + distance / scale
    )


road = inverse_distance(
    features["road_distance_m"],
    500.0,
)

settlement = inverse_distance(
    features["settlement_distance_m"],
    1000.0,
)

amenity = inverse_distance(
    features["amenity_distance_m"],
    1000.0,
)

features["exposure_score"] = (
    0.50 * road
    + 0.30 * settlement
    + 0.20 * amenity
) * 100.0


# ------------------------------------------------------------
# Scenarios
# ------------------------------------------------------------

scenarios = [
    ("BASELINE", 0.00),
    ("RAINFALL_PLUS_25_PERCENT", 0.25),
    ("RAINFALL_PLUS_50_PERCENT", 0.50),
    ("RAINFALL_PLUS_100_PERCENT", 1.00),
]


records = []


for scenario, increase in scenarios:

    rain24 = base_rain24 * (1.0 + increase)
    rain72 = base_rain72 * (1.0 + increase)
    rain7 = base_rain7 * (1.0 + increase)

    rain24_pct = percentile(
        era5["rain_24h_mm"],
        rain24,
    )

    rain72_pct = percentile(
        era5["rain_72h_mm"],
        rain72,
    )

    rain7_pct = percentile(
        era5["rain_7d_mm"],
        rain7,
    )

    soil1_pct = percentile(
        era5["swvl1"],
        base_soil1,
    )

    soil2_pct = percentile(
        era5["swvl2"],
        base_soil2,
    )

    rainfall_trigger = (
        0.40 * rain24_pct
        + 0.35 * rain72_pct
        + 0.25 * rain7_pct
    ) * 100.0

    soil_score = (
        0.50 * soil1_pct
        + 0.50 * soil2_pct
    ) * 100.0

    # Same susceptibility for all rainfall scenarios:
    # rainfall changes the triggering conditions, not
    # the static terrain susceptibility model.
    risk_score = (
        0.55
        * features["susceptibility_probability"]
        * 100.0
        + 0.25
        * rainfall_trigger
        + 0.10
        * soil_score
        + 0.10
        * features["exposure_score"]
    )

    if scenario == "BASELINE":
        baseline_score = risk_score.copy()

    for idx, row in features.iterrows():

        score = float(
            risk_score.loc[idx]
        )

        baseline = float(
            baseline_score.loc[idx]
        )

        if score < 25:
            category = "LOW"

        elif score < 50:
            category = "MODERATE"

        elif score < 75:
            category = "HIGH"

        else:
            category = "EXTREME"

        records.append(
            {
                "cell_id": row["cell_id"],
                "scenario": scenario,
                "rainfall_change_percent": increase * 100.0,
                "risk_score": score,
                "baseline_risk_score": baseline,
                "risk_score_change": score - baseline,
                "risk_category": category,
                "rainfall_trigger_score": rainfall_trigger,
                "susceptibility_probability": row[
                    "susceptibility_probability"
                ],
                "exposure_score": row[
                    "exposure_score"
                ],
            }
        )


result = pd.DataFrame(records)


# ------------------------------------------------------------
# Baseline category
# ------------------------------------------------------------

result["baseline_category"] = (
    result["baseline_risk_score"]
    .apply(
        lambda x:
        "LOW" if x < 25
        else "MODERATE" if x < 50
        else "HIGH" if x < 75
        else "EXTREME"
    )
)


# ------------------------------------------------------------
# Category transition
# ------------------------------------------------------------

category_rank = {
    "LOW": 0,
    "MODERATE": 1,
    "HIGH": 2,
    "EXTREME": 3,
}

result["category_change"] = (
    result.apply(
        lambda row:
        category_rank[row["risk_category"]]
        - category_rank[row["baseline_category"]],
        axis=1,
    )
)


result["escalates"] = (
    result["category_change"] > 0
).astype(int)


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
print("STEP 28")
print("AWAREON COUNTERFACTUAL RISK ANALYSIS")
print("========================================")

print(
    "Cells:",
    features["cell_id"].nunique(),
)

print(
    "Scenarios:",
    len(scenarios),
)

print(
    "Total scenario rows:",
    len(result),
)

print("\nEscalations by scenario:")

print(
    result.groupby("scenario")["escalates"]
    .sum()
    .to_string()
)

print("\nRisk category distribution:")

print(
    result.groupby(
        ["scenario", "risk_category"]
    ).size()
    .unstack(fill_value=0)
    .to_string()
)

print("\nMissing:")
print(
    int(result.isna().sum().sum())
)

print("\nOutput:")
print(OUTPUT)

print("\nSTEP 28 COMPLETE ✅")

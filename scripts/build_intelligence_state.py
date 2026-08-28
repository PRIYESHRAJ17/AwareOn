from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ENGINES = ROOT / "data/processed/engines"
OUT_DIR = ROOT / "data/processed/intelligence"

OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "awareon_intelligence_state.csv"


# ------------------------------------------------------------
# Load engine outputs
# ------------------------------------------------------------

sus = pd.read_csv(
    ENGINES / "susceptibility_engine_output.csv"
)

terrain = pd.read_csv(
    ENGINES / "terrain_instability_engine_output.csv"
)

exposure = pd.read_csv(
    ENGINES / "exposure_impact_engine_output.csv"
)

spatial = pd.read_csv(
    ENGINES / "spatial_propagation_engine_output.csv"
)

confidence = pd.read_csv(
    ENGINES / "confidence_uncertainty_engine_output.csv"
)

explanation = pd.read_csv(
    ENGINES / "explanation_recommendation_engine_output.csv"
)

rain = pd.read_csv(
    ENGINES / "rainfall_trigger_engine_output.csv"
)

soil = pd.read_csv(
    ENGINES / "soil_wetness_engine_output.csv"
)

temporal = pd.read_csv(
    ENGINES / "temporal_risk_engine_output.csv"
)

anomaly = pd.read_csv(
    ENGINES / "anomaly_detection_engine_output.csv"
)

sar = pd.read_csv(
    ENGINES / "sar_evidence_engine_output.csv"
)


# ------------------------------------------------------------
# Start spatial state
# ------------------------------------------------------------

state = sus[
    [
        "cell_id",
        "susceptibility_probability",
        "susceptibility_category",
    ]
].copy()


# ------------------------------------------------------------
# Merge spatial engines
# ------------------------------------------------------------

for source, columns in [
    (
        terrain,
        [
            "cell_id",
            "terrain_instability_score",
            "terrain_instability_category",
        ],
    ),
    (
        exposure,
        [
            "cell_id",
            "exposure_score",
            "exposure_category",
            "dominant_exposure",
        ],
    ),
    (
        spatial,
        [
            "cell_id",
            "spatial_pressure_score",
            "spatial_category",
        ],
    ),
    (
        confidence,
        [
            "cell_id",
            "confidence_score",
            "uncertainty_score",
            "confidence_category",
        ],
    ),
    (
        explanation,
        [
            "cell_id",
            "risk_label",
            "primary_reason",
            "recommended_action",
            "explanation",
        ],
    ),
]:

    state = state.merge(
        source[columns],
        on="cell_id",
        how="left",
    )


# ------------------------------------------------------------
# Attach global/current environmental state
# ------------------------------------------------------------

rain_row = rain.iloc[0]
soil_row = soil.iloc[0]
temporal_row = temporal.iloc[0]
anomaly_row = anomaly.iloc[0]
sar_row = sar.iloc[0]


state["rainfall_trigger_score"] = float(
    rain_row["rainfall_trigger_score"]
)

state["rainfall_trigger_category"] = (
    rain_row["rainfall_trigger_category"]
)

state["soil_wetness_score"] = float(
    soil_row["soil_wetness_score"]
)

state["soil_wetness_category"] = (
    soil_row["soil_wetness_category"]
)

state["temporal_trajectory"] = (
    temporal_row["risk_trajectory"]
)

state["temporal_category"] = (
    temporal_row["trajectory_category"]
)

state["anomaly_score"] = float(
    anomaly_row["anomaly_score"]
)

state["anomaly_category"] = (
    anomaly_row["anomaly_category"]
)

state["sar_data_quality"] = (
    sar_row["sar_data_quality"]
)


# ------------------------------------------------------------
# Unified state label
# ------------------------------------------------------------

def unified_category(row):

    risk_score = (
        0.45
        * row["susceptibility_probability"]
        * 100
        + 0.20
        * row["terrain_instability_score"]
        + 0.15
        * row["exposure_score"]
        + 0.10
        * row["spatial_pressure_score"]
        + 0.10
        * row["rainfall_trigger_score"]
    )

    if risk_score < 25:
        category = "LOW"
    elif risk_score < 50:
        category = "MODERATE"
    elif risk_score < 75:
        category = "HIGH"
    else:
        category = "EXTREME"

    return risk_score, category


state[
    [
        "unified_risk_score",
        "unified_risk_category",
    ]
] = state.apply(
    lambda row: pd.Series(
        unified_category(row)
    ),
    axis=1,
)


# ------------------------------------------------------------
# State consistency
# ------------------------------------------------------------

required = [
    "cell_id",
    "susceptibility_probability",
    "terrain_instability_score",
    "exposure_score",
    "spatial_pressure_score",
    "confidence_score",
    "rainfall_trigger_score",
    "soil_wetness_score",
    "unified_risk_score",
]


missing = state[required].isna().sum()

if missing.sum() > 0:
    raise RuntimeError(
        "Missing intelligence-state values:\n"
        + missing[missing > 0].to_string()
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

state.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON INTELLIGENCE STATE")
print("========================================")

print(
    "Cells:",
    len(state),
)

print(
    "Columns:",
    len(state.columns),
)

print("\nUnified risk categories:")
print(
    state["unified_risk_category"]
    .value_counts()
    .to_string()
)

print("\nUnified risk statistics:")
print(
    state["unified_risk_score"]
    .describe()
    .to_string()
)

print("\nSAR quality:")
print(
    state["sar_data_quality"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nSTEP 21.1 COMPLETE ✅")

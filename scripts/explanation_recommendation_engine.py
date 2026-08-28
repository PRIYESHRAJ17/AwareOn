from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SUS_FILE = (
    ROOT
    / "data/processed/engines/susceptibility_engine_output.csv"
)

RAIN_FILE = (
    ROOT
    / "data/processed/engines/rainfall_trigger_engine_output.csv"
)

SOIL_FILE = (
    ROOT
    / "data/processed/engines/soil_wetness_engine_output.csv"
)

TERRAIN_FILE = (
    ROOT
    / "data/processed/engines/terrain_instability_engine_output.csv"
)

EXPOSURE_FILE = (
    ROOT
    / "data/processed/engines/exposure_impact_engine_output.csv"
)

SPATIAL_FILE = (
    ROOT
    / "data/processed/engines/spatial_propagation_engine_output.csv"
)

TEMPORAL_FILE = (
    ROOT
    / "data/processed/engines/temporal_risk_engine_output.csv"
)

ANOMALY_FILE = (
    ROOT
    / "data/processed/engines/anomaly_detection_engine_output.csv"
)

CONFIDENCE_FILE = (
    ROOT
    / "data/processed/engines/"
    "confidence_uncertainty_engine_output.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR
    / "explanation_recommendation_engine_output.csv"
)


# ------------------------------------------------------------
# Load current-state engines
# ------------------------------------------------------------

sus = pd.read_csv(SUS_FILE)
rain = pd.read_csv(RAIN_FILE)
soil = pd.read_csv(SOIL_FILE)
terrain = pd.read_csv(TERRAIN_FILE)
exposure = pd.read_csv(EXPOSURE_FILE)
spatial = pd.read_csv(SPATIAL_FILE)
temporal = pd.read_csv(TEMPORAL_FILE)
anomaly = pd.read_csv(ANOMALY_FILE)
confidence = pd.read_csv(CONFIDENCE_FILE)


if sus.empty:
    raise RuntimeError("Susceptibility engine output is empty.")


# ------------------------------------------------------------
# Representative current location
# ------------------------------------------------------------

# Engine 01 is spatial, so create explanations for every
# susceptibility cell.
data = sus[
    [
        "cell_id",
        "susceptibility_probability",
        "susceptibility_category",
    ]
].copy()


# ------------------------------------------------------------
# Attach spatial engine outputs
# ------------------------------------------------------------

data = data.merge(
    terrain[
        [
            "cell_id",
            "terrain_instability_score",
            "terrain_instability_category",
        ]
    ],
    on="cell_id",
    how="left",
)

data = data.merge(
    exposure[
        [
            "cell_id",
            "exposure_score",
            "exposure_category",
            "dominant_exposure",
        ]
    ],
    on="cell_id",
    how="left",
)

data = data.merge(
    spatial[
        [
            "cell_id",
            "spatial_pressure_score",
            "spatial_category",
        ]
    ],
    on="cell_id",
    how="left",
)

data = data.merge(
    confidence[
        [
            "cell_id",
            "confidence_score",
            "uncertainty_score",
            "confidence_category",
        ]
    ],
    on="cell_id",
    how="left",
)


# ------------------------------------------------------------
# Current environmental state
# ------------------------------------------------------------

rain_row = rain.iloc[0]
soil_row = soil.iloc[0]
temporal_row = temporal.iloc[0]
anomaly_row = anomaly.iloc[0]


# ------------------------------------------------------------
# Recommendation logic
# ------------------------------------------------------------

def make_risk_label(row):

    probability = row["susceptibility_probability"]
    confidence = row["confidence_score"]

    if probability >= 0.75:
        label = "VERY HIGH SUSCEPTIBILITY"

    elif probability >= 0.50:
        label = "HIGH SUSCEPTIBILITY"

    elif probability >= 0.25:
        label = "MODERATE SUSCEPTIBILITY"

    else:
        label = "LOW SUSCEPTIBILITY"

    if confidence < 40:
        label += " / LOW CONFIDENCE"

    return label


def build_reason(row):

    reasons = []

    if row["susceptibility_probability"] >= 0.50:
        reasons.append(
            "high static landslide susceptibility"
        )

    if row["terrain_instability_score"] >= 60:
        reasons.append(
            "unstable terrain conditions"
        )

    if row["exposure_score"] >= 60:
        reasons.append(
            "high exposure to roads, settlements or infrastructure"
        )

    if row["spatial_pressure_score"] >= 60:
        reasons.append(
            "elevated neighbouring-cell risk"
        )

    if anomaly_row["anomaly_category"] in [
        "UNUSUAL",
        "EXTREME",
    ]:
        reasons.append(
            "unusual environmental conditions"
        )

    if temporal_row["trajectory_category"] in [
        "HIGH",
        "EXTREME",
    ]:
        reasons.append(
            "elevated temporal pressure"
        )

    if not reasons:
        reasons.append(
            "no major independent warning signal"
        )

    return "; ".join(reasons)


def build_action(row):

    actions = []

    if row["susceptibility_probability"] >= 0.75:
        actions.append(
            "prioritize location for detailed assessment"
        )

    if row["exposure_score"] >= 60:
        actions.append(
            "check nearby roads, settlements and infrastructure"
        )

    if temporal_row["trajectory_category"] in [
        "RISING",
        "RISING_FAST",
    ]:
        actions.append(
            "increase monitoring frequency"
        )

    if rain_row["rainfall_trigger_category"] in [
        "HIGH",
        "EXTREME",
    ]:
        actions.append(
            "review recent rainfall conditions"
        )

    if soil_row["soil_wetness_category"] in [
        "HIGH",
        "EXTREME",
    ]:
        actions.append(
            "check for elevated soil wetness"
        )

    if not actions:
        actions.append(
            "continue routine monitoring"
        )

    return "; ".join(actions)


def build_explanation(row):

    risk_label = make_risk_label(row)
    reasons = build_reason(row)
    actions = build_action(row)

    return (
        f"{risk_label}. "
        f"Main evidence: {reasons}. "
        f"Recommended response: {actions}."
    )


# ------------------------------------------------------------
# Build explanations
# ------------------------------------------------------------

data["risk_label"] = (
    data.apply(
        make_risk_label,
        axis=1,
    )
)

data["primary_reason"] = (
    data.apply(
        build_reason,
        axis=1,
    )
)

data["recommended_action"] = (
    data.apply(
        build_action,
        axis=1,
    )
)

data["explanation"] = (
    data.apply(
        build_explanation,
        axis=1,
    )
)


# ------------------------------------------------------------
# Attach current system-wide environmental context
# ------------------------------------------------------------

data["rainfall_trigger_category"] = (
    rain_row["rainfall_trigger_category"]
)

data["rainfall_trigger_score"] = (
    rain_row["rainfall_trigger_score"]
)

data["soil_wetness_category"] = (
    soil_row["soil_wetness_category"]
)

data["soil_wetness_score"] = (
    soil_row["soil_wetness_score"]
)

data["temporal_trajectory"] = (
    temporal_row["risk_trajectory"]
)

data["temporal_category"] = (
    temporal_row["trajectory_category"]
)

data["environment_anomaly_category"] = (
    anomaly_row["anomaly_category"]
)

data["environment_anomaly_score"] = (
    anomaly_row["anomaly_score"]
)

data["environment_timestamp"] = (
    rain_row["timestamp"]
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "susceptibility_probability",
    "susceptibility_category",
    "terrain_instability_score",
    "terrain_instability_category",
    "exposure_score",
    "exposure_category",
    "dominant_exposure",
    "spatial_pressure_score",
    "spatial_category",
    "rainfall_trigger_score",
    "rainfall_trigger_category",
    "soil_wetness_score",
    "soil_wetness_category",
    "temporal_trajectory",
    "temporal_category",
    "environment_anomaly_score",
    "environment_anomaly_category",
    "confidence_score",
    "uncertainty_score",
    "confidence_category",
    "risk_label",
    "primary_reason",
    "recommended_action",
    "explanation",
    "environment_timestamp",
]


data[output_columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 12")
print("EXPLANATION & RECOMMENDATION")
print("========================================")

print(
    "Cells explained:",
    len(data),
)

print("\nRisk labels:")
print(
    data["risk_label"]
    .value_counts()
    .to_string()
)

print("\nConfidence:")
print(
    data["confidence_category"]
    .value_counts()
    .to_string()
)

print("\nExample explanation:")

print(
    data[
        [
            "cell_id",
            "risk_label",
            "primary_reason",
            "recommended_action",
        ]
    ]
    .head(3)
    .to_string(index=False)
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 12 COMPLETE ✅")

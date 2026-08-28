from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SUS_FILE = (
    ROOT
    / "data/processed/engines/susceptibility_engine_output.csv"
)

FEATURE_FILE = (
    ROOT
    / "data/processed/features/static_ml_features_validated.csv"
)

ANOMALY_FILE = (
    ROOT
    / "data/processed/engines/anomaly_detection_engine_output.csv"
)

SAR_FILE = (
    ROOT
    / "data/processed/engines/sar_evidence_engine_output.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "confidence_uncertainty_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

sus = pd.read_csv(SUS_FILE)
features = pd.read_csv(FEATURE_FILE)
anomaly = pd.read_csv(ANOMALY_FILE)
sar = pd.read_csv(SAR_FILE)

if sus.empty:
    raise RuntimeError("Susceptibility output is empty.")

if features.empty:
    raise RuntimeError("Feature dataset is empty.")

if anomaly.empty:
    raise RuntimeError("Anomaly output is empty.")

if sar.empty:
    raise RuntimeError("SAR output is empty.")


# ------------------------------------------------------------
# Merge static quality signals
# ------------------------------------------------------------

features["cell_id"] = features["cell_id"].astype(str)
sus["cell_id"] = sus["cell_id"].astype(str)

data = sus.merge(
    features[
        [
            "cell_id",
            "terrain_imputed",
            "osm_context_available",
        ]
    ],
    on="cell_id",
    how="left",
)


# ------------------------------------------------------------
# Model certainty
# ------------------------------------------------------------

threshold = 0.45

data["model_margin"] = (
    data["susceptibility_probability"]
    - threshold
).abs()

# Convert distance from threshold to 0-100 certainty.
data["model_certainty"] = np.clip(
    data["model_margin"] / 0.55,
    0.0,
    1.0,
) * 100.0


# ------------------------------------------------------------
# Data-quality certainty
# ------------------------------------------------------------

data["terrain_quality"] = np.where(
    data["terrain_imputed"] == 0,
    100.0,
    70.0,
)

data["osm_quality"] = np.where(
    data["osm_context_available"] == 1,
    100.0,
    50.0,
)


# ------------------------------------------------------------
# SAR quality
# ------------------------------------------------------------

sar_quality_name = str(
    sar.iloc[0]["sar_data_quality"]
)

if sar_quality_name == "READY":
    sar_quality = 100.0

elif sar_quality_name == "UNREFERENCED":
    sar_quality = 40.0

else:
    sar_quality = 20.0


# ------------------------------------------------------------
# Environmental agreement
# ------------------------------------------------------------

anomaly_score = float(
    anomaly.iloc[0]["anomaly_score"]
)

# Convert anomaly score into a 0-100 agreement component.
# Low anomaly means the environment is not providing a
# strong independent warning signal, so this is neutral
# rather than treated as a failure.
environment_quality = np.clip(
    100.0 - abs(anomaly_score - 50.0),
    0.0,
    100.0,
)


# ------------------------------------------------------------
# Overall confidence
# ------------------------------------------------------------

data["confidence_score"] = (
    0.45 * data["model_certainty"]
    + 0.20 * data["terrain_quality"]
    + 0.15 * data["osm_quality"]
    + 0.10 * sar_quality
    + 0.10 * environment_quality
)


# Uncertainty is inverse confidence.
data["uncertainty_score"] = (
    100.0 - data["confidence_score"]
)


# ------------------------------------------------------------
# Confidence category
# ------------------------------------------------------------

def classify(score):

    if score >= 80:
        return "HIGH"

    if score >= 60:
        return "MODERATE"

    if score >= 40:
        return "LOW"

    return "VERY_LOW"


data["confidence_category"] = (
    data["confidence_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Explanation
# ------------------------------------------------------------

def explanation(row):

    reasons = []

    if row["model_certainty"] < 40:
        reasons.append("prediction near decision threshold")

    if row["terrain_imputed"] == 1:
        reasons.append("terrain fallback sampling used")

    if row["osm_context_available"] == 0:
        reasons.append("limited OSM context")

    if sar_quality_name == "UNREFERENCED":
        reasons.append("SAR is not spatially georeferenced")

    if not reasons:
        reasons.append("multiple data signals available")

    return "; ".join(reasons)


data["confidence_explanation"] = (
    data.apply(
        explanation,
        axis=1,
    )
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "susceptibility_probability",
    "model_margin",
    "model_certainty",
    "terrain_quality",
    "osm_quality",
    "confidence_score",
    "uncertainty_score",
    "confidence_category",
    "confidence_explanation",
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
print("AWAREON ENGINE 11")
print("CONFIDENCE & UNCERTAINTY")
print("========================================")

print(
    "Cells processed:",
    len(data),
)

print(
    "\nConfidence statistics:"
)

print(
    data["confidence_score"]
    .describe()
    .to_string()
)

print(
    "\nConfidence categories:"
)

print(
    data["confidence_category"]
    .value_counts()
    .to_string()
)

print(
    "\nSAR quality:",
    sar_quality_name,
)

print(
    "\nOutput:"
)

print(OUTPUT)

print(
    "\nENGINE 11 COMPLETE ✅"
)

from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

MODEL_FILE = (
    ROOT / "data/processed/models/best_susceptibility_model.joblib"
)

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

OUTPUT_DIR = ROOT / "data/processed/engines"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR / "susceptibility_engine_output.csv"
)


# ------------------------------------------------------------
# Load model
# ------------------------------------------------------------

bundle = joblib.load(MODEL_FILE)

model = bundle["model"]
features = bundle["features"]

threshold = float(
    bundle.get("threshold", 0.45)
)


# ------------------------------------------------------------
# Load feature matrix
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)

df["cell_id"] = df["cell_id"].astype(str)

X = df[features]


# ------------------------------------------------------------
# Predict susceptibility
# ------------------------------------------------------------

df["susceptibility_probability"] = (
    model.predict_proba(X)[:, 1]
)


# ------------------------------------------------------------
# Susceptibility category
# ------------------------------------------------------------

def classify(probability):

    if probability < 0.25:
        return "LOW"

    if probability < 0.50:
        return "MODERATE"

    if probability < 0.75:
        return "HIGH"

    return "VERY_HIGH"


df["susceptibility_category"] = (
    df["susceptibility_probability"]
    .apply(classify)
)


# ------------------------------------------------------------
# Decision flag
# ------------------------------------------------------------

df["susceptibility_alert"] = (
    df["susceptibility_probability"] >= threshold
).astype(int)


# ------------------------------------------------------------
# Model metadata
# ------------------------------------------------------------

df["model_name"] = (
    "RandomForest"
)

df["decision_threshold"] = threshold


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "label",
    "susceptibility_probability",
    "susceptibility_category",
    "susceptibility_alert",
    "decision_threshold",
    "model_name",
]

df[output_columns].to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 01")
print("LANDSLIDE SUSCEPTIBILITY ENGINE")
print("========================================")

print(
    "Cells processed:",
    len(df)
)

print(
    "Decision threshold:",
    threshold
)

print("\nCategories:")
print(
    df["susceptibility_category"]
    .value_counts()
    .to_string()
)

print("\nMean susceptibility:",
      round(
          df["susceptibility_probability"].mean(),
          4,
      )
)

print(
    "\nAlerts:",
    int(df["susceptibility_alert"].sum())
)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nENGINE 01 COMPLETE ✅")

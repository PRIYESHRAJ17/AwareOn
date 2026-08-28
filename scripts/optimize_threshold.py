from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
)


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

GT_DIR = ROOT / "data/processed/ground_truth"

TRAIN_FILE = GT_DIR / "ground_truth_train.csv"
VAL_FILE = GT_DIR / "ground_truth_validation.csv"
TEST_FILE = GT_DIR / "ground_truth_test.csv"

MODEL_FILE = (
    ROOT / "data/processed/models/baseline_random_forest.joblib"
)

OUT_DIR = ROOT / "data/processed/models"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUT_DIR / "threshold_optimization.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)
df["cell_id"] = df["cell_id"].astype(str)

train_ids = set(
    pd.read_csv(TRAIN_FILE)["cell_id"].astype(str)
)

val_ids = set(
    pd.read_csv(VAL_FILE)["cell_id"].astype(str)
)

test_ids = set(
    pd.read_csv(TEST_FILE)["cell_id"].astype(str)
)

val = df[df["cell_id"].isin(val_ids)].copy()
test = df[df["cell_id"].isin(test_ids)].copy()


# ------------------------------------------------------------
# Load baseline model
# ------------------------------------------------------------

bundle = joblib.load(MODEL_FILE)

model = bundle["model"]
feature_columns = bundle["features"]


X_val = val[feature_columns]
y_val = val["label"]

X_test = test[feature_columns]
y_test = test["label"]


# ------------------------------------------------------------
# Validation probabilities
# ------------------------------------------------------------

val_probability = model.predict_proba(X_val)[:, 1]


# ------------------------------------------------------------
# Find threshold
# ------------------------------------------------------------

rows = []

thresholds = np.arange(
    0.10,
    0.91,
    0.01,
)

for threshold in thresholds:

    prediction = (
        val_probability >= threshold
    ).astype(int)

    rows.append(
        {
            "threshold": threshold,
            "precision": precision_score(
                y_val,
                prediction,
                zero_division=0,
            ),
            "recall": recall_score(
                y_val,
                prediction,
                zero_division=0,
            ),
            "f1": f1_score(
                y_val,
                prediction,
                zero_division=0,
            ),
        }
    )


results = pd.DataFrame(rows)

# Choose threshold maximizing validation F1.
best = results.loc[
    results["f1"].idxmax()
]

best_threshold = float(
    best["threshold"]
)


# ------------------------------------------------------------
# Evaluate locked threshold on test
# ------------------------------------------------------------

test_probability = model.predict_proba(
    X_test
)[:, 1]

test_prediction = (
    test_probability >= best_threshold
).astype(int)


test_precision = precision_score(
    y_test,
    test_prediction,
    zero_division=0,
)

test_recall = recall_score(
    y_test,
    test_prediction,
    zero_division=0,
)

test_f1 = f1_score(
    y_test,
    test_prediction,
    zero_division=0,
)


# ------------------------------------------------------------
# Save threshold sweep
# ------------------------------------------------------------

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("THRESHOLD OPTIMIZATION")
print("========================================")

print(
    "Best validation threshold:",
    round(best_threshold, 2),
)

print(
    "Validation precision:",
    round(float(best["precision"]), 4),
)

print(
    "Validation recall:",
    round(float(best["recall"]), 4),
)

print(
    "Validation F1:",
    round(float(best["f1"]), 4),
)

print("\nLocked threshold applied to TEST:")

print(
    "Test precision:",
    round(test_precision, 4),
)

print(
    "Test recall:",
    round(test_recall, 4),
)

print(
    "Test F1:",
    round(test_f1, 4),
)

print("\nThreshold sweep:")
print(OUTPUT_FILE)

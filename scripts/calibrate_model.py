from pathlib import Path

import joblib
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    brier_score_loss,
    roc_auc_score,
)
from sklearn.frozen import FrozenEstimator


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

GT_DIR = ROOT / "data/processed/ground_truth"

VAL_FILE = GT_DIR / "ground_truth_validation.csv"
TEST_FILE = GT_DIR / "ground_truth_test.csv"

MODEL_FILE = (
    ROOT / "data/processed/models/baseline_random_forest.joblib"
)

OUT_DIR = ROOT / "data/processed/models"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CALIBRATED_MODEL_FILE = (
    OUT_DIR / "calibrated_random_forest.joblib"
)


# ------------------------------------------------------------
# Load feature data
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)

df["cell_id"] = df["cell_id"].astype(str)

val_ids = set(
    pd.read_csv(VAL_FILE)["cell_id"].astype(str)
)

test_ids = set(
    pd.read_csv(TEST_FILE)["cell_id"].astype(str)
)

val = df[
    df["cell_id"].isin(val_ids)
].copy()

test = df[
    df["cell_id"].isin(test_ids)
].copy()


# ------------------------------------------------------------
# Load baseline model
# ------------------------------------------------------------

bundle = joblib.load(MODEL_FILE)

base_model = bundle["model"]
feature_columns = bundle["features"]

X_val = val[feature_columns]
y_val = val["label"]

X_test = test[feature_columns]
y_test = test["label"]


# ------------------------------------------------------------
# Original probabilities
# ------------------------------------------------------------

uncalibrated_test = (
    base_model.predict_proba(X_test)[:, 1]
)


# ------------------------------------------------------------
# Calibration
# ------------------------------------------------------------
# The Random Forest is already fitted.
# FrozenEstimator tells the current sklearn API
# not to refit the underlying model.
# ------------------------------------------------------------

frozen_model = FrozenEstimator(
    base_model
)

calibrator = CalibratedClassifierCV(
    frozen_model,
    method="sigmoid",
)

calibrator.fit(
    X_val,
    y_val,
)


# ------------------------------------------------------------
# Calibrated probabilities
# ------------------------------------------------------------

calibrated_test = (
    calibrator.predict_proba(X_test)[:, 1]
)


# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

uncalibrated_brier = brier_score_loss(
    y_test,
    uncalibrated_test,
)

calibrated_brier = brier_score_loss(
    y_test,
    calibrated_test,
)

uncalibrated_auc = roc_auc_score(
    y_test,
    uncalibrated_test,
)

calibrated_auc = roc_auc_score(
    y_test,
    calibrated_test,
)


# ------------------------------------------------------------
# Save calibrated model
# ------------------------------------------------------------

joblib.dump(
    {
        "model": calibrator,
        "features": feature_columns,
        "threshold": 0.45,
    },
    CALIBRATED_MODEL_FILE,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("MODEL CALIBRATION")
print("========================================")

print(
    "Uncalibrated test Brier:",
    round(uncalibrated_brier, 4),
)

print(
    "Calibrated test Brier:",
    round(calibrated_brier, 4),
)

print(
    "Uncalibrated test ROC-AUC:",
    round(uncalibrated_auc, 4),
)

print(
    "Calibrated test ROC-AUC:",
    round(calibrated_auc, 4),
)

print(
    "\nSaved calibrated model:"
)

print(CALIBRATED_MODEL_FILE)

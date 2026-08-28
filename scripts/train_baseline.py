from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

GT_DIR = ROOT / "data/processed/ground_truth"

TRAIN_FILE = GT_DIR / "ground_truth_train.csv"
VAL_FILE = GT_DIR / "ground_truth_validation.csv"
TEST_FILE = GT_DIR / "ground_truth_test.csv"

OUT_DIR = ROOT / "data/processed/models"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = OUT_DIR / "baseline_random_forest.joblib"
IMPORTANCE_FILE = OUT_DIR / "baseline_feature_importance.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

features = pd.read_csv(FEATURE_FILE)
train_ids = pd.read_csv(TRAIN_FILE)["cell_id"].astype(str)
val_ids = pd.read_csv(VAL_FILE)["cell_id"].astype(str)
test_ids = pd.read_csv(TEST_FILE)["cell_id"].astype(str)

features["cell_id"] = features["cell_id"].astype(str)

feature_columns = [
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "elevation_std_m",
    "road_distance_m",
    "settlement_distance_m",
    "amenity_distance_m",
    "road_density_500m_km_per_km2",
    "settlements_within_1km",
    "amenities_within_1km",
    "near_road_250m",
    "near_settlement_1km",
    "near_amenity_1km",
]


# ------------------------------------------------------------
# Build splits
# ------------------------------------------------------------

train = features[
    features["cell_id"].isin(set(train_ids))
].copy()

val = features[
    features["cell_id"].isin(set(val_ids))
].copy()

test = features[
    features["cell_id"].isin(set(test_ids))
].copy()


X_train = train[feature_columns]
y_train = train["label"]

X_val = val[feature_columns]
y_val = val["label"]

X_test = test[feature_columns]
y_test = test["label"]


# ------------------------------------------------------------
# Train
# ------------------------------------------------------------

print("Training Random Forest...")

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=18,
    min_samples_leaf=3,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)


# ------------------------------------------------------------
# Evaluation helper
# ------------------------------------------------------------

def evaluate(name, X, y):

    probability = model.predict_proba(X)[:, 1]
    prediction = (probability >= 0.5).astype(int)

    print(f"\n===== {name} =====")

    print("Accuracy:", round(
        accuracy_score(y, prediction), 4
    ))

    print("Precision:", round(
        precision_score(y, prediction, zero_division=0), 4
    ))

    print("Recall:", round(
        recall_score(y, prediction, zero_division=0), 4
    ))

    print("F1:", round(
        f1_score(y, prediction, zero_division=0), 4
    ))

    print("ROC-AUC:", round(
        roc_auc_score(y, probability), 4
    ))

    print("PR-AUC:", round(
        average_precision_score(y, probability), 4
    ))

    print("Confusion matrix:")
    print(confusion_matrix(y, prediction))

    return probability


train_probability = evaluate(
    "TRAIN",
    X_train,
    y_train,
)

val_probability = evaluate(
    "VALIDATION",
    X_val,
    y_val,
)

test_probability = evaluate(
    "TEST",
    X_test,
    y_test,
)


# ------------------------------------------------------------
# Feature importance
# ------------------------------------------------------------

importance = pd.DataFrame(
    {
        "feature": feature_columns,
        "importance": model.feature_importances_,
    }
).sort_values(
    "importance",
    ascending=False,
)

importance.to_csv(
    IMPORTANCE_FILE,
    index=False,
)


# ------------------------------------------------------------
# Save model
# ------------------------------------------------------------

joblib.dump(
    {
        "model": model,
        "features": feature_columns,
    },
    MODEL_FILE,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("BASELINE MODEL COMPLETE")
print("========================================")

print("\nTop features:")
print(
    importance.head(10).to_string(index=False)
)

print("\nModel:")
print(MODEL_FILE)

print("\nFeature importance:")
print(IMPORTANCE_FILE)

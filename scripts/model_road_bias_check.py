from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT
    / "data/processed/features/static_ml_features_validated.csv"
)

GT_DIR = ROOT / "data/processed/ground_truth"

TRAIN_FILE = GT_DIR / "ground_truth_train.csv"
VAL_FILE = GT_DIR / "ground_truth_validation.csv"
TEST_FILE = GT_DIR / "ground_truth_test.csv"

OUT_DIR = ROOT / "data/processed/models"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = OUT_DIR / "road_bias_check.csv"


# ------------------------------------------------------------
# Load data
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

train = df[df["cell_id"].isin(train_ids)].copy()
val = df[df["cell_id"].isin(val_ids)].copy()
test = df[df["cell_id"].isin(test_ids)].copy()


# ------------------------------------------------------------
# Feature groups
# ------------------------------------------------------------

terrain_features = [
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "elevation_std_m",
]

non_road_exposure_features = [
    "settlement_distance_m",
    "amenity_distance_m",
    "settlements_within_1km",
    "amenities_within_1km",
    "near_settlement_1km",
    "near_amenity_1km",
]

full_features = [
    *terrain_features,
    "road_distance_m",
    "road_density_500m_km_per_km2",
    "near_road_250m",
    *non_road_exposure_features,
]

road_features = [
    "road_distance_m",
    "road_density_500m_km_per_km2",
    "near_road_250m",
]


# ------------------------------------------------------------
# Evaluation helper
# ------------------------------------------------------------

def evaluate(name, features):

    X_train = train[features]
    y_train = train["label"]

    X_val = val[features]
    y_val = val["label"]

    X_test = test[features]
    y_test = test["label"]

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=18,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    val_prob = model.predict_proba(X_val)[:, 1]
    test_prob = model.predict_proba(X_test)[:, 1]

    val_pred = (val_prob >= 0.5).astype(int)
    test_pred = (test_prob >= 0.5).astype(int)

    result = {
        "model": name,
        "features": len(features),
        "validation_roc_auc": roc_auc_score(
            y_val,
            val_prob,
        ),
        "validation_pr_auc": average_precision_score(
            y_val,
            val_prob,
        ),
        "validation_f1": f1_score(
            y_val,
            val_pred,
            zero_division=0,
        ),
        "test_roc_auc": roc_auc_score(
            y_test,
            test_prob,
        ),
        "test_pr_auc": average_precision_score(
            y_test,
            test_prob,
        ),
        "test_f1": f1_score(
            y_test,
            test_pred,
            zero_division=0,
        ),
    }

    print("\n========================================")
    print(name)
    print("========================================")

    print(
        "Validation ROC-AUC:",
        round(result["validation_roc_auc"], 4),
    )

    print(
        "Validation PR-AUC:",
        round(result["validation_pr_auc"], 4),
    )

    print(
        "Validation F1:",
        round(result["validation_f1"], 4),
    )

    print(
        "Test ROC-AUC:",
        round(result["test_roc_auc"], 4),
    )

    print(
        "Test PR-AUC:",
        round(result["test_pr_auc"], 4),
    )

    print(
        "Test F1:",
        round(result["test_f1"], 4),
    )

    return result


# ------------------------------------------------------------
# 1. Full model
# ------------------------------------------------------------

results = []

results.append(
    evaluate(
        "FULL MODEL",
        full_features,
    )
)


# ------------------------------------------------------------
# 2. Remove all road-derived features
# ------------------------------------------------------------

results.append(
    evaluate(
        "NO ROAD FEATURES",
        terrain_features + non_road_exposure_features,
    )
)


# ------------------------------------------------------------
# 3. Terrain only
# ------------------------------------------------------------

results.append(
    evaluate(
        "TERRAIN ONLY",
        terrain_features,
    )
)


# ------------------------------------------------------------
# Save report
# ------------------------------------------------------------

report = pd.DataFrame(results)

report.to_csv(
    REPORT_FILE,
    index=False,
)


# ------------------------------------------------------------
# Calculate degradation
# ------------------------------------------------------------

full_test_auc = results[0]["test_roc_auc"]
no_road_test_auc = results[1]["test_roc_auc"]

auc_drop = full_test_auc - no_road_test_auc

print("\n========================================")
print("ROAD-BIAS ANALYSIS")
print("========================================")

print(
    "Full test ROC-AUC:",
    round(full_test_auc, 4),
)

print(
    "No-road test ROC-AUC:",
    round(no_road_test_auc, 4),
)

print(
    "ROC-AUC drop:",
    round(auc_drop, 4),
)

print("\nReport:")
print(REPORT_FILE)

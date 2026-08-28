from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

GT_DIR = ROOT / "data/processed/ground_truth"

TRAIN_FILE = GT_DIR / "ground_truth_train.csv"
VAL_FILE = GT_DIR / "ground_truth_validation.csv"
TEST_FILE = GT_DIR / "ground_truth_test.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)
df["cell_id"] = df["cell_id"].astype(str)

train_ids = set(pd.read_csv(TRAIN_FILE)["cell_id"].astype(str))
val_ids = set(pd.read_csv(VAL_FILE)["cell_id"].astype(str))
test_ids = set(pd.read_csv(TEST_FILE)["cell_id"].astype(str))

train = df[df["cell_id"].isin(train_ids)]
val = df[df["cell_id"].isin(val_ids)]
test = df[df["cell_id"].isin(test_ids)]


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

exposure_features = [
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
# Train/evaluate helper
# ------------------------------------------------------------

def evaluate_model(name, features):

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

    print("\n========================================")
    print(name)
    print("========================================")

    print(
        "Validation ROC-AUC:",
        round(roc_auc_score(y_val, val_prob), 4)
    )

    print(
        "Validation PR-AUC:",
        round(average_precision_score(y_val, val_prob), 4)
    )

    print(
        "Validation F1:",
        round(f1_score(y_val, val_pred), 4)
    )

    print(
        "Test ROC-AUC:",
        round(roc_auc_score(y_test, test_prob), 4)
    )

    print(
        "Test PR-AUC:",
        round(average_precision_score(y_test, test_prob), 4)
    )

    print(
        "Test F1:",
        round(f1_score(y_test, test_pred), 4)
    )


# ------------------------------------------------------------
# Ablation 1: Terrain only
# ------------------------------------------------------------

evaluate_model(
    "TERRAIN ONLY",
    terrain_features,
)


# ------------------------------------------------------------
# Ablation 2: Exposure only
# ------------------------------------------------------------

evaluate_model(
    "EXPOSURE ONLY",
    exposure_features,
)


# ------------------------------------------------------------
# Ablation 3: Terrain + Exposure
# ------------------------------------------------------------

evaluate_model(
    "TERRAIN + EXPOSURE",
    terrain_features + exposure_features,
)


print("\n========================================")
print("ABLATION STUDY COMPLETE")
print("========================================")

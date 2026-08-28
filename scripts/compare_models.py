from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


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

REPORT_FILE = OUT_DIR / "model_comparison.csv"
BEST_MODEL_FILE = OUT_DIR / "best_susceptibility_model.joblib"


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
# Feature set
# ------------------------------------------------------------

features = [
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


X_train = train[features]
y_train = train["label"]

X_val = val[features]
y_val = val["label"]

X_test = test[features]
y_test = test["label"]


# ------------------------------------------------------------
# Models
# ------------------------------------------------------------

models = {
    "Random Forest": RandomForestClassifier(
        n_estimators=500,
        max_depth=18,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    ),

    "Logistic Regression": Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    ),
}


# ------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------

results = []

trained_models = {}


for name, model in models.items():

    print("\n========================================")
    print(name)
    print("========================================")

    model.fit(
        X_train,
        y_train,
    )

    trained_models[name] = model

    val_prob = model.predict_proba(
        X_val
    )[:, 1]

    test_prob = model.predict_proba(
        X_test
    )[:, 1]

    val_pred = (
        val_prob >= 0.45
    ).astype(int)

    test_pred = (
        test_prob >= 0.45
    ).astype(int)

    result = {
        "model": name,

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

        "validation_precision": precision_score(
            y_val,
            val_pred,
            zero_division=0,
        ),

        "validation_recall": recall_score(
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

        "test_precision": precision_score(
            y_test,
            test_pred,
            zero_division=0,
        ),

        "test_recall": recall_score(
            y_test,
            test_pred,
            zero_division=0,
        ),
    }

    results.append(result)

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


# ------------------------------------------------------------
# Select model using validation PR-AUC
# ------------------------------------------------------------

comparison = pd.DataFrame(results)

best_row = comparison.sort_values(
    "validation_pr_auc",
    ascending=False,
).iloc[0]

best_name = best_row["model"]

best_model = trained_models[best_name]


# ------------------------------------------------------------
# Save report
# ------------------------------------------------------------

comparison.to_csv(
    REPORT_FILE,
    index=False,
)


# ------------------------------------------------------------
# Save best model
# ------------------------------------------------------------

joblib.dump(
    {
        "model": best_model,
        "features": features,
        "threshold": 0.45,
        "selection_metric": "validation_pr_auc",
        "model_name": best_name,
    },
    BEST_MODEL_FILE,
)


# ------------------------------------------------------------
# Final report
# ------------------------------------------------------------

print("\n========================================")
print("MODEL COMPARISON COMPLETE")
print("========================================")

print(
    comparison[
        [
            "model",
            "validation_roc_auc",
            "validation_pr_auc",
            "validation_f1",
            "test_roc_auc",
            "test_pr_auc",
            "test_f1",
        ]
    ].to_string(index=False)
)

print(
    "\nSelected model:",
    best_name,
)

print(
    "Selection metric: validation PR-AUC"
)

print(
    "\nSaved:",
    BEST_MODEL_FILE,
)

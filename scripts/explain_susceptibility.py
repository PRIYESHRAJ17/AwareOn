from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.inspection import permutation_importance


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT / "data/processed/features/static_ml_features_validated.csv"
)

GT_DIR = ROOT / "data/processed/ground_truth"

VAL_FILE = GT_DIR / "ground_truth_validation.csv"
TEST_FILE = GT_DIR / "ground_truth_test.csv"

MODEL_FILE = (
    ROOT / "data/processed/models/best_susceptibility_model.joblib"
)

OUT_DIR = ROOT / "data/processed/models"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GLOBAL_OUTPUT = OUT_DIR / "permutation_importance.csv"
LOCAL_OUTPUT = OUT_DIR / "local_explanations.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)
df["cell_id"] = df["cell_id"].astype(str)

val_ids = set(
    pd.read_csv(VAL_FILE)["cell_id"].astype(str)
)

test_ids = set(
    pd.read_csv(TEST_FILE)["cell_id"].astype(str)
)

validation = df[
    df["cell_id"].isin(val_ids)
].copy()

test = df[
    df["cell_id"].isin(test_ids)
].copy()


# ------------------------------------------------------------
# Load selected model
# ------------------------------------------------------------

bundle = joblib.load(MODEL_FILE)

model = bundle["model"]
feature_columns = bundle["features"]


X_val = validation[feature_columns]
y_val = validation["label"]

X_test = test[feature_columns]


# ------------------------------------------------------------
# Global permutation importance
# ------------------------------------------------------------

print("Calculating permutation importance...")

perm = permutation_importance(
    model,
    X_val,
    y_val,
    scoring="average_precision",
    n_repeats=20,
    random_state=42,
    n_jobs=-1,
)

importance = pd.DataFrame(
    {
        "feature": feature_columns,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }
).sort_values(
    "importance_mean",
    ascending=False,
).reset_index(drop=True)

importance.to_csv(
    GLOBAL_OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Local explanation helper
# ------------------------------------------------------------

def explain_row(row):

    values = row[feature_columns].astype(float)

    base_probability = float(
        model.predict_proba(
            pd.DataFrame([values])
        )[0, 1]
    )

    contributions = []

    # Random Forest local explanation:
    # replace one feature with its validation median and
    # measure probability change.
    medians = X_val.median()

    for feature in feature_columns:

        modified = values.copy()

        modified[feature] = medians[feature]

        modified_probability = float(
            model.predict_proba(
                pd.DataFrame([modified])
            )[0, 1]
        )

        contribution = (
            base_probability
            - modified_probability
        )

        contributions.append(
            (
                feature,
                contribution,
                float(values[feature]),
            )
        )

    contributions.sort(
        key=lambda x: abs(x[1]),
        reverse=True,
    )

    top = contributions[:5]

    result = {
        "cell_id": row["cell_id"],
        "label": int(row["label"]),
        "risk_probability": base_probability,
    }

    for i, (feature, contribution, value) in enumerate(top, 1):

        result[f"factor_{i}"] = feature
        result[f"factor_{i}_contribution"] = contribution
        result[f"factor_{i}_value"] = value

    return result


# ------------------------------------------------------------
# Local explanations for test cells
# ------------------------------------------------------------

print("Generating local explanations...")

local_rows = []

for _, row in test.iterrows():
    local_rows.append(
        explain_row(row)
    )

local = pd.DataFrame(local_rows)

local.to_csv(
    LOCAL_OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 18 EXPLAINABILITY COMPLETE")
print("========================================")

print("\nGlobal permutation importance:")
print(
    importance.head(15).to_string(index=False)
)

print("\nLocal explanations generated:", len(local))

print("\nTop local example:")
print(
    local.head(1).T.to_string(
        header=False
    )
)

print("\nGlobal output:")
print(GLOBAL_OUTPUT)

print("\nLocal output:")
print(LOCAL_OUTPUT)

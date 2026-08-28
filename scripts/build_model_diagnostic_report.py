from pathlib import Path
import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = ROOT / "data/processed/models"

BASELINE_MODEL = MODEL_DIR / "baseline_random_forest.joblib"
IMPORTANCE_FILE = MODEL_DIR / "baseline_feature_importance.csv"
ROAD_BIAS_FILE = MODEL_DIR / "road_bias_check.csv"
THRESHOLD_FILE = MODEL_DIR / "threshold_optimization.csv"

OUTPUT = MODEL_DIR / "model_diagnostic_report.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

bundle = joblib.load(BASELINE_MODEL)

importance = pd.read_csv(IMPORTANCE_FILE)
road_bias = pd.read_csv(ROAD_BIAS_FILE)
thresholds = pd.read_csv(THRESHOLD_FILE)


# ------------------------------------------------------------
# Best threshold
# ------------------------------------------------------------

best_threshold_row = thresholds.loc[
    thresholds["f1"].idxmax()
]

best_threshold = float(
    best_threshold_row["threshold"]
)


# ------------------------------------------------------------
# Road-bias results
# ------------------------------------------------------------

full_model = road_bias[
    road_bias["model"] == "FULL MODEL"
].iloc[0]

no_road_model = road_bias[
    road_bias["model"] == "NO ROAD FEATURES"
].iloc[0]

terrain_model = road_bias[
    road_bias["model"] == "TERRAIN ONLY"
].iloc[0]


# ------------------------------------------------------------
# Diagnostic summary
# ------------------------------------------------------------

rows = [
    {
        "diagnostic": "Full model test ROC-AUC",
        "value": full_model["test_roc_auc"],
    },
    {
        "diagnostic": "Full model test PR-AUC",
        "value": full_model["test_pr_auc"],
    },
    {
        "diagnostic": "Full model test F1",
        "value": full_model["test_f1"],
    },
    {
        "diagnostic": "No-road test ROC-AUC",
        "value": no_road_model["test_roc_auc"],
    },
    {
        "diagnostic": "Terrain-only test ROC-AUC",
        "value": terrain_model["test_roc_auc"],
    },
    {
        "diagnostic": "Road-feature ROC-AUC contribution",
        "value": (
            full_model["test_roc_auc"]
            - no_road_model["test_roc_auc"]
        ),
    },
    {
        "diagnostic": "Optimal validation threshold",
        "value": best_threshold,
    },
    {
        "diagnostic": "Threshold validation F1",
        "value": best_threshold_row["f1"],
    },
]


report = pd.DataFrame(rows)
report.to_csv(
    OUTPUT,
    index=False,
)



# ------------------------------------------------------------
# Print report

# ------------------------------------------------------------

print("\n========================================")
print("STEP 16.5 MODEL DIAGNOSTIC REPORT")

print("========================================")

print(report.to_string(index=False))

print("\nTop 10 features:")
print(
    importance.head(10)
    .to_string(index=False)
)

print("\nRoad-bias comparison:")
print(
    road_bias[
        [
            "model",
            "test_roc_auc",
            "test_pr_auc",
            "test_f1",
        ]
    ].to_string(index=False)
)

print("\nCalibration decision:")
print(
    "Original RF retained as primary model "
    "because calibrated Brier was higher."
)

print("\nOutput:")
print(OUTPUT)

print("\nMODEL DIAGNOSTICS COMPLETE ✅")

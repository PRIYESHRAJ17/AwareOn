from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ENGINES = ROOT / "data/processed/engines"
INTELLIGENCE = ROOT / "data/processed/intelligence"

STATE_FILE = (
    INTELLIGENCE / "awareon_intelligence_state.csv"
)

OUTPUT = (
    INTELLIGENCE / "intelligence_state_validation.csv"
)


# ------------------------------------------------------------
# Expected engine outputs
# ------------------------------------------------------------

engine_files = {
    "susceptibility": "susceptibility_engine_output.csv",
    "terrain": "terrain_instability_engine_output.csv",
    "exposure": "exposure_impact_engine_output.csv",
    "spatial": "spatial_propagation_engine_output.csv",
    "confidence": "confidence_uncertainty_engine_output.csv",
    "explanation": "explanation_recommendation_engine_output.csv",
}


# ------------------------------------------------------------
# Load master state
# ------------------------------------------------------------

state = pd.read_csv(STATE_FILE)

state["cell_id"] = state["cell_id"].astype(str)

if state["cell_id"].duplicated().any():
    raise RuntimeError("Duplicate cell IDs in intelligence state.")


master_ids = set(state["cell_id"])


# ------------------------------------------------------------
# Validate each spatial engine
# ------------------------------------------------------------

results = []

for engine_name, filename in engine_files.items():

    path = ENGINES / filename

    if not path.exists():
        results.append(
            {
                "engine": engine_name,
                "status": "MISSING_FILE",
                "rows": 0,
                "missing_from_state": len(master_ids),
                "extra_cells": 0,
            }
        )
        continue

    df = pd.read_csv(path)

    df["cell_id"] = df["cell_id"].astype(str)

    ids = set(df["cell_id"])

    missing_from_state = master_ids - ids
    extra_cells = ids - master_ids

    duplicate_count = int(
        df["cell_id"].duplicated().sum()
    )

    status = "OK"

    if missing_from_state:
        status = "MISSING_CELLS"

    elif extra_cells:
        status = "EXTRA_CELLS"

    elif duplicate_count:
        status = "DUPLICATES"

    results.append(
        {
            "engine": engine_name,
            "status": status,
            "rows": len(df),
            "missing_from_state": len(
                missing_from_state
            ),
            "extra_cells": len(extra_cells),
        }
    )


report = pd.DataFrame(results)


# ------------------------------------------------------------
# Unified-state missing-value check
# ------------------------------------------------------------

missing_values = (
    state.isna()
    .sum()
    .sort_values(ascending=False)
)

missing_nonzero = missing_values[
    missing_values > 0
]


# ------------------------------------------------------------
# Risk range checks
# ------------------------------------------------------------

if not state[
    "susceptibility_probability"
].between(0, 1).all():
    raise RuntimeError(
        "Invalid susceptibility probability."
    )

if not state[
    "unified_risk_score"
].between(0, 100).all():
    raise RuntimeError(
        "Unified risk score outside 0-100."
    )

if not state[
    "confidence_score"
].between(0, 100).all():
    raise RuntimeError(
        "Confidence score outside 0-100."
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

report.to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 21.2 INTELLIGENCE STATE QA")
print("========================================")

print("\nEngine consistency:")
print(
    report.to_string(index=False)
)

print(
    "\nState rows:",
    len(state)
)

print(
    "Unique cell IDs:",
    state["cell_id"].nunique()
)

print(
    "Missing state values:",
    int(state.isna().sum().sum())
)

if missing_nonzero.empty:
    print("All state values present: YES")
else:
    print(
        "\nNon-zero missing values:"
    )
    print(missing_nonzero.to_string())


print(
    "\nUnified risk range:",
    round(state["unified_risk_score"].min(), 3),
    "to",
    round(state["unified_risk_score"].max(), 3),
)

print(
    "\nConfidence range:",
    round(state["confidence_score"].min(), 3),
    "to",
    round(state["confidence_score"].max(), 3),
)

print("\nValidation output:")
print(OUTPUT)

print("\nSTEP 21.2 COMPLETE ✅")

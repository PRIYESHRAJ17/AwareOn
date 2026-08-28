from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INCIDENT_FILE = (
    ROOT / "data/processed/intelligence/awareon_incidents.csv"
)

OUT_DIR = ROOT / "data/processed/intelligence"

OUTPUT = (
    OUT_DIR / "awareon_prioritized_incidents.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

incidents = pd.read_csv(INCIDENT_FILE)

if incidents.empty:
    raise RuntimeError(
        "No incidents/risk zones available."
    )


# ------------------------------------------------------------
# Normalize components
# ------------------------------------------------------------

def normalize(series):
    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            50.0,
            index=series.index,
        )

    return (
        (series - minimum)
        / (maximum - minimum)
        * 100.0
    )


incidents["risk_component"] = normalize(
    incidents["max_risk_score"]
)

incidents["mean_risk_component"] = normalize(
    incidents["mean_risk_score"]
)

incidents["priority_component"] = normalize(
    incidents["max_alert_priority"]
)

incidents["size_component"] = normalize(
    incidents["cell_count"]
)


# ------------------------------------------------------------
# Priority score
# ------------------------------------------------------------

incidents["priority_score"] = (
    0.45 * incidents["risk_component"]
    + 0.25 * incidents["priority_component"]
    + 0.20 * incidents["mean_risk_component"]
    + 0.10 * incidents["size_component"]
)


# ------------------------------------------------------------
# Priority level
# ------------------------------------------------------------

def classify(score):

    if score >= 80:
        return "P1_CRITICAL"

    if score >= 60:
        return "P2_HIGH"

    if score >= 35:
        return "P3_MODERATE"

    return "P4_LOW"


incidents["priority_level"] = (
    incidents["priority_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Rank
# ------------------------------------------------------------

incidents = incidents.sort_values(
    [
        "priority_score",
        "max_risk_score",
    ],
    ascending=False,
).reset_index(drop=True)

incidents["priority_rank"] = (
    incidents.index + 1
)


# ------------------------------------------------------------
# Operational recommendation
# ------------------------------------------------------------

def recommendation(level):

    if level == "P1_CRITICAL":
        return (
            "Immediate review and prioritized assessment."
        )

    if level == "P2_HIGH":
        return (
            "High-priority monitoring and infrastructure review."
        )

    if level == "P3_MODERATE":
        return (
            "Enhanced monitoring recommended."
        )

    return (
        "Routine monitoring."
    )


incidents["priority_recommendation"] = (
    incidents["priority_level"]
    .apply(recommendation)
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

incidents.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 25")
print("AWAREON INCIDENT PRIORITIZATION")
print("========================================")

print(
    "Risk zones:",
    len(incidents),
)

print("\nPriority levels:")

print(
    incidents["priority_level"]
    .value_counts()
    .sort_index()
    .to_string()
)

print(
    "\nTop 10 priority zones:"
)

print(
    incidents[
        [
            "priority_rank",
            "incident_id",
            "priority_score",
            "priority_level",
            "max_risk_score",
            "cell_count",
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print(
    "\nOutput:"
)

print(OUTPUT)

print(
    "\nSTEP 25 COMPLETE ✅"
)

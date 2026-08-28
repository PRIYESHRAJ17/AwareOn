from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

STATE_FILE = (
    ROOT
    / "data/processed/intelligence/awareon_intelligence_state.csv"
)

DECISION_FILE = (
    ROOT
    / "data/processed/intelligence/awareon_risk_decisions.csv"
)

OUT_DIR = ROOT / "data/processed/intelligence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "awareon_alerts.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

state = pd.read_csv(STATE_FILE)
decision = pd.read_csv(DECISION_FILE)

state["cell_id"] = state["cell_id"].astype(str)
decision["cell_id"] = decision["cell_id"].astype(str)

data = decision.merge(
    state[
        [
            "cell_id",
            "rainfall_trigger_score",
            "soil_wetness_score",
            "spatial_pressure_score",
            "temporal_category",
            "anomaly_category",
            "sar_data_quality",
        ]
    ],
    on="cell_id",
    how="left",
)

if len(data) != len(decision):
    raise RuntimeError(
        "Alert merge changed row count."
    )


# ------------------------------------------------------------
# Alert logic
# ------------------------------------------------------------

def determine_alert(row):

    risk = float(row["unified_risk_score"])
    rainfall = float(row["rainfall_trigger_score"])
    soil = float(row["soil_wetness_score"])
    confidence = float(row["confidence_score"])

    temporal = str(row["temporal_category"])
    anomaly = str(row["anomaly_category"])

    # CRITICAL
    if (
        risk >= 75
        and confidence >= 60
        and (
            rainfall >= 75
            or soil >= 75
            or temporal == "EXTREME"
            or anomaly == "EXTREME"
        )
    ):
        return "CRITICAL", 1

    # HIGH
    if (
        risk >= 60
        and confidence >= 50
        and (
            rainfall >= 60
            or soil >= 60
            or temporal in ["HIGH", "EXTREME"]
            or anomaly in ["UNUSUAL", "EXTREME"]
        )
    ):
        return "HIGH", 1

    # WATCH
    if (
        risk >= 50
        and (
            rainfall >= 50
            or soil >= 50
            or temporal in ["HIGH", "EXTREME"]
        )
    ):
        return "WATCH", 0

    return "ROUTINE", 0


alerts = data.apply(
    determine_alert,
    axis=1,
    result_type="expand",
)

alerts.columns = [
    "alert_level",
    "should_alert",
]

data = pd.concat(
    [data, alerts],
    axis=1,
)


# ------------------------------------------------------------
# Priority score
# ------------------------------------------------------------

data["alert_priority_score"] = (
    0.45 * data["unified_risk_score"]
    + 0.25 * data["rainfall_trigger_score"]
    + 0.15 * data["soil_wetness_score"]
    + 0.15 * data["spatial_pressure_score"]
)


# ------------------------------------------------------------
# Alert reason
# ------------------------------------------------------------

def build_reason(row):

    reasons = []

    if row["unified_risk_score"] >= 60:
        reasons.append(
            "elevated landslide risk"
        )

    if row["rainfall_trigger_score"] >= 60:
        reasons.append(
            "elevated rainfall trigger"
        )

    if row["soil_wetness_score"] >= 60:
        reasons.append(
            "elevated soil wetness"
        )

    if row["spatial_pressure_score"] >= 60:
        reasons.append(
            "elevated neighbouring-cell risk"
        )

    if row["temporal_category"] in [
        "HIGH",
        "EXTREME",
    ]:
        reasons.append(
            "elevated temporal pressure"
        )

    if row["anomaly_category"] in [
        "UNUSUAL",
        "EXTREME",
    ]:
        reasons.append(
            "unusual environmental conditions"
        )

    if not reasons:
        reasons.append(
            "no current multi-signal escalation"
        )

    return "; ".join(reasons)


data["alert_reason"] = data.apply(
    build_reason,
    axis=1,
)


# ------------------------------------------------------------
# Recommended action
# ------------------------------------------------------------

def response(level):

    if level == "CRITICAL":
        return (
            "Immediate review and prioritized field assessment."
        )

    if level == "HIGH":
        return (
            "Increase monitoring and inspect exposed infrastructure."
        )

    if level == "WATCH":
        return (
            "Maintain enhanced monitoring and reassess changing conditions."
        )

    return "Routine monitoring."


data["alert_action"] = (
    data["alert_level"]
    .apply(response)
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "unified_risk_score",
    "confidence_score",
    "rainfall_trigger_score",
    "soil_wetness_score",
    "spatial_pressure_score",
    "temporal_category",
    "anomaly_category",
    "alert_priority_score",
    "alert_level",
    "should_alert",
    "alert_reason",
    "alert_action",
]

data[output_columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

if data["cell_id"].duplicated().any():
    raise RuntimeError(
        "Duplicate cell IDs in alert output."
    )

if data[output_columns].isna().sum().sum() > 0:
    raise RuntimeError(
        "Missing values found in alert output."
    )


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 23")
print("AWAREON ALERT INTELLIGENCE ENGINE")
print("========================================")

print(
    "Cells processed:",
    len(data),
)

print("\nAlert levels:")
print(
    data["alert_level"]
    .value_counts()
    .to_string()
)

print(
    "\nCells generating alerts:",
    int(data["should_alert"].sum()),
)

print(
    "Mean alert priority:",
    round(
        data["alert_priority_score"].mean(),
        2,
    ),
)

print("\nTop alert locations:")

print(
    data[
        [
            "cell_id",
            "alert_level",
            "alert_priority_score",
            "alert_reason",
        ]
    ]
    .sort_values(
        "alert_priority_score",
        ascending=False,
    )
    .head(10)
    .to_string(index=False)
)

print("\nOutput:")
print(OUTPUT)

print("\nSTEP 23 COMPLETE ✅")

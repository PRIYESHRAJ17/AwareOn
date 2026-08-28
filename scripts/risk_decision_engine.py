from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

STATE_FILE = (
    ROOT
    / "data/processed/intelligence/awareon_intelligence_state.csv"
)

OUT_DIR = ROOT / "data/processed/intelligence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "awareon_risk_decisions.csv"
)


# ------------------------------------------------------------
# Load intelligence state
# ------------------------------------------------------------

df = pd.read_csv(STATE_FILE)

if df.empty:
    raise RuntimeError("Intelligence state is empty.")


# ------------------------------------------------------------
# Decision thresholds
# ------------------------------------------------------------

def severity(score):

    if score >= 75:
        return "EXTREME"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MODERATE"

    return "LOW"


# ------------------------------------------------------------
# Determine warning state
# ------------------------------------------------------------

def warning_state(row):

    risk = float(row["unified_risk_score"])

    rainfall = float(
        row["rainfall_trigger_score"]
    )

    terrain = float(
        row["terrain_instability_score"]
    )

    spatial = float(
        row["spatial_pressure_score"]
    )

    confidence = float(
        row["confidence_score"]
    )

    # Immediate warning conditions.
    if (
        risk >= 75
        and confidence >= 60
    ):
        return "CRITICAL"

    if (
        risk >= 50
        and rainfall >= 75
        and confidence >= 50
    ):
        return "WARNING"

    if (
        risk >= 50
        and terrain >= 70
    ):
        return "WARNING"

    if (
        spatial >= 75
        and risk >= 40
    ):
        return "WATCH"

    if risk >= 50:
        return "WATCH"

    return "NORMAL"


# ------------------------------------------------------------
# Identify dominant drivers
# ------------------------------------------------------------

def dominant_drivers(row):

    signals = {
        "susceptibility": float(
            row["susceptibility_probability"]
        ) * 100.0,

        "terrain_instability": float(
            row["terrain_instability_score"]
        ),

        "exposure": float(
            row["exposure_score"]
        ),

        "spatial_pressure": float(
            row["spatial_pressure_score"]
        ),

        "rainfall_trigger": float(
            row["rainfall_trigger_score"]
        ),

        "soil_wetness": float(
            row["soil_wetness_score"]
        ),
    }

    ordered = sorted(
        signals.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return ordered


# ------------------------------------------------------------
# Recommended response
# ------------------------------------------------------------

def recommendation(
    warning,
    severity_level,
    confidence,
    dominant,
):

    if warning == "CRITICAL":
        return (
            "Prioritize immediate field assessment; "
            "review nearby infrastructure and consider "
            "enhanced warning/monitoring procedures."
        )

    if warning == "WARNING":
        return (
            "Increase monitoring frequency; "
            "inspect exposed roads/settlements and "
            "review current rainfall and terrain conditions."
        )

    if warning == "WATCH":
        return (
            "Maintain enhanced monitoring and review "
            "changes in rainfall, soil wetness and "
            "neighboring risk."
        )

    if severity_level == "MODERATE":
        return (
            "Continue routine monitoring with attention "
            "to changing environmental conditions."
        )

    return (
        "No immediate escalation indicated; "
        "continue routine monitoring."
    )


# ------------------------------------------------------------
# Build decisions
# ------------------------------------------------------------

records = []

for _, row in df.iterrows():

    risk = float(
        row["unified_risk_score"]
    )

    confidence = float(
        row["confidence_score"]
    )

    uncertainty = float(
        row["uncertainty_score"]
    )

    severity_level = severity(risk)

    warning = warning_state(row)

    drivers = dominant_drivers(row)

    dominant_names = [
        item[0]
        for item in drivers[:3]
    ]

    dominant_scores = [
        round(item[1], 2)
        for item in drivers[:3]
    ]

    action = recommendation(
        warning,
        severity_level,
        confidence,
        dominant_names,
    )

    records.append(
        {
            "cell_id": row["cell_id"],

            "unified_risk_score": risk,
            "severity": severity_level,
            "warning_state": warning,

            "confidence_score": confidence,
            "uncertainty_score": uncertainty,

            "driver_1": dominant_names[0],
            "driver_1_score": dominant_scores[0],

            "driver_2": dominant_names[1],
            "driver_2_score": dominant_scores[1],

            "driver_3": dominant_names[2],
            "driver_3_score": dominant_scores[2],

            "rainfall_trigger_category": (
                row["rainfall_trigger_category"]
            ),

            "soil_wetness_category": (
                row["soil_wetness_category"]
            ),

            "temporal_trajectory": (
                row["temporal_trajectory"]
            ),

            "environment_anomaly_category": (
                row["anomaly_category"]
            ),

            "recommendation": action,
        }
    )


result = pd.DataFrame(records)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

if len(result) != len(df):
    raise RuntimeError(
        "Decision engine lost rows."
    )

if result["cell_id"].duplicated().any():
    raise RuntimeError(
        "Duplicate cell IDs in risk decisions."
    )

if result[
    "unified_risk_score"
].isna().any():
    raise RuntimeError(
        "Missing unified risk scores."
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 22")
print("AWAREON RISK DECISION ENGINE")
print("========================================")

print(
    "Cells processed:",
    len(result),
)

print("\nSeverity:")
print(
    result["severity"]
    .value_counts()
    .to_string()
)

print("\nWarning state:")
print(
    result["warning_state"]
    .value_counts()
    .to_string()
)

print("\nAverage confidence:",
      round(
          result["confidence_score"].mean(),
          2,
      )
)

print("\nCritical:", int(
    (result["warning_state"] == "CRITICAL").sum()
))

print("Warning:", int(
    (result["warning_state"] == "WARNING").sum()
))

print("Watch:", int(
    (result["warning_state"] == "WATCH").sum()
))

print("\nTop driver 1:")
print(
    result["driver_1"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nSTEP 22 COMPLETE ✅")

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ENGINES = ROOT / "data/processed/engines"
INTELLIGENCE = ROOT / "data/processed/intelligence"


# ------------------------------------------------------------
# Required outputs
# ------------------------------------------------------------

required_files = {
    "engine_01_susceptibility":
        ENGINES / "susceptibility_engine_output.csv",

    "engine_02_rainfall":
        ENGINES / "rainfall_trigger_engine_output.csv",

    "engine_03_soil":
        ENGINES / "soil_wetness_engine_output.csv",

    "engine_04_terrain":
        ENGINES / "terrain_instability_engine_output.csv",

    "engine_05_sar":
        ENGINES / "sar_evidence_engine_output.csv",

    "engine_06_history":
        ENGINES / "historical_event_engine_output.csv",

    "engine_07_anomaly":
        ENGINES / "anomaly_detection_engine_output.csv",

    "engine_08_exposure":
        ENGINES / "exposure_impact_engine_output.csv",

    "engine_09_spatial":
        ENGINES / "spatial_propagation_engine_output.csv",

    "engine_10_temporal":
        ENGINES / "temporal_risk_engine_output.csv",

    "engine_11_confidence":
        ENGINES / "confidence_uncertainty_engine_output.csv",

    "engine_12_explanation":
        ENGINES / "explanation_recommendation_engine_output.csv",

    "intelligence_state":
        INTELLIGENCE / "awareon_intelligence_state.csv",

    "state_validation":
        INTELLIGENCE / "intelligence_state_validation.csv",

    "risk_decisions":
        INTELLIGENCE / "awareon_risk_decisions.csv",

    "alerts":
        INTELLIGENCE / "awareon_alerts.csv",

    "incidents":
        INTELLIGENCE / "awareon_incidents.csv",

    "prioritized_incidents":
        INTELLIGENCE / "awareon_prioritized_incidents.csv",

    "historical_current":
        INTELLIGENCE / "historical_current_correlation.csv",

    "scenario_analysis":
        ENGINES / "counterfactual_risk_output.csv",
}


# ------------------------------------------------------------
# Check existence
# ------------------------------------------------------------

print("\n========================================")
print("STEP 29")
print("AWAREON INTELLIGENCE FINAL AUDIT")
print("========================================")

missing_files = []

for name, path in required_files.items():

    exists = path.exists()

    print(
        f"{name:<28}",
        "OK" if exists else "MISSING"
    )

    if not exists:
        missing_files.append(name)


if missing_files:
    raise RuntimeError(
        "Missing required outputs: "
        + ", ".join(missing_files)
    )


# ------------------------------------------------------------
# Load core datasets
# ------------------------------------------------------------

state = pd.read_csv(
    required_files["intelligence_state"]
)

decisions = pd.read_csv(
    required_files["risk_decisions"]
)

alerts = pd.read_csv(
    required_files["alerts"]
)

incidents = pd.read_csv(
    required_files["incidents"]
)

prioritized = pd.read_csv(
    required_files["prioritized_incidents"]
)

history_current = pd.read_csv(
    required_files["historical_current"]
)

scenario = pd.read_csv(
    required_files["scenario_analysis"]
)


# ------------------------------------------------------------
# Core row-count checks
# ------------------------------------------------------------

checks = []

checks.append(
    (
        "intelligence_state_rows",
        len(state) == 1298,
    )
)

checks.append(
    (
        "risk_decision_rows",
        len(decisions) == 1298,
    )
)

checks.append(
    (
        "alert_rows",
        len(alerts) == 1298,
    )
)

checks.append(
    (
        "scenario_rows",
        len(scenario) == 5192,
    )
)

checks.append(
    (
        "historical_current_rows",
        len(history_current) > 0,
    )
)

checks.append(
    (
        "incident_rows",
        len(incidents) >= 0,
    )
)

checks.append(
    (
        "priority_rows",
        len(prioritized) == len(incidents),
    )
)


# ------------------------------------------------------------
# Cell-ID integrity
# ------------------------------------------------------------

checks.append(
    (
        "unique_state_cells",
        state["cell_id"].nunique() == 1298,
    )
)

checks.append(
    (
        "unique_decision_cells",
        decisions["cell_id"].nunique() == 1298,
    )
)

checks.append(
    (
        "unique_alert_cells",
        alerts["cell_id"].nunique() == 1298,
    )
)


# ------------------------------------------------------------
# Missing-value checks
# ------------------------------------------------------------

checks.append(
    (
        "state_no_missing",
        state.isna().sum().sum() == 0,
    )
)

checks.append(
    (
        "decisions_no_missing",
        decisions.isna().sum().sum() == 0,
    )
)

checks.append(
    (
        "alerts_no_missing",
        alerts.isna().sum().sum() == 0,
    )
)

checks.append(
    (
        "scenario_no_missing",
        scenario.isna().sum().sum() == 0,
    )
)


# ------------------------------------------------------------
# Range checks
# ------------------------------------------------------------

checks.append(
    (
        "susceptibility_0_1",
        state[
            "susceptibility_probability"
        ].between(0, 1).all(),
    )
)

checks.append(
    (
        "risk_score_0_100",
        state[
            "unified_risk_score"
        ].between(0, 100).all(),
    )
)

checks.append(
    (
        "confidence_0_100",
        state[
            "confidence_score"
        ].between(0, 100).all(),
    )
)

checks.append(
    (
        "scenario_risk_0_100",
        scenario[
            "risk_score"
        ].between(0, 100).all(),
    )
)


# ------------------------------------------------------------
# Scenario structure
# ------------------------------------------------------------

scenario_names = set(
    scenario["scenario"]
)

expected_scenarios = {
    "BASELINE",
    "RAINFALL_PLUS_25_PERCENT",
    "RAINFALL_PLUS_50_PERCENT",
    "RAINFALL_PLUS_100_PERCENT",
}

checks.append(
    (
        "all_four_scenarios",
        scenario_names == expected_scenarios,
    )
)


# ------------------------------------------------------------
# Priority rank integrity
# ------------------------------------------------------------

if len(prioritized) > 0:

    checks.append(
        (
            "unique_priority_ranks",
            prioritized[
                "priority_rank"
            ].nunique()
            == len(prioritized),
        )
    )


# ------------------------------------------------------------
# Print checks
# ------------------------------------------------------------

print("\nIntegrity checks:")

failed = []

for name, passed in checks:

    print(
        f"{name:<32}",
        "PASS" if passed else "FAIL"
    )

    if not passed:
        failed.append(name)


# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

print("\n========================================")

if failed:

    print("AUDIT FAILED ❌")

    print("\nFailed checks:")
    for name in failed:
        print(" -", name)

    raise SystemExit(1)

else:

    print("AUDIT PASSED ✅")


print("========================================")

print("\nCore intelligence cells:", len(state))
print("Risk decisions:", len(decisions))
print("Alerts:", len(alerts))
print("Risk zones/incidents:", len(incidents))
print("Scenario rows:", len(scenario))

print(
    "\nIntelligence layer is ready for backend integration."
)

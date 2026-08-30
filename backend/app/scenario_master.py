from __future__ import annotations

from typing import Any


def build_scenario_master(
    summary: dict[str, Any],
    comparison: dict[str, Any],
    sensitivity: dict[str, Any],
    priority: dict[str, Any],
    recommendation: dict[str, Any],
    decision: dict[str, Any],
    spatial: dict[str, Any],
    curve: dict[str, Any],
    thresholds: dict[str, Any],
    forecast: dict[str, Any],
    uncertainty: dict[str, Any],
) -> dict[str, Any]:

    required = {
        "summary": summary,
        "comparison": comparison,
        "sensitivity": sensitivity,
        "priority": priority,
        "recommendation": recommendation,
        "decision": decision,
        "spatial": spatial,
        "curve": curve,
        "thresholds": thresholds,
        "forecast": forecast,
        "uncertainty": uncertainty,
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise ValueError(
            "Scenario master is missing: "
            + ", ".join(missing)
        )

    scenarios = summary.get(
        "scenarios",
        [],
    )

    scenario_count = len(
        scenarios
    )

    return {
        "engine": "AWAREON_SCENARIO_INTELLIGENCE",

        "version": "1.0",

        "status": "READY",

        "scenario_count": scenario_count,

        "supported_parameter":
            summary.get(
                "supported_parameter"
            ),

        "soil_scenario_available":
            summary.get(
                "soil_scenario_available",
                False,
            ),

        "scenario_summary":
            summary,

        "comparison":
            comparison,

        "sensitivity":
            {
                "record_count":
                    sensitivity.get(
                        "record_count"
                    ),

                "escalating_cells":
                    sensitivity.get(
                        "escalating_cells"
                    ),

                "high_or_extreme_escalations":
                    sensitivity.get(
                        "high_or_extreme_escalations"
                    ),

                "extreme_escalations":
                    sensitivity.get(
                        "extreme_escalations"
                    ),

                "very_high_sensitivity_cells":
                    sensitivity.get(
                        "very_high_sensitivity_cells"
                    ),

                "top_cells":
                    sensitivity.get(
                        "top_cells",
                        [],
                    )[:25],
            },

        "priority":
            priority,

        "recommendation":
            recommendation,

        "decision":
            decision,

        "spatial":
            {
                "scenario":
                    spatial.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    spatial.get(
                        "rainfall_change_percent"
                    ),

                "cell_count":
                    spatial.get(
                        "cell_count"
                    ),

                "escalating_cells":
                    spatial.get(
                        "escalating_cells"
                    ),

                "category_change_cells":
                    spatial.get(
                        "category_change_cells"
                    ),

                "new_high_or_extreme_cells":
                    spatial.get(
                        "new_high_or_extreme_cells"
                    ),

                "new_extreme_cells":
                    spatial.get(
                        "new_extreme_cells"
                    ),

                "top_sensitive_cells":
                    spatial.get(
                        "top_sensitive_cells",
                        [],
                    )[:25],

                "highest_risk_cells":
                    spatial.get(
                        "highest_risk_cells",
                        [],
                    )[:25],
            },

        "curve":
            curve,

        "thresholds":
            thresholds,

        "forecast":
            forecast,

        "uncertainty":
            uncertainty,

        "master_signal":
            {
                "scenario":
                    decision.get(
                        "scenario"
                    ),

                "operational_posture":
                    decision.get(
                        "operational_posture"
                    ),

                "recommendation_level":
                    decision.get(
                        "recommendation_level"
                    ),

                "headline":
                    decision.get(
                        "headline"
                    ),

                "trajectory":
                    forecast.get(
                        "trajectory_class"
                    ),

                "trajectory_confidence":
                    forecast.get(
                        "confidence"
                    ),

                "transition_region":
                    forecast.get(
                        "transition_region"
                    ),

                "early_warning":
                    forecast.get(
                        "early_warning_point"
                    ),

                "uncertainty":
                    uncertainty.get(
                        "uncertainty_level"
                    ),
            },

        "evidence_contract":
            {
                "tested_scenarios":
                    [
                        {
                            "scenario":
                                item.get(
                                    "scenario"
                                ),

                            "rainfall_change_percent":
                                item.get(
                                    "rainfall_change_percent"
                                ),
                        }
                        for item in scenarios
                    ],

                "supported_evidence":
                    uncertainty.get(
                        "supported_evidence",
                        [],
                    ),

                "derived_inferences":
                    uncertainty.get(
                        "derived_inferences",
                        [],
                    ),

                "unsupported_claims":
                    uncertainty.get(
                        "unsupported_claims",
                        [],
                    ),

                "boundaries":
                    uncertainty.get(
                        "boundaries",
                        [],
                    ),
            },

        "capabilities": [
            "SCENARIO_COMPARISON",
            "CELL_SENSITIVITY",
            "SPATIAL_PRIORITY",
            "DECISION_RECOMMENDATION",
            "SCENARIO_MAP",
            "RESPONSE_CURVE",
            "THRESHOLD_DETECTION",
            "TRAJECTORY_ANALYSIS",
            "UNCERTAINTY_BOUNDARY",
        ],
    }

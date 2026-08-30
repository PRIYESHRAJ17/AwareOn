from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

ENGINES_DIR = (
    ROOT
    / "data"
    / "processed"
    / "engines"
)

SCENARIO_FILE = (
    ENGINES_DIR
    / "scenario_simulation_engine_output.csv"
)

COUNTERFACTUAL_FILE = (
    ENGINES_DIR
    / "counterfactual_risk_output.csv"
)


# ============================================================
# SERVICE
# ============================================================

class ScenarioService:

    # --------------------------------------------------------
    # Load scenario trigger table
    # --------------------------------------------------------

    def load_scenario_table(self):

        if not SCENARIO_FILE.exists():

            raise FileNotFoundError(
                f"Scenario file not found: "
                f"{SCENARIO_FILE}"
            )

        df = pd.read_csv(
            SCENARIO_FILE
        )

        required = {
            "scenario",
            "rainfall_change_percent",
            "rain_24h_mm",
            "rain_72h_mm",
            "rain_7d_mm",
            "rain_24h_percentile",
            "rain_72h_percentile",
            "rain_7d_percentile",
            "rainfall_trigger_score",
            "trigger_category",
            "trigger_score_change_from_baseline",
        }

        missing = (
            required
            - set(df.columns)
        )

        if missing:

            raise RuntimeError(
                "Scenario simulation file "
                f"is missing columns: "
                f"{sorted(missing)}"
            )

        return df


    # --------------------------------------------------------
    # Load counterfactual table
    # --------------------------------------------------------

    def load_counterfactual_table(self):

        if not COUNTERFACTUAL_FILE.exists():

            raise FileNotFoundError(
                f"Counterfactual file not found: "
                f"{COUNTERFACTUAL_FILE}"
            )

        df = pd.read_csv(
            COUNTERFACTUAL_FILE
        )

        required = {
            "cell_id",
            "scenario",
            "rainfall_change_percent",
            "risk_score",
            "baseline_risk_score",
            "risk_score_change",
            "risk_category",
            "rainfall_trigger_score",
            "susceptibility_probability",
            "exposure_score",
            "baseline_category",
            "category_change",
            "escalates",
        }

        missing = (
            required
            - set(df.columns)
        )

        if missing:

            raise RuntimeError(
                "Counterfactual file "
                f"is missing columns: "
                f"{sorted(missing)}"
            )

        df["cell_id"] = (
            df["cell_id"]
            .astype(str)
        )

        return df


    # --------------------------------------------------------
    # Overall scenario summary
    # --------------------------------------------------------

    def get_summary(self):

        scenarios = (
            self.load_scenario_table()
        )

        counterfactual = (
            self.load_counterfactual_table()
        )


        baseline_rows = (
            counterfactual[
                counterfactual["scenario"]
                ==
                "BASELINE"
            ]
        )


        summary = []


        for _, row in (
            scenarios.iterrows()
        ):

            scenario_name = str(
                row["scenario"]
            )


            cf = (
                counterfactual[
                    counterfactual["scenario"]
                    ==
                    scenario_name
                ]
            )


            summary.append(
                {
                    "scenario":
                        scenario_name,

                    "rainfall_change_percent":
                        float(
                            row[
                                "rainfall_change_percent"
                            ]
                        ),

                    "rain_24h_mm":
                        float(
                            row[
                                "rain_24h_mm"
                            ]
                        ),

                    "rain_72h_mm":
                        float(
                            row[
                                "rain_72h_mm"
                            ]
                        ),

                    "rain_7d_mm":
                        float(
                            row[
                                "rain_7d_mm"
                            ]
                        ),

                    "rainfall_trigger_score":
                        float(
                            row[
                                "rainfall_trigger_score"
                            ]
                        ),

                    "trigger_category":
                        str(
                            row[
                                "trigger_category"
                            ]
                        ),

                    "trigger_score_change_from_baseline":
                        float(
                            row[
                                "trigger_score_change_from_baseline"
                            ]
                        ),

                    "cells":
                        int(
                            len(cf)
                        ),

                    "escalating_cells":
                        int(
                            cf[
                                "escalates"
                            ].sum()
                        ),

                    "new_high_or_extreme":
                        int(
                            (
                                (
                                    cf[
                                        "risk_category"
                                    ]
                                    .isin(
                                        [
                                            "HIGH",
                                            "EXTREME",
                                        ]
                                    )
                                )
                                &
                                (
                                    ~cf[
                                        "baseline_category"
                                    ]
                                    .isin(
                                        [
                                            "HIGH",
                                            "EXTREME",
                                        ]
                                    )
                                )
                            ).sum()
                        ),

                    "new_extreme_cells":
                        int(
                            (
                                (
                                    cf[
                                        "risk_category"
                                    ]
                                    ==
                                    "EXTREME"
                                )
                                &
                                (
                                    cf[
                                        "baseline_category"
                                    ]
                                    !=
                                    "EXTREME"
                                )
                            ).sum()
                        ),

                    "mean_risk_score":
                        float(
                            cf[
                                "risk_score"
                            ].mean()
                        ),

                    "max_risk_score":
                        float(
                            cf[
                                "risk_score"
                            ].max()
                        ),

                    "mean_risk_change":
                        float(
                            cf[
                                "risk_score_change"
                            ].mean()
                        ),

                    "max_risk_change":
                        float(
                            cf[
                                "risk_score_change"
                            ].max()
                        ),
                }
            )


        return {
            "scenario_count":
                len(summary),

            "cell_count":
                int(
                    baseline_rows["cell_id"]
                    .nunique()
                ),

            "scenarios":
                summary,

            "supported_parameter":
                "rainfall",

            "soil_scenario_available":
                False,
        }


    # --------------------------------------------------------
    # Single cell scenario
    # --------------------------------------------------------

    def get_cell_scenarios(
        self,
        cell_id: str,
    ):

        target = str(
            cell_id
        )


        df = (
            self.load_counterfactual_table()
        )


        matches = df[
            df["cell_id"]
            ==
            target
        ]


        if matches.empty:

            return None


        records = []


        for _, row in (
            matches.iterrows()
        ):

            records.append(
                {
                    "scenario":
                        str(
                            row[
                                "scenario"
                            ]
                        ),

                    "rainfall_change_percent":
                        float(
                            row[
                                "rainfall_change_percent"
                            ]
                        ),

                    "risk_score":
                        float(
                            row[
                                "risk_score"
                            ]
                        ),

                    "baseline_risk_score":
                        float(
                            row[
                                "baseline_risk_score"
                            ]
                        ),

                    "risk_score_change":
                        float(
                            row[
                                "risk_score_change"
                            ]
                        ),

                    "risk_category":
                        str(
                            row[
                                "risk_category"
                            ]
                        ),

                    "baseline_category":
                        str(
                            row[
                                "baseline_category"
                            ]
                        ),

                    "category_change":
                        int(
                            row[
                                "category_change"
                            ]
                        ),

                    "escalates":
                        int(
                            row[
                                "escalates"
                            ]
                        ),
                }
            )


        return {
            "cell_id":
                target,

            "scenario_count":
                len(records),

            "scenarios":
                records,
        }


    # --------------------------------------------------------
    # Simulate supported rainfall scenarios
    # --------------------------------------------------------

    def simulate(
        self,
        rainfall_change_percent: float,
    ):

        requested = float(
            rainfall_change_percent
        )


        df = (
            self.load_counterfactual_table()
        )


        available = sorted(
            df[
                "rainfall_change_percent"
            ]
            .unique()
            .tolist()
        )


        # ----------------------------------------------------
        # Current engine supports:
        #
        # 0, 25, 50, 100
        #
        # Do not silently invent intermediate model outputs.
        # ----------------------------------------------------

        exact = None


        for value in available:

            if abs(
                float(value)
                -
                requested
            ) < 1e-9:

                exact = float(
                    value
                )

                break


        if exact is None:

            nearest = min(
                available,
                key=lambda value:
                    abs(
                        float(value)
                        -
                        requested
                    ),
            )


            return {
                "supported": False,

                "requested_rainfall_change_percent":
                    requested,

                "available_scenarios":
                    available,

                "message":
                    (
                        "The current "
                        "counterfactual engine "
                        "only contains the "
                        "precomputed rainfall "
                        "scenarios."
                    ),

                "nearest_available_scenario":
                    float(
                        nearest
                    ),
            }


        scenario_name = None


        if exact == 0:
            scenario_name = "BASELINE"

        elif exact == 25:
            scenario_name = (
                "RAINFALL_PLUS_25_PERCENT"
            )

        elif exact == 50:
            scenario_name = (
                "RAINFALL_PLUS_50_PERCENT"
            )

        elif exact == 100:
            scenario_name = (
                "RAINFALL_PLUS_100_PERCENT"
            )


        matches = df[
            df["rainfall_change_percent"]
            ==
            exact
        ]


        return {
            "supported":
                True,

            "scenario":
                scenario_name,

            "rainfall_change_percent":
                exact,

            "cell_count":
                int(
                    matches[
                        "cell_id"
                    ].nunique()
                ),

            "mean_risk_score":
                float(
                    matches[
                        "risk_score"
                    ].mean()
                ),

            "max_risk_score":
                float(
                    matches[
                        "risk_score"
                    ].max()
                ),

            "mean_risk_change":
                float(
                    matches[
                        "risk_score_change"
                    ].mean()
                ),

            "max_risk_change":
                float(
                    matches[
                        "risk_score_change"
                    ].max()
                ),

            "escalating_cells":
                int(
                    matches[
                        "escalates"
                    ].sum()
                ),

            "new_extreme_cells":
                int(
                    (
                        (
                            matches[
                                "risk_category"
                            ]
                            ==
                            "EXTREME"
                        )
                        &
                        (
                            matches[
                                "baseline_category"
                            ]
                            !=
                            "EXTREME"
                        )
                    ).sum()
                ),

            "records":
                matches.to_dict(
                    orient="records"
                ),
        }


# ============================================================
# SERVICE INSTANCE
# ============================================================

scenario_service = ScenarioService()

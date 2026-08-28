from backend.app.services.repository import repository


class AssessmentService:

    def get_assessment(
        self,
        cell_id: str,
    ) -> dict | None:

        risk = repository.find_cell(
            "awareon_risk_decisions.csv",
            cell_id,
        )

        state = repository.find_cell(
            "awareon_intelligence_state.csv",
            cell_id,
        )

        if risk is None or state is None:
            return None

        return {
            "cell_id": str(cell_id),

            "unified_risk_score": float(
                risk["unified_risk_score"]
            ),
            "severity": str(
                risk["severity"]
            ),
            "warning_state": str(
                risk["warning_state"]
            ),

            "susceptibility_probability": float(
                state["susceptibility_probability"]
            ),
            "susceptibility_category": str(
                state["susceptibility_category"]
            ),

            "terrain_instability_score": float(
                state["terrain_instability_score"]
            ),
            "terrain_instability_category": str(
                state["terrain_instability_category"]
            ),

            "exposure_score": float(
                state["exposure_score"]
            ),
            "exposure_category": str(
                state["exposure_category"]
            ),
            "dominant_exposure": str(
                state["dominant_exposure"]
            ),

            "spatial_pressure_score": float(
                state["spatial_pressure_score"]
            ),
            "spatial_category": str(
                state["spatial_category"]
            ),

            "rainfall_trigger_score": float(
                state["rainfall_trigger_score"]
            ),
            "rainfall_trigger_category": str(
                state["rainfall_trigger_category"]
            ),

            "soil_wetness_score": float(
                state["soil_wetness_score"]
            ),
            "soil_wetness_category": str(
                state["soil_wetness_category"]
            ),

            "temporal_trajectory": str(
                state["temporal_trajectory"]
            ),
            "temporal_category": str(
                state["temporal_category"]
            ),

            "environment_anomaly_score": float(
                state["anomaly_score"]
            ),
            "environment_anomaly_category": str(
                state["anomaly_category"]
            ),

            "confidence_score": float(
                state["confidence_score"]
            ),
            "uncertainty_score": float(
                state["uncertainty_score"]
            ),
            "confidence_category": str(
                state["confidence_category"]
            ),

            "driver_1": str(
                risk["driver_1"]
            ),
            "driver_1_score": float(
                risk["driver_1_score"]
            ),

            "driver_2": str(
                risk["driver_2"]
            ),
            "driver_2_score": float(
                risk["driver_2_score"]
            ),

            "driver_3": str(
                risk["driver_3"]
            ),
            "driver_3_score": float(
                risk["driver_3_score"]
            ),

            "recommendation": str(
                risk["recommendation"]
            ),
        }


assessment_service = AssessmentService()

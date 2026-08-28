from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    intelligence_dir_exists: bool
    engine_dir_exists: bool


class RiskRecord(BaseModel):
    cell_id: str

    unified_risk_score: float
    severity: str
    warning_state: str

    confidence_score: float
    uncertainty_score: float

    driver_1: str
    driver_1_score: float

    driver_2: str
    driver_2_score: float

    driver_3: str
    driver_3_score: float

    rainfall_trigger_category: str
    soil_wetness_category: str
    temporal_trajectory: str
    environment_anomaly_category: str

    recommendation: str


class RiskResponse(BaseModel):
    count: int
    data: list[RiskRecord]


class AlertRecord(BaseModel):
    cell_id: str

    unified_risk_score: float
    confidence_score: float

    rainfall_trigger_score: float
    soil_wetness_score: float
    spatial_pressure_score: float

    temporal_category: str
    anomaly_category: str

    alert_priority_score: float
    alert_level: str
    should_alert: int

    alert_reason: str
    alert_action: str


class AlertResponse(BaseModel):
    count: int
    data: list[AlertRecord]


class IncidentRecord(BaseModel):
    incident_id: str
    cell_count: int

    max_risk_score: float
    mean_risk_score: float
    max_alert_priority: float

    highest_decision_state: str
    active_alert_cells: int

    latitude: float
    longitude: float

    affected_cells: str
    incident_category: str


class IncidentResponse(BaseModel):
    count: int
    data: list[IncidentRecord]


class EngineInfo(BaseModel):
    engine_id: str
    name: str
    description: str
    output_file: str


class EngineRegistryResponse(BaseModel):
    count: int
    engines: list[EngineInfo]
class AssessmentResponse(BaseModel):
    cell_id: str

    # Core risk
    unified_risk_score: float
    severity: str
    warning_state: str

    # ML
    susceptibility_probability: float
    susceptibility_category: str

    # Terrain
    terrain_instability_score: float
    terrain_instability_category: str

    # Exposure
    exposure_score: float
    exposure_category: str
    dominant_exposure: str

    # Spatial
    spatial_pressure_score: float
    spatial_category: str

    # Dynamic environment
    rainfall_trigger_score: float
    rainfall_trigger_category: str
    soil_wetness_score: float
    soil_wetness_category: str
    temporal_trajectory: str
    temporal_category: str
    environment_anomaly_score: float
    environment_anomaly_category: str

    # Confidence
    confidence_score: float
    uncertainty_score: float
    confidence_category: str

    # Explanation
    driver_1: str
    driver_1_score: float
    driver_2: str
    driver_2_score: float
    driver_3: str
    driver_3_score: float

    recommendation: str
class GISCellResponse(BaseModel):
    cell_id: str
    centroid_x: float
    centroid_y: float
    geometry: dict


class GISBoundaryResponse(BaseModel):
    type: str
    features: list

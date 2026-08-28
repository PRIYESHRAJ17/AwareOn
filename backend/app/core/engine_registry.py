from dataclasses import dataclass


@dataclass(frozen=True)
class EngineDefinition:
    engine_id: str
    name: str
    description: str
    output_file: str


ENGINES = [
    EngineDefinition(
        "01",
        "Landslide Susceptibility",
        "Static ML susceptibility prediction.",
        "susceptibility_engine_output.csv",
    ),
    EngineDefinition(
        "02",
        "Rainfall Trigger",
        "Historical-percentile rainfall trigger assessment.",
        "rainfall_trigger_engine_output.csv",
    ),
    EngineDefinition(
        "03",
        "Soil Wetness",
        "Soil moisture and moisture-change assessment.",
        "soil_wetness_engine_output.csv",
    ),
    EngineDefinition(
        "04",
        "Terrain Instability",
        "Terrain-derived instability assessment.",
        "terrain_instability_engine_output.csv",
    ),
    EngineDefinition(
        "05",
        "SAR Evidence",
        "Sentinel-1 evidence and data-quality assessment.",
        "sar_evidence_engine_output.csv",
    ),
    EngineDefinition(
        "06",
        "Historical Events",
        "Historical GSI event and hotspot intelligence.",
        "historical_event_engine_output.csv",
    ),
    EngineDefinition(
        "07",
        "Anomaly Detection",
        "Environmental anomaly detection.",
        "anomaly_detection_engine_output.csv",
    ),
    EngineDefinition(
        "08",
        "Exposure & Impact",
        "Road, settlement and infrastructure exposure.",
        "exposure_impact_engine_output.csv",
    ),
    EngineDefinition(
        "09",
        "Spatial Propagation",
        "Neighbourhood-level risk propagation.",
        "spatial_propagation_engine_output.csv",
    ),
    EngineDefinition(
        "10",
        "Temporal Risk",
        "Environmental risk trajectory assessment.",
        "temporal_risk_engine_output.csv",
    ),
    EngineDefinition(
        "11",
        "Confidence & Uncertainty",
        "Prediction confidence and uncertainty.",
        "confidence_uncertainty_engine_output.csv",
    ),
    EngineDefinition(
        "12",
        "Explanation & Recommendation",
        "Human-readable reasoning and recommended response.",
        "explanation_recommendation_engine_output.csv",
    ),
]


def get_engines():
    return ENGINES


def get_engine(engine_id: str):
    for engine in ENGINES:
        if engine.engine_id == engine_id:
            return engine

    return None

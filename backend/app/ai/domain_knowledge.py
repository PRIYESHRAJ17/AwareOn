from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KnowledgeEntry:
    entry_id: str
    topic: str
    title: str
    content: str
    keywords: tuple[str, ...]
    scope: str
    source_type: str
    source: str
    source_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "topic": self.topic,
            "title": self.title,
            "content": self.content,
            "keywords": list(self.keywords),
            "scope": self.scope,
            "source_type": self.source_type,
            "source": self.source,
            "source_date": self.source_date,
        }


GENERAL_ENTRIES: tuple[KnowledgeEntry, ...] = (

    KnowledgeEntry(
        "GEN-LS-009",
        "landslide_types",
        "Types of landslides",
        (
            "Landslides can be classified by the type of material and "
            "the style of movement. Common categories include falls, "
            "topples, slides, flows, and complex movements. Rock falls, "
            "debris slides, debris flows, and earth slides describe "
            "different combinations of material and movement."
        ),
        (
            "types",
            "type",
            "classification",
            "rockfall",
            "debris slide",
            "debris flow",
            "earth slide",
            "fall",
            "topple",
            "flow",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-010",
        "slope_stability",
        "How slope stability works",
        (
            "Slope stability depends on the balance between driving "
            "forces and resisting forces. Gravity provides an important "
            "driving force, while material strength, friction, root "
            "reinforcement, geometry, and drainage can contribute to "
            "resistance. Failure becomes more likely when driving forces "
            "increase or resisting forces decrease."
        ),
        (
            "slope stability",
            "stability",
            "driving force",
            "resisting force",
            "failure",
            "factor of safety",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-011",
        "pore_pressure",
        "Pore-water pressure and effective stress",
        (
            "Water pressure within soil or fractured material contributes "
            "to pore-water pressure. An increase in pore-water pressure "
            "can reduce effective stress and therefore reduce frictional "
            "resistance along potential failure surfaces. This is one "
            "important mechanism by which rainfall can destabilize slopes."
        ),
        (
            "pore-water pressure",
            "pore pressure",
            "effective stress",
            "effective stress",
            "friction",
            "shear strength",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-012",
        "drainage",
        "Drainage and landslide stability",
        (
            "Drainage influences where water accumulates and how quickly "
            "water leaves a slope. Poor or altered drainage can promote "
            "saturation and elevated pore pressure, while appropriately "
            "designed drainage can reduce water accumulation. Drainage "
            "performance must be assessed for the specific site."
        ),
        (
            "drainage",
            "surface water",
            "groundwater",
            "water accumulation",
            "runoff",
            "drain",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-013",
        "earthquake",
        "Earthquakes and landslides",
        (
            "Earthquakes can trigger landslides by imposing rapid ground "
            "shaking and changing the stress state of slopes. Strong "
            "earthquake shaking can destabilize susceptible slopes even "
            "where rainfall is not the immediate trigger."
        ),
        (
            "earthquake",
            "earthquakes",
            "seismic",
            "seismic shaking",
            "earthquake-triggered",
            "ground shaking",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-014",
        "geomorphology",
        "Geomorphology and landslides",
        (
            "Geomorphology describes the form and evolution of terrain. "
            "Ridges, valleys, scarps, channels, drainage networks, "
            "landforms, relief, and slope geometry can provide context "
            "for understanding where slope processes are more likely."
        ),
        (
            "geomorphology",
            "landform",
            "landforms",
            "relief",
            "valley",
            "ridge",
            "drainage network",
            "scarp",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-015",
        "debris_flow",
        "Debris flows",
        (
            "A debris flow is a rapidly moving mixture of water and "
            "sediment or other coarse material. Debris flows can travel "
            "through channels and gullies and can affect areas downslope "
            "from the initiating slope failure."
        ),
        (
            "debris flow",
            "debris flows",
            "mudflow",
            "channel",
            "gully",
            "sediment flow",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-016",
        "landslide_runout",
        "Landslide runout",
        (
            "Landslide runout refers to the downslope travel of failed "
            "material after movement begins. Runout can depend on slope "
            "geometry, material type, volume, confinement, water content, "
            "and channel conditions."
        ),
        (
            "runout",
            "run-out",
            "travel distance",
            "failed material",
            "downslope",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-017",
        "landslide_frequency",
        "Why repeated landslides can occur",
        (
            "A location can experience repeated landsliding when the "
            "underlying susceptibility remains high and triggering "
            "conditions recur. Repeated events can also modify terrain, "
            "drainage, vegetation, and material conditions, which means "
            "past activity can provide useful context without proving "
            "that failure will occur again."
        ),
        (
            "repeat landslide",
            "recurrent",
            "recurrence",
            "repeated",
            "past landslide",
            "history",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-RISK-002",
        "risk_concepts",
        "Risk versus susceptibility",
        (
            "A susceptibility map describes relative propensity for a "
            "hazard process under the modeled conditions. Risk is broader "
            "and depends on the hazard, exposure, vulnerability, and the "
            "consequences considered. A high-susceptibility location is "
            "not automatically a high-loss location if exposure is low."
        ),
        (
            "risk versus susceptibility",
            "difference between risk and susceptibility",
            "susceptibility versus risk",
            "hazard susceptibility",
            "vulnerability",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-RISK-003",
        "risk_concepts",
        "Risk scores and uncertainty",
        (
            "A risk score is a model-derived indicator, not a direct "
            "measurement of future damage. Interpretation should consider "
            "the score definition, underlying data, uncertainty, spatial "
            "scale, and the time context of the assessment."
        ),
        (
            "risk score",
            "score",
            "uncertainty",
            "confidence",
            "model confidence",
            "risk model",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-WEATHER-002",
        "rainfall",
        "Intensity, duration and antecedent rainfall",
        (
            "Rainfall-triggered instability can depend on rainfall "
            "intensity, duration, cumulative rainfall, and the wetness "
            "of the slope before a storm. The same short rainfall total "
            "can have different effects depending on antecedent moisture "
            "and drainage conditions."
        ),
        (
            "intensity duration",
            "rainfall duration",
            "rainfall intensity",
            "cumulative rainfall",
            "antecedent rainfall",
            "storm duration",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-WEATHER-003",
        "weather",
        "Weather versus climate",
        (
            "Weather describes atmospheric conditions over relatively "
            "short periods, while climate describes longer-term patterns "
            "and variability. A rainfall event is a weather condition; "
            "long-term changes in rainfall patterns belong to climate "
            "analysis and should not be conflated with a single event."
        ),
        (
            "weather",
            "climate",
            "climate versus weather",
            "long term",
            "short term",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SOIL-001",
        "soil",
        "Soil properties relevant to slope failure",
        (
            "Important soil properties can include grain-size distribution, "
            "density, cohesion, frictional strength, permeability, "
            "plasticity, structure, and water content. Different soils "
            "respond differently to wetting, loading, and drainage."
        ),
        (
            "soil properties",
            "cohesion",
            "friction angle",
            "permeability",
            "grain size",
            "soil strength",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SOIL-002",
        "soil",
        "Soil saturation",
        (
            "Saturation occurs when available pore spaces contain very "
            "high proportions of water. Increasing saturation can change "
            "pore pressure, effective stress, density, and drainage "
            "behavior. Saturation should not be inferred from rainfall "
            "alone without considering site conditions."
        ),
        (
            "saturation",
            "fully saturated",
            "soil water",
            "pore space",
            "water saturation",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-TERRAIN-001",
        "terrain",
        "DEM and digital elevation models",
        (
            "A Digital Elevation Model (DEM) represents elevation across "
            "a geographic area. DEM-derived products can support "
            "calculation of slope, aspect, relief, drainage, ruggedness, "
            "and other terrain attributes used in hazard analysis."
        ),
        (
            "dem",
            "digital elevation model",
            "elevation model",
            "terrain model",
            "aspect",
            "slope map",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-TERRAIN-002",
        "terrain",
        "Slope aspect",
        (
            "Slope aspect describes the direction a slope faces. Aspect "
            "can influence sunlight, vegetation, snow, moisture, and other "
            "environmental conditions, but its effect is location-specific "
            "and should not be interpreted as an independent deterministic "
            "landslide trigger."
        ),
        (
            "aspect",
            "slope direction",
            "slope facing",
            "orientation",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SAR-003",
        "satellite",
        "What Sentinel-1 SAR provides",
        (
            "Sentinel-1 provides synthetic aperture radar observations "
            "that can support mapping and change analysis. Radar can be "
            "useful in cloudy regions because microwave observations are "
            "not dependent on visible-light illumination."
        ),
        (
            "sentinel-1",
            "sentinel 1",
            "SAR satellite",
            "radar satellite",
            "C-band SAR",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SAR-004",
        "insar",
        "Limits of InSAR in mountainous terrain",
        (
            "InSAR measurements describe displacement along the radar "
            "line of sight and can be affected by decorrelation, steep "
            "terrain geometry, layover, shadow, vegetation, atmospheric "
            "effects, temporal sampling, and processing choices. InSAR "
            "results therefore require careful interpretation."
        ),
        (
            "InSAR limitations",
            "layover",
            "radar shadow",
            "decorrelation",
            "atmospheric effects",
            "line of sight",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SAR-005",
        "remote_sensing",
        "Remote sensing for landslide intelligence",
        (
            "Remote sensing can support landslide detection, mapping, "
            "change analysis, terrain characterization, and monitoring. "
            "Different sensors provide different information, so remote "
            "sensing evidence is strongest when interpreted with terrain, "
            "weather, field, and other contextual data."
        ),
        (
            "remote sensing",
            "earth observation",
            "satellite monitoring",
            "landslide mapping",
            "change detection",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-OPS-001",
        "monitoring",
        "Landslide monitoring",
        (
            "Monitoring can combine rainfall, soil moisture, deformation, "
            "terrain, visual observations, satellite observations, and "
            "other indicators. A good monitoring strategy should match "
            "the hazard mechanism, spatial scale, expected response time, "
            "and decision that must be supported."
        ),
        (
            "monitoring",
            "monitoring strategy",
            "monitor",
            "observation",
            "deformation monitoring",
            "rainfall monitoring",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-OPS-002",
        "early_warning",
        "Early warning for landslide hazards",
        (
            "An early-warning system seeks to detect conditions associated "
            "with increasing hazard and provide information early enough "
            "to support action. Effective warning requires defined "
            "thresholds or indicators, monitoring, communication, decision "
            "rules, and an understanding of uncertainty."
        ),
        (
            "early warning",
            "warning system",
            "warning threshold",
            "alerts",
            "trigger threshold",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-OPS-003",
        "mitigation",
        "Landslide mitigation",
        (
            "Mitigation measures depend on the failure mechanism and "
            "site conditions. Examples can include drainage control, "
            "slope regrading, retaining structures, erosion control, "
            "vegetation measures, rockfall protection, land-use controls, "
            "and monitoring. Engineering measures should be designed from "
            "site-specific investigation rather than generic advice."
        ),
        (
            "mitigation",
            "prevention",
            "stabilization",
            "slope stabilization",
            "retaining wall",
            "drainage control",
            "erosion control",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-OPS-004",
        "field_inspection",
        "What field teams should inspect",
        (
            "Field inspection may examine cracks, scarps, displaced "
            "material, drainage blockage, seepage, tension cracks, "
            "rockfall indicators, slope deformation, road cuts, retaining "
            "structures, culverts, channels, and nearby exposed assets. "
            "The exact inspection checklist should reflect the site and "
            "hazard mechanism."
        ),
        (
            "field inspection",
            "site inspection",
            "field assessment",
            "cracks",
            "scarps",
            "seepage",
            "road cut",
            "culvert",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-INFRA-001",
        "infrastructure",
        "Infrastructure exposure to landslides",
        (
            "Roads, bridges, buildings, utilities, settlements, and other "
            "infrastructure can be exposed to landslide processes through "
            "direct impact, loss of access, debris deposition, slope "
            "failure, or drainage disruption. Exposure is distinct from "
            "susceptibility and should be assessed separately."
        ),
        (
            "infrastructure",
            "road",
            "roads",
            "bridge",
            "utility",
            "settlement",
            "access",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SIKKIM-002",
        "sikkim_geography",
        "Sikkim terrain and landslide context",
        (
            "Sikkim is a mountainous Himalayan state characterized by "
            "steep terrain and substantial relief. Landslide analysis in "
            "the state therefore benefits from considering terrain, "
            "rainfall, geology, drainage, vegetation, infrastructure, and "
            "historical event patterns together."
        ),
        (
            "sikkim terrain",
            "sikkim geography",
            "himalayan terrain",
            "steep terrain",
            "mountain relief",
        ),
        "SIKKIM_DOMAIN",
        "OFFICIAL_SOURCE_SUMMARY",
        "Government of Sikkim natural-calamity material",
    ),
    KnowledgeEntry(
        "GEN-SIKKIM-003",
        "sikkim",
        "Sikkim districts and spatial context",
        (
            "Sikkim's districts and transport corridors occupy different "
            "terrain and environmental settings. A spatial question about "
            "Sikkim should therefore be interpreted using the requested "
            "location, district, corridor, or coordinates rather than "
            "assuming that conditions are uniform across the state."
        ),
        (
            "district",
            "districts",
            "east sikkim",
            "west sikkim",
            "north sikkim",
            "south sikkim",
            "gangtok",
            "pakyong",
        ),
        "SIKKIM_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SIKKIM-004",
        "sikkim_disasters",
        "Historical disasters as current-risk context",
        (
            "Historical landslide and disaster records can reveal repeated "
            "hazard locations, event patterns, triggering conditions, and "
            "infrastructure consequences. Historical evidence is contextual "
            "and should not automatically be interpreted as proof of current "
            "risk at the same location."
        ),
        (
            "historical disaster",
            "historical landslide",
            "past event",
            "previous event",
            "disaster history",
            "past accidents",
        ),
        "SIKKIM_DOMAIN",
        "DATASET_BACKED_KNOWLEDGE",
        "AwareOn historical event datasets",
    ),
    KnowledgeEntry(
        "GEN-AWAREON-001",
        "awareon",
        "How AwareOn risk intelligence should be interpreted",
        (
            "AwareOn combines multiple intelligence layers including "
            "spatial risk, terrain, soil, rainfall, historical context, "
            "scenario analysis, temporal analysis, exposure, and decision "
            "intelligence. Different outputs represent different evidence "
            "classes and should not be treated as interchangeable."
        ),
        (
            "awareon",
            "awareon intelligence",
            "how awareon works",
            "awareon risk",
            "intelligence layers",
        ),
        "AWAREON_SYSTEM",
        "SYSTEM_KNOWLEDGE",
        "AwareOn system architecture",
    ),
    KnowledgeEntry(
        "GEN-AWAREON-002",
        "awareon",
        "Observed, derived, simulated and historical information",
        (
            "AwareOn distinguishes between information observed or supplied "
            "by a data source, values derived by an intelligence engine, "
            "simulated scenario outputs, and historical/source-backed "
            "information. The distinction matters because these classes "
            "support different kinds of claims."
        ),
        (
            "observed",
            "derived",
            "simulated",
            "simulation",
            "historical",
            "evidence type",
        ),
        "AWAREON_SYSTEM",
        "SYSTEM_KNOWLEDGE",
        "AwareOn evidence architecture",
    ),
    KnowledgeEntry(
        "GEN-LS-001",
        "landslide",
        "What is a landslide?",
        (
            "A landslide is the downslope movement of soil, rock, "
            "debris, or a mixture of these materials under gravity. "
            "Landslides can occur gradually or rapidly and can range "
            "from small slope failures to large destructive events."
        ),
        (
            "landslide",
            "landslides",
            "mass movement",
            "mass wasting",
            "slope failure",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-002",
        "landslide",
        "Major landslide controls",
        (
            "Landslide occurrence is commonly influenced by interacting "
            "factors rather than one universal cause. Important controls "
            "include slope geometry, material strength and weathering, "
            "water and rainfall conditions, drainage, vegetation, "
            "geological structure, earthquakes, and human modification "
            "such as excavation, loading, road cutting, or drainage "
            "changes."
        ),
        (
            "causes",
            "cause",
            "reasons",
            "why",
            "trigger",
            "triggers",
            "factors",
            "slope stability",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-003",
        "rainfall",
        "Rainfall and slope failure",
        (
            "Rainfall can destabilize slopes by increasing water content "
            "and pore-water pressure, reducing effective stress and "
            "therefore reducing the resistance available to oppose "
            "downslope movement. The effect depends on rainfall intensity "
            "and duration, antecedent wetness, material properties, "
            "drainage, and slope geometry."
        ),
        (
            "rainfall",
            "rain",
            "precipitation",
            "pore pressure",
            "pore-water pressure",
            "saturation",
            "wetness",
            "heavy rain",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-004",
        "terrain",
        "Terrain and slope stability",
        (
            "Steeper slopes generally have greater gravitational driving "
            "forces. Terrain geometry, elevation, local relief, "
            "ruggedness, drainage configuration, and slope orientation "
            "can all influence slope stability. Terrain alone does not "
            "determine whether a landslide will occur."
        ),
        (
            "terrain",
            "slope",
            "steep slope",
            "elevation",
            "ruggedness",
            "topography",
            "slope angle",
            "slope stability",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-005",
        "soil",
        "Soil moisture and slope stability",
        (
            "Increasing soil moisture can change pore-water pressure, "
            "weight, and effective stress within a slope. Saturation "
            "conditions and drainage therefore matter when evaluating "
            "rainfall-triggered slope instability."
        ),
        (
            "soil",
            "soil moisture",
            "soil wetness",
            "water content",
            "saturation",
            "swvl",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-006",
        "geology",
        "Geology and slope failure",
        (
            "Rock and soil strength, weathering, fractures, faults, "
            "bedding, foliation, discontinuities, permeability, and "
            "material layering can influence how a slope responds to "
            "gravity and water. Geological controls often interact "
            "with terrain and rainfall."
        ),
        (
            "geology",
            "geological",
            "rock",
            "bedrock",
            "fracture",
            "fault",
            "bedding",
            "foliation",
            "weathering",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-007",
        "vegetation",
        "Vegetation and slope stability",
        (
            "Vegetation can influence slope stability through roots, "
            "soil reinforcement, interception of rainfall, and effects "
            "on evapotranspiration and drainage. Vegetation is not a "
            "universal safeguard: stability depends on slope material, "
            "water conditions, root structure, and disturbance."
        ),
        (
            "vegetation",
            "forest",
            "deforestation",
            "roots",
            "land cover",
            "land use",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-LS-008",
        "human_activity",
        "Human activity and slope instability",
        (
            "Human activities such as road cutting, excavation, "
            "slope loading, drainage modification, construction, "
            "quarrying, and removal of vegetation can alter slope "
            "geometry, water flow, loading, or material strength."
        ),
        (
            "road cutting",
            "excavation",
            "construction",
            "loading",
            "quarry",
            "road widening",
            "human activity",
            "anthropogenic",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SAR-001",
        "satellite",
        "Satellite and SAR observations",
        (
            "Synthetic Aperture Radar (SAR) uses active microwave "
            "signals and can acquire observations through clouds and "
            "during both day and night. Radar observations can support "
            "landslide mapping, surface-change analysis, and deformation "
            "studies."
        ),
        (
            "sar",
            "sentinel-1",
            "sentinel 1",
            "radar",
            "satellite",
            "satellite imagery",
            "remote sensing",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SAR-002",
        "insar",
        "InSAR and deformation",
        (
            "Interferometric SAR (InSAR) compares radar phase information "
            "between acquisitions to estimate changes in the radar line "
            "of sight. It can reveal ground deformation, but steep "
            "terrain, vegetation, temporal decorrelation, geometry, and "
            "processing assumptions can limit interpretation."
        ),
        (
            "insar",
            "interferometry",
            "deformation",
            "ground deformation",
            "phase",
            "line of sight",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-RISK-001",
        "risk",
        "Hazard, susceptibility, exposure and risk",
        (
            "Hazard describes a potentially damaging process; "
            "susceptibility describes how prone an area is to a process; "
            "exposure describes people, infrastructure, or assets that "
            "could be affected; risk combines the hazard/process with "
            "exposure and vulnerability considerations."
        ),
        (
            "risk",
            "hazard",
            "susceptibility",
            "exposure",
            "vulnerability",
            "risk score",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-WEATHER-001",
        "weather",
        "Weather variables relevant to landslide intelligence",
        (
            "Rainfall intensity, accumulated rainfall over multiple "
            "time windows, antecedent rainfall, soil moisture, and "
            "environmental variability can provide useful context for "
            "rainfall-related landslide assessment. A weather signal "
            "alone does not prove that a landslide will occur."
        ),
        (
            "weather",
            "rainfall",
            "rainfall intensity",
            "accumulated rainfall",
            "antecedent rainfall",
            "soil moisture",
            "storm",
        ),
        "GENERAL_DOMAIN",
        "CURATED_DOMAIN_KNOWLEDGE",
        "AwareOn domain knowledge",
    ),
    KnowledgeEntry(
        "GEN-SIKKIM-001",
        "sikkim",
        "Why Sikkim is important for landslide intelligence",
        (
            "Sikkim is a mountainous Himalayan state where landslides, "
            "floods, and river-bank erosion are recurring natural hazards. "
            "Terrain, rainfall, seismic conditions, drainage, land use, "
            "and infrastructure interactions all matter when assessing "
            "landslide-related risk in the state."
        ),
        (
            "sikkim",
            "himalaya",
            "himalayan",
            "gangtok",
            "mountain",
            "mountainous",
        ),
        "SIKKIM_DOMAIN",
        "OFFICIAL_SOURCE_SUMMARY",
        "Government of Sikkim — Natural Calamity",
    ),
)


def all_entries() -> tuple[KnowledgeEntry, ...]:
    return GENERAL_ENTRIES


def _normalise(text: str) -> str:
    return " ".join(
        text.lower()
        .strip()
        .split()
    )


def _score_entry(
    query: str,
    entry: KnowledgeEntry,
) -> float:
    text = _normalise(query)

    if not text:
        return 0.0

    score = 0.0

    if entry.topic.lower() in text:
        score += 4.0

    if entry.title.lower() in text:
        score += 5.0

    for keyword in entry.keywords:
        keyword = keyword.lower()

        if keyword in text:
            score += 2.0

    query_terms = set(
        text.split()
    )

    title_terms = set(
        _normalise(entry.title).split()
    )

    content_terms = set(
        _normalise(entry.content).split()
    )

    score += len(
        query_terms.intersection(
            title_terms
        )
    ) * 0.75

    score += min(
        3.0,
        len(
            query_terms.intersection(
                content_terms
            )
        ) * 0.10,
    )

    return score


def retrieve_awareon_knowledge(
    query: str,
    *,
    limit: int = 6,
    minimum_score: float = 1.5,
) -> dict[str, Any]:

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0."
        )

    scored = []

    for entry in all_entries():
        score = _score_entry(
            query,
            entry,
        )

        if score >= minimum_score:
            scored.append(
                (
                    score,
                    entry,
                )
            )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].entry_id,
        ),
        reverse=True,
    )

    selected = [
        entry
        for _, entry in scored[:limit]
    ]

    return {
        "query": query,
        "count": len(selected),
        "items": [
            entry.to_dict()
            for entry in selected
        ],
    }


def build_knowledge_context(
    query: str,
    *,
    limit: int = 6,
) -> dict[str, Any]:

    result = retrieve_awareon_knowledge(
        query,
        limit=limit,
    )

    lines = []

    for index, item in enumerate(
        result["items"],
        start=1,
    ):
        lines.append(
            (
                f"[KNOWLEDGE {index}] "
                f"{item['title']}\n"
                f"Scope: {item['scope']}\n"
                f"Source: {item['source']}\n"
                f"Content: {item['content']}"
            )
        )

    if lines:
        context = "\n\n".join(
            lines
        )
    else:
        context = (
            "No specific AwareOn domain-knowledge "
            "entry matched this query."
        )

    return {
        **result,
        "context": context,
    }


__all__ = [
    "KnowledgeEntry",
    "GENERAL_ENTRIES",
    "all_entries",
    "retrieve_awareon_knowledge",
    "build_knowledge_context",
]

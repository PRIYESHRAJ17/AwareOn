from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.early_warning import (
    build_early_warning_signal,
)
from backend.app.early_warning_master import (
    build_early_warning_master,
)
from backend.app.emerging_risk import (
    detect_emerging_risk,
)
from backend.app.event_progression import (
    build_event_progression,
)
from backend.app.historical_trajectory import (
    build_historical_trajectory,
)
from backend.app.multiscale_temporal import (
    build_multiscale_temporal_intelligence,
)
from backend.app.regional_temporal import (
    build_regional_temporal_intelligence,
)
from backend.app.risk_acceleration import (
    analyze_risk_acceleration,
)
from backend.app.temporal_anomaly_fusion import (
    build_temporal_anomaly_fusion,
)
from backend.app.temporal_scenario_coupling import (
    build_temporal_scenario_coupling,
)
from backend.app.services.assessment_service import (
    assessment_service,
)
from backend.app.services.scenario_service import (
    scenario_service,
)


DEFAULT_HISTORICAL_SOURCE = (
    "data/processed/weather/era5_environment_timeseries.csv"
)


@dataclass(frozen=True)
class TemporalIntelligenceResult:
    status: str
    cell_id: str | None
    historical: dict[str, Any]
    regional_context: dict[str, Any]
    regional_temporal: dict[str, Any]
    scenario_records: list[dict[str, Any]]
    acceleration: dict[str, Any]
    anomaly_fusion: dict[str, Any]
    emerging_risk: dict[str, Any]
    early_warning: dict[str, Any]
    progression: dict[str, Any]
    coupling: dict[str, Any]
    multiscale: dict[str, Any]
    early_warning_master: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "cell_id": self.cell_id,
            "historical": self.historical,
            "regional_context": self.regional_context,
            "regional_temporal": self.regional_temporal,
            "scenario_records": self.scenario_records,
            "acceleration": self.acceleration,
            "anomaly_fusion": self.anomaly_fusion,
            "emerging_risk": self.emerging_risk,
            "early_warning": self.early_warning,
            "progression": self.progression,
            "coupling": self.coupling,
            "multiscale": self.multiscale,
            "early_warning_master": self.early_warning_master,
        }


def _require_dict(
    value: Any,
    name: str,
) -> dict[str, Any]:

    if not isinstance(value, dict):
        raise TypeError(
            f"{name} must be a dictionary."
        )

    if not value:
        raise ValueError(
            f"{name} cannot be empty."
        )

    return value


def _require_scenario_records(
    value: Any,
) -> list[dict[str, Any]]:

    if not isinstance(
        value,
        list,
    ):
        raise TypeError(
            "scenario_records must be a list."
        )

    if len(value) < 2:
        raise ValueError(
            "At least two scenario records are required "
            "for temporal acceleration analysis."
        )

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise TypeError(
                f"scenario_records[{index}] must be a dictionary."
            )

    return value


def _build_regional_context(
    regional: dict[str, Any],
) -> dict[str, Any]:

    # The regional investigator exposes the canonical
    # regional intelligence result, rather than a regional
    # master object. This adapter preserves those values and
    # maps them into the contract consumed by
    # regional_temporal.

    regional_state = str(
        regional.get(
            "regional_state",
            "UNKNOWN",
        )
    ).upper()

    mean_risk = float(
        regional.get(
            "mean_risk_score",
            0.0,
        )
        or 0.0
    )

    maximum = regional.get(
        "maximum_risk",
        {},
    )

    if not isinstance(
        maximum,
        dict,
    ):
        maximum = {}

    spatial = regional.get(
        "spatial_pattern",
        {},
    )

    if not isinstance(
        spatial,
        dict,
    ):
        spatial = {}

    cell_count = int(
        regional.get(
            "cell_count",
            0,
        )
        or 0
    )

    extreme_cells = int(
        regional.get(
            "extreme_cells",
            0,
        )
        or 0
    )

    high_or_extreme = int(
        regional.get(
            "high_or_extreme_cells",
            0,
        )
        or 0
    )

    confidence = float(
        regional.get(
            "mean_confidence",
            0.0,
        )
        or 0.0
    )

    if regional_state.startswith(
        "CRITICAL"
    ):
        posture = "CRITICAL_AND_ESCALATING"
        urgency = "HIGH"
        operational_focus = (
            "REGIONAL_RISK_REVIEW"
        )
    elif mean_risk >= 70.0:
        posture = "HIGH_PRIORITY_REGION"
        urgency = "HIGH"
        operational_focus = (
            "ENHANCED_REGIONAL_MONITORING"
        )
    else:
        posture = "REGIONAL_MONITORING"
        urgency = "ROUTINE"
        operational_focus = (
            "ROUTINE_REGIONAL_MONITORING"
        )

    trajectory = str(
        spatial.get(
            "signal_alignment",
            "UNKNOWN",
        )
    ).upper()

    # The regional master contract expects an evolution
    # object. We use the actual regional spatial signal
    # only as context; we do not manufacture a numeric
    # temporal trend.
    evolution = {
        "trajectory":
            "UNKNOWN",

        "cluster_behavior":
            trajectory,

        "mean_risk_delta":
            0.0,

        "high_cell_delta":
            0,

        "extreme_cell_delta":
            0,
    }

    exposure = {
        "exposure_state":
            "UNKNOWN",

        "impact_focus":
            "UNKNOWN",

        "exposure_summary":
            {
                "high_exposure_cells":
                    0,

                "maximum_exposure":
                    0.0,
            },

        "coverage":
            0.0,
    }

    return {
        "engine":
            "AWAREON_REGIONAL_TEMPORAL_CONTEXT_ADAPTER",

        "version":
            "1.0",

        "status":
            "READY",

        "cluster_id":
            (
                "REGION:"
                f"{regional.get('region', {}).get('latitude')}:"
                f"{regional.get('region', {}).get('longitude')}"
            ),

        "master_state":
            regional_state,

        "regional_posture":
            posture,

        "urgency":
            urgency,

        "priority":
            {
                "level":
                    "P1"
                    if mean_risk >= 80.0
                    else "P2"
                    if mean_risk >= 70.0
                    else "P3",
                "score":
                    mean_risk,
            },

        "risk":
            {
                "cell_count":
                    cell_count,

                "extreme_cells":
                    extreme_cells,

                "mean_risk":
                    mean_risk,

                "maximum_risk":
                    float(
                        maximum.get(
                            "risk_score",
                            0.0,
                        )
                        or 0.0
                    ),

                "maximum_risk_cell":
                    maximum.get(
                        "cell_id"
                    ),
            },

        "evolution":
            evolution,

        "exposure":
            exposure,

        "operational_focus":
            operational_focus,

        "confidence":
            {
                "score":
                    confidence,

                "band":
                    str(
                        regional.get(
                            "confidence_band",
                            "UNKNOWN",
                        )
                    ).upper(),
            },

        "master_signal":
            {
                "regional_state":
                    regional_state,

                "posture":
                    posture,

                "urgency":
                    urgency,

                "trajectory":
                    evolution["trajectory"],

                "exposure":
                    exposure["exposure_state"],

                "impact_focus":
                    exposure["impact_focus"],

                "priority":
                    (
                        "P1"
                        if mean_risk >= 80.0
                        else "P2"
                        if mean_risk >= 70.0
                        else "P3"
                    ),
            },

        "decision":
            (
                f"Regional state is {regional_state}. "
                f"Mean risk is {mean_risk:.2f}. "
                f"{high_or_extreme} cells are HIGH or EXTREME, "
                f"including {extreme_cells} EXTREME cells."
            ),
    }


def _build_scenario_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    scenarios: list[dict[str, Any]] = []

    for item in records:

        risk_score = float(
            item.get(
                "risk_score",
                0.0,
            )
            or 0.0
        )

        risk_change = float(
            item.get(
                "risk_score_change",
                0.0,
            )
            or 0.0
        )

        category = str(
            item.get(
                "risk_category",
                "UNKNOWN",
            )
        ).upper()

        scenarios.append(
            {
                "scenario":
                    item.get(
                        "scenario"
                    ),

                "rainfall_change_percent":
                    float(
                        item.get(
                            "rainfall_change_percent",
                            0.0,
                        )
                        or 0.0
                    ),

                "new_high_or_extreme":
                    1
                    if category in {
                        "HIGH",
                        "EXTREME",
                    }
                    else 0,

                "new_extreme_cells":
                    1
                    if category == "EXTREME"
                    else 0,

                "escalating_cells":
                    1
                    if risk_change > 0.0
                    else 0,

                "mean_risk_change":
                    risk_change,

                "risk_score":
                    risk_score,

                "risk_category":
                    category,
            }
        )

    return {
        "status":
            "READY",

        "scenarios":
            scenarios,

        "scenario_count":
            len(scenarios),
    }


def run_temporal_intelligence(
    *,
    cell_id: str,
    regional_intelligence: dict[str, Any],
    historical_source: str = DEFAULT_HISTORICAL_SOURCE,
    recent_days: int = 30,
    baseline_years: int = 5,
) -> TemporalIntelligenceResult:

    if not cell_id:
        raise ValueError(
            "cell_id is required for full temporal "
            "early-warning orchestration."
        )

    regional_intelligence = _require_dict(
        regional_intelligence,
        "regional_intelligence",
    )

    # --------------------------------------------------------
    # Current canonical assessment
    # --------------------------------------------------------

    assessment = (
        assessment_service.get_assessment(
            str(cell_id)
        )
    )

    assessment = _require_dict(
        assessment,
        "assessment",
    )

    # --------------------------------------------------------
    # Canonical cell scenario states
    # --------------------------------------------------------

    scenario_payload = (
        scenario_service.get_cell_scenarios(
            str(cell_id)
        )
    )

    scenario_payload = _require_dict(
        scenario_payload,
        "scenario_payload",
    )

    scenario_records = _require_scenario_records(
        scenario_payload.get(
            "scenarios",
            [],
        )
    )

    scenario_summary = _build_scenario_summary(
        scenario_records
    )

    # --------------------------------------------------------
    # 1. Historical
    # --------------------------------------------------------

    historical = build_historical_trajectory(
        source=historical_source,
        recent_days=recent_days,
        baseline_years=baseline_years,
    )

    historical = _require_dict(
        historical,
        "historical",
    )

    # --------------------------------------------------------
    # 2. Regional context adapter
    # --------------------------------------------------------

    regional_context = _build_regional_context(
        regional_intelligence
    )

    regional_context = _require_dict(
        regional_context,
        "regional_context",
    )

    # --------------------------------------------------------
    # 3. Regional temporal
    # --------------------------------------------------------

    regional_temporal = (
        build_regional_temporal_intelligence(
            historical=historical,
            regional_master=regional_context,
        )
    )

    regional_temporal = _require_dict(
        regional_temporal,
        "regional_temporal",
    )

    # --------------------------------------------------------
    # 4. Risk acceleration
    # --------------------------------------------------------

    acceleration = analyze_risk_acceleration(
        scenario_records
    )

    acceleration = _require_dict(
        acceleration,
        "acceleration",
    )

    # --------------------------------------------------------
    # 5. Temporal anomaly fusion
    # --------------------------------------------------------

    anomaly_fusion = (
        build_temporal_anomaly_fusion(
            historical=historical,
            acceleration=acceleration,
            assessment=assessment,
        )
    )

    anomaly_fusion = _require_dict(
        anomaly_fusion,
        "anomaly_fusion",
    )

    # --------------------------------------------------------
    # 6. Emerging risk
    # --------------------------------------------------------

    emerging_risk = detect_emerging_risk(
        historical=historical,
        temporal_fusion=anomaly_fusion,
        assessment=assessment,
    )

    emerging_risk = _require_dict(
        emerging_risk,
        "emerging_risk",
    )

    # --------------------------------------------------------
    # 7. Early-warning signal
    # --------------------------------------------------------

    early_warning = build_early_warning_signal(
        historical=historical,
        temporal_fusion=anomaly_fusion,
        emerging_risk=emerging_risk,
        assessment=assessment,
        scenario_summary=scenario_summary,
    )

    early_warning = _require_dict(
        early_warning,
        "early_warning",
    )

    # --------------------------------------------------------
    # 8. Event progression
    # --------------------------------------------------------

    progression = build_event_progression(
        assessment=assessment,
        early_warning=early_warning,
        historical=historical,
        scenario_records=scenario_records,
    )

    progression = _require_dict(
        progression,
        "progression",
    )

    # --------------------------------------------------------
    # 9. Temporal/scenario coupling
    # --------------------------------------------------------

    coupling = build_temporal_scenario_coupling(
        historical=historical,
        temporal_fusion=anomaly_fusion,
        progression=progression,
    )

    coupling = _require_dict(
        coupling,
        "coupling",
    )

    # --------------------------------------------------------
    # 10. Multiscale temporal intelligence
    # --------------------------------------------------------

    multiscale = (
        build_multiscale_temporal_intelligence(
            source=historical_source
        )
    )

    multiscale = _require_dict(
        multiscale,
        "multiscale",
    )

    # --------------------------------------------------------
    # 11. Final early-warning master
    # --------------------------------------------------------

    early_warning_master = (
        build_early_warning_master(
            historical=historical,
            regional_temporal=regional_temporal,
            acceleration=acceleration,
            anomaly_fusion=anomaly_fusion,
            emerging_risk=emerging_risk,
            early_warning=early_warning,
            progression=progression,
            coupling=coupling,
            multiscale=multiscale,
        )
    )

    early_warning_master = _require_dict(
        early_warning_master,
        "early_warning_master",
    )

    return TemporalIntelligenceResult(
        status="READY",
        cell_id=str(cell_id),
        historical=historical,
        regional_context=regional_context,
        regional_temporal=regional_temporal,
        scenario_records=scenario_records,
        acceleration=acceleration,
        anomaly_fusion=anomaly_fusion,
        emerging_risk=emerging_risk,
        early_warning=early_warning,
        progression=progression,
        coupling=coupling,
        multiscale=multiscale,
        early_warning_master=early_warning_master,
    )


__all__ = [
    "TemporalIntelligenceResult",
    "run_temporal_intelligence",
]

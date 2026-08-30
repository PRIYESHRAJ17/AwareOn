from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from backend.app.exact_cell_intelligence import (
    build_exact_cell_intelligence,
)
from backend.app.regional_intelligence import (
    build_regional_intelligence,
)
from backend.app.historical_trajectory import (
    build_historical_trajectory,
)
from backend.app.services.gis_service import gis_service
from backend.app.services.scenario_service import (
    scenario_service,
)
from backend.app.early_warning_master import (
    build_early_warning_master,
)
from backend.app.decision_master import (
    build_decision_master,
)


# ============================================================
# TOOL SPECIFICATION
# ============================================================

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    intents: tuple[str, ...]
    callable: Callable[..., Any]
    required_arguments: tuple[str, ...]
    optional_arguments: tuple[str, ...]
    evidence_class: str
    output_class: str
    risk_level: str = "ANALYTICAL"

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "intents": list(self.intents),
            "required_arguments": list(
                self.required_arguments
            ),
            "optional_arguments": list(
                self.optional_arguments
            ),
            "evidence_class":
                self.evidence_class,
            "output_class":
                self.output_class,
            "risk_level":
                self.risk_level,
        }


# ============================================================
# CANONICAL TOOL REGISTRY
# ============================================================

class AwareOnToolRegistry:

    def __init__(self) -> None:

        self._tools: dict[str, ToolSpec] = {

            "exact_cell_intelligence":
                ToolSpec(
                    name="exact_cell_intelligence",
                    description=(
                        "Build comprehensive intelligence "
                        "for one exact AwareOn risk cell, "
                        "including current risk, scenario "
                        "response, neighborhood, spatial "
                        "pattern, evidence state, posture, "
                        "priority and confidence."
                    ),
                    intents=(
                        "CELL_RISK",
                        "EXPLANATION",
                        "SCENARIO",
                        "DECISION",
                    ),
                    callable=
                        build_exact_cell_intelligence,
                    required_arguments=(
                        "cell_id",
                    ),
                    optional_arguments=(
                        "rainfall_change_percent",
                        "radius_m",
                    ),
                    evidence_class="FUSED_MODELLED",
                    output_class="CELL_INTELLIGENCE",
                ),

            "regional_intelligence":
                ToolSpec(
                    name="regional_intelligence",
                    description=(
                        "Analyze regional risk around "
                        "a geographic coordinate, including "
                        "regional state, high-risk cells, "
                        "extreme cells, spatial pattern, "
                        "confidence and top cells."
                    ),
                    intents=(
                        "REGIONAL_RISK",
                        "EXPLANATION",
                        "DECISION",
                        "EXPOSURE",
                    ),
                    callable=
                        build_regional_intelligence,
                    required_arguments=(
                        "latitude",
                        "longitude",
                    ),
                    optional_arguments=(
                        "radius_m",
                    ),
                    evidence_class="FUSED_SPATIAL",
                    output_class="REGIONAL_INTELLIGENCE",
                ),

            "historical_trajectory":
                ToolSpec(
                    name="historical_trajectory",
                    description=(
                        "Analyze the long-term environmental "
                        "trajectory using the available "
                        "historical ERA5 time series."
                    ),
                    intents=(
                        "TEMPORAL",
                        "EXPLANATION",
                        "EARLY_WARNING",
                    ),
                    callable=
                        build_historical_trajectory,
                    required_arguments=(),
                    optional_arguments=(
                        "source",
                        "recent_days",
                        "baseline_years",
                    ),
                    evidence_class="HISTORICAL_OBSERVATION",
                    output_class="HISTORICAL_TRAJECTORY",
                ),

            "nearby_cells":
                ToolSpec(
                    name="nearby_cells",
                    description=(
                        "Resolve nearby AwareOn spatial "
                        "cells around a geographic coordinate."
                    ),
                    intents=(
                        "CELL_RISK",
                        "REGIONAL_RISK",
                        "EXPOSURE",
                        "DECISION",
                    ),
                    callable=
                        gis_service.get_nearby_cells,
                    required_arguments=(
                        "latitude",
                        "longitude",
                    ),
                    optional_arguments=(
                        "radius_m",
                    ),
                    evidence_class="SPATIAL_OBSERVATION",
                    output_class="GIS_NEIGHBORHOOD",
                ),

            "scenario_simulation":
                ToolSpec(
                    name="scenario_simulation",
                    description=(
                        "Simulate the AwareOn risk system "
                        "under a specified rainfall change."
                    ),
                    intents=(
                        "SCENARIO",
                        "DECISION",
                        "EARLY_WARNING",
                    ),
                    callable=
                        scenario_service.simulate,
                    required_arguments=(
                        "rainfall_change_percent",
                    ),
                    optional_arguments=(),
                    evidence_class="SIMULATED",
                    output_class="SCENARIO_RESULT",
                ),

            "early_warning_master":
                ToolSpec(
                    name="early_warning_master",
                    description=(
                        "Produce the consolidated "
                        "AwareOn early-warning intelligence "
                        "state from validated temporal and "
                        "warning layers."
                    ),
                    intents=(
                        "EARLY_WARNING",
                        "DECISION",
                    ),
                    callable=
                        build_early_warning_master,
                    required_arguments=(
                        "historical",
                        "regional_temporal",
                        "acceleration",
                        "anomaly_fusion",
                        "emerging_risk",
                        "early_warning",
                        "progression",
                        "coupling",
                        "multiscale",
                    ),
                    optional_arguments=(),
                    evidence_class="FUSED_TEMPORAL",
                    output_class="EARLY_WARNING_MASTER",
                ),

            "decision_master":
                ToolSpec(
                    name="decision_master",
                    description=(
                        "Produce consolidated AwareOn "
                        "decision intelligence from "
                        "intervention, infrastructure, "
                        "field, monitoring, response, "
                        "optimization and trade-off layers."
                    ),
                    intents=(
                        "DECISION",
                        "EXPOSURE",
                        "EARLY_WARNING",
                    ),
                    callable=
                        build_decision_master,
                    required_arguments=(
                        "intervention",
                        "infrastructure",
                        "field",
                        "monitoring",
                        "response",
                        "optimization",
                        "comparison",
                        "tradeoff",
                        "operational",
                    ),
                    optional_arguments=(),
                    evidence_class="FUSED_DECISION",
                    output_class="DECISION_MASTER",
                    risk_level="DECISION_SUPPORT",
                ),
        }

    def get(
        self,
        name: str,
    ) -> ToolSpec:

        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown AwareOn tool: {name}"
            ) from exc

    def names(self) -> list[str]:
        return sorted(
            self._tools.keys()
        )

    def all(
        self,
    ) -> list[ToolSpec]:

        return [
            self._tools[name]
            for name in self.names()
        ]

    def by_intent(
        self,
        intent: str,
    ) -> list[ToolSpec]:

        normalized = str(
            intent
        ).upper()

        return [
            tool
            for tool in self.all()
            if normalized in {
                value.upper()
                for value in tool.intents
            }
        ]

    def describe(
        self,
    ) -> list[dict[str, Any]]:

        return [
            tool.summary()
            for tool in self.all()
        ]


tool_registry = AwareOnToolRegistry()

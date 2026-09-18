from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import ScenarioProfile, clamp


SUPPORTED = (0.0, 25.0, 50.0, 100.0)
CATEGORY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "EXTREME": 3}


def _scenario_file(root: Path) -> Path:
    return root / "data" / "processed" / "engines" / "counterfactual_risk_output.csv"


def _category(score: float) -> str:
    if score < 25:
        return "LOW"
    if score < 50:
        return "MODERATE"
    if score < 75:
        return "HIGH"
    return "EXTREME"


def build_resilience_profile(root: Path, cell_id: str) -> dict[str, Any]:
    path = _scenario_file(root)
    if not path.exists():
        raise FileNotFoundError(f"Scenario artifact missing: {path}")
    df = pd.read_csv(path)
    required = {
        "cell_id",
        "scenario",
        "rainfall_change_percent",
        "risk_score",
        "baseline_risk_score",
        "risk_score_change",
        "risk_category",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"Scenario artifact missing columns: {missing}")

    local = df.loc[df["cell_id"].astype(str) == str(cell_id)].copy()
    if local.empty:
        raise KeyError(f"Unknown scenario cell: {cell_id}")

    local["rainfall_change_percent"] = pd.to_numeric(local["rainfall_change_percent"], errors="coerce")
    local["risk_score"] = pd.to_numeric(local["risk_score"], errors="coerce")
    local["risk_score_change"] = pd.to_numeric(local["risk_score_change"], errors="coerce")
    local = local.dropna(subset=["rainfall_change_percent", "risk_score"])
    local = local.sort_values("rainfall_change_percent")

    supported = [float(v) for v in local["rainfall_change_percent"].tolist()]
    supported = [v for v in supported if v in SUPPORTED]
    local = local[local["rainfall_change_percent"].isin(supported)]
    if local.empty:
        raise RuntimeError("No supported scenario rows remain after validation.")

    scores = local["risk_score"].tolist()
    worst_idx = int(local["risk_score"].idxmax())
    worst = local.loc[worst_idx]
    baseline_row = local.iloc[0]
    threshold_crossings: list[str] = []

    baseline_rank = CATEGORY_RANK[_category(float(baseline_row["risk_score"]))]
    for _, row in local.iterrows():
        cat = _category(float(row["risk_score"]))
        if CATEGORY_RANK[cat] > baseline_rank:
            threshold_crossings.append(
                f"+{float(row['rainfall_change_percent']):g}% -> {cat}"
            )

    monotonic = all(a <= b + 1e-9 for a, b in zip(scores, scores[1:]))
    delta = float(worst["risk_score"] - baseline_row["risk_score"])
    robustness = clamp(100.0 - max(0.0, delta) / 75.0 * 100.0)
    if not monotonic:
        robustness = min(robustness, 60.0)

    profile = ScenarioProfile(
        cell_id=str(cell_id),
        supported_scenarios=tuple(f"+{v:g}%" for v in supported),
        baseline_risk=float(baseline_row["risk_score"]),
        worst_case_risk=float(worst["risk_score"]),
        worst_case_scenario=str(worst["scenario"]),
        max_risk_delta=delta,
        threshold_crossings=tuple(threshold_crossings),
        monotonic_rainfall_response=bool(monotonic),
        robustness_score=robustness,
        limitations=(
            "This profile is based on AwareOn's supported tested rainfall scenarios.",
            "It is a modeled counterfactual, not an observed future event or official forecast.",
        ),
    )
    return profile.to_dict()

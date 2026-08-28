from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

HOTSPOT_FILE = (
    ROOT
    / "data/processed/engines/historical_event_engine_output.csv"
)

RISK_FILE = (
    ROOT
    / "data/processed/intelligence/awareon_prioritized_incidents.csv"
)

GRID_FILE = (
    ROOT
    / "data/processed/grid/master_grid_100m.geojson"
)

OUT_DIR = ROOT / "data/processed/intelligence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "historical_current_correlation.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

hotspots = pd.read_csv(HOTSPOT_FILE)
risk = pd.read_csv(RISK_FILE)
grid = gpd.read_file(GRID_FILE).to_crs("EPSG:32645")

if hotspots.empty:
    raise RuntimeError("Historical hotspot dataset is empty.")

if risk.empty:
    raise RuntimeError("Prioritized risk dataset is empty.")

grid["cell_id"] = grid["cell_id"].astype(str)


# ------------------------------------------------------------
# Historical hotspots
# ------------------------------------------------------------

# Engine 06 stored UTM X/Y in columns named latitude/longitude.
hotspot_points = gpd.GeoDataFrame(
    hotspots.copy(),
    geometry=gpd.points_from_xy(
        hotspots["longitude"],
        hotspots["latitude"],
    ),
    crs="EPSG:32645",
)


# ------------------------------------------------------------
# Current risk zones
# ------------------------------------------------------------

# Incident coordinates are also UTM coordinates.
risk_points = gpd.GeoDataFrame(
    risk.copy(),
    geometry=gpd.points_from_xy(
        risk["longitude"],
        risk["latitude"],
    ),
    crs="EPSG:32645",
)


# ------------------------------------------------------------
# Nearest historical hotspot for each risk zone
# ------------------------------------------------------------

joined = gpd.sjoin_nearest(
    risk_points,
    hotspot_points[
        [
            "hotspot_id",
            "event_count",
            "hotspot_score",
            "hotspot_category",
            "geometry",
        ]
    ],
    how="left",
    distance_col="historical_hotspot_distance_m",
)


# ------------------------------------------------------------
# Persistence score
# ------------------------------------------------------------

# Smaller distance + stronger historical activity
# produces a larger persistence score.

distance_score = (
    1.0
    / (
        1.0
        + joined[
            "historical_hotspot_distance_m"
        ] / 5000.0
    )
)

historical_strength = (
    joined["hotspot_score"] / 100.0
)

current_strength = (
    joined["max_risk_score"] / 100.0
)

joined["historical_current_score"] = (
    0.45 * historical_strength * 100.0
    + 0.35 * current_strength * 100.0
    + 0.20 * distance_score * 100.0
)


# ------------------------------------------------------------
# Correlation category
# ------------------------------------------------------------

def classify(score):

    if score >= 75:
        return "VERY_STRONG"

    if score >= 50:
        return "STRONG"

    if score >= 25:
        return "MODERATE"

    return "WEAK"


joined["historical_current_category"] = (
    joined["historical_current_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Persistent hotspot flag
# ------------------------------------------------------------

joined["persistent_risk_zone"] = (
    (
        joined["historical_hotspot_distance_m"]
        <= 2000
    )
    &
    (
        joined["hotspot_score"]
        >= 50
    )
    &
    (
        joined["max_risk_score"]
        >= 50
    )
).astype(int)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "incident_id",
    "priority_rank",
    "priority_score",
    "priority_level",
    "max_risk_score",
    "historical_hotspot_distance_m",
    "hotspot_id",
    "event_count",
    "hotspot_score",
    "hotspot_category",
    "historical_current_score",
    "historical_current_category",
    "persistent_risk_zone",
]

joined[output_columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("STEP 26")
print("HISTORICAL ↔ CURRENT RISK CORRELATION")
print("========================================")

print(
    "Current risk zones:",
    len(joined),
)

print(
    "Historical hotspots:",
    len(hotspots),
)

print(
    "\nCorrelation categories:"
)

print(
    joined[
        "historical_current_category"
    ]
    .value_counts()
    .to_string()
)

print(
    "\nPersistent risk zones:",
    int(
        joined[
            "persistent_risk_zone"
        ].sum()
    ),
)

print(
    "\nMean historical-hotspot distance:",
    round(
        joined[
            "historical_hotspot_distance_m"
        ].mean(),
        2,
    ),
    "m",
)

print(
    "\nTop persistent/current overlaps:"
)

print(
    joined[
        [
            "incident_id",
            "priority_rank",
            "historical_current_score",
            "historical_current_category",
            "historical_hotspot_distance_m",
        ]
    ]
    .sort_values(
        "historical_current_score",
        ascending=False,
    )
    .head(10)
    .to_string(index=False)
)

print("\nOutput:")
print(OUTPUT)

print("\nSTEP 26 COMPLETE ✅")

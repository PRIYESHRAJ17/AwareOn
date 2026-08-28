from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = (
    ROOT / "data/processed/grid/master_grid_100m.geojson"
)

DECISION_FILE = (
    ROOT / "data/processed/intelligence/awareon_risk_decisions.csv"
)

ALERT_FILE = (
    ROOT / "data/processed/intelligence/awareon_alerts.csv"
)

OUT_DIR = ROOT / "data/processed/intelligence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = (
    OUT_DIR / "awareon_incidents.csv"
)

OUTPUT_GEOJSON = (
    OUT_DIR / "awareon_incidents.geojson"
)


# ------------------------------------------------------------
# Load the 1,298 modelling cells
# ------------------------------------------------------------

grid = gpd.read_file(
    GRID_FILE
).to_crs("EPSG:32645")

decision = pd.read_csv(
    DECISION_FILE
)

alerts = pd.read_csv(
    ALERT_FILE
)

grid["cell_id"] = grid["cell_id"].astype(str)
decision["cell_id"] = decision["cell_id"].astype(str)
alerts["cell_id"] = alerts["cell_id"].astype(str)


# ------------------------------------------------------------
# Keep only cells participating in the intelligence model
# ------------------------------------------------------------

data = grid.merge(
    decision,
    on="cell_id",
    how="inner",
)

if len(data) != len(decision):
    raise RuntimeError(
        f"Decision/grid mismatch: "
        f"matched {len(data)} of {len(decision)} decision cells."
    )


# ------------------------------------------------------------
# Add alert information where available
# ------------------------------------------------------------

alert_columns = [
    "cell_id",
    "alert_level",
    "should_alert",
    "alert_priority_score",
]

available_alert_columns = [
    column
    for column in alert_columns
    if column in alerts.columns
]

data = data.merge(
    alerts[available_alert_columns],
    on="cell_id",
    how="left",
)


# ------------------------------------------------------------
# Normalize alert fields
# ------------------------------------------------------------

if "should_alert" not in data.columns:
    data["should_alert"] = 0

if "alert_priority_score" not in data.columns:
    data["alert_priority_score"] = 0.0

if "alert_level" not in data.columns:
    data["alert_level"] = "ROUTINE"

data["should_alert"] = (
    pd.to_numeric(
        data["should_alert"],
        errors="coerce",
    )
    .fillna(0)
    .astype(int)
)

data["alert_priority_score"] = (
    pd.to_numeric(
        data["alert_priority_score"],
        errors="coerce",
    )
    .fillna(0.0)
)


# ------------------------------------------------------------
# Select risk zones
# ------------------------------------------------------------

risk_zone_levels = [
    "WATCH",
    "WARNING",
    "HIGH",
    "CRITICAL",
]

risk_zones = data[
    data["warning_state"].isin(
        risk_zone_levels
    )
].copy()


print("\n========================================")
print("STEP 24")
print("AWAREON RISK-ZONE CLUSTERING")
print("========================================")

print(
    "Master grid cells:",
    len(grid),
)

print(
    "Decision/model cells:",
    len(decision),
)

print(
    "Matched modelling cells:",
    len(data),
)

print("\nWarning states:")
print(
    data["warning_state"]
    .value_counts()
    .to_string()
)

print(
    "\nRisk-zone cells:",
    len(risk_zones),
)


# ------------------------------------------------------------
# No risk zones
# ------------------------------------------------------------

if risk_zones.empty:

    columns = [
        "incident_id",
        "cell_count",
        "max_risk_score",
        "mean_risk_score",
        "max_alert_priority",
        "highest_decision_state",
        "active_alert_cells",
        "latitude",
        "longitude",
        "affected_cells",
        "incident_category",
    ]

    pd.DataFrame(
        columns=columns
    ).to_csv(
        OUTPUT_CSV,
        index=False,
    )

    empty_geo = gpd.GeoDataFrame(
        columns=columns + ["geometry"],
        geometry="geometry",
        crs="EPSG:32645",
    )

    empty_geo.to_crs(
        "EPSG:4326"
    ).to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    print("\nRisk-zone cells: 0")
    print("Incidents: 0")
    print("\nSTEP 24 COMPLETE ✅")

    raise SystemExit(0)


# ------------------------------------------------------------
# Spatial clustering
# ------------------------------------------------------------

centroids = risk_zones.geometry.centroid

coordinates = np.column_stack(
    [
        centroids.x.values,
        centroids.y.values,
    ]
)

clusterer = DBSCAN(
    eps=500,
    min_samples=2,
)

risk_zones["cluster_label"] = (
    clusterer.fit_predict(coordinates)
)


# ------------------------------------------------------------
# Assign incident IDs
# ------------------------------------------------------------

isolated_counter = 0
incident_ids = []

for label in risk_zones["cluster_label"]:

    if label == -1:

        incident_ids.append(
            f"RISK_ZONE_ISOLATED_{isolated_counter}"
        )

        isolated_counter += 1

    else:

        incident_ids.append(
            f"RISK_ZONE_CLUSTER_{label}"
        )


risk_zones["incident_id"] = incident_ids


# ------------------------------------------------------------
# Aggregate incidents
# ------------------------------------------------------------

state_order = {
    "NORMAL": 0,
    "WATCH": 1,
    "WARNING": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

records = []

for incident_id, group in risk_zones.groupby(
    "incident_id"
):

    union = group.geometry.union_all()

    centroid = union.centroid

    highest_state = max(
        group["warning_state"],
        key=lambda x: state_order.get(
            x,
            0,
        ),
    )

    active_alert_cells = int(
        group["should_alert"].sum()
    )

    if highest_state == "CRITICAL":
        category = "CRITICAL_RISK_ZONE"

    elif highest_state in [
        "WARNING",
        "HIGH",
    ]:
        category = "HIGH_PRIORITY_RISK_ZONE"

    else:
        category = "MONITORING_RISK_ZONE"

    records.append(
        {
            "incident_id": incident_id,

            "cell_count": int(
                len(group)
            ),

            "max_risk_score": float(
                group["unified_risk_score"].max()
            ),

            "mean_risk_score": float(
                group["unified_risk_score"].mean()
            ),

            "max_alert_priority": float(
                group["alert_priority_score"].max()
            ),

            "highest_decision_state": highest_state,

            "active_alert_cells": active_alert_cells,

            "latitude": float(
                centroid.y
            ),

            "longitude": float(
                centroid.x
            ),

            "affected_cells": ",".join(
                group["cell_id"].astype(str)
            ),

            "incident_category": category,
        }
    )


incidents = pd.DataFrame(records)


# ------------------------------------------------------------
# Save CSV
# ------------------------------------------------------------

incidents.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Save GeoJSON
# ------------------------------------------------------------

incident_geo = gpd.GeoDataFrame(
    incidents.copy(),
    geometry=gpd.points_from_xy(
        incidents["longitude"],
        incidents["latitude"],
    ),
    crs="EPSG:32645",
)

incident_geo.to_crs(
    "EPSG:4326"
).to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print(
    "\nRisk-zone clusters:",
    len(incidents),
)

print("\nIncident categories:")
print(
    incidents[
        "incident_category"
    ]
    .value_counts()
    .to_string()
)

print(
    "\nClusters containing active alerts:",
    int(
        (
            incidents["active_alert_cells"] > 0
        ).sum()
    ),
)

print("\nLargest risk zones:")

print(
    incidents.sort_values(
        "cell_count",
        ascending=False,
    )
    .head(10)
    .to_string(index=False)
)

print("\nCSV:")
print(OUTPUT_CSV)

print("\nGeoJSON:")
print(OUTPUT_GEOJSON)

print("\nSTEP 24 COMPLETE ✅")

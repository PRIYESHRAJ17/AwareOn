from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = (
    ROOT / "data/processed/grid/master_grid_100m.geojson"
)

SUS_FILE = (
    ROOT / "data/processed/engines/"
    "susceptibility_engine_output.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "spatial_propagation_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

grid = gpd.read_file(GRID_FILE).to_crs("EPSG:32645")
sus = pd.read_csv(SUS_FILE)

grid["cell_id"] = grid["cell_id"].astype(str)
sus["cell_id"] = sus["cell_id"].astype(str)

data = grid.merge(
    sus[
        [
            "cell_id",
            "susceptibility_probability",
        ]
    ],
    on="cell_id",
    how="inner",
)

if len(data) != len(sus):
    raise RuntimeError(
        f"Grid/susceptibility mismatch: "
        f"{len(data)} vs {len(sus)}"
    )


# ------------------------------------------------------------
# Spatial index
# ------------------------------------------------------------

print("Building spatial index...")


# ------------------------------------------------------------
# Neighborhood features
# ------------------------------------------------------------

mean_risk = []
max_risk = []
risk_std = []
high_fraction = []
neighbor_count = []


for idx, geom in data.geometry.items():

    # 500 m neighborhood around each cell.
    zone = geom.centroid.buffer(500)

    nearby = data[
        data.geometry.intersects(zone)
    ]

    # Exclude the target cell itself.
    nearby = nearby[
        nearby.index != idx
    ]

    if nearby.empty:
        mean_risk.append(0.0)
        max_risk.append(0.0)
        risk_std.append(0.0)
        high_fraction.append(0.0)
        neighbor_count.append(0)
        continue

    risks = nearby[
        "susceptibility_probability"
    ].astype(float)

    mean_risk.append(
        float(risks.mean())
    )

    max_risk.append(
        float(risks.max())
    )

    risk_std.append(
        float(risks.std())
        if len(risks) > 1
        else 0.0
    )

    high_fraction.append(
        float(
            (risks >= 0.45).mean()
        )
    )

    neighbor_count.append(
        int(len(risks))
    )


data["neighbor_mean_risk"] = mean_risk
data["neighbor_max_risk"] = max_risk
data["neighbor_risk_std"] = risk_std
data["neighbor_high_risk_fraction"] = high_fraction
data["neighbor_count"] = neighbor_count


# ------------------------------------------------------------
# Spatial pressure score
# ------------------------------------------------------------

data["spatial_pressure_score"] = (
    0.40
    * data["neighbor_mean_risk"]
    * 100.0
    +
    0.30
    * data["neighbor_max_risk"]
    * 100.0
    +
    0.30
    * data["neighbor_high_risk_fraction"]
    * 100.0
)


# ------------------------------------------------------------
# Category
# ------------------------------------------------------------

def classify(score):

    if score < 25:
        return "LOW"

    if score < 50:
        return "MODERATE"

    if score < 75:
        return "HIGH"

    return "EXTREME"


data["spatial_category"] = (
    data["spatial_pressure_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "susceptibility_probability",
    "neighbor_count",
    "neighbor_mean_risk",
    "neighbor_max_risk",
    "neighbor_risk_std",
    "neighbor_high_risk_fraction",
    "spatial_pressure_score",
    "spatial_category",
]

data[output_columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 09")
print("SPATIAL PROPAGATION ENGINE")
print("========================================")

print(
    "Cells processed:",
    len(data),
)

print(
    "Mean neighbors:",
    round(
        data["neighbor_count"].mean(),
        2,
    ),
)

print("\nSpatial categories:")
print(
    data["spatial_category"]
    .value_counts()
    .to_string()
)

print("\nSpatial pressure statistics:")
print(
    data["spatial_pressure_score"]
    .describe()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 09 COMPLETE ✅")

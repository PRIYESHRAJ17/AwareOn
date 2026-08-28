from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = ROOT / "data/processed/grid/master_grid_100m.geojson"
POSITIVE_FILE = ROOT / "data/processed/ground_truth/positive_cells.csv"

OUT_DIR = ROOT / "data/processed/ground_truth"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUT_DIR / "negative_cells.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

grid = gpd.read_file(GRID_FILE).to_crs("EPSG:32645")
positive = pd.read_csv(POSITIVE_FILE)

if "cell_id" not in positive.columns:
    raise RuntimeError("positive_cells.csv has no cell_id column.")


# ------------------------------------------------------------
# Mark positive cells
# ------------------------------------------------------------

grid["label"] = 0

positive_ids = set(
    positive["cell_id"].astype(str)
)

grid["cell_id"] = grid["cell_id"].astype(str)

grid.loc[
    grid["cell_id"].isin(positive_ids),
    "label"
] = 1


# ------------------------------------------------------------
# Create exclusion zone around positive cells
# ------------------------------------------------------------

positive_geometries = grid.loc[
    grid["label"] == 1,
    "geometry",
]

if positive_geometries.empty:
    raise RuntimeError("No positive cells found.")


positive_union = unary_union(
    positive_geometries.tolist()
)

# 500 m exclusion zone.
exclusion_zone = positive_union.buffer(500)


# ------------------------------------------------------------
# Candidate negatives
# ------------------------------------------------------------

negative_candidates = grid[
    (grid["label"] == 0)
    & (~grid.geometry.intersects(exclusion_zone))
].copy()


if negative_candidates.empty:
    raise RuntimeError(
        "No negative candidates remain after 500 m exclusion."
    )


# ------------------------------------------------------------
# Spatially balanced sampling
# ------------------------------------------------------------

# Target approximately 1:1 negatives to positives.
target_count = min(
    len(positive),
    len(negative_candidates),
)

# Use deterministic random state for reproducibility.
negative_sample = negative_candidates.sample(
    n=target_count,
    random_state=42,
)

negative_sample = negative_sample[
    ["cell_id"]
].copy()

negative_sample["label"] = 0


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

negative_sample.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("NEGATIVE SAMPLE CONSTRUCTION")
print("========================================")

print("Positive cells:", len(positive))
print("Negative candidates:", len(negative_candidates))
print("Negative samples:", len(negative_sample))
print("Exclusion radius: 500 m")

print("\nClass ratio:")
print(
    "Positive : Negative = "
    f"{len(positive)} : {len(negative_sample)}"
)

print("\nOutput:")
print(OUTPUT_FILE)

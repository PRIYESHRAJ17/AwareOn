from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = ROOT / "data/processed/grid/master_grid_100m.geojson"
POS_FILE = ROOT / "data/processed/ground_truth/positive_cells.csv"
NEG_FILE = ROOT / "data/processed/ground_truth/negative_cells.csv"

OUT_DIR = ROOT / "data/processed/ground_truth"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Load labels
# ------------------------------------------------------------

positive = pd.read_csv(POS_FILE)[["cell_id"]].copy()
positive["label"] = 1

negative = pd.read_csv(NEG_FILE)[["cell_id"]].copy()
negative["label"] = 0

labels = pd.concat(
    [positive, negative],
    ignore_index=True,
)

labels["cell_id"] = labels["cell_id"].astype(str)


# ------------------------------------------------------------
# Load grid
# ------------------------------------------------------------

grid = gpd.read_file(GRID_FILE).to_crs("EPSG:32645")
grid["cell_id"] = grid["cell_id"].astype(str)

data = grid.merge(
    labels,
    on="cell_id",
    how="inner",
)

if len(data) != len(labels):
    raise RuntimeError(
        f"Grid/label mismatch: {len(data)} vs {len(labels)}"
    )


# ------------------------------------------------------------
# Spatial block IDs
# ------------------------------------------------------------

# 10 km blocks.
# Cells within the same block always stay in the same split.
BLOCK_SIZE = 10000

data["block_x"] = (
    data.geometry.centroid.x // BLOCK_SIZE
).astype(int)

data["block_y"] = (
    data.geometry.centroid.y // BLOCK_SIZE
).astype(int)

data["block_id"] = (
    data["block_x"].astype(str)
    + "_"
    + data["block_y"].astype(str)
)


# ------------------------------------------------------------
# Create stratification at block level
# ------------------------------------------------------------

block_stats = (
    data.groupby("block_id")
    .agg(
        cells=("cell_id", "count"),
        positives=("label", "sum"),
    )
    .reset_index()
)

block_stats["positive_rate"] = (
    block_stats["positives"]
    / block_stats["cells"]
)


# ------------------------------------------------------------
# Deterministic block assignment
# ------------------------------------------------------------

# Hash block IDs so results are reproducible.
block_stats["hash"] = (
    pd.util.hash_pandas_object(
        block_stats["block_id"],
        index=False,
    )
    .astype("uint64")
)

block_stats = block_stats.sort_values(
    "hash"
).reset_index(drop=True)


n_blocks = len(block_stats)

n_train = max(1, int(n_blocks * 0.70))
n_val = max(1, int(n_blocks * 0.15))

block_stats["split"] = "test"

block_stats.loc[
    : n_train - 1,
    "split"
] = "train"

block_stats.loc[
    n_train : n_train + n_val - 1,
    "split"
] = "val"


# ------------------------------------------------------------
# Merge split assignment back
# ------------------------------------------------------------

data = data.merge(
    block_stats[["block_id", "split"]],
    on="block_id",
    how="left",
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

train = data[data["split"] == "train"].copy()
val = data[data["split"] == "val"].copy()
test = data[data["split"] == "test"].copy()

for name, frame in [
    ("train", train),
    ("validation", val),
    ("test", test),
]:

    frame[
        ["cell_id", "label", "block_id", "geometry"]
    ].to_file(
        OUT_DIR / f"ground_truth_{name}.geojson",
        driver="GeoJSON",
    )

    frame[
        ["cell_id", "label", "block_id"]
    ].to_csv(
        OUT_DIR / f"ground_truth_{name}.csv",
        index=False,
    )


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("SPATIAL GROUND-TRUTH SPLIT")
print("========================================")

print("Total cells:", len(data))
print("Spatial blocks:", n_blocks)

for name, frame in [
    ("TRAIN", train),
    ("VALIDATION", val),
    ("TEST", test),
]:

    print(
        f"\n{name}: "
        f"{len(frame)} cells | "
        f"positives={int(frame['label'].sum())} | "
        f"negatives={int((frame['label'] == 0).sum())}"
    )

print("\nFiles created in:")
print(OUT_DIR)

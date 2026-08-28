from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = ROOT / "data/processed/grid/master_grid_100m.geojson"
GSI_FILE = ROOT / "data/processed/landslides/gsi_sikkim_inventory_clean.geojson"

OUT_DIR = ROOT / "data/processed/ground_truth"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUT_DIR / "positive_cells.csv"


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

grid = gpd.read_file(GRID_FILE)
gsi = gpd.read_file(GSI_FILE)

if grid.empty:
    raise RuntimeError("Master grid is empty.")

if gsi.empty:
    raise RuntimeError("GSI inventory is empty.")


# ------------------------------------------------------------
# Ensure projected CRS
# ------------------------------------------------------------

grid = grid.to_crs("EPSG:32645")
gsi = gsi.to_crs("EPSG:32645")


# ------------------------------------------------------------
# Assign each GSI point to a grid cell
# ------------------------------------------------------------

joined = gpd.sjoin(
    gsi,
    grid[["cell_id", "geometry"]],
    how="inner",
    predicate="within",
)


if joined.empty:
    raise RuntimeError(
        "No GSI points intersected the master grid."
    )


# ------------------------------------------------------------
# Collapse multiple GSI events in the same cell
# ------------------------------------------------------------

positive = (
    joined.groupby("cell_id")
    .agg(
        landslide_count=("landslide_id", "count"),
        record_ids=("record_id", lambda x: ",".join(
            map(str, sorted(set(x)))
        )),
    )
    .reset_index()
)


positive["label"] = 1


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

positive.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("GROUND-TRUTH POSITIVE LABELS")
print("========================================")

print("GSI records:", len(gsi))
print("Matched GSI records:", len(joined))
print("Unique positive cells:", len(positive))

print(
    "Maximum landslides in one 100 m cell:",
    int(positive["landslide_count"].max())
)

print("\nOutput:")
print(OUTPUT_FILE)

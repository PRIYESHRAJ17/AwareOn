from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import distance_transform_edt
from rasterio.transform import rowcol


ROOT = Path(__file__).resolve().parents[1]

GRID_FILE = ROOT / "data/processed/grid/master_grid_100m.geojson"
POS_FILE = ROOT / "data/processed/ground_truth/positive_cells.csv"
NEG_FILE = ROOT / "data/processed/ground_truth/negative_cells.csv"

DEM_FILE = ROOT / "data/processed/grid/sikkim_dem_utm45.tif"
SLOPE_FILE = ROOT / "data/processed/grid/slope.tif"
ASPECT_FILE = ROOT / "data/processed/grid/aspect.tif"

OUT_DIR = ROOT / "data/processed/features"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "ground_truth_terrain_features.csv"


# ------------------------------------------------------------
# Load labelled cells
# ------------------------------------------------------------

positive = pd.read_csv(POS_FILE)[["cell_id", "label"]].copy()
negative = pd.read_csv(NEG_FILE)[["cell_id", "label"]].copy()

labels = pd.concat(
    [positive, negative],
    ignore_index=True,
)

labels["cell_id"] = labels["cell_id"].astype(str)

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

print("Labelled cells:", len(data))


# ------------------------------------------------------------
# Nearest valid raster values
# ------------------------------------------------------------

def load_raster(raster_path):
    with rasterio.open(raster_path) as src:
        arr = src.read(1).astype("float32")
        transform = src.transform
        nodata = src.nodata
        profile = src.profile.copy()

    valid = np.isfinite(arr)

    if nodata is not None:
        valid &= ~np.isclose(arr, nodata)

    return arr, valid, transform, profile


def nearest_valid_values(arr, valid, rows, cols):
    """
    Return values at requested raster locations.

    If a requested pixel is invalid, use the globally nearest
    valid raster pixel and mark it as imputed.
    """

    # Nearest valid pixel for every raster pixel.
    invalid = ~valid

    if invalid.any():
        _, indices = distance_transform_edt(
            invalid,
            return_distances=True,
            return_indices=True,
        )

        nearest_rows = indices[0]
        nearest_cols = indices[1]

    values = []
    imputed = []

    for row, col in zip(rows, cols):

        if (
            row < 0
            or row >= arr.shape[0]
            or col < 0
            or col >= arr.shape[1]
        ):
            values.append(np.nan)
            imputed.append(1)
            continue

        if valid[row, col]:
            values.append(float(arr[row, col]))
            imputed.append(0)
        else:
            nr = int(nearest_rows[row, col])
            nc = int(nearest_cols[row, col])

            if valid[nr, nc]:
                values.append(float(arr[nr, nc]))
                imputed.append(1)
            else:
                values.append(np.nan)
                imputed.append(1)

    return values, imputed


# ------------------------------------------------------------
# Prepare centroid raster locations
# ------------------------------------------------------------

centroids = data.geometry.centroid


# ------------------------------------------------------------
# Elevation
# ------------------------------------------------------------

print("Sampling elevation...")

dem, dem_valid, dem_transform, _ = load_raster(DEM_FILE)

dem_rows = []
dem_cols = []

for point in centroids:
    row, col = rowcol(
        dem_transform,
        point.x,
        point.y,
    )
    dem_rows.append(row)
    dem_cols.append(col)

elevation, elevation_imputed = nearest_valid_values(
    dem,
    dem_valid,
    dem_rows,
    dem_cols,
)

data["elevation_m"] = elevation


# ------------------------------------------------------------
# Slope
# ------------------------------------------------------------

print("Sampling slope...")

slope, slope_valid, slope_transform, _ = load_raster(
    SLOPE_FILE
)

slope_rows = []
slope_cols = []

for point in centroids:
    row, col = rowcol(
        slope_transform,
        point.x,
        point.y,
    )
    slope_rows.append(row)
    slope_cols.append(col)

slope_values, slope_imputed = nearest_valid_values(
    slope,
    slope_valid,
    slope_rows,
    slope_cols,
)

data["slope_deg"] = slope_values


# ------------------------------------------------------------
# Aspect
# ------------------------------------------------------------

print("Sampling aspect...")

aspect, aspect_valid, aspect_transform, _ = load_raster(
    ASPECT_FILE
)

aspect_rows = []
aspect_cols = []

for point in centroids:
    row, col = rowcol(
        aspect_transform,
        point.x,
        point.y,
    )
    aspect_rows.append(row)
    aspect_cols.append(col)

aspect_values, aspect_imputed = nearest_valid_values(
    aspect,
    aspect_valid,
    aspect_rows,
    aspect_cols,
)

data["aspect_deg"] = aspect_values


# ------------------------------------------------------------
# Terrain ruggedness
# ------------------------------------------------------------

print("Calculating terrain ruggedness...")

ruggedness = []
ruggedness_imputed = []

for point in centroids:

    row, col = rowcol(
        dem_transform,
        point.x,
        point.y,
    )

    if (
        row < 0
        or row >= dem.shape[0]
        or col < 0
        or col >= dem.shape[1]
    ):
        ruggedness.append(np.nan)
        ruggedness_imputed.append(1)
        continue

    found = False

    # First try progressively larger local windows.
    for radius in [1, 2, 3, 5, 8]:

        r0 = max(0, row - radius)
        r1 = min(dem.shape[0], row + radius + 1)

        c0 = max(0, col - radius)
        c1 = min(dem.shape[1], col + radius + 1)

        window = dem[r0:r1, c0:c1]
        window_valid = dem_valid[r0:r1, c0:c1]

        values = window[window_valid]

        if len(values) >= 5:
            ruggedness.append(float(np.std(values)))

            # Radius > 1 means we're using a broader fallback
            # neighborhood rather than the immediate 3x3 area.
            ruggedness_imputed.append(
                1 if radius > 1 else 0
            )

            found = True
            break

    if found:
        continue

    # Global nearest-valid fallback.
    if dem_valid.any():

        valid_positions = np.argwhere(dem_valid)

        distances = (
            (valid_positions[:, 0] - row) ** 2
            + (valid_positions[:, 1] - col) ** 2
        )

        nearest_index = int(np.argmin(distances))

        nr, nc = valid_positions[nearest_index]

        # Compute a small neighbourhood around nearest valid point.
        r0 = max(0, nr - 2)
        r1 = min(dem.shape[0], nr + 3)

        c0 = max(0, nc - 2)
        c1 = min(dem.shape[1], nc + 3)

        window = dem[r0:r1, c0:c1]
        window_valid = dem_valid[r0:r1, c0:c1]

        values = window[window_valid]

        if len(values) >= 2:
            ruggedness.append(float(np.std(values)))
            ruggedness_imputed.append(1)
        else:
            ruggedness.append(np.nan)
            ruggedness_imputed.append(1)

    else:
        ruggedness.append(np.nan)
        ruggedness_imputed.append(1)


data["elevation_std_m"] = ruggedness


# ------------------------------------------------------------
# Circular aspect encoding
# ------------------------------------------------------------

aspect_rad = np.deg2rad(
    data["aspect_deg"]
)

data["aspect_sin"] = np.sin(
    aspect_rad
)

data["aspect_cos"] = np.cos(
    aspect_rad
)


# ------------------------------------------------------------
# Overall terrain-imputation flag
# ------------------------------------------------------------

data["terrain_imputed"] = (
    np.array(elevation_imputed)
    | np.array(slope_imputed)
    | np.array(aspect_imputed)
    | np.array(ruggedness_imputed)
).astype(int)


# ------------------------------------------------------------
# Final validation
# ------------------------------------------------------------

terrain_columns = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "elevation_std_m",
    "aspect_sin",
    "aspect_cos",
]

print("\nMissing terrain values:")
print(
    data[terrain_columns]
    .isna()
    .sum()
    .to_string()
)

print(
    "\nTerrain-imputed cells:",
    int(data["terrain_imputed"].sum())
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "label",
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "elevation_std_m",
    "aspect_sin",
    "aspect_cos",
    "terrain_imputed",
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
print("STEP 14.1 TERRAIN FEATURES COMPLETE")
print("========================================")

print("Rows:", len(data))

print("Columns:")
for column in output_columns:
    print(" -", column)

print("\nTerrain statistics:")
print(
    data[
        [
            "elevation_m",
            "slope_deg",
            "aspect_deg",
            "elevation_std_m",
        ]
    ].describe().to_string()
)

print("\nOutput:")
print(OUTPUT)

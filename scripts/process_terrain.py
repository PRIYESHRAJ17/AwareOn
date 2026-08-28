from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling


ROOT = Path(__file__).resolve().parents[1]

DEM_DIR = ROOT / "data/raw/terrain/dem"
OUT_DIR = ROOT / "data/processed/grid"
BOUNDARY = OUT_DIR / "sikkim_boundary.geojson"

OUT_DIR.mkdir(parents=True, exist_ok=True)

dem_files = sorted(DEM_DIR.glob("*.tif"))

if len(dem_files) != 9:
    raise RuntimeError(f"Expected 9 DEM tiles, found {len(dem_files)}")


# ------------------------------------------------------------
# 1. Mosaic
# ------------------------------------------------------------

srcs = [rasterio.open(path) for path in dem_files]

try:
    mosaic, mosaic_transform = merge(
        srcs,
        nodata=-32767,
    )

    profile = srcs[0].profile.copy()
    profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=mosaic_transform,
        count=1,
        nodata=-32767,
        compress="deflate",
    )

    mosaic_path = OUT_DIR / "sikkim_dem_mosaic.tif"

    with rasterio.open(mosaic_path, "w", **profile) as dst:
        dst.write(mosaic[0], 1)

finally:
    for src in srcs:
        src.close()


# ------------------------------------------------------------
# 2. Clip to study boundary
# ------------------------------------------------------------

boundary = gpd.read_file(BOUNDARY).to_crs("EPSG:4326")

with rasterio.open(mosaic_path) as src:

    clipped, clipped_transform = mask(
        src,
        boundary.geometry,
        crop=True,
        filled=True,
        nodata=-32767,
    )

    clipped_profile = src.profile.copy()
    clipped_profile.update(
        height=clipped.shape[1],
        width=clipped.shape[2],
        transform=clipped_transform,
        nodata=-32767,
        compress="deflate",
    )

clipped_path = OUT_DIR / "sikkim_dem_clipped.tif"

with rasterio.open(clipped_path, "w", **clipped_profile) as dst:
    dst.write(clipped)


# ------------------------------------------------------------
# 3. Reproject to UTM 45N
# ------------------------------------------------------------

with rasterio.open(clipped_path) as src:

    dst_transform, dst_width, dst_height = calculate_default_transform(
        src.crs,
        "EPSG:32645",
        src.width,
        src.height,
        *src.bounds,
    )

    reproj_profile = src.profile.copy()
    reproj_profile.update(
        crs="EPSG:32645",
        transform=dst_transform,
        width=dst_width,
        height=dst_height,
        nodata=-32767,
        compress="deflate",
    )

    reproj_path = OUT_DIR / "sikkim_dem_utm45.tif"

    with rasterio.open(reproj_path, "w", **reproj_profile) as dst:

        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:32645",
            src_nodata=-32767,
            dst_nodata=-32767,
            resampling=Resampling.bilinear,
        )


# ------------------------------------------------------------
# 4. Calculate slope and aspect
# ------------------------------------------------------------

with rasterio.open(reproj_path) as src:
    dem = src.read(1).astype(np.float32)
    transform = src.transform
    profile = src.profile.copy()

valid = np.isfinite(dem) & (dem != -32767)

# Start with NaN everywhere.
dem_float = np.where(valid, dem, np.nan)

pixel_x = abs(transform.a)
pixel_y = abs(transform.e)

# Use centered finite differences.
dz_dy, dz_dx = np.gradient(
    dem_float,
    pixel_y,
    pixel_x,
)

# A pixel is usable only when its local derivatives are finite.
derivative_valid = (
    valid
    & np.isfinite(dz_dx)
    & np.isfinite(dz_dy)
)

# Slope in degrees.
slope = np.full(
    dem.shape,
    -9999,
    dtype=np.float32,
)

slope[derivative_valid] = np.degrees(
    np.arctan(
        np.sqrt(
            dz_dx[derivative_valid] ** 2
            + dz_dy[derivative_valid] ** 2
        )
    )
)

# Aspect in degrees clockwise from north.
aspect = np.full(
    dem.shape,
    -9999,
    dtype=np.float32,
)

aspect_values = (
    np.degrees(
        np.arctan2(
            -dz_dx[derivative_valid],
            dz_dy[derivative_valid],
        )
    )
    + 360.0
) % 360.0

aspect[derivative_valid] = aspect_values


# ------------------------------------------------------------
# 5. Save slope
# ------------------------------------------------------------

terrain_profile = profile.copy()

terrain_profile.update(
    dtype="float32",
    count=1,
    nodata=-9999,
    compress="deflate",
)

slope_path = OUT_DIR / "slope.tif"

with rasterio.open(slope_path, "w", **terrain_profile) as dst:
    dst.write(slope, 1)


# ------------------------------------------------------------
# 6. Save aspect
# ------------------------------------------------------------

aspect_path = OUT_DIR / "aspect.tif"

with rasterio.open(aspect_path, "w", **terrain_profile) as dst:
    dst.write(aspect, 1)


print("Terrain processing complete.")
print(f"Valid slope pixels: {int((slope != -9999).sum())}")
print(f"Valid aspect pixels: {int((aspect != -9999).sum())}")

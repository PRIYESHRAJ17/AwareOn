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


# ------------------------------------------------------------
# 1. Find DEM tiles
# ------------------------------------------------------------
dem_files = sorted(DEM_DIR.glob("*.tif"))

if len(dem_files) != 9:
    raise RuntimeError(f"Expected 9 DEM tiles, found {len(dem_files)}")

print(f"Found {len(dem_files)} DEM tiles.")


# ------------------------------------------------------------
# 2. Mosaic DEM tiles
# ------------------------------------------------------------
srcs = [rasterio.open(path) for path in dem_files]

try:
    mosaic, mosaic_transform = merge(srcs)

    mosaic_profile = srcs[0].profile.copy()
    mosaic_profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=mosaic_transform,
        count=1,
        compress="deflate",
    )

    mosaic_path = OUT_DIR / "sikkim_dem_mosaic.tif"

    with rasterio.open(mosaic_path, "w", **mosaic_profile) as dst:
        dst.write(mosaic[0], 1)

finally:
    for src in srcs:
        src.close()

print(f"Mosaic created: {mosaic_path}")


# ------------------------------------------------------------
# 3. Clip DEM to AwareOn study boundary
# ------------------------------------------------------------
boundary = gpd.read_file(BOUNDARY).to_crs("EPSG:4326")

with rasterio.open(mosaic_path) as src:
    clipped, clipped_transform = mask(
        src,
        boundary.geometry,
        crop=True,
    )

    clipped_profile = src.profile.copy()
    clipped_profile.update(
        height=clipped.shape[1],
        width=clipped.shape[2],
        transform=clipped_transform,
    )

clipped_path = OUT_DIR / "sikkim_dem_clipped.tif"

with rasterio.open(clipped_path, "w", **clipped_profile) as dst:
    dst.write(clipped)

print(f"Clipped DEM created: {clipped_path}")


# ------------------------------------------------------------
# 4. Reproject DEM to UTM Zone 45N
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
            resampling=Resampling.bilinear,
        )

print(f"Reprojected DEM created: {reproj_path}")


# ------------------------------------------------------------
# 5. Calculate elevation, slope and aspect
# ------------------------------------------------------------
with rasterio.open(reproj_path) as src:
    dem = src.read(1).astype(np.float32)
    transform = src.transform
    profile = src.profile.copy()

pixel_x = abs(transform.a)
pixel_y = abs(transform.e)

if pixel_x <= 0 or pixel_y <= 0:
    raise RuntimeError("Invalid DEM pixel size.")

# Gradient of elevation
dz_dy, dz_dx = np.gradient(dem, pixel_y, pixel_x)

# Slope in degrees
slope = np.degrees(
    np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
).astype(np.float32)

# Aspect: degrees clockwise from north
aspect = (
    np.degrees(np.arctan2(-dz_dx, dz_dy)) + 360.0
) % 360.0

aspect = aspect.astype(np.float32)


# ------------------------------------------------------------
# 6. Save slope
# ------------------------------------------------------------
terrain_profile = profile.copy()
terrain_profile.update(
    dtype="float32",
    count=1,
    nodata=-9999.0,
    compress="deflate",
)

slope_path = OUT_DIR / "slope.tif"

with rasterio.open(slope_path, "w", **terrain_profile) as dst:
    dst.write(slope, 1)

print(f"Slope created: {slope_path}")


# ------------------------------------------------------------
# 7. Save aspect
# ------------------------------------------------------------
aspect_path = OUT_DIR / "aspect.tif"

with rasterio.open(aspect_path, "w", **terrain_profile) as dst:
    dst.write(aspect, 1)

print(f"Aspect created: {aspect_path}")


print("\nTerrain processing complete.")

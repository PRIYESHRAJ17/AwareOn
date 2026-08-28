from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[1]

SAR_DIR = ROOT / "data/raw/satellite/sentinel1"

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "sar_evidence_engine_output.csv"


# ------------------------------------------------------------
# Locate VV / VH
# ------------------------------------------------------------

vv_files = list(
    SAR_DIR.glob("*vv*.tiff")
)

vh_files = list(
    SAR_DIR.glob("*vh*.tiff")
)

if not vv_files:
    raise RuntimeError("Sentinel-1 VV file not found.")

if not vh_files:
    raise RuntimeError("Sentinel-1 VH file not found.")

vv_file = vv_files[0]
vh_file = vh_files[0]


# ------------------------------------------------------------
# Read SAR statistics
# ------------------------------------------------------------

def raster_statistics(path):
    with rasterio.open(path) as src:

        arr = src.read(1).astype("float32")

        valid = np.isfinite(arr)

        if src.nodata is not None:
            valid &= ~np.isclose(
                arr,
                src.nodata,
            )

        values = arr[valid]

        if values.size == 0:
            raise RuntimeError(
                f"No valid pixels found in {path}"
            )

        return {
            "width": src.width,
            "height": src.height,
            "crs": str(src.crs),
            "transform": str(src.transform),
            "dtype": str(src.dtypes[0]),
            "valid_pixels": int(values.size),
            "mean": float(values.mean()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
            "p05": float(np.percentile(values, 5)),
            "p25": float(np.percentile(values, 25)),
            "median": float(np.median(values)),
            "p75": float(np.percentile(values, 75)),
            "p95": float(np.percentile(values, 95)),
        }


print("Reading VV...")
vv = raster_statistics(vv_file)

print("Reading VH...")
vh = raster_statistics(vh_file)


# ------------------------------------------------------------
# SAR relationship
# ------------------------------------------------------------

# Approximate channel contrast from image-wide means.
# This is an evidence descriptor, not a calibrated physical
# backscatter coefficient.
vv_vh_ratio = (
    vv["mean"] / vh["mean"]
    if vh["mean"] != 0
    else np.nan
)


# ------------------------------------------------------------
# Data quality
# ------------------------------------------------------------

georeferenced = (
    vv["crs"] != "None"
    and vh["crs"] != "None"
)

same_shape = (
    vv["width"] == vh["width"]
    and vv["height"] == vh["height"]
)

same_dtype = (
    vv["dtype"] == vh["dtype"]
)


if not georeferenced:
    quality = "UNREFERENCED"

elif not same_shape:
    quality = "MISMATCHED_SHAPE"

elif not same_dtype:
    quality = "MISMATCHED_DTYPE"

else:
    quality = "READY"


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

output = pd.DataFrame(
    [
        {
            "vv_file": vv_file.name,
            "vh_file": vh_file.name,

            "width": vv["width"],
            "height": vv["height"],

            "vv_mean": vv["mean"],
            "vv_std": vv["std"],
            "vv_min": vv["min"],
            "vv_max": vv["max"],
            "vv_p05": vv["p05"],
            "vv_median": vv["median"],
            "vv_p95": vv["p95"],

            "vh_mean": vh["mean"],
            "vh_std": vh["std"],
            "vh_min": vh["min"],
            "vh_max": vh["max"],
            "vh_p05": vh["p05"],
            "vh_median": vh["median"],
            "vh_p95": vh["p95"],

            "vv_vh_mean_ratio": vv_vh_ratio,

            "vv_crs": vv["crs"],
            "vh_crs": vh["crs"],

            "same_shape": int(same_shape),
            "same_dtype": int(same_dtype),
            "georeferenced": int(georeferenced),

            "sar_data_quality": quality,
        }
    ]
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output.to_csv(
    OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 05")
print("SAR EVIDENCE ENGINE")
print("========================================")

print("VV:", vv_file.name)
print("VH:", vh_file.name)

print("\nDimensions:")
print(
    vv["width"],
    "x",
    vv["height"],
)

print("\nVV statistics:")
print("Mean:", round(vv["mean"], 4))
print("Std:", round(vv["std"], 4))
print("Min:", vv["min"])
print("Max:", vv["max"])

print("\nVH statistics:")
print("Mean:", round(vh["mean"], 4))
print("Std:", round(vh["std"], 4))
print("Min:", vh["min"])
print("Max:", vh["max"])

print(
    "\nVV/VH mean ratio:",
    round(vv_vh_ratio, 4),
)

print(
    "\nGeoreferenced:",
    georeferenced,
)

print(
    "Same shape:",
    same_shape,
)

print(
    "SAR quality:",
    quality,
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 05 COMPLETE ✅")

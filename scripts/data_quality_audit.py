from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import geopandas as gpd
except Exception:
    gpd = None

try:
    import rasterio
except Exception:
    rasterio = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "data_foundation_audit"
OUT.mkdir(parents=True, exist_ok=True)

DATASETS = [
    ("gsi_clean", "data/processed/landslides/gsi_sikkim_inventory_clean.csv"),
    ("static_features", "data/processed/features/static_ml_features.csv"),
    ("static_features_validated", "data/processed/features/static_ml_features_validated.csv"),
    ("ground_truth_train", "data/processed/ground_truth/ground_truth_train.csv"),
    ("ground_truth_validation", "data/processed/ground_truth/ground_truth_validation.csv"),
    ("ground_truth_test", "data/processed/ground_truth/ground_truth_test.csv"),
    ("positive_cells", "data/processed/ground_truth/positive_cells.csv"),
    ("negative_cells", "data/processed/ground_truth/negative_cells.csv"),
    ("era5_environment", "data/processed/weather/era5_environment_timeseries.csv"),
    ("current_risk", "data/processed/risk/current_risk_scores.csv"),
    ("intelligence_state", "data/processed/intelligence/awareon_intelligence_state.csv"),
]

RASters = [
    ("dem_clipped", "data/processed/grid/sikkim_dem_clipped.tif"),
    ("dem_utm45", "data/processed/grid/sikkim_dem_utm45.tif"),
    ("slope", "data/processed/grid/slope.tif"),
    ("aspect", "data/processed/grid/aspect.tif"),
]

results = []


def add(name, kind, status, details):
    results.append({
        "dataset": name,
        "kind": kind,
        "status": status,
        "details": details,
    })


def audit_csv(name, rel):
    path = ROOT / rel

    if not path.exists():
        add(name, "CSV", "MISSING", rel)
        return

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        add(name, "CSV", "ERROR", f"read failed: {exc}")
        return

    issues = []

    if df.empty:
        issues.append("empty")

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        issues.append(f"duplicate_rows={duplicate_rows}")

    numeric = df.select_dtypes(include=[np.number])

    # Some engineered time-series features have mathematically
    # unavailable warm-up values. These must remain NaN rather than
    # being fabricated as zero. AwareOn marks such rows explicitly.
    expected_warmup_nan = 0

    if (
        "rain_change_24h_mm" in df.columns
        and "rain_change_24h_available" in df.columns
    ):
        warmup_mask = (
            df["rain_change_24h_available"].eq(False)
            & df["rain_change_24h_mm"].isna()
        )
        expected_warmup_nan = int(warmup_mask.sum())

        unexpected_rain_nan = (
            df["rain_change_24h_mm"].isna()
            & ~warmup_mask
        )
        unexpected_count = int(unexpected_rain_nan.sum())

        if unexpected_count:
            issues.append(
                f"rain_change_24h_unexpected_nan={unexpected_count}"
            )

    nan_count_raw = int(numeric.isna().sum().sum())

    nan_count = nan_count_raw - expected_warmup_nan

    inf_count = (
        int(np.isinf(numeric.to_numpy()).sum())
        if not numeric.empty
        else 0
    )

    if nan_count:
        issues.append(f"numeric_unexpected_nan={nan_count}")

    if inf_count:
        issues.append(f"numeric_inf={inf_count}")

    cell_cols = [c for c in df.columns if c.lower() in {
        "cell_id", "grid_id", "cellid"
    }]

    for col in cell_cols:
        null_ids = int(df[col].isna().sum())
        duplicate_ids = int(df[col].duplicated().sum())

        if null_ids:
            issues.append(f"{col}_null={null_ids}")

        if duplicate_ids:
            issues.append(f"{col}_duplicates={duplicate_ids}")

    date_cols = [
        c for c in df.columns
        if any(
            token in c.lower()
            for token in ("date", "time", "timestamp")
        )
    ]

    date_info = []

    for col in date_cols:
        raw = df[col]

        missing = int(raw.isna().sum())
        present = raw.notna()

        parsed = pd.to_datetime(
            raw[present],
            errors="coerce",
        )

        invalid_nonmissing = int(parsed.isna().sum())

        if invalid_nonmissing:
            issues.append(
                f"{col}_invalid_nonmissing_dates={invalid_nonmissing}"
            )

        valid = parsed.dropna()

        date_info.append({
            "column": col,
            "missing_source_values": missing,
            "valid_dates": int(valid.shape[0]),
            "invalid_nonmissing_dates": invalid_nonmissing,
            "min": str(valid.min()) if not valid.empty else None,
            "max": str(valid.max()) if not valid.empty else None,
        })

    status = "PASS" if not issues else "ISSUES_FOUND"

    add(
        name,
        "CSV",
        status,
        {
            "path": rel,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": [str(c) for c in df.columns],
            "numeric_columns": [str(c) for c in numeric.columns],
            "duplicate_rows": duplicate_rows,
            "nan_values_numeric_raw": nan_count_raw,
            "expected_warmup_nan": expected_warmup_nan,
            "nan_values_numeric_unexpected": nan_count,
            "inf_values_numeric": inf_count,
            "date_columns": date_info,
            "issues": issues,
        },
    )


def audit_raster(name, rel):
    path = ROOT / rel

    if not path.exists():
        add(name, "RASTER", "MISSING", rel)
        return

    if rasterio is None:
        add(
            name,
            "RASTER",
            "UNVERIFIED",
            {
                "path": rel,
                "reason": "rasterio unavailable in audit environment",
                "not_a_dataset_failure": True,
            },
        )
        return

    try:
        with rasterio.open(path) as src:
            data = src.read(masked=True)

            raw = np.asarray(data.filled(np.nan), dtype=float)

            nan_count = int(np.isnan(raw).sum())
            inf_count = int(np.isinf(raw).sum())

            valid = raw[np.isfinite(raw)]

            issues = []

            if not valid.size:
                issues.append("no finite pixels")

            if inf_count:
                issues.append(f"inf_pixels={inf_count}")

            if nan_count:
                issues.append(f"nan_pixels={nan_count}")

            status = "PASS" if not issues else "ISSUES_FOUND"

            add(
                name,
                "RASTER",
                status,
                {
                    "path": rel,
                    "width": src.width,
                    "height": src.height,
                    "bands": src.count,
                    "crs": str(src.crs),
                    "resolution": [float(src.res[0]), float(src.res[1])],
                    "nodata": src.nodata,
                    "bounds": [
                        float(src.bounds.left),
                        float(src.bounds.bottom),
                        float(src.bounds.right),
                        float(src.bounds.top),
                    ],
                    "dtype": str(src.dtypes[0]),
                    "finite_min": float(valid.min()) if valid.size else None,
                    "finite_max": float(valid.max()) if valid.size else None,
                    "finite_mean": float(valid.mean()) if valid.size else None,
                    "nan_pixels": nan_count,
                    "inf_pixels": inf_count,
                    "issues": issues,
                },
            )

    except Exception as exc:
        add(name, "RASTER", "ERROR", str(exc))


for name, rel in DATASETS:
    audit_csv(name, rel)

for name, rel in RASters:
    audit_raster(name, rel)

report = {
    "project": "AwareOn",
    "audit": "data_quality",
    "status": (
        "ISSUES_FOUND"
        if any(x["status"] in {"ISSUES_FOUND", "ERROR", "MISSING"} for x in results)
        else "PASS"
    ),
    "results": results,
}

json_path = OUT / "data_quality_results.json"
json_path.write_text(
    json.dumps(report, indent=2, default=str),
    encoding="utf-8",
)

md = [
    "# AwareOn Data Quality Audit",
    "",
    f"Overall status: `{report['status']}`",
    "",
    "| Dataset | Type | Status |",
    "|---|---|---|",
]

for item in results:
    md.append(
        f"| `{item['dataset']}` | {item['kind']} | `{item['status']}` |"
    )

md.extend([
    "",
    "## Details",
    "",
])

for item in results:
    md.append(f"### {item['dataset']}")
    md.append(f"- Type: `{item['kind']}`")
    md.append(f"- Status: `{item['status']}`")
    md.append(f"- Details: `{json.dumps(item['details'], default=str)}`")
    md.append("")

md_path = OUT / "DATA_QUALITY_REPORT.md"
md_path.write_text("\n".join(md), encoding="utf-8")

print("=" * 72)
print("AWAREON DATA QUALITY AUDIT")
print("=" * 72)
print("Overall:", report["status"])
print()

for item in results:
    print(
        f"{item['status']:14} "
        f"{item['kind']:7} "
        f"{item['dataset']}"
    )

print()
print("JSON :", json_path)
print("REPORT:", md_path)
print("=" * 72)

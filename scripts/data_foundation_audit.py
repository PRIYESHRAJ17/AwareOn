from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    "artifacts",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".geojson",
    ".tif",
    ".tiff",
    ".nc",
    ".parquet",
    ".sql",
}


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        yield path


def safe_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def classify(path: Path, text: str) -> set[str]:
    low = text.lower()
    tags = set()

    patterns = {
        "ingestion": [
            "read_csv",
            "read_file",
            "read_parquet",
            "read_json",
            "read_excel",
            "open_dataset",
            "rasterio.open",
            "gpd.read",
            "xarray",
            "requests.get",
            "httpx",
        ],
        "cleaning": [
            "dropna",
            "fillna",
            "interpolate",
            "replace",
            "clean",
            "normalize",
            "standardize",
        ],
        "features": [
            "feature",
            "features",
            "transform",
            "engineering",
            "scaler",
            "standardscaler",
            "minmaxscaler",
        ],
        "spatial": [
            "crs",
            "to_crs",
            "geometry",
            "geodataframe",
            "latitude",
            "longitude",
            "lat",
            "lon",
            "spatial",
            "gis",
        ],
        "temporal": [
            "timestamp",
            "datetime",
            "date",
            "time",
            "temporal",
            "forecast",
            "historical",
        ],
        "validation": [
            "validate",
            "validation",
            "assert ",
            "schema",
            "quality",
            "range check",
            "outlier",
        ],
        "provenance": [
            "provenance",
            "source",
            "dataset",
            "metadata",
            "lineage",
            "freshness",
        ],
    }

    for tag, needles in patterns.items():
        if any(needle in low for needle in needles):
            tags.add(tag)

    return tags


def audit():
    files = []
    tag_counts: dict[str, int] = {}
    suspicious_inputs = []

    for path in iter_files():
        text = safe_text(path)
        tags = classify(path, text)

        record = {
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "tags": sorted(tags),
        }
        files.append(record)

        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        low = text.lower()

        # Candidate signals only. These require manual/runtime verification.
        if any(
            token in low
            for token in (
                "fallback",
                "default_data",
                "synthetic",
                "mock",
                "dummy",
                "fake",
                "placeholder",
            )
        ):
            suspicious_inputs.append(record["file"])

    result = {
        "project": "AwareOn",
        "audit": "data_foundation",
        "status": "DISCOVERY_ONLY",
        "source_file_count": len(files),
        "tag_counts": dict(sorted(tag_counts.items())),
        "suspicious_input_candidates": sorted(set(suspicious_inputs)),
        "files": sorted(files, key=lambda x: x["file"]),
        "limitations": [
            "Static discovery is candidate evidence only.",
            "No source is declared authoritative without runtime/code verification.",
            "No fabricated dataset or feature entry is created.",
            "Runtime validation must follow discovery.",
        ],
    }

    output_dir = ROOT / "artifacts" / "data_foundation_audit"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = output_dir / "data_foundation_discovery.json"
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report = output_dir / "DATA_FOUNDATION_REPORT.md"

    lines = [
        "# AwareOn Data Foundation Audit",
        "",
        f"Source files inspected: `{len(files)}`",
        "",
        "Status:",
        "`DISCOVERY_ONLY`",
        "",
        "## Classification counts",
        "",
    ]

    for key, value in sorted(tag_counts.items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Suspicious input candidates",
            "",
        ]
    )

    if suspicious_inputs:
        lines.extend(f"- `{item}`" for item in sorted(set(suspicious_inputs)))
    else:
        lines.append("- None detected by static keyword discovery.")

    lines.extend(
        [
            "",
            "## Important",
            "",
            "Static discovery is candidate evidence only.",
            "It does not prove that a dataset is authoritative, live,",
            "correctly transformed, or safe for production use.",
        ]
    )

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=" * 72)
    print("AWAREON DATA FOUNDATION DISCOVERY")
    print("=" * 72)
    print(f"Source files inspected : {len(files)}")
    print(f"Output                  : {output}")
    print(f"Report                  : {report}")
    print("=" * 72)


if __name__ == "__main__":
    audit()

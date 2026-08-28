from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

GSI_FILE = (
    ROOT
    / "data/processed/landslides/gsi_sikkim_inventory_clean.geojson"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "historical_event_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

gsi = gpd.read_file(GSI_FILE)

if gsi.empty:
    raise RuntimeError("GSI inventory is empty.")

gsi = gsi.to_crs("EPSG:32645")


# ------------------------------------------------------------
# Historical summary
# ------------------------------------------------------------

total_events = len(gsi)

district_counts = (
    gsi["district"]
    .value_counts()
    .to_dict()
)

movement_counts = (
    gsi["movement_type"]
    .value_counts()
    .to_dict()
)


# ------------------------------------------------------------
# Spatial grid for hotspot analysis
# ------------------------------------------------------------

# 1 km spatial bins.
gsi["grid_x"] = (
    np.floor(
        gsi.geometry.x / 1000.0
    ).astype(int)
)

gsi["grid_y"] = (
    np.floor(
        gsi.geometry.y / 1000.0
    ).astype(int)
)

gsi["hotspot_id"] = (
    gsi["grid_x"].astype(str)
    + "_"
    + gsi["grid_y"].astype(str)
)


hotspots = (
    gsi.groupby("hotspot_id")
    .agg(
        event_count=("landslide_id", "count"),
        latitude=("geometry", lambda x: x.y.mean()),
        longitude=("geometry", lambda x: x.x.mean()),
    )
    .reset_index()
)


# ------------------------------------------------------------
# Normalize hotspot intensity
# ------------------------------------------------------------

max_events = hotspots["event_count"].max()

if max_events > 0:
    hotspots["hotspot_score"] = (
        hotspots["event_count"]
        / max_events
        * 100.0
    )
else:
    hotspots["hotspot_score"] = 0.0


# ------------------------------------------------------------
# Hotspot category
# ------------------------------------------------------------

def classify(score):

    if score < 25:
        return "LOW"

    if score < 50:
        return "MODERATE"

    if score < 75:
        return "HIGH"

    return "VERY_HIGH"


hotspots["hotspot_category"] = (
    hotspots["hotspot_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Geographic event extent
# ------------------------------------------------------------

minx, miny, maxx, maxy = gsi.total_bounds


# ------------------------------------------------------------
# Save hotspot output
# ------------------------------------------------------------

hotspots.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Summary output
# ------------------------------------------------------------

SUMMARY_OUTPUT = (
    OUT_DIR
    / "historical_event_summary.csv"
)

summary_rows = [
    {
        "metric": "total_events",
        "value": total_events,
    },
    {
        "metric": "number_of_hotspots",
        "value": len(hotspots),
    },
    {
        "metric": "max_events_in_hotspot",
        "value": int(max_events),
    },
    {
        "metric": "mean_events_per_hotspot",
        "value": float(
            hotspots["event_count"].mean()
        ),
    },
]

summary = pd.DataFrame(summary_rows)

summary.to_csv(
    SUMMARY_OUTPUT,
    index=False,
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 06")
print("HISTORICAL EVENT INTELLIGENCE")
print("========================================")

print(
    "Total historical events:",
    total_events,
)

print(
    "Spatial hotspots:",
    len(hotspots),
)

print(
    "Max events in one 1 km hotspot:",
    int(max_events),
)

print(
    "\nDistrict distribution:"
)

print(
    pd.Series(
        district_counts
    ).to_string()
)

print(
    "\nMovement types:"
)

print(
    pd.Series(
        movement_counts
    ).head(15).to_string()
)

print(
    "\nGeographic extent (UTM metres):"
)

print(
    minx,
    miny,
    maxx,
    maxy,
)

print(
    "\nHotspot categories:"
)

print(
    hotspots["hotspot_category"]
    .value_counts()
    .to_string()
)

print(
    "\nHotspot output:"
)

print(OUTPUT)

print(
    "\nSummary output:"
)

print(SUMMARY_OUTPUT)

print(
    "\nENGINE 06 COMPLETE ✅"
)

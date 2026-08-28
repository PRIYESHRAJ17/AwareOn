from pathlib import Path

import pandas as pd
import geopandas as gpd


ROOT = Path(__file__).resolve().parents[1]

GSI_FILE = (
    ROOT
    / "data/processed/landslides/gsi_sikkim_inventory_clean.geojson"
)

ERA5_FILE = (
    ROOT
    / "data/processed/weather/era5_environment_timeseries.csv"
)

OUT_DIR = ROOT / "data/processed/ground_truth"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUT_DIR / "dated_landslide_events.csv"
OUTPUT_GEOJSON = OUT_DIR / "dated_landslide_events.geojson"


# ------------------------------------------------------------
# Load GSI inventory
# ------------------------------------------------------------

gsi = gpd.read_file(GSI_FILE)

gsi["event_date"] = pd.to_datetime(
    gsi["event_date"],
    errors="coerce",
)

dated = gsi[gsi["event_date"].notna()].copy()

if dated.empty:
    raise RuntimeError("No dated landslide events found.")


# ------------------------------------------------------------
# Keep one event record per source record
# ------------------------------------------------------------

dated = dated.drop_duplicates(
    subset=[
        "record_id",
        "landslide_id",
        "latitude",
        "longitude",
    ]
).reset_index(drop=True)


# ------------------------------------------------------------
# Load ERA5
# ------------------------------------------------------------

era5 = pd.read_csv(
    ERA5_FILE,
    parse_dates=["valid_time"],
)

era5 = era5.sort_values("valid_time")


# ------------------------------------------------------------
# Build event-level rainfall context
# ------------------------------------------------------------

event_rows = []

for _, event in dated.iterrows():

    event_date = event["event_date"]

    # Midnight anchor for daily event context.
    event_time = pd.Timestamp(event_date).normalize()

    # Find the nearest ERA5 timestamp.
    idx = (
        (era5["valid_time"] - event_time)
        .abs()
        .idxmin()
    )

    weather = era5.loc[idx]

    event_rows.append(
        {
            "record_id": event["record_id"],
            "landslide_id": event["landslide_id"],
            "district": event["district"],
            "location": event["location"],
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "event_date": event_date,
            "precip_mm": weather["precip_mm"],
            "rain_24h_mm": weather["rain_24h_mm"],
            "rain_72h_mm": weather["rain_72h_mm"],
            "rain_7d_mm": weather["rain_7d_mm"],
            "swvl1": weather["swvl1"],
            "swvl2": weather["swvl2"],
        }
    )


events = pd.DataFrame(event_rows)


# ------------------------------------------------------------
# Convert to GeoDataFrame
# ------------------------------------------------------------

geometry = gpd.points_from_xy(
    events["longitude"],
    events["latitude"],
)

event_gdf = gpd.GeoDataFrame(
    events,
    geometry=geometry,
    crs="EPSG:4326",
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

events.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8",
)

event_gdf.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("DATED LANDSLIDE EVENT DATASET")
print("========================================")

print("Total GSI records:", len(gsi))
print("Dated events:", len(events))

print(
    "Date range:",
    events["event_date"].min(),
    "to",
    events["event_date"].max(),
)

print("\nDistricts:")
print(
    events["district"]
    .value_counts()
    .to_string()
)

print("\nRainfall statistics:")
print(
    events[
        [
            "precip_mm",
            "rain_24h_mm",
            "rain_72h_mm",
            "rain_7d_mm",
        ]
    ]
    .describe()
    .to_string()
)

print("\nOutputs:")
print(OUTPUT_CSV)
print(OUTPUT_GEOJSON)

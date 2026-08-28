from pathlib import Path
import re
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data/processed/landslides/gsi_inventory_extracted.csv"
OUT_DIR = ROOT / "data/processed/landslides"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "gsi_sikkim_inventory.csv"
OUT_GEOJSON = OUT_DIR / "gsi_sikkim_inventory.geojson"


# Sikkim districts appearing in the GSI inventory
DISTRICT_PATTERN = r"(North Sikkim|South Sikkim|East Sikkim|West Sikkim)"

# Coordinates
COORD_PATTERN = r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)$"

# History can be a date or NA
DATE_PATTERN = (
    r"(\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{4})$"
)

rows = []

df = pd.read_csv(INPUT)

for _, record in df.iterrows():

    line = str(record["raw_line"]).strip()

    # Only Sikkim records
    if " Sikkim " not in f" {line} ":
        continue

    # Basic record structure
    m = re.match(
        rf"^(\d+)\s+(\S+)\s+Sikkim\s+{DISTRICT_PATTERN}\s+(.*?)\s+"
        rf"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(.+)$",
        line,
    )

    if not m:
        continue

    record_id = int(m.group(1))
    landslide_id = m.group(2)
    district = m.group(3)
    location = m.group(4).strip()
    latitude = float(m.group(5))
    longitude = float(m.group(6))
    trailing = m.group(7).strip()

    # Separate movement type from history/date
    history = None
    movement_type = trailing

    if trailing == "NA":
        history = "NA"

    else:
        date_match = re.search(DATE_PATTERN, trailing)

        if date_match:
            history = date_match.group(1)
            movement_type = trailing[:date_match.start()].strip()

    # Study area filter
    if not (26.8 <= latitude <= 28.3 and 87.9 <= longitude <= 89.1):
        continue

    rows.append(
        {
            "record_id": record_id,
            "landslide_id": landslide_id,
            "state": "Sikkim",
            "district": district,
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "movement_type": movement_type,
            "history": history,
        }
    )


result = pd.DataFrame(rows)

if result.empty:
    raise RuntimeError("No Sikkim records were successfully parsed.")

# Remove exact duplicate records
result = result.drop_duplicates(
    subset=["record_id", "latitude", "longitude"]
).reset_index(drop=True)

# Save CSV
result.to_csv(OUT_CSV, index=False, encoding="utf-8")

# Save GeoJSON
geometry = [
    Point(lon, lat)
    for lon, lat in zip(result["longitude"], result["latitude"])
]

gdf = gpd.GeoDataFrame(
    result,
    geometry=geometry,
    crs="EPSG:4326",
)

gdf.to_file(
    OUT_GEOJSON,
    driver="GeoJSON",
)

print("GSI Sikkim parsing complete.")
print("Records:", len(result))
print("CSV:", OUT_CSV)
print("GeoJSON:", OUT_GEOJSON)

print("\nDistricts:")
print(result["district"].value_counts())

print("\nMovement types:")
print(result["movement_type"].value_counts().head(20))

print("\nBounds:")
print(gdf.total_bounds)

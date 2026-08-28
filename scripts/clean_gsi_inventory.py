from pathlib import Path
import re

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[1]

INPUT_CSV = ROOT / "data/processed/landslides/gsi_sikkim_inventory.csv"
OUT_DIR = ROOT / "data/processed/landslides"

OUTPUT_CSV = OUT_DIR / "gsi_sikkim_inventory_clean.csv"
OUTPUT_GEOJSON = OUT_DIR / "gsi_sikkim_inventory_clean.geojson"


# ------------------------------------------------------------
# Patterns
# ------------------------------------------------------------

DATE_PATTERN = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+"
    r"(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")


# ------------------------------------------------------------
# Text helpers
# ------------------------------------------------------------

def clean_text(value):
    """Convert values to clean strings; treat NA/NaN as missing."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if not text:
        return None

    if text.upper() in {"NA", "N/A", "NAN", "NONE"}:
        return None

    return re.sub(r"\s+", " ", text)


def split_movement_and_history(value):
    """
    Split movement type from trailing event-history/date information.
    """

    text = clean_text(value)

    if text is None:
        return None, None

    # Remove terminal NA
    text = re.sub(
        r"\s+NA\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    if not text:
        return None, None

    # --------------------------------------------------------
    # Full date present
    # --------------------------------------------------------

    date_match = DATE_PATTERN.search(text)

    if date_match:
        movement = text[:date_match.start()].strip(" ,-")
        history = text[date_match.start():].strip()

        return movement or None, history or None

    # --------------------------------------------------------
    # Year present without a full date
    # --------------------------------------------------------

    years = list(YEAR_PATTERN.finditer(text))

    if years:
        match = years[-1]

        if match.start() > 0:
            movement = text[:match.start()].strip(" ,-")
            history = text[match.start():].strip()

            # Avoid splitting legitimate movement names containing years
            if movement:
                return movement, history

    return text, None


def normalize_movement_type(value):
    """Normalize obvious GSI movement-type variants."""

    text = clean_text(value)

    if text is None:
        return None

    t = text.lower()

    mappings = {
        "debris slide": "Debris Slide",
        "debris debris slide": "Debris Slide",
        "earth slide": "Earth Slide",
        "rock slide": "Rock Slide",
        "rock fall": "Rock Fall",
        "rock topple": "Rock Topple",
        "debris subsidence": "Debris Subsidence",
        "debris fall and slide": "Debris Fall and Slide",
        "debris flow": "Debris Flow",
        "rock": "Rock",
        "earth flow": "Earth Flow",
        "debris complex": "Debris Complex",
    }

    return mappings.get(t, text)


def extract_event_date(history):
    """Extract a real date from history; otherwise return NaT."""

    history = clean_text(history)

    if history is None:
        return pd.NaT

    match = DATE_PATTERN.search(history)

    if not match:
        return pd.NaT

    day = int(match.group(1))
    month = match.group(2)
    year = int(match.group(3))

    return pd.to_datetime(
        f"{day} {month} {year}",
        format="%d %B %Y",
        errors="coerce",
    )


# ------------------------------------------------------------
# Load source CSV
# ------------------------------------------------------------

if not INPUT_CSV.exists():
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_CSV}"
    )

df = pd.read_csv(INPUT_CSV)

required_columns = [
    "record_id",
    "landslide_id",
    "state",
    "district",
    "location",
    "latitude",
    "longitude",
    "movement_type",
    "history",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise RuntimeError(
        f"Missing required columns: {missing_columns}"
    )

input_count = len(df)


# ------------------------------------------------------------
# Basic cleaning
# ------------------------------------------------------------

df["location"] = df["location"].apply(clean_text)

df["history"] = df["history"].apply(clean_text)

df["movement_type"] = df["movement_type"].apply(clean_text)


# ------------------------------------------------------------
# Separate movement type and history
# ------------------------------------------------------------

split_result = df["movement_type"].apply(
    split_movement_and_history
)

df["movement_clean"] = [
    item[0] for item in split_result
]

history_from_movement = pd.Series(
    [item[1] for item in split_result],
    index=df.index,
)

# Prefer explicit history column when available.
df["history_clean"] = df["history"]

df["history_clean"] = df["history_clean"].where(
    df["history_clean"].notna(),
    history_from_movement,
)


# ------------------------------------------------------------
# Normalize movement types
# ------------------------------------------------------------

df["movement_clean"] = df["movement_clean"].apply(
    normalize_movement_type
)


# ------------------------------------------------------------
# Event dates
# ------------------------------------------------------------

df["event_date"] = df["history_clean"].apply(
    extract_event_date
)


# ------------------------------------------------------------
# Numeric coordinates
# ------------------------------------------------------------

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce",
)

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce",
)


# ------------------------------------------------------------
# Remove invalid coordinates
# ------------------------------------------------------------

before_coordinate_filter = len(df)

df = df[
    df["latitude"].between(-90, 90)
    & df["longitude"].between(-180, 180)
].copy()

invalid_coordinate_rows = (
    before_coordinate_filter - len(df)
)


# ------------------------------------------------------------
# AwareOn study-area filter
# ------------------------------------------------------------

before_study_filter = len(df)

df = df[
    df["latitude"].between(26.8, 28.3)
    & df["longitude"].between(87.9, 89.1)
].copy()

outside_study_area = (
    before_study_filter - len(df)
)


# ------------------------------------------------------------
# Remove duplicates
# ------------------------------------------------------------

before_duplicates = len(df)

df = df.drop_duplicates(
    subset=[
        "record_id",
        "landslide_id",
        "latitude",
        "longitude",
    ]
).copy()

duplicates_removed = (
    before_duplicates - len(df)
)


# ------------------------------------------------------------
# Final columns
# ------------------------------------------------------------

result = df[
    [
        "record_id",
        "landslide_id",
        "state",
        "district",
        "location",
        "latitude",
        "longitude",
        "movement_clean",
        "history_clean",
        "event_date",
    ]
].rename(
    columns={
        "movement_clean": "movement_type",
        "history_clean": "history",
    }
).reset_index(drop=True)


# ------------------------------------------------------------
# GeoDataFrame
# ------------------------------------------------------------

geometry = [
    Point(lon, lat)
    for lon, lat in zip(
        result["longitude"],
        result["latitude"],
    )
]

gdf = gpd.GeoDataFrame(
    result,
    geometry=geometry,
    crs="EPSG:4326",
)


# ------------------------------------------------------------
# Save outputs
# ------------------------------------------------------------

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

result.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8",
)

gdf.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON",
)


# ------------------------------------------------------------
# Validation report
# ------------------------------------------------------------

print("\n========================================")
print("GSI INVENTORY CLEANING COMPLETE")
print("========================================")

print(f"Input records:              {input_count}")
print(f"Invalid coordinates removed: {invalid_coordinate_rows}")
print(f"Outside study area removed:  {outside_study_area}")
print(f"Duplicates removed:          {duplicates_removed}")
print(f"Final records:               {len(result)}")

print("\nColumns:")
print(result.columns.tolist())

print("\nDistrict counts:")
print(
    result["district"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nMovement types:")
print(
    result["movement_type"]
    .value_counts(dropna=False)
    .to_string()
)

print(
    "\nEvent dates successfully parsed:",
    int(result["event_date"].notna().sum())
)

print("\nMissing values:")
print(
    result.isna()
    .sum()
    .to_string()
)

print("\nCoordinate bounds:")
print(gdf.total_bounds)

print("\nOutput CSV:")
print(OUTPUT_CSV)

print("\nOutput GeoJSON:")
print(OUTPUT_GEOJSON)

from pathlib import Path

import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]

WEATHER_DIR = ROOT / "data/raw/weather/ERA5_Land"
OUT_DIR = ROOT / "data/processed/weather"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRECIP_FILE = next(WEATHER_DIR.glob("*pressure-precipitation*.nc"))
SOIL_FILE = next(WEATHER_DIR.glob("*soil-water*.nc"))

# Load
precip = xr.open_dataset(PRECIP_FILE)
soil = xr.open_dataset(SOIL_FILE)

# Convert to dataframe
df_p = precip[["tp"]].to_dataframe().reset_index()
df_s = soil[["swvl1", "swvl2"]].to_dataframe().reset_index()

# Merge on time
df = df_p.merge(
    df_s,
    on="valid_time",
    how="inner",
)

# Sort
df = df.sort_values("valid_time").reset_index(drop=True)

# ERA5-Land total precipitation is in metres.
# Convert to millimetres.
df["precip_mm"] = df["tp"] * 1000.0

# Remove original tp column
df = df.drop(columns=["tp"])

# Basic missing-value handling
df["precip_mm"] = df["precip_mm"].clip(lower=0)

# Rolling rainfall features
df["rain_3h_mm"] = (
    df["precip_mm"]
    .rolling(3, min_periods=1)
    .sum()
)

df["rain_6h_mm"] = (
    df["precip_mm"]
    .rolling(6, min_periods=1)
    .sum()
)

df["rain_12h_mm"] = (
    df["precip_mm"]
    .rolling(12, min_periods=1)
    .sum()
)

df["rain_24h_mm"] = (
    df["precip_mm"]
    .rolling(24, min_periods=1)
    .sum()
)

df["rain_72h_mm"] = (
    df["precip_mm"]
    .rolling(72, min_periods=1)
    .sum()
)

df["rain_7d_mm"] = (
    df["precip_mm"]
    .rolling(24 * 7, min_periods=1)
    .sum()
)

# Rate/trend indicator
df["rain_change_24h_mm"] = (
    df["rain_24h_mm"]
    .diff(24)
)

# Metadata
df["latitude"] = float(precip.latitude.values)
df["longitude"] = float(precip.longitude.values)

# Final order
columns = [
    "valid_time",
    "latitude",
    "longitude",
    "precip_mm",
    "swvl1",
    "swvl2",
    "rain_3h_mm",
    "rain_6h_mm",
    "rain_12h_mm",
    "rain_24h_mm",
    "rain_72h_mm",
    "rain_7d_mm",
    "rain_change_24h_mm",
]

df = df[columns]

# Save
output = OUT_DIR / "era5_environment_timeseries.csv"
df.to_csv(output, index=False)

print("ERA5 processing complete")
print("Rows:", len(df))
print("Columns:", list(df.columns))
print("Location:", df["latitude"].iloc[0], df["longitude"].iloc[0])
print("Time:", df["valid_time"].min(), "to", df["valid_time"].max())
print("Missing values:")
print(df.isna().sum().to_string())
print("Output:", output)

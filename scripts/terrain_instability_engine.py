from pathlib import Path

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    ROOT
    / "data/processed/features/static_ml_features_validated.csv"
)

OUT_DIR = ROOT / "data/processed/engines"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = (
    OUT_DIR / "terrain_instability_engine_output.csv"
)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)

if df.empty:
    raise RuntimeError("Feature dataset is empty.")


# ------------------------------------------------------------
# Percentile scoring helper
# ------------------------------------------------------------

def percentile_score(series):
    """
    Convert a feature to a 0-100 percentile score.
    Larger values -> larger instability contribution.
    """

    return (
        series.rank(
            pct=True,
            method="average",
        )
        * 100.0
    )


# ------------------------------------------------------------
# Terrain component scores
# ------------------------------------------------------------

# Steeper slope -> greater potential instability.
df["slope_score"] = percentile_score(
    df["slope_deg"]
)

# Elevation is treated as a contextual terrain factor,
# not as intrinsically dangerous by itself.
df["elevation_score"] = percentile_score(
    df["elevation_m"]
)

# Larger local elevation variability -> more rugged terrain.
df["ruggedness_score"] = percentile_score(
    df["elevation_std_m"]
)


# ------------------------------------------------------------
# Aspect handling
# ------------------------------------------------------------
#
# Aspect itself is circular and should not be treated as
# numerically ordered. We use the existing sin/cos encoding
# only as contextual terms and do not assign them an arbitrary
# "danger" direction in this prototype.
# ------------------------------------------------------------

aspect_variability = (
    np.sqrt(
        df["aspect_sin"] ** 2
        + df["aspect_cos"] ** 2
    )
)

# Normally approximately 1.0 for valid aspect values.
aspect_quality_score = (
    np.clip(
        aspect_variability,
        0.0,
        1.0,
    )
    * 100.0
)


# ------------------------------------------------------------
# Terrain instability score
# ------------------------------------------------------------

df["terrain_instability_score"] = (
    0.55 * df["slope_score"]
    + 0.25 * df["ruggedness_score"]
    + 0.15 * df["elevation_score"]
    + 0.05 * aspect_quality_score
)


# ------------------------------------------------------------
# Category
# ------------------------------------------------------------

def classify(score):

    if score < 25:
        return "LOW"

    if score < 50:
        return "MODERATE"

    if score < 75:
        return "HIGH"

    return "EXTREME"


df["terrain_instability_category"] = (
    df["terrain_instability_score"]
    .apply(classify)
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_columns = [
    "cell_id",
    "label",
    "elevation_m",
    "slope_deg",
    "elevation_std_m",
    "slope_score",
    "ruggedness_score",
    "elevation_score",
    "terrain_instability_score",
    "terrain_instability_category",
]

df[output_columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8",
)


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("\n========================================")
print("AWAREON ENGINE 04")
print("TERRAIN INSTABILITY ENGINE")
print("========================================")

print(
    "Cells processed:",
    len(df),
)

print("\nScore statistics:")
print(
    df["terrain_instability_score"]
    .describe()
    .to_string()
)

print("\nCategories:")
print(
    df["terrain_instability_category"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

print("\nENGINE 04 COMPLETE ✅")

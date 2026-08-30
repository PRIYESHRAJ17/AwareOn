from __future__ import annotations

import pickle
from pathlib import Path
from time import perf_counter

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RISK_FILE = (
    ROOT
    / "data"
    / "processed"
    / "intelligence"
    / "awareon_risk_decisions.csv"
)

FULL_CACHE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cache"
    / "grid_spatial_cache.pkl"
)

COMPACT_CACHE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cache"
    / "risk_spatial_cache.pkl"
)


def build_cache() -> None:
    started = perf_counter()

    if not RISK_FILE.exists():
        raise FileNotFoundError(
            f"Risk file not found: {RISK_FILE}"
        )

    if not FULL_CACHE_FILE.exists():
        raise FileNotFoundError(
            f"Spatial cache not found: {FULL_CACHE_FILE}"
        )

    print("Loading risk decisions...")

    risk_df = pd.read_csv(
        RISK_FILE
    )

    if "cell_id" not in risk_df.columns:
        raise RuntimeError(
            "Risk file does not contain cell_id."
        )

    risk_ids = {
        str(cell_id)
        for cell_id in risk_df["cell_id"]
    }

    print(
        f"Risk cells: {len(risk_ids):,}"
    )

    print("Loading full spatial cache once...")

    with FULL_CACHE_FILE.open(
        "rb"
    ) as file:
        full_cache = pickle.load(
            file
        )

    records = full_cache.get(
        "records",
        []
    )

    compact_records = []

    for record in records:

        cell_id = str(
            record.get(
                "cell_id"
            )
        )

        if cell_id not in risk_ids:
            continue

        compact_records.append(
            {
                "cell_id":
                    cell_id,

                "x":
                    float(
                        record["x"]
                    ),

                "y":
                    float(
                        record["y"]
                    ),

                "geometry":
                    record["geometry"],
            }
        )

    if not compact_records:
        raise RuntimeError(
            "No risk cells were found in the spatial cache."
        )

    payload = {
        "version": 1,

        "source":
            str(RISK_FILE),

        "feature_count":
            len(compact_records),

        "records":
            compact_records,
    }

    COMPACT_CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Writing compact risk cache...")

    with COMPACT_CACHE_FILE.open(
        "wb"
    ) as file:
        pickle.dump(
            payload,
            file,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    elapsed = (
        perf_counter()
        -
        started
    )

    print(
        f"Compact cache created: "
        f"{COMPACT_CACHE_FILE}"
    )

    print(
        f"Compact records: "
        f"{len(compact_records):,}"
    )

    print(
        f"Build time: "
        f"{elapsed:.2f} sec"
    )


if __name__ == "__main__":
    build_cache()

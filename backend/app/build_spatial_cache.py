from __future__ import annotations

import json
import pickle
from pathlib import Path
from time import perf_counter

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]

GRID_FILE = (
    ROOT
    / "data"
    / "processed"
    / "grid"
    / "master_grid_100m.geojson"
)

CACHE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "cache"
)

CACHE_FILE = (
    CACHE_DIR
    / "grid_spatial_cache.pkl"
)


def build_cache() -> None:
    started = perf_counter()

    if not GRID_FILE.exists():
        raise FileNotFoundError(
            f"Grid file not found: {GRID_FILE}"
        )

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Loading master grid..."
    )

    with GRID_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    features = data.get(
        "features",
        [],
    )

    if not features:
        raise RuntimeError(
            "Master grid contains no features."
        )

    records = []

    total = len(features)

    for index, feature in enumerate(
        features,
        start=1,
    ):

        properties = feature.get(
            "properties",
            {},
        )

        geometry = feature.get(
            "geometry"
        )

        if not isinstance(
            properties,
            dict,
        ):
            continue

        if not geometry:
            continue

        cell_id = (
            properties.get(
                "cell_id"
            )
            or
            properties.get(
                "id"
            )
        )

        if cell_id is None:
            continue

        geom = shape(
            geometry
        )

        centroid = geom.centroid

        records.append(
            {
                "cell_id":
                    str(cell_id),

                "x":
                    float(centroid.x),

                "y":
                    float(centroid.y),

                "geometry":
                    geometry,
            }
        )

        if index % 100000 == 0:
            print(
                f"Processed {index:,}/{total:,}"
            )

    payload = {
        "version": 1,

        "source":
            str(GRID_FILE),

        "feature_count":
            len(records),

        "records":
            records,
    }

    print(
        "Writing cache..."
    )

    with CACHE_FILE.open(
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
        f"Cache created: {CACHE_FILE}"
    )

    print(
        f"Cached records: {len(records):,}"
    )

    print(
        f"Build time: {elapsed:.2f} sec"
    )


if __name__ == "__main__":
    build_cache()

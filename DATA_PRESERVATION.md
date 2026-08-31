# AwareOn Data Preservation — Levels 13–20

The application source package intentionally excludes multi-gigabyte local datasets and runtime artifacts. The production AwareOn tree should retain its existing `data/` directory from the user's working installation, including DEM/raster/GIS/weather/satellite assets.

Recommended local layout while upgrading:

- `AwareOn_backup/` — untouched previous working tree.
- `AwareOn/` — upgraded source tree.
- Copy `AwareOn_backup/data/` into `AwareOn/data/` if the new tree does not already contain the local datasets.
- Copy/reuse the existing `.venv/` only when required by the local environment.

Do not delete `AwareOn_backup/` until Level 20 E2E QA passes locally.

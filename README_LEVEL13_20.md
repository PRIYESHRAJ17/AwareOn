# AwareOn — Levels 13–20 Delivery

This source delivery contains the Level 13–20 application refinements built on the previously verified Levels 1–12 AI foundation.

## Primary product standard

The UI is map-first and intentionally avoids dashboard overload. The interaction language follows the current Atlas product direction—conversation and search lead into a live map workspace, context is revealed progressively, and spatial workflows remain visible and inspectable—while AwareOn retains its own risk/evidence/decision semantics.

## Local installation

1. Keep the existing full-data AwareOn directory as `AwareOn_backup`.
2. Place this package as the new `AwareOn` directory.
3. Run `INSTALL_FROM_BACKUP.ps1` on Windows or `INSTALL_FROM_BACKUP.sh` in Git Bash/WSL if the data/.venv need to be restored.
4. Start the backend and frontend using the existing AwareOn commands.
5. Run `python scripts/level20_e2e.py`.
6. Complete the browser checklist in `LEVEL20_E2E_QA.md`.

## Scope

Levels 13–20 are included. Levels 21–22 are intentionally not included.

Large local datasets are not distributed in this source-only package. Their expected paths remain unchanged under `data/`.

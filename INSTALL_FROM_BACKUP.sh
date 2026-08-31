#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="$(dirname "$ROOT")/AwareOn_backup"
echo "AwareOn Levels 13–20 installer"
if [[ ! -d "$ROOT/.venv" && -d "$BACKUP/.venv" ]]; then
  cp -a "$BACKUP/.venv" "$ROOT/.venv"
fi
if [[ -d "$BACKUP/data" ]]; then
  mkdir -p "$ROOT/data"
  cp -a "$BACKUP/data/." "$ROOT/data/"
fi
echo "Install complete. Keep AwareOn_backup until Level 20 E2E QA passes."

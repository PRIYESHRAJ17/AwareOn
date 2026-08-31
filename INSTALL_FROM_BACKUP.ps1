$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backup = Join-Path (Split-Path $root -Parent) "AwareOn_backup"

Write-Host "AwareOn Levels 13–20 installer" -ForegroundColor Cyan
Write-Host "New source: $root"

if (Test-Path (Join-Path $root ".venv")) {
  Write-Host ".venv already present — preserving it." -ForegroundColor Green
} elseif (Test-Path (Join-Path $backup ".venv")) {
  Write-Host "Copying existing .venv from AwareOn_backup..." -ForegroundColor Yellow
  Copy-Item (Join-Path $backup ".venv") (Join-Path $root ".venv") -Recurse -Force
}

if (Test-Path (Join-Path $backup "data")) {
  Write-Host "Restoring local data assets from AwareOn_backup..." -ForegroundColor Yellow
  New-Item -ItemType Directory -Force -Path (Join-Path $root "data") | Out-Null
  robocopy (Join-Path $backup "data") (Join-Path $root "data") /E /R:1 /W:1 /NFL /NDL /NJH /NJS | Out-Null
  Write-Host "Data restoration complete." -ForegroundColor Green
} else {
  Write-Warning "AwareOn_backup\data was not found. Keep your original data tree available before starting the backend."
}

Write-Host "Install complete. Do not delete AwareOn_backup until Level 20 E2E QA passes." -ForegroundColor Green

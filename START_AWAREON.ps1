$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "Missing .venv. Reuse/create the project virtual environment first." -ForegroundColor Yellow
  exit 1
}
& ".venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload

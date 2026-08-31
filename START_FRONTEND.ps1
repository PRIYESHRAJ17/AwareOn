$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m http.server 5500 --directory frontend

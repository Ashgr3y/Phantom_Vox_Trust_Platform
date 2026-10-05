$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDir

if (-not (Test-Path ".venv")) {
  py -3.12 -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install -r backend\requirements-base.txt
if (-not (Test-Path "frontend\node_modules")) {
  npm --prefix frontend install
}
npm --prefix frontend run build
Set-Location backend
& ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

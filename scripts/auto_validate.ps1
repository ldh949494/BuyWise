$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = if (Test-Path -LiteralPath ".\.venv\Scripts\python.exe") {
    ".\.venv\Scripts\python.exe"
} else {
    "python"
}

Write-Host "========== Backend Validation =========="

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt pytest

@'
from app.api.v1.endpoints.health import health_check
from app.main import app

registered_paths = {route.path for route in app.routes}
if "/api/v1/health" not in registered_paths:
    raise SystemExit("Health route is not registered on the FastAPI app.")

payload = health_check()
if payload.status != "ok" or payload.service != "shopagent-backend":
    raise SystemExit(f"Unexpected health payload: {payload.model_dump()}")

print("Backend smoke check passed.")
'@ | & $python -

if (Test-Path -LiteralPath "tests") {
    pytest -q
} else {
    Write-Host "No project tests directory found, smoke check only."
}

Write-Host "========== Android Build Validation =========="

if (-not (Test-Path -LiteralPath "android-app")) {
    throw "android-app directory is missing."
}

Push-Location "android-app"
try {
    .\gradlew.bat :app:assembleDebug
} finally {
    Pop-Location
}

Write-Host "All checks passed."

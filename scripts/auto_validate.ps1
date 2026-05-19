param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipAndroidBuild
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Agent map: AGENTS.md"

$pytestBaseTemp = Join-Path $repoRoot ".pytest_tmp\auto-validate"
New-Item -ItemType Directory -Force -Path $pytestBaseTemp | Out-Null

$python = if (Test-Path -LiteralPath ".\.venv\Scripts\python.exe") {
    ".\.venv\Scripts\python.exe"
} else {
    "python"
}

Write-Host "========== Backend Validation =========="

if (-not $SkipDependencyInstall) {
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements-dev.txt
} else {
    Write-Host "Dependency installation skipped."
}

Write-Host "========== Documentation Validation =========="
& $python scripts/validate_docs.py

Write-Host "========== Provider Validation =========="
& $python scripts/validate_providers.py

Write-Host "========== Custom Repository Lint =========="
& $python scripts/validate_repo_lint.py

Write-Host "========== Entropy Validation =========="
& $python scripts/validate_entropy.py

@'
from app.api.v1.health import health_check
from app.main import app

registered_paths = {route.path for route in app.routes}
if "/api/v1/health" not in registered_paths:
    raise SystemExit("Health route is not registered on the FastAPI app.")

payload = health_check()
if payload.status != "ok" or payload.service != "buywise-backend":
    raise SystemExit(f"Unexpected health payload: {payload.model_dump()}")

print("Backend smoke check passed.")
'@ | & $python -

$testFiles = @()
if (Test-Path -LiteralPath "tests") {
    $testFiles = Get-ChildItem -Path "tests" -Recurse -File -Include "test_*.py", "*_test.py" -ErrorAction SilentlyContinue
}

if ($testFiles.Count -gt 0) {
    $previousLlmProvider = [System.Environment]::GetEnvironmentVariable("LLM_PROVIDER", "Process")
    $previousTmp = [System.Environment]::GetEnvironmentVariable("TMP", "Process")
    $previousTemp = [System.Environment]::GetEnvironmentVariable("TEMP", "Process")
    try {
        $env:LLM_PROVIDER = "mock"
        $env:TMP = $pytestBaseTemp
        $env:TEMP = $pytestBaseTemp
        & $python -m pytest -q -p no:cacheprovider --basetemp $pytestBaseTemp
    } finally {
        if ($null -eq $previousLlmProvider) {
            [System.Environment]::SetEnvironmentVariable("LLM_PROVIDER", $null, "Process")
        } else {
            $env:LLM_PROVIDER = $previousLlmProvider
        }
        if ($null -eq $previousTmp) {
            [System.Environment]::SetEnvironmentVariable("TMP", $null, "Process")
        } else {
            $env:TMP = $previousTmp
        }
        if ($null -eq $previousTemp) {
            [System.Environment]::SetEnvironmentVariable("TEMP", $null, "Process")
        } else {
            $env:TEMP = $previousTemp
        }
    }
} else {
    Write-Host "No project tests directory found, smoke check only."
}

Write-Host "========== Android Build Validation =========="

if ($SkipAndroidBuild) {
    Write-Host "Android build skipped."
    Write-Host "All checks passed."
    exit 0
}

if (-not (Test-Path -LiteralPath "android-app")) {
    throw "android-app directory is missing."
}

Push-Location "android-app"
try {
    $isWindowsPlatform = [System.Environment]::OSVersion.Platform -eq "Win32NT"
    if ($isWindowsPlatform) {
        .\gradlew.bat :app:assembleDebug
    } else {
        chmod +x ./gradlew
        ./gradlew :app:assembleDebug
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Android Gradle build failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

Write-Host "All checks passed."

param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipAndroidBuild,
    [switch]$SkipAdminWebBuild
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Assert-LastExitCode {
    param([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE."
    }
}

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
    Assert-LastExitCode "pip upgrade"
    & $python -m pip install -r requirements-dev.txt
    Assert-LastExitCode "dependency installation"
} else {
    Write-Host "Dependency installation skipped."
}

Write-Host "========== Documentation Validation =========="
& $python scripts/validate_docs.py
Assert-LastExitCode "documentation validation"

Write-Host "========== Provider Validation =========="
& $python scripts/validate_providers.py
Assert-LastExitCode "provider validation"

Write-Host "========== Custom Repository Lint =========="
& $python scripts/validate_repo_lint.py
Assert-LastExitCode "custom repository lint"

Write-Host "========== Secret Validation =========="
& $python scripts/validate_secrets.py
Assert-LastExitCode "secret validation"

Write-Host "========== Entropy Validation =========="
& $python scripts/validate_entropy.py
Assert-LastExitCode "entropy validation"

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
Assert-LastExitCode "backend smoke check"

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
        Assert-LastExitCode "pytest"
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

Write-Host "========== Admin Web Build Validation =========="

if ($SkipAdminWebBuild) {
    Write-Host "Admin web build skipped."
} elseif (Test-Path -LiteralPath "admin-web/package.json") {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm is required to build admin-web. Install Node.js/npm or pass -SkipAdminWebBuild for backend-only validation."
    }

    Push-Location "admin-web"
    try {
        if (-not $SkipDependencyInstall) {
            if (Test-Path -LiteralPath "package-lock.json") {
                npm ci
            } else {
                npm install
            }
            Assert-LastExitCode "admin-web dependency installation"
        } elseif (-not (Test-Path -LiteralPath "node_modules")) {
            throw "admin-web dependencies are missing. Run npm ci in admin-web, rerun without -SkipDependencyInstall, or pass -SkipAdminWebBuild."
        }

        npm run build
        Assert-LastExitCode "admin-web build"
    } finally {
        Pop-Location
    }
} else {
    Write-Host "admin-web package.json not found, build skipped."
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

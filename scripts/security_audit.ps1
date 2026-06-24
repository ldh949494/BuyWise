param(
    [switch]$SkipPython,
    [switch]$SkipAdminWeb
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

$python = if (Test-Path -LiteralPath ".\.venv\Scripts\python.exe") {
    ".\.venv\Scripts\python.exe"
} else {
    "python"
}

if (-not $SkipPython) {
    Write-Host "========== Chroma Boundary Validation =========="
    & $python scripts/validate_chroma_boundary.py
    Assert-LastExitCode "Chroma boundary validation"

    Write-Host "========== Python Dependency Audit =========="
    Write-Host "Ignoring CVE-2026-45829 only after verifying BuyWise does not expose the vulnerable Chroma HTTP API."
    & $python -m pip_audit `
        -r requirements.txt `
        -r requirements-dev.txt `
        --disable-pip `
        --no-deps `
        --ignore-vuln CVE-2026-45829
    Assert-LastExitCode "Python dependency audit"
}

if (-not $SkipAdminWeb -and (Test-Path -LiteralPath "admin-web/package.json")) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm is required to audit admin-web dependencies."
    }

    Write-Host "========== Admin Web Dependency Audit =========="
    Push-Location "admin-web"
    try {
        npm audit
        Assert-LastExitCode "admin-web dependency audit"
    } finally {
        Pop-Location
    }
}

Write-Host "Security audit passed."

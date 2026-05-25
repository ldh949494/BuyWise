param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$ReadinessToken,
    [switch]$IncludeAi
)

$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m app.scripts.readiness_check

$smokeArgs = @(
    "scripts\closed_beta_smoke.py",
    "--base-url",
    $BaseUrl,
    "--token",
    $Token,
    "--readiness-token",
    $ReadinessToken
)

if ($IncludeAi) {
    $smokeArgs += "--include-ai"
}

& $python @smokeArgs

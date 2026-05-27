param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$ReadinessToken,
    [int]$ExpectedActiveProducts = 0,
    [switch]$IncludeAi
)

$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m app.scripts.print_runtime_config_summary

$readinessArgs = @("-m", "app.scripts.readiness_check")
if ($ExpectedActiveProducts -gt 0) {
    $readinessArgs += @("--expected-active-products", $ExpectedActiveProducts.ToString())
}
& $python @readinessArgs

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

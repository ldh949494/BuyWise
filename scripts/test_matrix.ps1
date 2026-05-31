param(
    [ValidateSet("unit", "integration", "release")]
    [string]$Tier = "unit",
    [switch]$SkipDependencyInstall,
    [switch]$SkipAndroidBuild,
    [switch]$SkipAndroidAnalyze,
    [switch]$CheckIndex,
    [switch]$CheckOpenApiContract,
    [switch]$RunRagEval,
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$Token = "",
    [string]$ReadinessToken = "",
    [int]$ExpectedActiveProducts = 0,
    [switch]$IncludeAiSmoke
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = if (Test-Path -LiteralPath ".\.venv\Scripts\python.exe") {
    ".\.venv\Scripts\python.exe"
} else {
    "python"
}

function Assert-LastExitCode {
    param([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE."
    }
}

function Invoke-PytestTier {
    param([string]$MarkerExpression, [string]$BaseTemp)
    New-Item -ItemType Directory -Force -Path $BaseTemp | Out-Null
    & $python -m pytest -q -m $MarkerExpression -p no:cacheprovider --basetemp $BaseTemp
    Assert-LastExitCode "pytest $MarkerExpression"
}

if ($Tier -eq "unit") {
    Invoke-PytestTier "not integration and not release" ".pytest_tmp\unit"
    return
}

if ($Tier -eq "integration") {
    Invoke-PytestTier "integration and not release" ".pytest_tmp\integration"
    return
}

$releaseArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\release_check.ps1")
if ($SkipDependencyInstall) {
    $releaseArgs += "-SkipDependencyInstall"
}
if ($SkipAndroidBuild) {
    $releaseArgs += "-SkipAndroidBuild"
}
if ($SkipAndroidAnalyze) {
    $releaseArgs += "-SkipAndroidAnalyze"
}
if ($CheckIndex) {
    $releaseArgs += "-CheckIndex"
}
if ($CheckOpenApiContract) {
    $releaseArgs += "-CheckOpenApiContract"
}
if ($RunRagEval) {
    $releaseArgs += "-RunRagEval"
}
if ($Token -or $ReadinessToken) {
    $releaseArgs += @("-BaseUrl", $BaseUrl, "-Token", $Token, "-ReadinessToken", $ReadinessToken)
}
if ($ExpectedActiveProducts -gt 0) {
    $releaseArgs += @("-ExpectedActiveProducts", $ExpectedActiveProducts.ToString())
}
if ($IncludeAiSmoke) {
    $releaseArgs += "-IncludeAiSmoke"
}

& powershell.exe @releaseArgs
Assert-LastExitCode "release test tier"

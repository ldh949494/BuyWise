param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipAndroidBuild,
    [switch]$SkipAndroidAnalyze,
    [switch]$CheckIndex,
    [switch]$CheckOpenApiContract,
    [ValidateSet("", "android-contract", "demo")]
    [string]$IndexProfile = "",
    [switch]$RunRagEval,
    [ValidateSet("android-contract", "demo", "beta-fixture")]
    [string]$RagEvalProfile = "android-contract",
    [ValidateSet("fallback", "vector")]
    [string]$RagEvalRetrieval = "fallback",
    [int]$RagEvalTopK = 5,
    [double]$MinRagRecall = 0.70,
    [double]$MinRagTop1 = 0.90,
    [double]$MinRagMrr = 0.70,
    [double]$MaxRagFallbackRate = 0.20,
    [double]$MaxRagEmptyResultRate = 0.0,
    [string]$RagEvalOutputJson = "",
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

Write-Host "========== BuyWise Release Check =========="

$autoValidateArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\auto_validate.ps1")
if ($SkipDependencyInstall) {
    $autoValidateArgs += "-SkipDependencyInstall"
}
if ($SkipAndroidBuild) {
    $autoValidateArgs += "-SkipAndroidBuild"
}
& powershell.exe @autoValidateArgs
Assert-LastExitCode "auto validation"

if (-not $SkipAndroidAnalyze) {
    Write-Host "========== Android Analyze =========="
    Push-Location "android-app"
    try {
        $isWindowsPlatform = [System.Environment]::OSVersion.Platform -eq "Win32NT"
        if ($isWindowsPlatform) {
            .\gradlew.bat :app:lintDebug
        } else {
            chmod +x ./gradlew
            ./gradlew :app:lintDebug
        }
        Assert-LastExitCode "Android lint"
    } finally {
        Pop-Location
    }
}

if ($CheckIndex) {
    Write-Host "========== Vector Index Health =========="
    $indexArgs = @("-m", "app.scripts.check_vector_index")
    if ($IndexProfile) {
        $indexArgs += @("--profile", $IndexProfile)
    }
    & $python @indexArgs
    Assert-LastExitCode "vector index health"
}

if ($CheckOpenApiContract) {
    Write-Host "========== OpenAPI Contract =========="
    & $python -m app.scripts.openapi_contract
    Assert-LastExitCode "OpenAPI contract"
}

if ($RunRagEval) {
    Write-Host "========== RAG Evaluation Gate =========="
    $ragEvalArgs = @(
        "-m",
        "app.scripts.rag_eval_gate",
        "--profile",
        $RagEvalProfile,
        "--retrieval",
        $RagEvalRetrieval,
        "--top-k",
        $RagEvalTopK.ToString(),
        "--min-recall",
        $MinRagRecall.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        "--min-top1",
        $MinRagTop1.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        "--min-mrr",
        $MinRagMrr.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        "--max-fallback-rate",
        $MaxRagFallbackRate.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        "--max-empty-result-rate",
        $MaxRagEmptyResultRate.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    )
    if ($RagEvalOutputJson) {
        $ragEvalArgs += @("--output-json", $RagEvalOutputJson)
    }
    & $python @ragEvalArgs
    Assert-LastExitCode "RAG evaluation gate"
}

if ($Token -or $ReadinessToken) {
    if (-not $Token -or -not $ReadinessToken) {
        throw "-Token and -ReadinessToken must be provided together for closed beta smoke."
    }
    Write-Host "========== Closed Beta Smoke =========="
    $smokeArgs = @(
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ".\scripts\closed_beta_verify.ps1",
        "-BaseUrl",
        $BaseUrl,
        "-Token",
        $Token,
        "-ReadinessToken",
        $ReadinessToken
    )
    if ($ExpectedActiveProducts -gt 0) {
        $smokeArgs += @("-ExpectedActiveProducts", $ExpectedActiveProducts.ToString())
    }
    if ($IncludeAiSmoke) {
        $smokeArgs += "-IncludeAi"
    }
    & powershell.exe @smokeArgs
    Assert-LastExitCode "closed beta smoke"
} else {
    Write-Host "Closed beta smoke skipped because -Token and -ReadinessToken were not provided."
}

Write-Host "Release checks passed."

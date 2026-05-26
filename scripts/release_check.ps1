param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipAndroidBuild,
    [switch]$SkipAndroidAnalyze,
    [switch]$CheckIndex,
    [ValidateSet("", "android-contract", "demo")]
    [string]$IndexProfile = "",
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$Token = "",
    [string]$ReadinessToken = "",
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
    if ($IncludeAiSmoke) {
        $smokeArgs += "-IncludeAi"
    }
    & powershell.exe @smokeArgs
    Assert-LastExitCode "closed beta smoke"
} else {
    Write-Host "Closed beta smoke skipped because -Token and -ReadinessToken were not provided."
}

Write-Host "Release checks passed."

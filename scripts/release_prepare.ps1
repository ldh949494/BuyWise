param(
    [ValidateSet("", "android-contract", "demo")]
    [string]$SeedProfile = "",
    [string]$ImportCsv = "",
    [switch]$RequireRealCatalog,
    [switch]$BuildIndex,
    [ValidateSet("upsert", "rebuild")]
    [string]$IndexMode = "upsert",
    [switch]$CheckIndex
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

function Read-ReleaseEnv {
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }
    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
    return $values
}

function Get-ReleaseEnvValue {
    param(
        [hashtable]$Values,
        [string]$Name
    )
    if ($Values.ContainsKey($Name)) {
        return $Values[$Name]
    }
    return [Environment]::GetEnvironmentVariable($Name)
}

if ($SeedProfile -and $ImportCsv) {
    throw "Use either -SeedProfile or -ImportCsv, not both, to avoid mixing deterministic seed data with imported catalog data."
}

if ($RequireRealCatalog -and -not $ImportCsv) {
    throw "-RequireRealCatalog requires -ImportCsv."
}

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$envValues = Read-ReleaseEnv ".env"
$mysqlHost = Get-ReleaseEnvValue $envValues "MYSQL_HOST"
if ($mysqlHost -eq "mysql") {
    $env:MYSQL_HOST = "127.0.0.1"
    Write-Host "MYSQL_HOST=mysql detected in .env; using 127.0.0.1 for host-side release preparation."
}

Write-Host "========== BuyWise Release Prepare =========="
$seedLabel = "disabled"
if ($SeedProfile) {
    $seedLabel = $SeedProfile
}
$importLabel = "disabled"
if ($ImportCsv) {
    $importLabel = $ImportCsv
    if ($RequireRealCatalog) {
        $importLabel = "$ImportCsv (real catalog validation)"
    }
}
$indexLabel = "disabled"
if ($BuildIndex) {
    $indexLabel = $IndexMode
}
$checkLabel = "disabled"
if ($CheckIndex) {
    $checkLabel = "enabled"
}
Write-Host "Migration: enabled"
Write-Host "Seed profile: $seedLabel"
Write-Host "Import CSV: $importLabel"
Write-Host "Build index: $indexLabel"
Write-Host "Check index: $checkLabel"

Write-Host "========== Database Migration =========="
& $python -m app.scripts.migrate_database

if ($SeedProfile) {
    Write-Host "========== Seed Products =========="
    & $python -m app.scripts.seed_products --profile $SeedProfile
}

if ($ImportCsv) {
    if (-not (Test-Path $ImportCsv)) {
        throw "Import CSV not found: $ImportCsv"
    }
    Write-Host "========== Import Products =========="
    $importArgs = @("-m", "app.scripts.import_products", "--csv", $ImportCsv)
    if ($RequireRealCatalog) {
        $importArgs += "--require-real-assets"
    }
    & $python @importArgs
}

if ($BuildIndex) {
    Write-Host "========== Build Vector Index =========="
    & $python -m app.scripts.build_vector_index --mode $IndexMode
}

if ($CheckIndex) {
    Write-Host "========== Check Vector Index =========="
    $checkArgs = @("-m", "app.scripts.check_vector_index")
    if ($SeedProfile) {
        $checkArgs += @("--profile", $SeedProfile)
    }
    & $python @checkArgs
}

Write-Host "========== Release Prepare Complete =========="

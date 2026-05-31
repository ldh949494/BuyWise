param(
    [ValidateSet("", "android-contract", "demo")]
    [string]$SeedProfile = "",
    [string]$ImportCsv = "",
    [switch]$RequireRealCatalog,
    [switch]$BuildIndex,
    [ValidateSet("upsert", "rebuild")]
    [string]$IndexMode = "upsert",
    [switch]$CheckIndex,
    [string]$ArtifactDir = "",
    [string]$ArtifactJson = ""
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

function Assert-LastExitCode {
    param([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE."
    }
}

$script:ReleasePrepareStartedAt = [DateTimeOffset]::UtcNow
$script:ReleasePrepareSteps = @()
$script:ReleasePrepareArtifactPath = ""
$script:ReleasePrepareArtifactDir = ""

function Initialize-ReleasePrepareArtifact {
    if (-not $ArtifactDir -and -not $ArtifactJson) {
        return
    }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    if ($ArtifactJson) {
        $script:ReleasePrepareArtifactPath = $ArtifactJson
        $parent = Split-Path -Parent $ArtifactJson
        if ($parent) {
            $script:ReleasePrepareArtifactDir = $parent
        } else {
            $script:ReleasePrepareArtifactDir = "."
        }
    } else {
        $script:ReleasePrepareArtifactDir = $ArtifactDir
        $script:ReleasePrepareArtifactPath = Join-Path $ArtifactDir "release-prepare-$stamp.json"
    }
    New-Item -ItemType Directory -Force -Path $script:ReleasePrepareArtifactDir | Out-Null
}

function New-ChildArtifactPath {
    param([string]$Name)
    if (-not $script:ReleasePrepareArtifactPath) {
        return ""
    }
    return Join-Path $script:ReleasePrepareArtifactDir "$Name.json"
}

function Write-ReleasePrepareArtifact {
    param(
        [string]$Status,
        [object]$ErrorInfo = $null
    )
    if (-not $script:ReleasePrepareArtifactPath) {
        return
    }
    $payload = [ordered]@{
        job_name = "release_prepare"
        status = $Status
        started_at = $script:ReleasePrepareStartedAt.ToString("o")
        finished_at = ([DateTimeOffset]::UtcNow).ToString("o")
        inputs = [ordered]@{
            seed_profile = $SeedProfile
            import_csv = $ImportCsv
            require_real_catalog = [bool]$RequireRealCatalog
            build_index = [bool]$BuildIndex
            index_mode = $IndexMode
            check_index = [bool]$CheckIndex
        }
        steps = $script:ReleasePrepareSteps
        error = $ErrorInfo
        environment = [ordered]@{
            cwd = (Get-Location).Path
            operator = [Environment]::UserName
            app_env = [Environment]::GetEnvironmentVariable("APP_ENV")
        }
    }
    $payload | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 -Path $script:ReleasePrepareArtifactPath
}

function Invoke-ReleasePrepareStep {
    param(
        [string]$Name,
        [hashtable]$Inputs,
        [scriptblock]$Action,
        [string]$ChildArtifact = ""
    )
    $started = [DateTimeOffset]::UtcNow
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $step = [ordered]@{
        name = $Name
        status = "running"
        started_at = $started.ToString("o")
        finished_at = $null
        duration_ms = 0
        inputs = $Inputs
        child_artifact = $ChildArtifact
        error = $null
    }
    try {
        & $Action
        $step.status = "succeeded"
    } catch {
        $step.status = "failed"
        $step.error = [ordered]@{
            type = $_.Exception.GetType().Name
            message = $_.Exception.Message
        }
        throw
    } finally {
        $timer.Stop()
        $step.finished_at = ([DateTimeOffset]::UtcNow).ToString("o")
        $step.duration_ms = [int]$timer.ElapsedMilliseconds
        $script:ReleasePrepareSteps += $step
        if ($step.status -eq "failed") {
            Write-ReleasePrepareArtifact -Status "failed" -ErrorInfo $step.error
        }
    }
}

if ($SeedProfile -and $ImportCsv) {
    throw "Use either -SeedProfile or -ImportCsv, not both, to avoid mixing deterministic seed data with imported catalog data."
}

if ($RequireRealCatalog -and -not $ImportCsv) {
    throw "-RequireRealCatalog requires -ImportCsv."
}

if ($RequireRealCatalog -and (-not $BuildIndex -or $IndexMode -ne "rebuild" -or -not $CheckIndex)) {
    throw "-RequireRealCatalog requires -BuildIndex -IndexMode rebuild -CheckIndex."
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
Initialize-ReleasePrepareArtifact
Write-Host "Migration: enabled"
Write-Host "Seed profile: $seedLabel"
Write-Host "Import CSV: $importLabel"
Write-Host "Build index: $indexLabel"
Write-Host "Check index: $checkLabel"

try {
    Write-Host "========== Database Migration =========="
    Invoke-ReleasePrepareStep -Name "database_migration" -Inputs @{ enabled = $true } -Action {
        & $python -m app.scripts.migrate_database
        Assert-LastExitCode "database migration"
    }

    if ($SeedProfile) {
        Write-Host "========== Seed Products =========="
        Invoke-ReleasePrepareStep -Name "seed_products" -Inputs @{ profile = $SeedProfile } -Action {
            & $python -m app.scripts.seed_products --profile $SeedProfile
            Assert-LastExitCode "seed products"
        }
    }

    if ($ImportCsv) {
        if (-not (Test-Path $ImportCsv)) {
            throw "Import CSV not found: $ImportCsv"
        }
        Write-Host "========== Import Products =========="
        $importArgs = @("-m", "app.scripts.import_products", "--csv", $ImportCsv)
        $importArtifact = New-ChildArtifactPath "import-products"
        if ($RequireRealCatalog) {
            $importArgs += "--require-real-assets"
        }
        if ($importArtifact) {
            $importArgs += @("--artifact-json", $importArtifact)
        }
        Invoke-ReleasePrepareStep -Name "import_products" -Inputs @{ csv = $ImportCsv; require_real_catalog = [bool]$RequireRealCatalog } -ChildArtifact $importArtifact -Action {
            & $python @importArgs
            Assert-LastExitCode "import products"
        }
    }

    if ($BuildIndex) {
        Write-Host "========== Build Vector Index =========="
        $buildArgs = @("-m", "app.scripts.build_vector_index", "--mode", $IndexMode)
        $buildArtifact = New-ChildArtifactPath "build-vector-index"
        if ($buildArtifact) {
            $buildArgs += @("--artifact-json", $buildArtifact)
        }
        Invoke-ReleasePrepareStep -Name "build_vector_index" -Inputs @{ mode = $IndexMode } -ChildArtifact $buildArtifact -Action {
            & $python @buildArgs
            Assert-LastExitCode "build vector index"
        }
    }

    if ($CheckIndex) {
        Write-Host "========== Check Vector Index =========="
        $checkArgs = @("-m", "app.scripts.check_vector_index")
        if ($SeedProfile) {
            $checkArgs += @("--profile", $SeedProfile)
        }
        Invoke-ReleasePrepareStep -Name "check_vector_index" -Inputs @{ profile = $SeedProfile } -Action {
            & $python @checkArgs
            Assert-LastExitCode "check vector index"
        }
    }

    Write-ReleasePrepareArtifact -Status "succeeded"
    Write-Host "========== Release Prepare Complete =========="
    if ($script:ReleasePrepareArtifactPath) {
        Write-Host "Release prepare artifact: $script:ReleasePrepareArtifactPath"
    }
} catch {
    $errorInfo = [ordered]@{
        type = $_.Exception.GetType().Name
        message = $_.Exception.Message
    }
    Write-ReleasePrepareArtifact -Status "failed" -ErrorInfo $errorInfo
    throw
}

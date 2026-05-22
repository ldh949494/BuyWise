param(
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$SkipMigration
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

function Read-BackendEnv {
    param([string]$Path)

    $values = @{}
    foreach ($line in Get-Content -Encoding utf8 -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $values
}

function Get-BackendEnvValue {
    param(
        [hashtable]$Values,
        [string]$Name
    )

    if ($Values.ContainsKey($Name)) {
        return $Values[$Name]
    }
    return ""
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = if (Test-Path -LiteralPath ".\.venv\Scripts\python.exe") {
    ".\.venv\Scripts\python.exe"
} else {
    "python"
}

if (-not (Test-Path -LiteralPath ".env")) {
    throw ".env is missing. Copy .env.example to .env before starting the backend."
}

$envValues = Read-BackendEnv ".env"
$mysqlHost = Get-BackendEnvValue $envValues "MYSQL_HOST"

if ($mysqlHost -eq "mysql") {
    $env:MYSQL_HOST = "127.0.0.1"
    Write-Host "MYSQL_HOST=mysql detected in .env; using 127.0.0.1 for local backend startup."
}

Write-Host "========== BuyWise Backend Startup =========="
Write-Host "Python: $python"
Write-Host "Backend: http://127.0.0.1:$Port"
Write-Host "Swagger: http://127.0.0.1:$Port/docs"

if (-not $SkipMigration) {
    Write-Host "========== Database Migration =========="
    & $python -m app.scripts.migrate_database
} else {
    Write-Host "Database migration skipped."
}

Write-Host "========== Start Backend =========="
$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--port", $Port.ToString())
if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

& $python @uvicornArgs

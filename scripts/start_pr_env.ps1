param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [string]$Branch,
    [string]$WorktreeRoot,
    [int]$BackendPort = 8000,
    [int]$MysqlPort = 3306,
    [int]$PrometheusPort = 9090,
    [int]$LokiPort = 3100,
    [int]$GrafanaPort = 3000,
    [switch]$Observability,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

$safeName = ($Name.ToLowerInvariant() -replace "[^a-z0-9_.-]", "-").Trim("-")
if (-not $safeName) {
    throw "Name must contain at least one letter or number."
}

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if (-not $WorktreeRoot) {
    $WorktreeRoot = Split-Path -Parent $repoRoot
}

$worktreePath = Join-Path $WorktreeRoot "BuyWise-$safeName"
if (-not (Test-Path -LiteralPath $worktreePath)) {
    if ($Branch) {
        & git worktree add $worktreePath $Branch
    } else {
        & git worktree add $worktreePath HEAD
    }
}

Push-Location $worktreePath
try {
    if (-not (Test-Path -LiteralPath ".env") -and (Test-Path -LiteralPath ".env.dev.example")) {
        Copy-Item ".env.dev.example" ".env"
    }

    $env:COMPOSE_PROJECT_NAME = "buywise-$safeName"
    $env:BACKEND_PORT = $BackendPort.ToString()
    $env:MYSQL_PORT = $MysqlPort.ToString()
    $env:PROMETHEUS_PORT = $PrometheusPort.ToString()
    $env:LOKI_PORT = $LokiPort.ToString()
    $env:GRAFANA_PORT = $GrafanaPort.ToString()

    $composeArgs = @("compose", "-p", $env:COMPOSE_PROJECT_NAME, "-f", "docker-compose.yml")
    if ($Observability) {
        $composeArgs += @("-f", "docker-compose.observability.yml")
    }
    $composeArgs += "up"
    $composeArgs += "-d"
    if (-not $NoBuild) {
        $composeArgs += "--build"
    }

    & docker @composeArgs

    Write-Host "Project: $env:COMPOSE_PROJECT_NAME"
    Write-Host "Worktree: $worktreePath"
    Write-Host "Backend: http://127.0.0.1:$BackendPort"
    if ($Observability) {
        Write-Host "Prometheus: http://127.0.0.1:$PrometheusPort"
        Write-Host "Loki: http://127.0.0.1:$LokiPort"
        Write-Host "Grafana: http://127.0.0.1:$GrafanaPort"
    }
} finally {
    Pop-Location
}

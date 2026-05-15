param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [string]$WorktreeRoot,
    [switch]$Observability,
    [switch]$RemoveVolumes,
    [switch]$RemoveWorktree
)

$ErrorActionPreference = "Stop"

$safeName = ($Name.ToLowerInvariant() -replace "[^a-z0-9_.-]", "-").Trim("-")
if (-not $safeName) {
    throw "Name must contain at least one letter or number."
}

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if (-not $WorktreeRoot) {
    $WorktreeRoot = Split-Path -Parent $repoRoot
}

$worktreePath = Join-Path $WorktreeRoot "BuyWise-$safeName"
$projectName = "buywise-$safeName"

$composeArgs = @("compose", "-p", $projectName)
if (Test-Path -LiteralPath $worktreePath) {
    Push-Location $worktreePath
} else {
    Push-Location $repoRoot
}

try {
    $composeArgs += @("-f", "docker-compose.yml")
    if ($Observability) {
        $composeArgs += @("-f", "docker-compose.observability.yml")
    }
    $composeArgs += "down"
    if ($RemoveVolumes) {
        $composeArgs += "-v"
    }
    & docker @composeArgs
} finally {
    Pop-Location
}

if ($RemoveWorktree -and (Test-Path -LiteralPath $worktreePath)) {
    & git worktree remove $worktreePath
}

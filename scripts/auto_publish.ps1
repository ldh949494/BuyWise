$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$excludedPaths = @(
    ".idea",
    "emulator_shopagent.png"
)

Write-Host "========== Validate Before Publish =========="
& powershell.exe -ExecutionPolicy Bypass -File ".\scripts\auto_validate.ps1"

Write-Host "========== Prepare Git Changes =========="

git add -u
git add .

foreach ($path in $excludedPaths) {
    git reset -- $path 2>$null
}

$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "No publishable changes found. Skip commit and push."
    exit 0
}

Write-Host "Changes staged for publish:"
$staged | ForEach-Object { Write-Host " - $_" }

Write-Host "========== Commit =========="
$commitMessage = "chore: validate and publish local changes"
git commit -m $commitMessage

Write-Host "========== Push =========="
$branch = git branch --show-current
if (-not $branch) {
    throw "Unable to detect the current Git branch."
}

git push origin $branch

Write-Host "Publish completed on branch '$branch'."

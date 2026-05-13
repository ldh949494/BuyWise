param(
    [string]$BaseBranch = "main",
    [string]$CommitMessage = "chore: validate and publish local changes"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$excludedPaths = @(
    ".idea",
    "emulator_shopagent.png"
)

Write-Host "========== Validate Before Publish =========="
& powershell.exe -ExecutionPolicy Bypass -File ".\scripts\auto_validate.ps1"

Write-Host "========== Create Publish Branch =========="
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$publishBranch = "auto/local-$timestamp"

$currentBranch = git branch --show-current
if (-not $currentBranch) {
    throw "Unable to detect the current Git branch."
}

git switch -c $publishBranch
Write-Host "Created branch '$publishBranch' from '$currentBranch'."

Write-Host "========== Prepare Git Changes =========="
git add -u
git add -- .

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
git commit -m $CommitMessage

Write-Host "========== Push =========="
git push origin $publishBranch

Write-Host "========== Create Pull Request =========="
$ghAvailable = [bool](Get-Command gh -ErrorAction SilentlyContinue)
$ghLoggedIn = $false

if ($ghAvailable) {
    gh auth status *> $null
    $ghLoggedIn = ($LASTEXITCODE -eq 0)
}

if ($ghLoggedIn) {
    gh pr create `
        --base $BaseBranch `
        --head $publishBranch `
        --title $CommitMessage `
        --body "Local validation passed. This PR was created by scripts/auto_publish.ps1."
} else {
    $remoteUrl = git remote get-url origin
    $repoUrl = $remoteUrl

    if ($repoUrl -match "^git@github\.com:(.+)\.git$") {
        $repoUrl = "https://github.com/$($Matches[1])"
    } elseif ($repoUrl -match "^https://github\.com/(.+)\.git$") {
        $repoUrl = "https://github.com/$($Matches[1])"
    }

    Write-Host "GitHub CLI is unavailable or not authenticated."
    Write-Host "Create the PR manually:"
    Write-Host "$repoUrl/compare/$BaseBranch...$publishBranch?expand=1"
}

Write-Host "Publish completed on branch '$publishBranch'."

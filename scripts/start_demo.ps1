param(
    [int]$Port = 8000,
    [switch]$SkipIndex,
    [switch]$NoReload,
    [switch]$AllowMockLlm
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\set_utf8.ps1"

function Assert-LastExitCode {
    param([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE."
    }
}

function Read-DemoEnv {
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

function Get-DemoEnvValue {
    param(
        [hashtable]$Values,
        [string]$Name
    )

    $environmentValue = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($environmentValue)) {
        return $environmentValue
    }
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
    throw ".env is missing. Copy .env.example to .env and configure LLM_PROVIDER, LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL."
}

$envValues = Read-DemoEnv ".env"
$llmProvider = Get-DemoEnvValue $envValues "LLM_PROVIDER"
$llmApiKey = Get-DemoEnvValue $envValues "LLM_API_KEY"
$embeddingProvider = Get-DemoEnvValue $envValues "EMBEDDING_PROVIDER"
$embeddingBaseUrl = Get-DemoEnvValue $envValues "EMBEDDING_BASE_URL"
$embeddingApiKey = Get-DemoEnvValue $envValues "EMBEDDING_API_KEY"
$mysqlHost = Get-DemoEnvValue $envValues "MYSQL_HOST"
$visionProvider = Get-DemoEnvValue $envValues "VISION_PROVIDER"
$speechProvider = Get-DemoEnvValue $envValues "SPEECH_PROVIDER"
$uploadProvider = Get-DemoEnvValue $envValues "UPLOAD_PROVIDER"
$uploadPublicBaseUrl = Get-DemoEnvValue $envValues "UPLOAD_PUBLIC_BASE_URL"

if ($mysqlHost -eq "mysql") {
    $env:MYSQL_HOST = "127.0.0.1"
    Write-Host "MYSQL_HOST=mysql detected in .env; using 127.0.0.1 for local demo startup."
}

if ($llmProvider -ne "openai-compatible" -and -not $AllowMockLlm) {
    throw "Demo expects LLM_PROVIDER=openai-compatible. Use -AllowMockLlm only for offline smoke checks."
}

if (-not $AllowMockLlm -and ([string]::IsNullOrWhiteSpace($llmApiKey) -or $llmApiKey -like "your-*")) {
    throw "LLM_API_KEY is missing or still a placeholder in .env."
}

$usesExternalEmbedding = $embeddingProvider -and $embeddingProvider -ne "mock"
if (-not $SkipIndex -and $usesExternalEmbedding) {
    $missingEmbeddingBaseUrl = [string]::IsNullOrWhiteSpace($embeddingBaseUrl)
    $missingEmbeddingApiKey = [string]::IsNullOrWhiteSpace($embeddingApiKey) -or $embeddingApiKey -like "your-*"
    if ($missingEmbeddingBaseUrl -or $missingEmbeddingApiKey) {
        throw "Non-mock EMBEDDING_PROVIDER requires EMBEDDING_BASE_URL and EMBEDDING_API_KEY when building the demo vector index. Use -SkipIndex to start without rebuilding the index."
    }
}

$usesExternalMultimodal = ($visionProvider -and $visionProvider -ne "mock") -or ($speechProvider -and $speechProvider -ne "mock")
$hasPublicUploadUrl = -not [string]::IsNullOrWhiteSpace($uploadPublicBaseUrl) -or $uploadProvider -eq "cos"
if ($usesExternalMultimodal -and -not $hasPublicUploadUrl) {
    throw "Non-mock VISION_PROVIDER or SPEECH_PROVIDER requires UPLOAD_PUBLIC_BASE_URL, unless UPLOAD_PROVIDER=cos."
}

Write-Host "========== BuyWise Demo Startup =========="
Write-Host "Python: $python"
Write-Host "Backend: http://127.0.0.1:$Port"
Write-Host "Swagger: http://127.0.0.1:$Port/docs"
Write-Host "LLM provider: $llmProvider"
Write-Host "Embedding provider: $embeddingProvider"
Write-Host "Vision provider: $visionProvider"
Write-Host "Speech provider: $speechProvider"

Write-Host "========== Database Migration =========="
& $python -m app.scripts.migrate_database
Assert-LastExitCode "database migration"

Write-Host "========== Demo Seed Data =========="
& $python -m app.scripts.seed_products --profile demo
Assert-LastExitCode "demo seed data"

if (-not $SkipIndex) {
    Write-Host "========== Vector Index =========="
    & $python -m app.scripts.build_vector_index
    Assert-LastExitCode "vector index build"
} else {
    Write-Host "Vector index skipped."
}

Write-Host "========== Start Backend =========="
$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--port", $Port.ToString())
if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

Write-Host "After startup, verify fallback API path in another terminal:"
Write-Host ".\.venv\Scripts\python.exe .\scripts\demo_api_check.py --base-url http://127.0.0.1:$Port"
& $python @uvicornArgs

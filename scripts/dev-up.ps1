param(
    [switch]$Rebuild,
    [int]$HealthTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

$composeArgs = @("compose", "up", "-d")
if ($Rebuild) {
    $composeArgs += "--build"
}

Write-Host "Starting mongo, ollama, backend, and frontend..."
docker @composeArgs
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up failed"
}

$healthUrl = "http://localhost:8000/health"
$deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
$healthy = $false

Write-Host "Waiting for backend health endpoint..."
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $healthy) {
    Write-Host "Backend did not become healthy in time. Recent backend logs:" -ForegroundColor Yellow
    docker compose logs backend --tail 100
    throw "backend health check failed"
}

Write-Host ""
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000"
Write-Host "Health:   http://localhost:8000/health"

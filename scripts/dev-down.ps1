$ErrorActionPreference = "Stop"

Write-Host "Stopping mongo, ollama, backend, and frontend..."
docker compose down

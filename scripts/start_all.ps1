$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backendScript = Join-Path $PSScriptRoot 'start_backend.ps1'
$frontendScript = Join-Path $PSScriptRoot 'start_frontend.ps1'

Write-Host "=================================================="
Write-Host "   AI GitHub Repository Auditor - Launching Platform"
Write-Host "=================================================="

Write-Host "Ensuring ports 8000 and 3000 are clean..."
Get-NetTCPConnection -LocalPort 8000,3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 800

& $backendScript
& $frontendScript

$backendReady = $false
$frontendReady = $false
$maxAttempts = 20

for ($attempt = 0; $attempt -lt $maxAttempts; $attempt++) {
    try {
        $backendResp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2
        if ($backendResp.StatusCode -eq 200) { $backendReady = $true }
    }
    catch {
        $backendReady = $false
    }

    try {
        $frontendResp = Invoke-WebRequest -Uri 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 2
        if ($frontendResp.StatusCode -eq 200) { $frontendReady = $true }
    }
    catch {
        $frontendReady = $false
    }

    if ($backendReady -and $frontendReady) {
        break
    }

    Start-Sleep -Milliseconds 800
}

Write-Host ""
if ($backendReady -and $frontendReady) {
    Write-Host "Platform successfully launched!"
    Write-Host "- Web Dashboard: http://localhost:3000"
    Write-Host "- Swagger Docs:  http://localhost:8000/docs"
    Write-Host "=================================================="
    Start-Process 'http://localhost:3000'
    Start-Process 'http://localhost:8000/docs'
    exit 0
}

Write-Host "One or more services may already be running or are still starting up."
Write-Host "Check the health endpoints manually: http://localhost:8000/health and http://localhost:3000"
Write-Host "Logs folder: $root\logs"
exit 0

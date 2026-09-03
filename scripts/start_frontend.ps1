$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $root 'frontend'
$frontendLogDir = Join-Path $root 'logs'
$frontendLogPath = Join-Path $frontendLogDir 'frontend.log'
$frontendErrorPath = Join-Path $frontendLogDir 'frontend.err'

if (-not (Test-Path $frontendDir)) {
    Write-Error "Frontend directory not found: $frontendDir"
    exit 1
}

New-Item -ItemType Directory -Force -Path $frontendLogDir | Out-Null

$port = 3000
$portInUse = $false
try {
    $portInUse = @((Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue)).Count -gt 0
}
catch {
    $portInUse = $false
}

if ($portInUse) {
    Write-Host "Releasing port $port to launch updated frontend..."
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 800
}

Write-Host "Starting Next.js frontend on http://localhost:$port"
Start-Process -FilePath 'npm.cmd' -ArgumentList @('run','dev') -WorkingDirectory $frontendDir -RedirectStandardOutput $frontendLogPath -RedirectStandardError $frontendErrorPath -WindowStyle Normal

for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$port" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) {
            Write-Host "Frontend ready on http://localhost:$port"
            Start-Process "http://localhost:$port"
            exit 0
        }
    }
    catch {
        # Wait for startup to complete.
    }
}

Write-Host "Frontend did not become ready within the expected startup window. See logs at: $frontendLogPath"
exit 0

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backendLogDir = Join-Path $root 'logs'
$backendLogPath = Join-Path $backendLogDir 'backend.log'
$backendErrorPath = Join-Path $backendLogDir 'backend.err'
$pythonExe = Join-Path $root 'venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python virtual environment not found at: $pythonExe"
    exit 1
}

New-Item -ItemType Directory -Force -Path $backendLogDir | Out-Null

$port = 8000
$portInUse = $false
try {
    $portInUse = @((Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue)).Count -gt 0
}
catch {
    $portInUse = $false
}

if ($portInUse) {
    Write-Host "Releasing port $port to launch updated backend..."
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 800
}

Write-Host "Starting FastAPI backend on http://localhost:$port"
Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','0.0.0.0','--port','8000','--reload') -WorkingDirectory $root -RedirectStandardOutput $backendLogPath -RedirectStandardError $backendErrorPath -WindowStyle Normal

for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) {
            Write-Host "Backend ready on http://localhost:$port"
            exit 0
        }
    }
    catch {
        # Wait for startup to complete.
    }
}

Write-Host "Backend did not become ready within the expected startup window. See logs at: $backendLogPath"
exit 0

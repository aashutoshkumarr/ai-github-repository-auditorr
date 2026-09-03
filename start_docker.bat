@echo off
echo ===================================================
echo   Starting AI GitHub Repository Auditor (Docker)
echo ===================================================
echo.
echo [1/3] Checking Docker daemon...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo Please open Docker Desktop and wait until it says 'Engine running'.
    pause
    exit /b 1
)

echo [2/3] Spinning up container cluster with Docker Compose...
docker compose up -d --build

echo.
echo [3/3] Checking running services...
docker compose ps

echo.
echo ===================================================
echo   Cluster is UP and running!
echo   - Web Dashboard:  http://localhost:3000
echo   - Backend API:    http://localhost:8000/docs
echo   - MinIO Storage:  http://localhost:9001 (auditor / auditor123)
echo ===================================================
echo.
echo Opening Web Dashboard and MinIO Console in browser...
timeout /t 3 >nul
start http://localhost:3000
start http://localhost:9001
echo.
echo To view real-time logs, run: docker compose logs -f
echo To stop the cluster, run:    .\stop_docker.bat
echo.

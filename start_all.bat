@echo off
title AI GitHub Repository Auditor - Local Starter
echo ========================================================
echo   AI GitHub Repository Auditor - Starting Local Stack
echo ========================================================

echo 1. Freeing ports 8000 and 3000 from any old processes...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $PSItem -Force -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 1 /nobreak >nul

echo 2. Launching Backend on http://localhost:8000...
start "AI Auditor - Backend (Port 8000)" cmd /k "cd /d %~dp0 && .\venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo 3. Launching Frontend on http://localhost:3000...
start "AI Auditor - Frontend (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo 4. Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo 5. Opening browser tabs...
start http://localhost:3000
start http://localhost:8000/docs

echo ========================================================
echo   Platform is running!
echo   - Frontend: http://localhost:3000
echo   - Backend:  http://localhost:8000/docs
echo   - To stop:  Run .\stop_local.bat or close the 2 windows
echo ========================================================

@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_frontend.ps1"
if not "%ERRORLEVEL%"=="0" (
    exit /b %ERRORLEVEL%
)

pause

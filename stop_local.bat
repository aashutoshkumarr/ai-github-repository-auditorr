@echo off
echo Stopping local background services on port 8000 and 3000...
powershell -Command "Get-NetTCPConnection -LocalPort 8000,3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
echo Local services on ports 8000 and 3000 have been stopped.

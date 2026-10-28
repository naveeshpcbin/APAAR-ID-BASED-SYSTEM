@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0opendemo.ps1"
echo.
echo =================================================================
echo  Servers are running:
echo   - Backend API:  http://127.0.0.1:8000/docs
echo   - Web Portal:   http://localhost:3000/login
echo =================================================================
echo  Press any key to close this launcher window (services keep running)...
pause >nul

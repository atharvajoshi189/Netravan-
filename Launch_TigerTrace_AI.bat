@echo off
TITLE TigerTrace AI - Pench Tiger Reserve Command Center
COLOR 0A

echo =========================================================================
echo       TIGERTRACE AI - PENCH TIGER RESERVE FIELD COMMAND CENTER
echo               100%% Offline Edge Biometric Intelligence
echo =========================================================================
echo.
echo [1/3] Initializing Offline Wildlife Vision Engine...
cd /d "%~dp0TigerTrace_AI"

echo [2/3] Starting Local Server on localhost:8000...
start /b python ui\app.py > nul 2>&1

echo [3/3] Launching Field Command Center in Browser...
timeout /t 2 /nobreak > nul
start http://127.0.0.1:8000

echo.
echo =========================================================================
echo  [ACTIVE] TigerTrace AI is now running locally in your browser!
echo  URL: http://127.0.0.1:8000
echo.
echo  To shut down the system when finished, simply close this window.
echo =========================================================================
echo.
pause

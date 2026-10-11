@echo off
TITLE TigerTrace AI - Modern Web Intelligence Command Center
COLOR 0B

echo =========================================================================
echo       TIGERTRACE AI - MODERN WEB INTELLIGENCE PLATFORM (VITE + REACT)
echo =========================================================================
echo.
echo [1/2] Navigating to web_ui workspace...
cd /d "%~dp0web_ui"

echo [2/2] Starting Vite Development Server with FastAPI API Proxy...
echo.
echo =========================================================================
echo  [ACTIVE] Web UI starting on: http://127.0.0.1:3000
echo  Backend API Proxy target:   http://127.0.0.1:8000
echo =========================================================================
echo.

npm run dev -- --host 127.0.0.1 --port 3000
pause

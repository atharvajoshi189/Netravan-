@echo off
TITLE NETRAVAN - Web UI Studio
COLOR 0B

echo =========================================================================
echo       NETRAVAN - TADBOA WILDLIFE INTELLIGENCE WEB STUDIO
echo =========================================================================
echo.
cd /d "%~dp0web_ui"
echo Starting Vite Dev Server on port 3000...
npm run dev -- --host 127.0.0.1 --port 3000
pause

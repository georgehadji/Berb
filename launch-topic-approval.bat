@echo off
REM Berb Topic Approval - Launch Script
REM Starts server and opens browser

echo ========================================
echo   Berb Topic Approval System
echo ========================================
echo.
echo Starting server...
echo.

set OPENROUTER_API_KEY=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

cd /d "%~dp0"
start "Berb Server" cmd /k "python -m berb.server.web_api_real"

echo Server starting on http://localhost:8001
echo.
echo Waiting for server to be ready...
timeout /t 8 /nobreak >nul

echo.
echo Opening browser...
start http://localhost:8001

echo.
echo ========================================
echo   Server: http://localhost:8001
echo   UI: http://localhost:8001
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul

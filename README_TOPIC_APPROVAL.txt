@echo off
REM Berb Topic Approval - Manual Launch Instructions
REM Run these commands in TWO separate command windows

echo ========================================
echo   Berb Topic Approval System
echo ========================================
echo.
echo WINDOW 1 - UI Server:
echo ----------------------
echo cd E:\Documents\Vibe-Coding\Berb\berb\ui
echo python -m http.server 8080
echo.
echo WINDOW 2 - API Server:
echo -----------------------
echo cd E:\Documents\Vibe-Coding\Berb
echo set OPENROUTER_API_KEY=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
echo python -m berb.server.web_api_real
echo.
echo After both servers start, open in browser:
echo http://localhost:8080/topic-approval.html
echo ========================================

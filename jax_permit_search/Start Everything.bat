@echo off
cd /d "%~dp0"
title JAX Permit Search - Running

echo ============================================
echo  JAX Permit Search - Starting Up
echo ============================================
echo.

REM ── Step 1: Close Opera so we can reopen it in debug mode ──
echo [1/3] Closing Opera...
taskkill /IM opera.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM ── Step 2: Open Opera with remote debugging (VPN stays active) ──
echo [2/3] Opening Opera with VPN...
start "" "C:\Users\user\AppData\Local\Programs\Opera\opera.exe" --remote-debugging-port=9222
timeout /t 4 /nobreak >nul

REM ── Step 3: Start the local bridge server ──
echo [3/3] Starting permit search bridge...
echo.
echo ============================================
echo  Ready! Now:
echo  1. Make sure VPN is ON in Opera
echo  2. Open your BRRRR Calculator in any browser
echo  3. Fill in the address and click the search icon
echo.
echo  Keep this window open while you work.
echo  Close this window to stop everything.
echo ============================================
echo.

python local_server.py

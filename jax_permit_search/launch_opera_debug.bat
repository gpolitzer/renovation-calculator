@echo off
echo ============================================
echo  Starting Opera with remote debugging
echo  (your VPN will stay active)
echo ============================================
echo.
echo Step 1: Close ALL Opera windows first, then press any key...
pause

echo.
echo Step 2: Opening Opera with remote debugging port...
start "" "C:\Users\user\AppData\Local\Programs\Opera\opera.exe" --remote-debugging-port=9222

echo.
echo Opera is starting...
timeout /t 3 /nobreak > nul

echo.
echo ============================================
echo  Opera is ready!
echo  Now go back to your terminal and run:
echo  python discover_site.py
echo    or
echo  python search_permits.py "YOUR ADDRESS"
echo ============================================
echo.
pause

@echo off
cd /d "%~dp0"
python permit_search_gui.py
if errorlevel 1 (
    echo.
    echo Something went wrong. Make sure Python is installed.
    pause
)

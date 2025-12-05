@echo off
REM mat2h5.bat - Windows double-clickable script
REM Double-click this file to open Command Prompt and start conversion

REM Get the directory where this script is located
cd /d "%~dp0"

REM Run mat2h5 with auto command
python mat2h5.py convert auto

REM Keep window open so user can see results
echo.
echo Press any key to close...
pause >nul


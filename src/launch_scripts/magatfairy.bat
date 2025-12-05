@echo off
REM magatfairy.bat - Windows double-clickable script
REM Double-click this file to open Command Prompt and start conversion

REM Get repo root (one level above src)
set "REPO_ROOT=%~dp0..\.."
pushd "%REPO_ROOT%"

REM Ensure Python can find cli package
set "PYTHONPATH=%REPO_ROOT%\src"

REM Quick environment check (systemfairy)
python -m cli.magatfairy systemfairy
echo.

REM Run magatfairy (module form to avoid blocked exe)
python -m cli.magatfairy convert auto

REM Keep window open so user can see results
echo.
echo Press any key to close...
pause >nul

popd


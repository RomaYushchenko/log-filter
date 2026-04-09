@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Log Filter - Virtual environment setup (Windows)
REM Creates venv if missing, activates it, installs skill runtime dependencies.
REM After this, use: .\venv\Scripts\python.exe ...
REM ============================================================================

set "SCRIPT_DIR=%~dp0"
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"

echo Log Filter - Python environment setup
echo.

call :setup_environment
if errorlevel 1 exit /b 1

call :setup_venv
if errorlevel 1 exit /b 1

call :ensure_dependencies
if errorlevel 1 exit /b 1

echo.
echo ============================================================================
echo Virtual environment is ready.
echo Location: !SCRIPT_DIR!\venv
echo Python:   !SCRIPT_DIR!\venv\Scripts\python.exe
echo.
echo Example ^(from this directory^):
echo   .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'scripts'); from log_filter import run_filter; ..."
echo.
echo To activate for an interactive session:
echo   !SCRIPT_DIR!\venv\Scripts\activate.bat
echo ============================================================================

exit /b 0

REM ============================================================================
REM Subroutines
REM ============================================================================

:setup_environment
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not on PATH.
    exit /b 1
)
cd /d "!SCRIPT_DIR!"
exit /b 0

:setup_venv
set "VENV_DIR=!SCRIPT_DIR!\venv"

if not exist "!VENV_DIR!" (
    echo Creating virtual environment in !VENV_DIR! ...
    python -m venv "!VENV_DIR!"
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

if exist "!VENV_DIR!\Scripts\activate.bat" (
    call "!VENV_DIR!\Scripts\activate.bat"
    if errorlevel 1 (
        echo Error: Failed to activate virtual environment.
        exit /b 1
    )
) else (
    echo Error: activate.bat not found under !VENV_DIR!\Scripts
    exit /b 1
)
exit /b 0

:ensure_dependencies
call :install_dependencies
if errorlevel 1 exit /b 1
exit /b 0

:install_dependencies
set "REQ=!SCRIPT_DIR!\scripts\requirements-log-filter.txt"
echo Installing / updating dependencies from scripts\requirements-log-filter.txt ...

if not exist "!REQ!" (
    echo Error: File not found: !REQ!
    exit /b 1
)

python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "!REQ!" --upgrade
if errorlevel 1 (
    echo Error: pip install failed.
    exit /b 1
)
echo Dependencies OK.
exit /b 0

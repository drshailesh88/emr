@echo off
REM DocAssist EMR - Windows One-Click Installer
REM Batch script wrapper for install.py

setlocal enabledelayedexpansion

REM Script configuration
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "INSTALL_SCRIPT=%SCRIPT_DIR%install.py"

REM Colors (using echo for compatibility)
set "COLOR_RESET=[0m"
set "COLOR_GREEN=[32m"
set "COLOR_RED=[31m"
set "COLOR_CYAN=[36m"
set "COLOR_YELLOW=[33m"

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo %COLOR_YELLOW%Warning: Running as Administrator. This may install system-wide.%COLOR_RESET%
    echo.
)

REM Print banner
echo.
echo %COLOR_CYAN%============================================================%COLOR_RESET%
echo %COLOR_CYAN%  DocAssist EMR - Windows Installer%COLOR_RESET%
echo %COLOR_CYAN%  Version 1.0.0%COLOR_RESET%
echo %COLOR_CYAN%============================================================%COLOR_RESET%
echo.

REM Check for Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    where py >nul 2>&1
    if !errorLevel! neq 0 (
        echo %COLOR_RED%Error: Python is not installed or not in PATH%COLOR_RESET%
        echo.
        echo Please install Python 3.11 or later from:
        echo https://www.python.org/downloads/
        echo.
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)

REM Check Python version
echo %COLOR_CYAN%Checking Python version...%COLOR_RESET%
%PYTHON_CMD% --version
if %errorLevel% neq 0 (
    echo %COLOR_RED%Error: Failed to get Python version%COLOR_RESET%
    pause
    exit /b 1
)
echo.

REM Check if install.py exists
if not exist "%INSTALL_SCRIPT%" (
    echo %COLOR_RED%Error: install.py not found at: %INSTALL_SCRIPT%%COLOR_RESET%
    pause
    exit /b 1
)

REM Run the Python installer
echo %COLOR_CYAN%Running Python installer...%COLOR_RESET%
echo.

cd /d "%PROJECT_DIR%"
%PYTHON_CMD% "%INSTALL_SCRIPT%" %*

set "EXIT_CODE=%errorLevel%"

echo.

if %EXIT_CODE% equ 0 (
    echo %COLOR_GREEN%============================================================%COLOR_RESET%
    echo %COLOR_GREEN%  Installation completed successfully!%COLOR_RESET%
    echo %COLOR_GREEN%============================================================%COLOR_RESET%
    echo.
    echo Next steps:
    echo   1. Activate virtual environment: venv\Scripts\activate
    echo   2. Run DocAssist: python main.py
    echo   3. Install Ollama from: https://ollama.ai/download/windows
    echo.
) else (
    echo %COLOR_RED%============================================================%COLOR_RESET%
    echo %COLOR_RED%  Installation failed with exit code: %EXIT_CODE%%COLOR_RESET%
    echo %COLOR_RED%============================================================%COLOR_RESET%
    echo.
    echo Please check the error messages above.
    echo.
)

REM Ask before closing
echo Press any key to exit...
pause >nul

exit /b %EXIT_CODE%

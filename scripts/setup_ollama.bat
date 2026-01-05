@echo off
REM Ollama Auto-Setup Script for Windows
REM DocAssist EMR - Local-First AI-Powered EMR

echo ============================================================
echo DocAssist EMR - Ollama Auto-Setup (Windows)
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.11+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [*] Python found
python --version

REM Check if required packages are installed
echo.
echo [*] Checking Python dependencies...
python -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo [!] Installing requests...
    pip install requests
)

python -c "import psutil" 2>nul
if %errorlevel% neq 0 (
    echo [!] Installing psutil...
    pip install psutil
)

REM Check if Ollama is installed
echo.
echo [*] Checking if Ollama is installed...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo OLLAMA NOT FOUND
    echo ============================================================
    echo.
    echo Please install Ollama for Windows:
    echo.
    echo Option 1: Download from https://ollama.ai/download/windows
    echo           Run the installer (OllamaSetup.exe^)
    echo.
    echo Option 2: Use winget (if available^)
    echo           winget install Ollama.Ollama
    echo.
    echo After installation, run this script again.
    echo ============================================================
    pause
    exit /b 1
)

echo [+] Ollama found
ollama --version

REM Check if Ollama is running
echo.
echo [*] Checking if Ollama service is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Ollama is not running. Starting Ollama...

    REM Try to start Ollama
    start "" "ollama" serve

    REM Wait for it to start
    echo [*] Waiting for Ollama to start...
    timeout /t 5 /nobreak >nul

    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Could not start Ollama automatically
        echo.
        echo Please start Ollama manually:
        echo   1. Open Ollama from Start Menu, or
        echo   2. Run: ollama serve
        echo.
        echo Then run this script again.
        pause
        exit /b 1
    )
)

echo [+] Ollama service is running

REM Run the Python setup script
echo.
echo [*] Running Python setup script...
echo ============================================================
python "%~dp0setup_ollama.py"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Ollama setup complete
    echo ============================================================
    echo.
    echo You can now run DocAssist EMR:
    echo   python main.py
    echo.
) else (
    echo.
    echo ============================================================
    echo Setup encountered errors. Please check the output above.
    echo ============================================================
    echo.
)

pause

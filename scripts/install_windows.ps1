# DocAssist EMR - Windows Installation Script
# PowerShell script for Windows setup

<#
.SYNOPSIS
    Installs DocAssist EMR on Windows.

.DESCRIPTION
    This script:
    - Checks system requirements
    - Installs Python dependencies
    - Creates data directories
    - Creates Start Menu shortcut
    - Sets up file associations
    - Optionally installs Ollama

.PARAMETER InstallOllama
    If specified, downloads and installs Ollama.

.PARAMETER CreateShortcuts
    If specified, creates desktop and Start Menu shortcuts (default: true).

.PARAMETER AddToPath
    If specified, adds DocAssist to PATH (default: false).

.EXAMPLE
    .\install_windows.ps1
    Basic installation

.EXAMPLE
    .\install_windows.ps1 -InstallOllama
    Installation with Ollama
#>

param(
    [switch]$InstallOllama = $false,
    [switch]$CreateShortcuts = $true,
    [switch]$AddToPath = $false,
    [switch]$SkipPython = $false
)

# Script configuration
$ErrorActionPreference = "Stop"
$AppName = "DocAssist"
$AppVersion = "1.0.0"
$RequiredPythonVersion = "3.11"

# Colors for output
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  DocAssist EMR - Windows Installer" -ForegroundColor Cyan
    Write-Host "  Version $AppVersion" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check system requirements
function Test-SystemRequirements {
    Write-Info "Checking system requirements..."

    # Check Windows version
    $winVersion = [System.Environment]::OSVersion.Version
    if ($winVersion.Major -lt 10) {
        Write-Error "Windows 10 or later is required. You have Windows $($winVersion.Major).$($winVersion.Minor)"
        exit 1
    }
    Write-Success "Windows version: $($winVersion.Major).$($winVersion.Minor) (OK)"

    # Check Python
    if (-not $SkipPython) {
        try {
            $pythonVersion = (python --version 2>&1) -replace 'Python ', ''
            Write-Success "Python version: $pythonVersion"

            # Verify minimum version
            if ($pythonVersion -lt $RequiredPythonVersion) {
                Write-Warning "Python $RequiredPythonVersion or later is recommended. You have $pythonVersion"
            }
        }
        catch {
            Write-Error "Python is not installed or not in PATH"
            Write-Info "Please install Python from https://www.python.org/downloads/"
            Write-Info "Make sure to check 'Add Python to PATH' during installation"
            exit 1
        }
    }

    # Check available disk space
    $rootDrive = $env:SystemDrive
    $drive = Get-PSDrive -Name $rootDrive.TrimEnd(':')
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)

    if ($freeSpaceGB -lt 5) {
        Write-Warning "Low disk space: $freeSpaceGB GB free. At least 5 GB recommended."
    }
    else {
        Write-Success "Disk space: $freeSpaceGB GB free (OK)"
    }

    # Check RAM
    $ram = Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
    $ramGB = [math]::Round($ram / 1GB, 2)
    Write-Success "RAM: $ramGB GB"

    if ($ramGB -lt 4) {
        Write-Warning "Low RAM: $ramGB GB. At least 4 GB recommended for LLM features."
    }

    Write-Host ""
}

# Install Python dependencies
function Install-PythonDependencies {
    Write-Info "Installing Python dependencies..."

    # Get script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectDir = Split-Path -Parent $scriptDir

    # Check if requirements.txt exists
    $requirementsFile = Join-Path $projectDir "requirements.txt"

    if (-not (Test-Path $requirementsFile)) {
        Write-Error "requirements.txt not found at: $requirementsFile"
        exit 1
    }

    try {
        # Install dependencies
        python -m pip install --upgrade pip
        python -m pip install -r $requirementsFile

        Write-Success "Python dependencies installed"
    }
    catch {
        Write-Error "Failed to install Python dependencies: $_"
        exit 1
    }

    Write-Host ""
}

# Create application directories
function New-ApplicationDirectories {
    Write-Info "Creating application directories..."

    # Data directory
    $dataDir = Join-Path $env:LOCALAPPDATA $AppName
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
        Write-Success "Created data directory: $dataDir"
    }
    else {
        Write-Success "Data directory exists: $dataDir"
    }

    # Config directory
    $configDir = Join-Path $env:APPDATA $AppName
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        Write-Success "Created config directory: $configDir"
    }
    else {
        Write-Success "Config directory exists: $configDir"
    }

    # Database directory
    $dbDir = Join-Path $dataDir "data"
    if (-not (Test-Path $dbDir)) {
        New-Item -ItemType Directory -Path $dbDir -Force | Out-Null
        Write-Success "Created database directory: $dbDir"
    }

    # Vector store directory
    $chromaDir = Join-Path $dbDir "chroma"
    if (-not (Test-Path $chromaDir)) {
        New-Item -ItemType Directory -Path $chromaDir -Force | Out-Null
        Write-Success "Created vector store directory: $chromaDir"
    }

    Write-Host ""
}

# Create shortcuts
function New-Shortcuts {
    if (-not $CreateShortcuts) {
        return
    }

    Write-Info "Creating shortcuts..."

    # Get script and project directories
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectDir = Split-Path -Parent $scriptDir
    $mainPy = Join-Path $projectDir "main.py"

    if (-not (Test-Path $mainPy)) {
        Write-Warning "main.py not found at: $mainPy. Skipping shortcut creation."
        return
    }

    # Create WScript Shell object
    $WshShell = New-Object -ComObject WScript.Shell

    # Desktop shortcut
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $desktopShortcut = Join-Path $desktopPath "$AppName.lnk"

    try {
        $shortcut = $WshShell.CreateShortcut($desktopShortcut)
        $shortcut.TargetPath = "python"
        $shortcut.Arguments = "`"$mainPy`""
        $shortcut.WorkingDirectory = $projectDir
        $shortcut.Description = "DocAssist EMR - Local-First AI-Powered EMR"
        # TODO: Set icon if available
        $shortcut.Save()

        Write-Success "Created desktop shortcut: $desktopShortcut"
    }
    catch {
        Write-Warning "Failed to create desktop shortcut: $_"
    }

    # Start Menu shortcut
    $startMenuPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
    $appStartMenuDir = Join-Path $startMenuPath $AppName

    if (-not (Test-Path $appStartMenuDir)) {
        New-Item -ItemType Directory -Path $appStartMenuDir -Force | Out-Null
    }

    $startMenuShortcut = Join-Path $appStartMenuDir "$AppName.lnk"

    try {
        $shortcut = $WshShell.CreateShortcut($startMenuShortcut)
        $shortcut.TargetPath = "python"
        $shortcut.Arguments = "`"$mainPy`""
        $shortcut.WorkingDirectory = $projectDir
        $shortcut.Description = "DocAssist EMR - Local-First AI-Powered EMR"
        $shortcut.Save()

        Write-Success "Created Start Menu shortcut: $startMenuShortcut"
    }
    catch {
        Write-Warning "Failed to create Start Menu shortcut: $_"
    }

    Write-Host ""
}

# Install Ollama
function Install-Ollama {
    if (-not $InstallOllama) {
        return
    }

    Write-Info "Installing Ollama..."

    # Check if Ollama is already installed
    try {
        $ollamaVersion = ollama --version 2>&1
        Write-Success "Ollama is already installed: $ollamaVersion"
        return
    }
    catch {
        # Not installed, proceed with installation
    }

    Write-Info "Downloading Ollama installer..."

    # Ollama download URL
    $ollamaUrl = "https://ollama.ai/download/OllamaSetup.exe"
    $installerPath = Join-Path $env:TEMP "OllamaSetup.exe"

    try {
        # Download installer
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $installerPath

        Write-Success "Downloaded Ollama installer"
        Write-Info "Running Ollama installer..."
        Write-Info "Please follow the installer prompts..."

        # Run installer
        Start-Process -FilePath $installerPath -Wait

        Write-Success "Ollama installation completed"
        Write-Info "You can download models with: ollama pull qwen2.5:3b"
    }
    catch {
        Write-Warning "Failed to install Ollama: $_"
        Write-Info "You can manually download Ollama from https://ollama.ai/download"
    }

    Write-Host ""
}

# Create .env file if not exists
function New-EnvFile {
    Write-Info "Checking .env file..."

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectDir = Split-Path -Parent $scriptDir
    $envFile = Join-Path $projectDir ".env"
    $envExample = Join-Path $projectDir ".env.example"

    if (Test-Path $envFile) {
        Write-Success ".env file already exists"
    }
    elseif (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Success "Created .env file from .env.example"
    }
    else {
        Write-Warning ".env.example not found. Skipping .env creation."
    }

    Write-Host ""
}

# Display post-installation instructions
function Show-PostInstallInstructions {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Configure Ollama (if not already done):" -ForegroundColor White
    Write-Host "   ollama pull qwen2.5:3b" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Start DocAssist EMR:" -ForegroundColor White
    Write-Host "   python main.py" -ForegroundColor Gray
    Write-Host "   OR use the desktop/Start Menu shortcut" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Data locations:" -ForegroundColor White
    Write-Host "   Data:   $env:LOCALAPPDATA\$AppName" -ForegroundColor Gray
    Write-Host "   Config: $env:APPDATA\$AppName" -ForegroundColor Gray
    Write-Host ""

    if ($InstallOllama) {
        Write-Host "4. Ollama is installed. Start it with:" -ForegroundColor White
        Write-Host "   ollama serve" -ForegroundColor Gray
        Write-Host ""
    }

    Write-Host "For help, visit: https://github.com/docassist/emr" -ForegroundColor White
    Write-Host ""
}

# Main installation flow
function Start-Installation {
    Show-Banner

    # Check for admin (warn if not)
    if (-not (Test-Administrator)) {
        Write-Warning "Not running as Administrator. Some features may require elevation."
        Write-Host ""
    }

    # Run installation steps
    Test-SystemRequirements
    Install-PythonDependencies
    New-ApplicationDirectories
    New-Shortcuts
    Install-Ollama
    New-EnvFile

    Show-PostInstallInstructions
}

# Run installation
try {
    Start-Installation
}
catch {
    Write-Host ""
    Write-Error "Installation failed: $_"
    Write-Host ""
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}

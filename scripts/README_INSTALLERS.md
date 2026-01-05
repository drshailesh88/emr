# DocAssist EMR - Installation Scripts

This directory contains cross-platform installation scripts for DocAssist EMR.

## Available Installers

### 1. `install.py` - Cross-Platform Python Installer (Recommended)
A comprehensive Python-based installer that works on all platforms.

**Features:**
- Python version check (3.11+ required)
- Virtual environment creation
- Automatic pip upgrade
- Requirements installation from `requirements.txt`
- Platform-specific dependency checks
- Critical imports verification
- Optional Whisper model download
- System resource checks (RAM, disk space)
- Colored terminal output
- Error handling and recovery

**Usage:**
```bash
# Basic installation (creates venv, installs all dependencies)
python3 scripts/install.py

# Skip virtual environment
python3 scripts/install.py --no-venv

# Force recreate virtual environment
python3 scripts/install.py --force-venv

# Skip Whisper model download
python3 scripts/install.py --skip-whisper

# Show help
python3 scripts/install.py --help
```

**What it does:**
1. Checks Python version (3.11+)
2. Verifies pip and venv are available
3. Creates virtual environment in `./venv/`
4. Upgrades pip to latest version
5. Installs all requirements from `requirements.txt`
6. Verifies critical imports (flet, chromadb, sentence-transformers, etc.)
7. Optionally downloads Whisper model for voice input
8. Creates `.env` file from `.env.example`
9. Displays system resources (RAM, disk space)
10. Shows post-installation instructions

---

### 2. `install.sh` - Unix One-Click Installer (Linux/macOS)
A bash wrapper script that provides a simple one-click installation experience.

**Features:**
- Auto-detects OS (Linux or macOS)
- Can use Python installer (default) or native platform installer
- Colored terminal output
- Comprehensive help text
- Flexible argument handling

**Usage:**
```bash
# Make executable (first time only)
chmod +x scripts/install.sh

# Basic installation (uses Python installer)
./scripts/install.sh

# Use native platform-specific installer
./scripts/install.sh --native

# Native installer with Ollama
./scripts/install.sh --native --install-ollama

# Python installer without venv
./scripts/install.sh --no-venv

# Show help
./scripts/install.sh --help
```

**Options:**
- `--python` - Use Python installer (default, cross-platform)
- `--native` - Use native platform installer (install_linux.sh or install_macos.sh)
- `--no-venv` - Skip virtual environment (Python installer)
- `--force-venv` - Recreate virtual environment (Python installer)
- `--skip-whisper` - Skip Whisper model download (Python installer)
- `--install-ollama` - Install Ollama (native installer)
- `--create-systemd-service` - Create systemd service (Linux native)
- `--create-launch-agent` - Create launch agent (macOS native)
- `--install-system-deps` - Install system dependencies (native)

---

### 3. `install.bat` - Windows One-Click Installer
A batch file wrapper for Windows users.

**Features:**
- Checks for Python installation
- Handles both `python` and `py` commands
- Colored terminal output (where supported)
- Administrator detection warning
- Auto-pause at end for error review

**Usage:**
```cmd
REM Double-click install.bat in Windows Explorer
REM OR run from Command Prompt:
install.bat

REM With options:
install.bat --no-venv
install.bat --skip-whisper
```

**What it does:**
1. Checks for Python in PATH
2. Verifies Python version
3. Calls `install.py` with any provided arguments
4. Shows success/failure message
5. Displays next steps
6. Pauses for user review

---

## Platform-Specific Installers

These are more comprehensive installers that handle system-level dependencies:

- **`install_linux.sh`** - Full Linux installer with systemd service creation
- **`install_macos.sh`** - Full macOS installer with launch agent creation
- **`install_windows.ps1`** - PowerShell installer for Windows (advanced)

Use these via the `--native` flag with `install.sh`:
```bash
./scripts/install.sh --native --install-ollama
```

---

## Quick Start Examples

### Windows
```cmd
REM One-click installation
install.bat

REM Then activate and run:
venv\Scripts\activate
python main.py
```

### Linux
```bash
# One-click installation
chmod +x scripts/install.sh && ./scripts/install.sh

# Then activate and run:
source venv/bin/activate
python main.py
```

### macOS
```bash
# One-click installation
chmod +x scripts/install.sh && ./scripts/install.sh

# Then activate and run:
source venv/bin/activate
python main.py
```

---

## Troubleshooting

### Python not found
**Windows:**
- Install from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# OR download from python.org
```

### Virtual environment creation fails
If `venv` module is not available:

**Linux:**
```bash
sudo apt install python3-venv  # Ubuntu/Debian
```

**Alternative:**
```bash
# Skip venv and install globally (not recommended)
python3 scripts/install.py --no-venv
```

### pip not found
```bash
# Linux/macOS
python3 -m ensurepip --upgrade

# Windows
py -m ensurepip --upgrade
```

### ImportError after installation
Try upgrading pip and reinstalling:
```bash
python3 -m pip install --upgrade pip
python3 scripts/install.py --force-venv
```

---

## Post-Installation

After successful installation:

1. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

2. **Install and configure Ollama:**
   - Windows: https://ollama.ai/download/windows
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`
   - macOS: `brew install ollama`

3. **Pull an LLM model:**
   ```bash
   ollama pull qwen2.5:3b
   ```

4. **Run DocAssist:**
   ```bash
   python main.py
   ```

---

## File Structure

```
scripts/
├── install.py              # Cross-platform Python installer (recommended)
├── install.sh              # Unix wrapper (Linux/macOS)
├── install.bat             # Windows wrapper
├── install_linux.sh        # Native Linux installer
├── install_macos.sh        # Native macOS installer
├── install_windows.ps1     # Native Windows PowerShell installer
└── README_INSTALLERS.md    # This file
```

---

## Development Notes

- The Python installer (`install.py`) is the most portable and recommended for most users
- Native installers provide additional features like systemd services, desktop files, and system-wide installation
- All installers handle errors gracefully and provide clear error messages
- Colors are automatically disabled on terminals without ANSI support

---

## License

Part of DocAssist EMR - Local-First AI-Powered EMR for Indian Doctors

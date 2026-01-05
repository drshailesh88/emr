# DocAssist EMR - Installation Guide

Complete installation instructions for Windows, macOS, and Linux.

## Table of Contents

- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [macOS Installation](#macos-installation)
- [Linux Installation](#linux-installation)
- [Post-Installation Setup](#post-installation-setup)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, macOS 12+, Ubuntu 20.04+ (or equivalent) |
| **Python** | 3.11 or later |
| **RAM** | 4 GB (for basic features) |
| **Disk Space** | 5 GB free space |
| **Display** | 1366x768 minimum resolution |

### Recommended Requirements

| Component | Recommendation |
|-----------|----------------|
| **RAM** | 8 GB or more (for LLM features) |
| **Disk Space** | 10 GB free space |
| **Display** | 1920x1080 or higher |
| **LLM Backend** | Ollama installed (for AI features) |

### Platform-Specific Notes

- **Windows**: Windows 10 version 1809 or later recommended
- **macOS**: macOS 12 (Monterey) or later, both Intel and Apple Silicon supported
- **Linux**: Works on Ubuntu, Fedora, Arch, and other modern distributions

---

## Windows Installation

### Method 1: Automated Installation (Recommended)

1. **Download the Project**
   ```powershell
   git clone https://github.com/docassist/emr.git
   cd emr
   ```

2. **Run the Installation Script**
   ```powershell
   .\scripts\install_windows.ps1
   ```

   **Optional Flags:**
   - `-InstallOllama`: Automatically install Ollama
   - `-CreateShortcuts`: Create desktop and Start Menu shortcuts (default: true)

   **Example with Ollama:**
   ```powershell
   .\scripts\install_windows.ps1 -InstallOllama
   ```

3. **Follow On-Screen Instructions**

   The script will:
   - Check system requirements
   - Install Python dependencies
   - Create application directories
   - Set up shortcuts
   - Optionally install Ollama

### Method 2: Manual Installation

1. **Install Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Install Dependencies**
   ```powershell
   cd emr
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. **Create Data Directories**
   ```powershell
   mkdir "$env:LOCALAPPDATA\DocAssist"
   mkdir "$env:APPDATA\DocAssist"
   ```

4. **Install Ollama (Optional)**
   - Download from [ollama.ai](https://ollama.ai/download)
   - Install and run: `ollama pull qwen2.5:3b`

5. **Create .env File**
   ```powershell
   copy .env.example .env
   ```

### Windows Directory Locations

| Type | Location |
|------|----------|
| **Data** | `C:\Users\<YourName>\AppData\Local\DocAssist` |
| **Config** | `C:\Users\<YourName>\AppData\Roaming\DocAssist` |
| **Database** | `%LOCALAPPDATA%\DocAssist\data\clinic.db` |

### Running on Windows

- **Via Shortcut**: Click desktop icon or Start Menu → DocAssist
- **Via Command Line**: `python main.py`
- **Via PowerShell**: `cd emr; python main.py`

---

## macOS Installation

### Method 1: Automated Installation (Recommended)

1. **Download the Project**
   ```bash
   git clone https://github.com/docassist/emr.git
   cd emr
   ```

2. **Run the Installation Script**
   ```bash
   ./scripts/install_macos.sh
   ```

   **Optional Flags:**
   - `--install-ollama`: Install Ollama via Homebrew
   - `--create-launch-agent`: Create macOS launch agent

   **Example with Ollama:**
   ```bash
   ./scripts/install_macos.sh --install-ollama
   ```

3. **Follow On-Screen Instructions**

### Method 2: Manual Installation

1. **Install Homebrew** (if not installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.11+**
   ```bash
   brew install python@3.11
   ```

3. **Install Dependencies**
   ```bash
   cd emr
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   ```

4. **Create Data Directories**
   ```bash
   mkdir -p "$HOME/Library/Application Support/DocAssist"
   mkdir -p "$HOME/Library/Preferences/DocAssist"
   mkdir -p "$HOME/Library/Caches/DocAssist"
   ```

5. **Install Ollama (Optional)**
   ```bash
   brew install ollama
   brew services start ollama
   ollama pull qwen2.5:3b
   ```

6. **Create .env File**
   ```bash
   cp .env.example .env
   ```

### macOS Directory Locations

| Type | Location |
|------|----------|
| **Data** | `~/Library/Application Support/DocAssist` |
| **Config** | `~/Library/Preferences/DocAssist` |
| **Cache** | `~/Library/Caches/DocAssist` |
| **Database** | `~/Library/Application Support/DocAssist/data/clinic.db` |

### Running on macOS

- **Via Launcher**: `~/Applications/DocAssist`
- **Via Terminal**: `python3 main.py`
- **Via Symlink**: `docassist` (if installed to /Applications)

---

## Linux Installation

### Method 1: Automated Installation (Recommended)

1. **Download the Project**
   ```bash
   git clone https://github.com/docassist/emr.git
   cd emr
   ```

2. **Run the Installation Script**
   ```bash
   ./scripts/install_linux.sh
   ```

   **Optional Flags:**
   - `--install-ollama`: Install Ollama
   - `--create-systemd-service`: Create systemd user service
   - `--install-system-deps`: Install system dependencies (requires sudo)

   **Example with all options:**
   ```bash
   ./scripts/install_linux.sh --install-ollama --create-systemd-service --install-system-deps
   ```

3. **Follow On-Screen Instructions**

### Method 2: Manual Installation

#### Ubuntu/Debian

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-dev build-essential libsqlite3-dev
   ```

2. **Install Python Packages**
   ```bash
   cd emr
   python3 -m pip install --upgrade pip --user
   python3 -m pip install -r requirements.txt --user
   ```

3. **Create Data Directories** (XDG compliant)
   ```bash
   mkdir -p "$HOME/.local/share/docassist"
   mkdir -p "$HOME/.config/docassist"
   mkdir -p "$HOME/.cache/docassist"
   ```

4. **Install Ollama (Optional)**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama serve &
   ollama pull qwen2.5:3b
   ```

5. **Create .env File**
   ```bash
   cp .env.example .env
   ```

#### Fedora

```bash
sudo dnf install python3 python3-devel gcc gcc-c++ make sqlite-devel
python3 -m pip install -r requirements.txt --user
```

#### Arch Linux

```bash
sudo pacman -S python python-pip base-devel sqlite
python3 -m pip install -r requirements.txt --user
```

### Linux Directory Locations (XDG Base Directory)

| Type | Location | Environment Variable |
|------|----------|---------------------|
| **Data** | `~/.local/share/docassist` | `$XDG_DATA_HOME` |
| **Config** | `~/.config/docassist` | `$XDG_CONFIG_HOME` |
| **Cache** | `~/.cache/docassist` | `$XDG_CACHE_HOME` |
| **Database** | `~/.local/share/docassist/data/clinic.db` | — |

### Running on Linux

- **Via Desktop Entry**: Applications menu → DocAssist EMR
- **Via Terminal**: `python3 main.py`
- **Via Launcher Script**: `docassist` (if ~/.local/bin is in PATH)
- **Via systemd** (if configured): `systemctl --user start docassist`

### Creating Desktop Entry Manually

If the installation script didn't create it:

```bash
cat > ~/.local/share/applications/docassist.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=DocAssist EMR
Comment=Local-First AI-Powered EMR
Exec=python3 /path/to/emr/main.py
Path=/path/to/emr
Icon=docassist
Terminal=false
Categories=Office;Medical;Science;
EOF

chmod 644 ~/.local/share/applications/docassist.desktop
update-desktop-database ~/.local/share/applications
```

---

## Post-Installation Setup

### 1. Configure Ollama (For AI Features)

**Download AI Model:**

```bash
# Recommended model based on RAM:
# < 6GB RAM: qwen2.5:1.5b
ollama pull qwen2.5:1.5b

# 6-10GB RAM: qwen2.5:3b (default)
ollama pull qwen2.5:3b

# > 10GB RAM: qwen2.5:7b
ollama pull qwen2.5:7b
```

**Start Ollama Server:**

- **Windows**: Ollama runs automatically after installation
- **macOS**: `brew services start ollama` or `ollama serve`
- **Linux**: `ollama serve` or use systemd service

**Verify Ollama:**

```bash
ollama list
curl http://localhost:11434/api/tags
```

### 2. Configure Environment Variables

Edit `.env` file:

```bash
# Database location (optional, uses platform default if not set)
DATABASE_PATH=/path/to/custom/location/clinic.db

# Ollama configuration
OLLAMA_HOST=http://localhost:11434

# Model selection (auto-detects based on RAM if not set)
# LLM_MODEL=qwen2.5:3b

# Logging level
LOG_LEVEL=INFO
```

### 3. Initialize Database

First run will automatically create the database:

```bash
python3 main.py
```

Or manually initialize:

```bash
python3 -c "from src.services.database import Database; Database().initialize()"
```

### 4. Verify Installation

**Run Platform Tests:**

```bash
# Test all cross-platform features
python3 tests/platform/run_all_platforms.py

# Test current platform only
python3 tests/platform/run_all_platforms.py --current-only
```

**Check Installation:**

```bash
# Verify Python dependencies
python3 -m pip check

# Verify Ollama connection
curl http://localhost:11434/api/tags

# Verify data directories exist
python3 -c "from src.utils.platform_utils import *; print(f'Data: {get_data_directory()}'); print(f'Config: {get_config_directory()}')"
```

---

## Troubleshooting

### Common Issues

#### Python Not Found

**Windows:**
```powershell
# Reinstall Python and check "Add to PATH"
# Or add manually to PATH:
$env:Path += ";C:\Python311;C:\Python311\Scripts"
```

**macOS/Linux:**
```bash
# Install via package manager
brew install python@3.11  # macOS
sudo apt install python3  # Ubuntu
```

#### Permission Errors

**Windows:**
```powershell
# Run PowerShell as Administrator
# Or install to user directory:
python -m pip install -r requirements.txt --user
```

**macOS/Linux:**
```bash
# Use --user flag
python3 -m pip install -r requirements.txt --user

# Or fix permissions
sudo chown -R $USER:$USER ~/.local
```

#### Ollama Connection Failed

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama manually
ollama serve

# Check logs
journalctl --user -u ollama  # Linux systemd
```

#### Import Errors

```bash
# Reinstall dependencies
python3 -m pip install --force-reinstall -r requirements.txt

# Check Python version
python3 --version  # Should be 3.11+
```

#### Database Locked

```bash
# Close all instances of DocAssist
# Remove lock file
rm ~/.local/share/docassist/data/clinic.db-wal  # Linux
```

#### Display Issues

**High DPI Displays:**

- **Windows**: Right-click main.py → Properties → Compatibility → Change high DPI settings
- **macOS**: Handled automatically by Flet
- **Linux**: Set `GDK_SCALE=2` or `GDK_DPI_SCALE=0.5`

**Wayland Issues (Linux):**
```bash
# Force X11
GDK_BACKEND=x11 python3 main.py
```

### Platform-Specific Issues

#### Windows

**PowerShell Execution Policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Antivirus Blocking:**
- Add DocAssist folder to antivirus exceptions

#### macOS

**"App is damaged" Error:**
```bash
xattr -cr /path/to/DocAssist
```

**Gatekeeper Issues:**
```bash
# Allow unsigned apps
sudo spctl --master-disable
```

#### Linux

**Missing Dependencies:**
```bash
# Ubuntu/Debian
sudo apt install python3-dev build-essential libsqlite3-dev

# Fedora
sudo dnf install python3-devel gcc sqlite-devel

# Arch
sudo pacman -S python base-devel sqlite
```

### Getting Help

1. **Check Logs:**
   - Windows: `%LOCALAPPDATA%\DocAssist\logs\`
   - macOS: `~/Library/Caches/DocAssist/logs/`
   - Linux: `~/.cache/docassist/logs/`

2. **Run Tests:**
   ```bash
   python3 tests/platform/run_all_platforms.py
   ```

3. **Report Issues:**
   - GitHub: https://github.com/docassist/emr/issues
   - Include: OS version, Python version, error logs

---

## Uninstallation

### Windows

**Automated:**
```powershell
# Remove application data
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\DocAssist"
Remove-Item -Recurse -Force "$env:APPDATA\DocAssist"

# Remove shortcuts
Remove-Item "$env:USERPROFILE\Desktop\DocAssist.lnk"
Remove-Item -Recurse "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\DocAssist"
```

**Manual:**
1. Delete project folder
2. Delete `%LOCALAPPDATA%\DocAssist`
3. Delete `%APPDATA%\DocAssist`
4. Remove desktop/Start Menu shortcuts
5. Uninstall Python packages: `pip uninstall -r requirements.txt -y`

### macOS

**Automated:**
```bash
# Remove application data
rm -rf "$HOME/Library/Application Support/DocAssist"
rm -rf "$HOME/Library/Preferences/DocAssist"
rm -rf "$HOME/Library/Caches/DocAssist"

# Remove launcher
rm -f "$HOME/Applications/DocAssist"
sudo rm -f "/Applications/DocAssist"

# Remove launch agent
rm -f "$HOME/Library/LaunchAgents/com.docassist.emr.plist"
launchctl unload "$HOME/Library/LaunchAgents/com.docassist.emr.plist"
```

### Linux

**Automated:**
```bash
# Remove application data
rm -rf "$HOME/.local/share/docassist"
rm -rf "$HOME/.config/docassist"
rm -rf "$HOME/.cache/docassist"

# Remove desktop entry
rm -f "$HOME/.local/share/applications/docassist.desktop"
update-desktop-database ~/.local/share/applications

# Remove launcher
rm -f "$HOME/.local/bin/docassist"

# Remove systemd service
systemctl --user stop docassist
systemctl --user disable docassist
rm -f "$HOME/.config/systemd/user/docassist.service"
```

### Removing Ollama

**Windows:**
```powershell
# Uninstall via Settings → Apps → Ollama
```

**macOS:**
```bash
brew uninstall ollama
rm -rf ~/.ollama
```

**Linux:**
```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /usr/local/bin/ollama
sudo rm /etc/systemd/system/ollama.service
rm -rf ~/.ollama
```

---

## Next Steps

After installation:

1. **Configure Settings**: Launch DocAssist and configure clinic details
2. **Import Data**: Import existing patient data if migrating
3. **Download LLM Models**: `ollama pull qwen2.5:3b`
4. **Create Backup**: Set up encrypted cloud backup (optional)
5. **Mobile Setup**: Install DocAssist Mobile for on-the-go access

For more information, see:
- [README.md](README.md) - Project overview
- [CLAUDE.md](CLAUDE.md) - Development guide
- [TESTING_QUICK_START.md](TESTING_QUICK_START.md) - Testing guide

---

## License

DocAssist EMR is released under the MIT License. See [LICENSE](LICENSE) for details.

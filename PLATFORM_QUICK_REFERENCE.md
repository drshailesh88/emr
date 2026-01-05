# Platform Compatibility - Quick Reference Card

## Import and Use Platform Utilities

```python
from src.utils.platform_utils import (
    # Platform detection
    get_platform_name,         # Returns: "windows", "macos", "linux"
    get_platform_info,         # Returns: dict with detailed info

    # Directories
    get_data_directory,        # App data storage
    get_config_directory,      # App configuration
    get_cache_directory,       # App cache
    get_documents_directory,   # User Documents
    get_temp_directory,        # Temp files

    # Utilities
    normalize_path,            # Expand ~, env vars, make absolute
    ensure_directory_exists,   # Create dir with permissions

    # Platform info
    is_admin,                  # Check if running as admin/root
    get_display_scale,         # Get HiDPI scaling factor
    get_executable_extension,  # ".exe" on Windows, "" on Unix
    get_path_separator,        # ";" on Windows, ":" on Unix
)
```

## Platform-Specific Paths

| Platform | Data | Config | Cache |
|----------|------|--------|-------|
| **Windows** | `%LOCALAPPDATA%\DocAssist` | `%APPDATA%\DocAssist` | `%LOCALAPPDATA%\DocAssist\Cache` |
| **macOS** | `~/Library/Application Support/DocAssist` | `~/Library/Preferences/DocAssist` | `~/Library/Caches/DocAssist` |
| **Linux** | `~/.local/share/docassist` | `~/.config/docassist` | `~/.cache/docassist` |

## Common Usage Patterns

### Database Path
```python
from pathlib import Path
from src.utils.platform_utils import get_data_directory, ensure_directory_exists

# Get data directory
data_dir = get_data_directory()

# Ensure it exists
ensure_directory_exists(data_dir)

# Database file
db_path = data_dir / "data" / "clinic.db"
ensure_directory_exists(db_path.parent)
```

### PDF Export Path
```python
from src.utils.platform_utils import get_documents_directory

# Get Documents folder
docs_dir = get_documents_directory()

# Create DocAssist subfolder
exports_dir = docs_dir / "DocAssist" / "Exports"
ensure_directory_exists(exports_dir)

# Export file
pdf_path = exports_dir / f"prescription_{patient_id}.pdf"
```

### User Configuration
```python
from src.utils.platform_utils import get_config_directory

# Get config directory
config_dir = get_config_directory()
ensure_directory_exists(config_dir)

# Config file
config_file = config_dir / "settings.json"
```

### Normalize User Input
```python
from src.utils.platform_utils import normalize_path

# User enters: ~/Documents/exports
user_input = "~/Documents/exports"

# Normalize to absolute path
export_path = normalize_path(user_input)
# Result: /home/user/Documents/exports (Linux)
#     or: C:\Users\User\Documents\exports (Windows)
```

## Installation Commands

### Windows
```powershell
# Basic installation
.\scripts\install_windows.ps1

# With Ollama
.\scripts\install_windows.ps1 -InstallOllama

# Help
Get-Help .\scripts\install_windows.ps1
```

### macOS
```bash
# Basic installation
./scripts/install_macos.sh

# With Ollama and launch agent
./scripts/install_macos.sh --install-ollama --create-launch-agent

# Help
./scripts/install_macos.sh --help
```

### Linux
```bash
# Basic installation
./scripts/install_linux.sh

# Full installation
./scripts/install_linux.sh --install-ollama --create-systemd-service --install-system-deps

# Help
./scripts/install_linux.sh --help
```

## Testing Commands

### Run Platform Tests
```bash
# All platforms (auto-skip non-matching)
python3 tests/platform/run_all_platforms.py

# Current platform only
python3 tests/platform/run_all_platforms.py --current-only

# Generate reports
python3 tests/platform/run_all_platforms.py
# Creates: tests/platform/compatibility_report.txt
#          tests/platform/compatibility_report.json
```

### Test Platform Utilities
```bash
# Print platform info
python3 src/utils/platform_utils.py

# Quick test
python3 -c "from src.utils.platform_utils import *; print(get_platform_name(), get_data_directory())"
```

## Platform Detection

```python
from src.utils.platform_utils import get_platform_name

platform = get_platform_name()

if platform == "windows":
    # Windows-specific code
    pass
elif platform == "macos":
    # macOS-specific code
    pass
elif platform == "linux":
    # Linux-specific code
    pass
else:
    # Unknown platform
    pass
```

## Common Pitfalls to Avoid

❌ **Don't:**
```python
# Hardcoded paths
db_path = "C:\\Users\\Doctor\\data\\clinic.db"  # Windows-only!
db_path = "/home/doctor/data/clinic.db"          # Linux-only!

# String concatenation
path = "data" + "/" + "clinic.db"                # Wrong separator on Windows!

# Hardcoded separators
path = "data\\clinic.db"                         # Won't work on Unix!
```

✅ **Do:**
```python
# Use platform utilities
from src.utils.platform_utils import get_data_directory
db_path = get_data_directory() / "data" / "clinic.db"

# Use pathlib
from pathlib import Path
path = Path("data") / "clinic.db"

# Normalize user input
from src.utils.platform_utils import normalize_path
path = normalize_path(user_input)
```

## Permission Handling

```python
from src.utils.platform_utils import ensure_directory_exists, get_platform_name

# Create directory with permissions (Unix only, ignored on Windows)
data_dir = ensure_directory_exists(path, mode=0o755)

# Check if permissions are relevant
if get_platform_name() != "windows":
    # Set Unix permissions
    path.chmod(0o600)  # Owner read/write only
```

## Display Scaling

```python
from src.utils.platform_utils import get_display_scale

# Get scaling factor
scale = get_display_scale()

# Adjust UI elements
button_size = int(48 * scale)  # 48px @ 1.0, 96px @ 2.0 (Retina)
```

## Environment Variables

```python
import os
from src.utils.platform_utils import normalize_path

# Get and expand environment variables
db_path = os.getenv("DOCASSIST_DB_PATH", "~/Documents/docassist/clinic.db")
db_path = normalize_path(db_path)  # Expands ~ and env vars
```

## File Dialog Paths

```python
from src.utils.platform_utils import get_documents_directory

# Initial directory for file dialog
initial_dir = get_documents_directory()

# Use with flet file picker
file_picker.initial_directory = str(initial_dir)
```

## Checklist for New Features

When adding a new feature that uses files/directories:

- [ ] Use `pathlib.Path` for all path operations
- [ ] Import from `src.utils.platform_utils`
- [ ] Get platform-appropriate directories
- [ ] Use `ensure_directory_exists()` for creation
- [ ] Use `normalize_path()` for user input
- [ ] Don't hardcode path separators
- [ ] Test on all platforms (or use test runner)
- [ ] Handle permission differences (Windows vs Unix)

## Integration Example

Before:
```python
# Old code (platform-specific)
def get_database_path():
    return "data/clinic.db"
```

After:
```python
# New code (cross-platform)
from pathlib import Path
from src.utils.platform_utils import get_data_directory, ensure_directory_exists

def get_database_path() -> Path:
    data_dir = get_data_directory()
    db_dir = data_dir / "data"
    ensure_directory_exists(db_dir)
    return db_dir / "clinic.db"
```

## Resources

- **Documentation:** `/home/user/emr/INSTALLATION.md`
- **Summary:** `/home/user/emr/CROSS_PLATFORM_SETUP_SUMMARY.md`
- **Checklist:** `/home/user/emr/PLATFORM_COMPATIBILITY_CHECKLIST.md`
- **Tests:** `/home/user/emr/tests/platform/`
- **Scripts:** `/home/user/emr/scripts/`
- **Source:** `/home/user/emr/src/utils/platform_utils.py`

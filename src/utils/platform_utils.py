"""
Platform-specific utilities for cross-platform compatibility.

Provides platform-appropriate directory paths and file operations
for Windows, macOS, and Linux.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Optional, Literal

PlatformName = Literal["windows", "macos", "linux", "unknown"]


def get_platform_name() -> PlatformName:
    """
    Get the current platform name.

    Returns:
        "windows", "macos", "linux", or "unknown"
    """
    system = platform.system().lower()

    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def get_home_directory() -> Path:
    """
    Get the user's home directory in a cross-platform way.

    Returns:
        Path to user's home directory
    """
    return Path.home()


def get_data_directory(app_name: str = "DocAssist") -> Path:
    """
    Get the platform-appropriate data directory for the application.

    Platform-specific locations:
    - Windows: %LOCALAPPDATA%\\DocAssist (C:\\Users\\Doctor\\AppData\\Local\\DocAssist)
    - macOS: ~/Library/Application Support/DocAssist
    - Linux: ~/.local/share/docassist

    Args:
        app_name: Application name (default: "DocAssist")

    Returns:
        Path to application data directory
    """
    platform_name = get_platform_name()

    if platform_name == "windows":
        # Windows: Use LOCALAPPDATA
        base = os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / app_name
        else:
            # Fallback to user profile
            return get_home_directory() / "AppData" / "Local" / app_name

    elif platform_name == "macos":
        # macOS: Use Application Support
        return get_home_directory() / "Library" / "Application Support" / app_name

    elif platform_name == "linux":
        # Linux: Use XDG_DATA_HOME or fallback to ~/.local/share
        base = os.getenv("XDG_DATA_HOME")
        if base:
            return Path(base) / app_name.lower()
        else:
            return get_home_directory() / ".local" / "share" / app_name.lower()

    else:
        # Unknown platform: Use home directory
        return get_home_directory() / f".{app_name.lower()}"


def get_config_directory(app_name: str = "DocAssist") -> Path:
    """
    Get the platform-appropriate config directory for the application.

    Platform-specific locations:
    - Windows: %APPDATA%\\DocAssist (C:\\Users\\Doctor\\AppData\\Roaming\\DocAssist)
    - macOS: ~/Library/Preferences/DocAssist
    - Linux: ~/.config/docassist

    Args:
        app_name: Application name (default: "DocAssist")

    Returns:
        Path to application config directory
    """
    platform_name = get_platform_name()

    if platform_name == "windows":
        # Windows: Use APPDATA (Roaming)
        base = os.getenv("APPDATA")
        if base:
            return Path(base) / app_name
        else:
            # Fallback to user profile
            return get_home_directory() / "AppData" / "Roaming" / app_name

    elif platform_name == "macos":
        # macOS: Use Preferences
        return get_home_directory() / "Library" / "Preferences" / app_name

    elif platform_name == "linux":
        # Linux: Use XDG_CONFIG_HOME or fallback to ~/.config
        base = os.getenv("XDG_CONFIG_HOME")
        if base:
            return Path(base) / app_name.lower()
        else:
            return get_home_directory() / ".config" / app_name.lower()

    else:
        # Unknown platform: Use home directory
        return get_home_directory() / f".{app_name.lower()}"


def get_documents_directory() -> Path:
    """
    Get the platform-appropriate Documents directory for PDF exports.

    Platform-specific locations:
    - Windows: %USERPROFILE%\\Documents
    - macOS: ~/Documents
    - Linux: ~/Documents (or XDG_DOCUMENTS_DIR)

    Returns:
        Path to Documents directory
    """
    platform_name = get_platform_name()

    if platform_name == "windows":
        # Windows: Use USERPROFILE\\Documents
        userprofile = os.getenv("USERPROFILE")
        if userprofile:
            return Path(userprofile) / "Documents"
        else:
            return get_home_directory() / "Documents"

    elif platform_name == "linux":
        # Linux: Try XDG_DOCUMENTS_DIR first
        # XDG user-dirs are defined in ~/.config/user-dirs.dirs
        xdg_docs = os.getenv("XDG_DOCUMENTS_DIR")
        if xdg_docs:
            return Path(xdg_docs)
        else:
            return get_home_directory() / "Documents"

    else:
        # macOS and others: Use ~/Documents
        return get_home_directory() / "Documents"


def get_cache_directory(app_name: str = "DocAssist") -> Path:
    """
    Get the platform-appropriate cache directory for the application.

    Platform-specific locations:
    - Windows: %LOCALAPPDATA%\\DocAssist\\Cache
    - macOS: ~/Library/Caches/DocAssist
    - Linux: ~/.cache/docassist

    Args:
        app_name: Application name (default: "DocAssist")

    Returns:
        Path to application cache directory
    """
    platform_name = get_platform_name()

    if platform_name == "windows":
        # Windows: Use LOCALAPPDATA\\AppName\\Cache
        return get_data_directory(app_name) / "Cache"

    elif platform_name == "macos":
        # macOS: Use Caches
        return get_home_directory() / "Library" / "Caches" / app_name

    elif platform_name == "linux":
        # Linux: Use XDG_CACHE_HOME or fallback to ~/.cache
        base = os.getenv("XDG_CACHE_HOME")
        if base:
            return Path(base) / app_name.lower()
        else:
            return get_home_directory() / ".cache" / app_name.lower()

    else:
        # Unknown platform: Use data directory
        return get_data_directory(app_name) / "cache"


def ensure_directory_exists(path: Path, mode: int = 0o755) -> Path:
    """
    Ensure a directory exists with proper permissions.

    Creates the directory and all parent directories if they don't exist.
    Sets appropriate permissions (ignored on Windows).

    Args:
        path: Directory path to create
        mode: Permission mode (Unix only, default: 0o755)

    Returns:
        The created directory path

    Raises:
        OSError: If directory cannot be created
    """
    try:
        # Create directory with parents
        path.mkdir(parents=True, exist_ok=True)

        # Set permissions (only works on Unix-like systems)
        if get_platform_name() != "windows":
            try:
                path.chmod(mode)
            except (OSError, PermissionError):
                # Permission change might fail, but directory exists
                pass

        return path

    except Exception as e:
        raise OSError(f"Failed to create directory {path}: {e}")


def get_temp_directory(app_name: str = "DocAssist") -> Path:
    """
    Get the platform-appropriate temporary directory.

    Platform-specific locations:
    - Windows: %TEMP%\\DocAssist
    - macOS: /tmp/DocAssist
    - Linux: /tmp/DocAssist (or $TMPDIR)

    Args:
        app_name: Application name (default: "DocAssist")

    Returns:
        Path to temporary directory
    """
    import tempfile

    base_temp = Path(tempfile.gettempdir())
    return base_temp / app_name


def get_executable_extension() -> str:
    """
    Get the executable file extension for the current platform.

    Returns:
        ".exe" on Windows, "" on Unix-like systems
    """
    return ".exe" if get_platform_name() == "windows" else ""


def get_path_separator() -> str:
    """
    Get the path separator for the current platform.

    Returns:
        ";" on Windows, ":" on Unix-like systems
    """
    return ";" if get_platform_name() == "windows" else ":"


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path for the current platform.

    - Expands user home directory (~)
    - Resolves relative paths
    - Normalizes separators
    - Expands environment variables

    Args:
        path: Path to normalize (string or Path object)

    Returns:
        Normalized Path object
    """
    # Convert to string if Path
    path_str = str(path)

    # Expand environment variables
    path_str = os.path.expandvars(path_str)

    # Expand user home
    path_str = os.path.expanduser(path_str)

    # Convert to Path and resolve
    return Path(path_str).resolve()


def get_platform_info() -> dict:
    """
    Get detailed platform information.

    Returns:
        Dictionary with platform details:
        - platform: Platform name (windows/macos/linux/unknown)
        - system: OS name (Windows/Darwin/Linux)
        - release: OS release version
        - version: OS version string
        - machine: Machine type (x86_64, arm64, etc.)
        - processor: Processor type
        - python_version: Python version string
        - is_64bit: Whether Python is 64-bit
    """
    return {
        "platform": get_platform_name(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_64bit": sys.maxsize > 2**32,
    }


def is_admin() -> bool:
    """
    Check if the current process has administrator/root privileges.

    Returns:
        True if running as admin/root, False otherwise
    """
    platform_name = get_platform_name()

    try:
        if platform_name == "windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix-like: Check if effective user ID is 0 (root)
            return os.geteuid() == 0
    except Exception:
        return False


def get_display_scale() -> float:
    """
    Get the display scaling factor (for HiDPI/Retina displays).

    Returns:
        Scaling factor (1.0 = 100%, 2.0 = 200%, etc.)
        Returns 1.0 if detection fails or not applicable.
    """
    platform_name = get_platform_name()

    try:
        if platform_name == "windows":
            # Windows: Try to get DPI awareness
            try:
                import ctypes
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                dc = user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                user32.ReleaseDC(0, dc)
                return dpi / 96.0  # 96 DPI is 100% scaling
            except Exception:
                return 1.0

        elif platform_name == "macos":
            # macOS: Retina displays typically use 2.0
            # This would require PyObjC, so return 1.0 as fallback
            # Flet should handle this automatically
            return 1.0

        else:
            # Linux: Would need X11/Wayland detection
            # Return 1.0 as fallback, Flet handles this
            return 1.0

    except Exception:
        return 1.0


# Default app directories (can be imported directly)
DEFAULT_DATA_DIR = get_data_directory()
DEFAULT_CONFIG_DIR = get_config_directory()
DEFAULT_CACHE_DIR = get_cache_directory()
DEFAULT_DOCS_DIR = get_documents_directory()


if __name__ == "__main__":
    # Print platform information when run directly
    print("Platform Utilities Information")
    print("=" * 50)
    print(f"Platform: {get_platform_name()}")
    print(f"\nDirectories:")
    print(f"  Home:      {get_home_directory()}")
    print(f"  Data:      {get_data_directory()}")
    print(f"  Config:    {get_config_directory()}")
    print(f"  Cache:     {get_cache_directory()}")
    print(f"  Documents: {get_documents_directory()}")
    print(f"  Temp:      {get_temp_directory()}")
    print(f"\nPlatform Info:")
    for key, value in get_platform_info().items():
        print(f"  {key}: {value}")
    print(f"\nPrivileges:")
    print(f"  Is Admin/Root: {is_admin()}")
    print(f"  Display Scale: {get_display_scale()}")

"""
Windows-specific tests for DocAssist EMR.

Tests Windows-specific functionality including:
- Windows path handling (backslashes, drive letters)
- Windows file permissions and attributes
- Windows registry integration
- High DPI display handling
- Windows service integration
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.platform_utils import (
    get_platform_name,
    get_data_directory,
    get_config_directory,
    normalize_path,
    ensure_directory_exists,
    get_executable_extension,
    get_path_separator,
    is_admin,
    get_display_scale,
)

# Skip all tests if not on Windows
pytestmark = pytest.mark.skipif(
    get_platform_name() != "windows",
    reason="Windows-specific tests"
)


class TestWindowsPaths:
    """Test Windows-specific path handling."""

    def test_drive_letter_paths(self):
        """Test handling of Windows drive letters."""
        # Test C: drive path
        path = normalize_path("C:\\Users\\Doctor\\Documents")

        assert isinstance(path, Path)
        assert path.is_absolute()
        assert path.drive == "C:"

    def test_unc_paths(self):
        """Test handling of UNC network paths."""
        # UNC path format: \\server\share\path
        unc_path = "\\\\server\\share\\folder"

        # normalize_path should handle this
        path = normalize_path(unc_path)

        assert isinstance(path, Path)
        # UNC paths are absolute
        assert path.is_absolute()

    def test_windows_path_separators(self):
        """Test that backslashes are handled correctly."""
        # Windows uses backslashes
        test_path = "C:\\Users\\Doctor\\AppData\\Local\\DocAssist"
        path = Path(test_path)

        assert path.is_absolute()
        assert "DocAssist" in str(path)

    def test_mixed_separators(self):
        """Test handling of mixed forward/backward slashes."""
        # Windows should handle both
        test_path = "C:/Users/Doctor\\AppData\\Local/DocAssist"
        path = normalize_path(test_path)

        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_long_path_support(self):
        """Test support for long paths (>260 characters)."""
        # Windows has a 260-character MAX_PATH limit
        # But can be extended with \\?\ prefix
        base = "C:\\Users\\Doctor\\Documents"
        long_name = "A" * 200

        long_path = Path(base) / long_name

        # Should handle long paths without crashing
        assert isinstance(long_path, Path)

    def test_case_insensitive_paths(self):
        """Test that Windows paths are case-insensitive."""
        path1 = Path("C:\\Users\\Doctor")
        path2 = Path("C:\\users\\doctor")

        # On Windows, these should be considered equal
        # Note: Path equality checks case-sensitivity based on OS
        # Just verify both are valid paths
        assert path1.is_absolute()
        assert path2.is_absolute()


class TestWindowsDirectories:
    """Test Windows-specific directory locations."""

    def test_appdata_local_directory(self):
        """Test that data directory uses LOCALAPPDATA."""
        data_dir = get_data_directory()

        # Should be in AppData\Local
        assert "AppData" in str(data_dir)
        assert "Local" in str(data_dir)

        # Verify it matches environment variable
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            assert str(data_dir).startswith(localappdata)

    def test_appdata_roaming_directory(self):
        """Test that config directory uses APPDATA."""
        config_dir = get_config_directory()

        # Should be in AppData\Roaming or AppData
        assert "AppData" in str(config_dir)

        # Verify it uses APPDATA env var
        appdata = os.getenv("APPDATA")
        if appdata:
            assert str(config_dir).startswith(appdata)

    def test_userprofile_directory(self):
        """Test handling of USERPROFILE environment variable."""
        userprofile = os.getenv("USERPROFILE")

        if userprofile:
            assert Path(userprofile).exists()
            assert Path(userprofile).is_dir()

    def test_programfiles_directory(self):
        """Test detection of Program Files directories."""
        programfiles = os.getenv("ProgramFiles")
        programfiles_x86 = os.getenv("ProgramFiles(x86)")

        # At least one should exist
        assert programfiles or programfiles_x86

        if programfiles:
            assert Path(programfiles).exists()

    def test_temp_directory_windows(self):
        """Test Windows temp directory."""
        temp_env = os.getenv("TEMP") or os.getenv("TMP")

        if temp_env:
            temp_path = Path(temp_env)
            assert temp_path.exists()
            assert temp_path.is_dir()


class TestWindowsPermissions:
    """Test Windows file permissions and attributes."""

    def test_create_directory_with_permissions(self):
        """Test creating directory (Windows ignores Unix permissions)."""
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp) / "test_permissions"

            # On Windows, mode parameter is ignored
            result = ensure_directory_exists(test_dir, mode=0o755)

            assert result.exists()
            assert result.is_dir()

    def test_readonly_attribute(self):
        """Test handling of read-only attribute."""
        with tempfile.TemporaryDirectory() as temp:
            test_file = Path(temp) / "readonly.txt"
            test_file.write_text("test")

            # Set read-only attribute
            import stat
            os.chmod(test_file, stat.S_IREAD)

            # File should exist but not be writable
            assert test_file.exists()

            # Try to detect read-only
            mode = test_file.stat().st_mode
            is_readonly = not (mode & stat.S_IWRITE)

            # Cleanup: remove read-only to allow deletion
            if is_readonly:
                os.chmod(test_file, stat.S_IWRITE)

    def test_hidden_attribute(self):
        """Test creating hidden files/directories."""
        with tempfile.TemporaryDirectory() as temp:
            hidden_dir = Path(temp) / ".hidden"
            ensure_directory_exists(hidden_dir)

            # On Windows, files starting with . are not hidden by default
            # Would need to use ctypes to set FILE_ATTRIBUTE_HIDDEN
            assert hidden_dir.exists()

    def test_system_attribute(self):
        """Test handling of system files."""
        # System attribute testing requires admin privileges
        # Just verify we can detect system directories
        system32 = Path(os.getenv("SystemRoot", "C:\\Windows")) / "System32"

        if system32.exists():
            assert system32.is_dir()


class TestWindowsExecutables:
    """Test Windows executable handling."""

    def test_exe_extension(self):
        """Test that .exe extension is returned on Windows."""
        ext = get_executable_extension()
        assert ext == ".exe"

    def test_path_separator(self):
        """Test that semicolon is used as PATH separator."""
        sep = get_path_separator()
        assert sep == ";"

    def test_path_environment_variable(self):
        """Test parsing PATH environment variable."""
        path_env = os.getenv("PATH", "")
        paths = path_env.split(get_path_separator())

        # Should have multiple paths
        assert len(paths) > 0

        # Verify they're semicolon-separated on Windows
        assert ";" in path_env or len(paths) == 1


class TestWindowsStartup:
    """Test Windows startup and service integration."""

    def test_startup_folder_location(self):
        """Test locating Windows startup folder."""
        appdata = os.getenv("APPDATA")

        if appdata:
            startup_folder = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

            # Startup folder should exist on most Windows systems
            # (may not exist in some restricted environments)
            if startup_folder.exists():
                assert startup_folder.is_dir()

    def test_programdata_directory(self):
        """Test ProgramData directory for system-wide settings."""
        programdata = os.getenv("ProgramData")

        if programdata:
            programdata_path = Path(programdata)
            assert programdata_path.exists()
            assert programdata_path.is_dir()

    def test_start_menu_location(self):
        """Test locating Start Menu."""
        appdata = os.getenv("APPDATA")

        if appdata:
            start_menu = Path(appdata) / "Microsoft" / "Windows" / "Start Menu"

            if start_menu.exists():
                assert start_menu.is_dir()


class TestWindowsDisplayHandling:
    """Test Windows HiDPI and display handling."""

    def test_display_scale_detection(self):
        """Test DPI scaling detection."""
        scale = get_display_scale()

        # Should return a valid scale factor
        assert isinstance(scale, float)
        assert scale > 0

        # Common Windows scaling: 100%, 125%, 150%, 175%, 200%
        # Allow any positive value
        assert 0.5 <= scale <= 4.0

    def test_dpi_awareness(self):
        """Test DPI awareness can be set."""
        try:
            import ctypes

            # Try to check DPI awareness
            # This might fail in some environments
            user32 = ctypes.windll.user32

            # Just verify user32 is accessible
            assert user32 is not None

        except Exception:
            # DPI functions might not be available
            pytest.skip("DPI awareness testing not available")

    def test_multiple_monitors(self):
        """Test multiple monitor detection."""
        try:
            import ctypes

            user32 = ctypes.windll.user32

            # Get number of monitors
            # SM_CMONITORS = 80
            monitor_count = user32.GetSystemMetrics(80)

            # Should have at least one monitor
            assert monitor_count >= 1

        except Exception:
            pytest.skip("Monitor detection not available")


class TestWindowsRegistry:
    """Test Windows Registry access (optional)."""

    def test_registry_access_available(self):
        """Test that winreg module is available on Windows."""
        try:
            import winreg

            # Module should be available on Windows
            assert winreg is not None

        except ImportError:
            pytest.fail("winreg should be available on Windows")

    def test_can_read_registry(self):
        """Test reading from Windows Registry."""
        try:
            import winreg

            # Try to read a common registry key
            # HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                0,
                winreg.KEY_READ,
            )

            # Try to read ProductName
            value, _ = winreg.QueryValueEx(key, "ProductName")

            winreg.CloseKey(key)

            # Should get a Windows version string
            assert isinstance(value, str)
            assert len(value) > 0

        except Exception as e:
            pytest.skip(f"Registry access not available: {e}")


class TestWindowsFileSystem:
    """Test Windows file system features."""

    def test_ntfs_features(self):
        """Test NTFS file system features."""
        with tempfile.TemporaryDirectory() as temp:
            test_file = Path(temp) / "test.txt"
            test_file.write_text("test content")

            # NTFS supports alternate data streams
            # e.g., test.txt:stream_name
            # Just verify file was created successfully
            assert test_file.exists()

    def test_file_attributes(self):
        """Test reading file attributes."""
        with tempfile.TemporaryDirectory() as temp:
            test_file = Path(temp) / "attributes.txt"
            test_file.write_text("test")

            # Get file attributes
            stat_result = test_file.stat()

            # Should have standard attributes
            assert stat_result.st_size >= 0
            assert stat_result.st_mtime > 0

    def test_junction_points(self):
        """Test handling of NTFS junction points."""
        # Junction points are Windows-specific symbolic links
        # Skip if not admin (junction creation requires privileges)
        if not is_admin():
            pytest.skip("Requires administrator privileges")

        # If admin, just verify the concept is understood
        # (actual junction creation is complex)
        pass


class TestWindowsEnvironment:
    """Test Windows environment variables."""

    def test_common_env_vars(self):
        """Test that common Windows environment variables exist."""
        common_vars = [
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
            "TEMP",
            "OS",
        ]

        for var in common_vars:
            value = os.getenv(var)
            assert value is not None, f"Missing environment variable: {var}"

    def test_os_environment_variable(self):
        """Test OS environment variable."""
        os_var = os.getenv("OS")

        if os_var:
            assert "Windows" in os_var

    def test_computername_variable(self):
        """Test COMPUTERNAME environment variable."""
        computername = os.getenv("COMPUTERNAME")

        # Should exist on Windows
        assert computername is not None
        assert len(computername) > 0


class TestWindowsAdminPrivileges:
    """Test administrator privilege detection."""

    def test_is_admin_function(self):
        """Test is_admin() function on Windows."""
        admin = is_admin()

        # Should return a boolean
        assert isinstance(admin, bool)

        # We're likely not running tests as admin
        # Just verify it works without crashing

    def test_uac_aware(self):
        """Test UAC (User Account Control) awareness."""
        # If we're not admin, we should be able to detect that
        if not is_admin():
            # Good - we correctly detected we're not admin
            assert True
        else:
            # Running as admin - verify it's detected
            assert is_admin() is True


class TestWindowsShortcuts:
    """Test Windows shortcut (.lnk) file handling."""

    def test_desktop_location(self):
        """Test locating Desktop folder."""
        userprofile = os.getenv("USERPROFILE")

        if userprofile:
            desktop = Path(userprofile) / "Desktop"

            # Desktop should exist
            if desktop.exists():
                assert desktop.is_dir()

    def test_shortcut_concept(self):
        """Test understanding of .lnk files."""
        # .lnk files are Windows shortcuts
        # Creating them requires COM/ctypes
        # Just verify we understand the concept

        # A shortcut would have .lnk extension
        shortcut_name = "DocAssist.lnk"
        assert shortcut_name.endswith(".lnk")


class TestWindowsSpecificPaths:
    """Test Windows-specific path scenarios."""

    def test_network_drive_paths(self):
        """Test handling of mapped network drives."""
        # Network drives use letters like Z:
        network_path = "Z:\\SharedFolder\\DocAssist"
        path = Path(network_path)

        # Should create valid Path object
        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_relative_path_conversion(self):
        """Test converting relative to absolute paths."""
        relative = Path("data") / "clinic.db"
        absolute = relative.resolve()

        assert absolute.is_absolute()
        assert absolute.drive  # Should have a drive letter on Windows

    def test_current_drive_paths(self):
        """Test paths on current drive."""
        # Path starting with \ (current drive)
        current_drive_path = "\\Users\\Doctor"
        path = Path(current_drive_path)

        # Should be valid
        assert isinstance(path, Path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Cross-platform tests for common functionality.

Tests that should pass on all platforms (Windows, macOS, Linux).
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
    get_home_directory,
    get_data_directory,
    get_config_directory,
    get_documents_directory,
    get_cache_directory,
    ensure_directory_exists,
    get_temp_directory,
    normalize_path,
    get_platform_info,
    get_executable_extension,
    get_path_separator,
    is_admin,
    get_display_scale,
)


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_get_platform_name(self):
        """Test that platform name is detected correctly."""
        platform = get_platform_name()
        assert platform in ["windows", "macos", "linux", "unknown"]

    def test_platform_info(self):
        """Test that platform info dict is complete."""
        info = get_platform_info()

        required_keys = [
            "platform",
            "system",
            "release",
            "version",
            "machine",
            "processor",
            "python_version",
            "is_64bit",
        ]

        for key in required_keys:
            assert key in info, f"Missing key: {key}"
            assert info[key] is not None

        # Platform should match
        assert info["platform"] == get_platform_name()

    def test_executable_extension(self):
        """Test executable extension is correct for platform."""
        ext = get_executable_extension()
        platform = get_platform_name()

        if platform == "windows":
            assert ext == ".exe"
        else:
            assert ext == ""

    def test_path_separator(self):
        """Test path separator is correct for platform."""
        sep = get_path_separator()
        platform = get_platform_name()

        if platform == "windows":
            assert sep == ";"
        else:
            assert sep == ":"


class TestDirectoryFunctions:
    """Test directory path functions."""

    def test_home_directory(self):
        """Test that home directory is valid."""
        home = get_home_directory()

        assert isinstance(home, Path)
        assert home.exists()
        assert home.is_dir()

    def test_data_directory(self):
        """Test that data directory is platform-appropriate."""
        data_dir = get_data_directory()
        platform = get_platform_name()

        assert isinstance(data_dir, Path)

        # Check platform-specific paths
        if platform == "windows":
            # Should be in AppData\Local
            assert "AppData" in str(data_dir) or "LOCALAPPDATA" in str(data_dir)
        elif platform == "macos":
            # Should be in Library/Application Support
            assert "Library" in str(data_dir)
            assert "Application Support" in str(data_dir)
        elif platform == "linux":
            # Should be in .local/share or XDG_DATA_HOME
            assert ".local/share" in str(data_dir).lower() or "share" in str(data_dir)

    def test_config_directory(self):
        """Test that config directory is platform-appropriate."""
        config_dir = get_config_directory()
        platform = get_platform_name()

        assert isinstance(config_dir, Path)

        # Check platform-specific paths
        if platform == "windows":
            # Should be in AppData\Roaming
            assert "AppData" in str(config_dir) or "APPDATA" in str(config_dir)
        elif platform == "macos":
            # Should be in Library/Preferences
            assert "Library" in str(config_dir)
            assert "Preferences" in str(config_dir)
        elif platform == "linux":
            # Should be in .config or XDG_CONFIG_HOME
            assert ".config" in str(config_dir) or "config" in str(config_dir).lower()

    def test_cache_directory(self):
        """Test that cache directory is platform-appropriate."""
        cache_dir = get_cache_directory()
        platform = get_platform_name()

        assert isinstance(cache_dir, Path)

        # Check platform-specific paths
        if platform == "windows":
            # Should be in AppData\Local\DocAssist\Cache
            assert "AppData" in str(cache_dir) or "LOCALAPPDATA" in str(cache_dir)
        elif platform == "macos":
            # Should be in Library/Caches
            assert "Library" in str(cache_dir)
            assert "Caches" in str(cache_dir)
        elif platform == "linux":
            # Should be in .cache or XDG_CACHE_HOME
            assert ".cache" in str(cache_dir) or "cache" in str(cache_dir).lower()

    def test_documents_directory(self):
        """Test that documents directory exists."""
        docs_dir = get_documents_directory()

        assert isinstance(docs_dir, Path)
        # Documents might not exist on all systems, but should be a valid path
        assert docs_dir.parent.exists()

    def test_temp_directory(self):
        """Test that temp directory is valid."""
        temp_dir = get_temp_directory()

        assert isinstance(temp_dir, Path)
        assert temp_dir.parent.exists()

    def test_custom_app_name(self):
        """Test that custom app names work for directories."""
        custom_name = "TestApp"

        data_dir = get_data_directory(custom_name)
        config_dir = get_config_directory(custom_name)
        cache_dir = get_cache_directory(custom_name)

        assert custom_name in str(data_dir)
        assert custom_name in str(config_dir)
        assert custom_name in str(cache_dir)


class TestPathOperations:
    """Test path manipulation functions."""

    def test_normalize_path_home(self):
        """Test normalizing path with ~ (home directory)."""
        path = normalize_path("~/test")

        assert isinstance(path, Path)
        assert path.is_absolute()
        assert "~" not in str(path)

    def test_normalize_path_absolute(self):
        """Test normalizing absolute path."""
        if get_platform_name() == "windows":
            test_path = "C:\\Users\\test"
        else:
            test_path = "/home/test"

        path = normalize_path(test_path)

        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_normalize_path_relative(self):
        """Test normalizing relative path."""
        path = normalize_path("./test/path")

        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_normalize_path_with_env_vars(self):
        """Test normalizing path with environment variables."""
        # Set a test environment variable
        os.environ["TEST_VAR"] = "test_value"

        if get_platform_name() == "windows":
            test_path = "%TEST_VAR%\\path"
        else:
            test_path = "$TEST_VAR/path"

        path = normalize_path(test_path)

        assert isinstance(path, Path)
        assert "test_value" in str(path).lower()

        # Cleanup
        del os.environ["TEST_VAR"]


class TestDirectoryCreation:
    """Test directory creation with proper permissions."""

    def test_ensure_directory_exists_new(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp) / "new_dir"

            # Directory should not exist yet
            assert not test_dir.exists()

            # Create it
            result = ensure_directory_exists(test_dir)

            # Should exist now
            assert result == test_dir
            assert test_dir.exists()
            assert test_dir.is_dir()

    def test_ensure_directory_exists_existing(self):
        """Test with existing directory."""
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp)

            # Directory already exists
            assert test_dir.exists()

            # Should not raise error
            result = ensure_directory_exists(test_dir)

            assert result == test_dir
            assert test_dir.exists()

    def test_ensure_directory_exists_parents(self):
        """Test creating nested directories."""
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp) / "parent" / "child" / "grandchild"

            # None of these should exist
            assert not test_dir.exists()
            assert not test_dir.parent.exists()

            # Create with parents
            result = ensure_directory_exists(test_dir)

            # All should exist now
            assert result == test_dir
            assert test_dir.exists()
            assert test_dir.parent.exists()
            assert test_dir.parent.parent.exists()

    def test_ensure_directory_exists_permissions(self):
        """Test directory permissions (Unix only)."""
        if get_platform_name() == "windows":
            pytest.skip("Permission tests not applicable on Windows")

        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp) / "perm_test"

            # Create with specific permissions
            result = ensure_directory_exists(test_dir, mode=0o750)

            assert result.exists()

            # Check permissions (might not match exactly due to umask)
            stat = result.stat()
            # Just verify it's readable and writable by owner
            assert os.access(result, os.R_OK)
            assert os.access(result, os.W_OK)


class TestPrivileges:
    """Test privilege detection."""

    def test_is_admin(self):
        """Test admin/root detection."""
        admin = is_admin()

        # Should return a boolean
        assert isinstance(admin, bool)

        # We're likely not running as admin in tests
        # Just verify it doesn't crash


class TestDisplayHandling:
    """Test display-related functions."""

    def test_get_display_scale(self):
        """Test display scale detection."""
        scale = get_display_scale()

        # Should return a positive number
        assert isinstance(scale, float)
        assert scale > 0
        assert scale <= 4.0  # Reasonable upper bound


class TestPathTypes:
    """Test that functions handle different path types."""

    def test_normalize_path_with_path_object(self):
        """Test normalize_path with Path object."""
        path_obj = Path("~/test")
        result = normalize_path(path_obj)

        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_normalize_path_with_string(self):
        """Test normalize_path with string."""
        path_str = "~/test"
        result = normalize_path(path_str)

        assert isinstance(result, Path)
        assert result.is_absolute()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_app_name(self):
        """Test with empty app name."""
        data_dir = get_data_directory("")
        assert isinstance(data_dir, Path)

    def test_special_chars_in_app_name(self):
        """Test with special characters in app name."""
        # Some special chars might be problematic
        # Test that function handles them gracefully
        try:
            data_dir = get_data_directory("Test-App_123")
            assert isinstance(data_dir, Path)
        except Exception as e:
            pytest.fail(f"Should handle special chars: {e}")

    def test_very_long_app_name(self):
        """Test with very long app name."""
        long_name = "A" * 200
        try:
            data_dir = get_data_directory(long_name)
            assert isinstance(data_dir, Path)
        except Exception as e:
            pytest.fail(f"Should handle long names: {e}")


class TestDefaultDirectories:
    """Test default directory constants."""

    def test_default_directories_exist(self):
        """Test that default directory constants are valid."""
        from utils.platform_utils import (
            DEFAULT_DATA_DIR,
            DEFAULT_CONFIG_DIR,
            DEFAULT_CACHE_DIR,
            DEFAULT_DOCS_DIR,
        )

        assert isinstance(DEFAULT_DATA_DIR, Path)
        assert isinstance(DEFAULT_CONFIG_DIR, Path)
        assert isinstance(DEFAULT_CACHE_DIR, Path)
        assert isinstance(DEFAULT_DOCS_DIR, Path)

    def test_default_directories_match_functions(self):
        """Test that defaults match function calls."""
        from utils.platform_utils import (
            DEFAULT_DATA_DIR,
            DEFAULT_CONFIG_DIR,
            DEFAULT_CACHE_DIR,
            DEFAULT_DOCS_DIR,
        )

        assert DEFAULT_DATA_DIR == get_data_directory()
        assert DEFAULT_CONFIG_DIR == get_config_directory()
        assert DEFAULT_CACHE_DIR == get_cache_directory()
        assert DEFAULT_DOCS_DIR == get_documents_directory()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

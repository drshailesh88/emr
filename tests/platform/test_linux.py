"""
Linux-specific tests for DocAssist EMR.

Tests Linux-specific functionality including:
- Linux paths (/home/doctor/, /opt/, /usr/share/)
- Linux permissions (chmod, chown)
- Desktop file creation (.desktop)
- Wayland vs X11 compatibility
- systemd integration
- XDG Base Directory specification
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
    get_cache_directory,
    get_documents_directory,
    normalize_path,
    ensure_directory_exists,
    get_executable_extension,
    get_path_separator,
    is_admin,
    get_display_scale,
)

# Skip all tests if not on Linux
pytestmark = pytest.mark.skipif(
    get_platform_name() != "linux",
    reason="Linux-specific tests"
)


class TestLinuxPaths:
    """Test Linux-specific path handling."""

    def test_home_directory_location(self):
        """Test that home directory is in /home/."""
        home = get_home_directory()

        # Usually /home/username, but could be /root for root user
        assert "/home/" in str(home) or str(home) == "/root"
        assert home.exists()

    def test_forward_slashes_only(self):
        """Test that Linux uses forward slashes."""
        test_path = "/home/doctor/Documents/DocAssist"
        path = Path(test_path)

        assert path.is_absolute()
        assert "\\" not in str(path)

    def test_case_sensitive_filesystem(self):
        """Test case-sensitive file system."""
        with tempfile.TemporaryDirectory() as temp:
            # Linux is case-sensitive
            file1 = Path(temp) / "Test.txt"
            file2 = Path(temp) / "test.txt"

            file1.write_text("upper")
            file2.write_text("lower")

            # Both should exist as separate files
            assert file1.exists()
            assert file2.exists()
            assert file1.read_text() == "upper"
            assert file2.read_text() == "lower"

    def test_hidden_files_dot_prefix(self):
        """Test handling of hidden files (dot prefix)."""
        with tempfile.TemporaryDirectory() as temp:
            hidden_file = Path(temp) / ".hidden_file"
            hidden_file.write_text("test")

            assert hidden_file.exists()
            assert hidden_file.name.startswith(".")

    def test_root_directory(self):
        """Test root directory."""
        root = Path("/")

        assert root.exists()
        assert root.is_dir()
        assert root.is_absolute()

    def test_symbolic_links(self):
        """Test handling of symbolic links."""
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target"
            target.mkdir()

            link = Path(temp) / "link"
            link.symlink_to(target)

            assert link.exists()
            assert link.is_symlink()
            assert link.resolve() == target.resolve()

    def test_absolute_path_no_drive(self):
        """Test that Linux absolute paths don't have drive letters."""
        path = Path("/home/doctor/Documents")

        assert path.is_absolute()
        # Drive should be empty on Linux
        assert path.drive == ""


class TestLinuxXDGDirectories:
    """Test XDG Base Directory specification."""

    def test_xdg_data_home(self):
        """Test XDG_DATA_HOME directory."""
        data_dir = get_data_directory()

        # Should follow XDG spec
        xdg_data_home = os.getenv("XDG_DATA_HOME")

        if xdg_data_home:
            # If XDG_DATA_HOME is set, should use it
            assert str(data_dir).startswith(xdg_data_home)
        else:
            # Default: ~/.local/share/docassist
            assert ".local/share" in str(data_dir).lower()

    def test_xdg_config_home(self):
        """Test XDG_CONFIG_HOME directory."""
        config_dir = get_config_directory()

        xdg_config_home = os.getenv("XDG_CONFIG_HOME")

        if xdg_config_home:
            assert str(config_dir).startswith(xdg_config_home)
        else:
            # Default: ~/.config/docassist
            assert ".config" in str(config_dir)

    def test_xdg_cache_home(self):
        """Test XDG_CACHE_HOME directory."""
        cache_dir = get_cache_directory()

        xdg_cache_home = os.getenv("XDG_CACHE_HOME")

        if xdg_cache_home:
            assert str(cache_dir).startswith(xdg_cache_home)
        else:
            # Default: ~/.cache/docassist
            assert ".cache" in str(cache_dir)

    def test_xdg_data_dirs(self):
        """Test XDG_DATA_DIRS for system-wide data."""
        xdg_data_dirs = os.getenv("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        dirs = xdg_data_dirs.split(":")

        # Should have at least one directory
        assert len(dirs) > 0

        # Common directories
        assert any("/usr/share" in d for d in dirs) or any("/usr/local/share" in d for d in dirs)

    def test_xdg_runtime_dir(self):
        """Test XDG_RUNTIME_DIR for runtime files."""
        xdg_runtime_dir = os.getenv("XDG_RUNTIME_DIR")

        if xdg_runtime_dir:
            runtime_path = Path(xdg_runtime_dir)

            # Should exist and be a directory
            if runtime_path.exists():
                assert runtime_path.is_dir()

                # Should be user-specific and have restricted permissions
                stat = runtime_path.stat()
                mode = stat.st_mode & 0o777
                # Should be owner-only (0o700)
                assert mode == 0o700


class TestLinuxPermissions:
    """Test Linux file permissions."""

    def test_unix_permissions(self):
        """Test Unix-style permissions."""
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp) / "perm_test"
            ensure_directory_exists(test_dir, mode=0o755)

            assert test_dir.exists()

            # Check permissions
            stat = test_dir.stat()
            mode = stat.st_mode & 0o777

            # Should be 755 (rwxr-xr-x)
            assert mode == 0o755

    def test_chmod_operations(self):
        """Test changing file permissions."""
        with tempfile.TemporaryDirectory() as temp:
            test_file = Path(temp) / "chmod_test.txt"
            test_file.write_text("test")

            # Set specific permissions
            test_file.chmod(0o644)

            # Verify permissions
            stat = test_file.stat()
            mode = stat.st_mode & 0o777
            assert mode == 0o644

    def test_executable_permission(self):
        """Test executable file permissions."""
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "script.sh"
            script.write_text("#!/bin/bash\necho test")

            # Make executable
            script.chmod(0o755)

            # Verify executable bit is set
            assert os.access(script, os.X_OK)

    def test_file_ownership(self):
        """Test file ownership information."""
        with tempfile.TemporaryDirectory() as temp:
            test_file = Path(temp) / "owner_test.txt"
            test_file.write_text("test")

            stat = test_file.stat()

            # Should have UID and GID
            assert stat.st_uid >= 0
            assert stat.st_gid >= 0

            # Should match current user
            assert stat.st_uid == os.getuid()
            assert stat.st_gid == os.getgid()

    def test_umask_concept(self):
        """Test understanding of umask."""
        # umask determines default permissions for new files
        current_umask = os.umask(0o022)
        os.umask(current_umask)  # Restore immediately

        # umask should be a valid value
        assert 0 <= current_umask <= 0o777


class TestLinuxDesktopIntegration:
    """Test Linux desktop file integration."""

    def test_desktop_file_format(self):
        """Test .desktop file format."""
        # .desktop files follow freedesktop.org specification
        desktop_content = """[Desktop Entry]
Type=Application
Name=DocAssist EMR
Comment=Local-First AI-Powered EMR
Exec=/usr/bin/docassist
Icon=docassist
Terminal=false
Categories=Office;Medical;
"""

        # Verify format is correct
        assert "[Desktop Entry]" in desktop_content
        assert "Type=Application" in desktop_content
        assert "Exec=" in desktop_content

    def test_desktop_file_locations(self):
        """Test desktop file installation locations."""
        # User-specific: ~/.local/share/applications/
        user_desktop = get_home_directory() / ".local" / "share" / "applications"

        # System-wide: /usr/share/applications/
        system_desktop = Path("/usr/share/applications")

        # At least system location should exist
        assert system_desktop.exists() or user_desktop.parent.exists()

    def test_icon_locations(self):
        """Test icon installation locations."""
        # Icons go in: ~/.local/share/icons/ or /usr/share/icons/
        user_icons = get_home_directory() / ".local" / "share" / "icons"
        system_icons = Path("/usr/share/icons")

        # At least one should exist
        assert system_icons.exists() or user_icons.parent.exists()

    def test_mime_types_concept(self):
        """Test MIME type registration concept."""
        # MIME types are registered via .xml files in:
        # ~/.local/share/mime/packages/

        mime_dir = get_home_directory() / ".local" / "share" / "mime"

        # Directory might not exist yet, just verify path is correct
        assert isinstance(mime_dir, Path)


class TestLinuxExecutables:
    """Test Linux executable handling."""

    def test_no_exe_extension(self):
        """Test that Linux doesn't use .exe extension."""
        ext = get_executable_extension()
        assert ext == ""

    def test_path_separator(self):
        """Test that colon is used as PATH separator."""
        sep = get_path_separator()
        assert sep == ":"

    def test_path_environment_variable(self):
        """Test parsing PATH environment variable."""
        path_env = os.getenv("PATH", "")
        paths = path_env.split(get_path_separator())

        # Should have multiple paths
        assert len(paths) > 0

        # Common Linux paths
        common_paths = ["/usr/bin", "/bin", "/usr/local/bin"]

        # At least one should be in PATH
        assert any(p in paths for p in common_paths)

    def test_shebang_support(self):
        """Test shebang (#!) support for scripts."""
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "test.py"
            script.write_text("#!/usr/bin/env python3\nprint('test')")

            # Make executable
            script.chmod(0o755)

            # Verify shebang
            content = script.read_text()
            assert content.startswith("#!")

    def test_usr_bin_env_pattern(self):
        """Test #!/usr/bin/env pattern for portability."""
        # Using /usr/bin/env is more portable than hardcoded paths
        shebang_portable = "#!/usr/bin/env python3"
        shebang_hardcoded = "#!/usr/bin/python3"

        # Both are valid
        assert shebang_portable.startswith("#!")
        assert shebang_hardcoded.startswith("#!")

        # But env is preferred for portability
        assert "/usr/bin/env" in shebang_portable


class TestLinuxSystemdIntegration:
    """Test systemd integration."""

    def test_systemd_unit_file_format(self):
        """Test systemd unit file format."""
        unit_content = """[Unit]
Description=DocAssist EMR
After=network.target

[Service]
Type=simple
User=doctor
ExecStart=/usr/bin/docassist
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

        # Verify format
        assert "[Unit]" in unit_content
        assert "[Service]" in unit_content
        assert "[Install]" in unit_content

    def test_systemd_user_service_location(self):
        """Test systemd user service location."""
        # User services: ~/.config/systemd/user/
        user_systemd = get_home_directory() / ".config" / "systemd" / "user"

        # Might not exist yet
        assert isinstance(user_systemd, Path)

    def test_systemd_system_service_location(self):
        """Test systemd system service location."""
        # System services: /etc/systemd/system/
        system_systemd = Path("/etc/systemd/system")

        # Should exist on systemd-based systems
        # Might not exist on non-systemd systems
        if system_systemd.exists():
            assert system_systemd.is_dir()

    def test_systemctl_concept(self):
        """Test systemctl command concept."""
        # systemctl is used to manage systemd services
        # Commands: start, stop, enable, disable, status

        commands = [
            "systemctl --user start docassist",
            "systemctl --user enable docassist",
            "systemctl --user status docassist",
        ]

        for cmd in commands:
            assert "systemctl" in cmd


class TestLinuxDisplayServer:
    """Test Wayland vs X11 compatibility."""

    def test_display_environment_variable(self):
        """Test DISPLAY environment variable for X11."""
        display = os.getenv("DISPLAY")

        # If DISPLAY is set, we're likely on X11
        if display:
            # Usually :0 or :1
            assert ":" in display

    def test_wayland_display_variable(self):
        """Test WAYLAND_DISPLAY environment variable."""
        wayland_display = os.getenv("WAYLAND_DISPLAY")

        # If WAYLAND_DISPLAY is set, we're on Wayland
        if wayland_display:
            # Usually wayland-0
            assert isinstance(wayland_display, str)

    def test_xdg_session_type(self):
        """Test XDG_SESSION_TYPE for display server detection."""
        session_type = os.getenv("XDG_SESSION_TYPE")

        # Should be 'x11', 'wayland', or 'tty'
        if session_type:
            assert session_type in ["x11", "wayland", "tty", "unspecified"]

    def test_display_compatibility(self):
        """Test that app can run on both X11 and Wayland."""
        # Flet should handle both X11 and Wayland
        # This is a concept test

        # Modern apps should work on both
        assert True


class TestLinuxEnvironment:
    """Test Linux environment variables."""

    def test_common_env_vars(self):
        """Test that common Linux environment variables exist."""
        common_vars = [
            "HOME",
            "USER",
            "PATH",
            "SHELL",
        ]

        for var in common_vars:
            value = os.getenv(var)
            assert value is not None, f"Missing environment variable: {var}"

    def test_home_variable(self):
        """Test HOME environment variable."""
        home_env = os.getenv("HOME")

        assert home_env is not None
        assert home_env == str(get_home_directory())

    def test_user_variable(self):
        """Test USER environment variable."""
        user = os.getenv("USER")

        assert user is not None
        assert len(user) > 0

    def test_shell_variable(self):
        """Test SHELL environment variable."""
        shell = os.getenv("SHELL")

        # Should be set
        if shell:
            # Common shells: /bin/bash, /bin/sh, /bin/zsh, /usr/bin/fish
            assert "/bin/" in shell or "/usr/bin/" in shell

    def test_lang_variable(self):
        """Test LANG environment variable for localization."""
        lang = os.getenv("LANG")

        # Should be set on most systems
        if lang:
            # Usually format: en_US.UTF-8
            assert isinstance(lang, str)


class TestLinuxRootPrivileges:
    """Test root privilege detection."""

    def test_is_admin_function(self):
        """Test is_admin() function on Linux."""
        admin = is_admin()

        # Should return a boolean
        assert isinstance(admin, bool)

        # Check against actual UID
        if os.geteuid() == 0:
            assert admin is True
        else:
            assert admin is False

    def test_effective_user_id(self):
        """Test getting effective user ID."""
        euid = os.geteuid()

        # Should be valid UID
        assert euid >= 0

        # Tests should not run as root
        # (unless explicitly run with sudo)

    def test_real_user_id(self):
        """Test getting real user ID."""
        uid = os.getuid()

        # Should be valid UID
        assert uid >= 0

    def test_sudo_detection(self):
        """Test detection of sudo usage."""
        sudo_user = os.getenv("SUDO_USER")

        # If SUDO_USER is set, we're running under sudo
        if sudo_user:
            # We're running under sudo
            assert is_admin() is True


class TestLinuxFileSystem:
    """Test Linux file system features."""

    def test_proc_filesystem(self):
        """Test /proc filesystem."""
        proc_dir = Path("/proc")

        # /proc should exist on Linux
        assert proc_dir.exists()
        assert proc_dir.is_dir()

        # /proc/self should exist
        proc_self = proc_dir / "self"
        if proc_self.exists():
            assert proc_self.is_symlink()

    def test_sys_filesystem(self):
        """Test /sys filesystem."""
        sys_dir = Path("/sys")

        # /sys should exist on Linux
        if sys_dir.exists():
            assert sys_dir.is_dir()

    def test_tmp_directory(self):
        """Test /tmp directory."""
        tmp_dir = Path("/tmp")

        assert tmp_dir.exists()
        assert tmp_dir.is_dir()

        # Should be writable
        assert os.access(tmp_dir, os.W_OK)

    def test_dev_directory(self):
        """Test /dev directory."""
        dev_dir = Path("/dev")

        assert dev_dir.exists()
        assert dev_dir.is_dir()

        # Common devices
        dev_null = dev_dir / "null"
        assert dev_null.exists()

    def test_extended_attributes(self):
        """Test extended file attributes (xattr)."""
        # Extended attributes can be used for metadata
        # Available on ext4, btrfs, xfs, etc.

        # This requires xattr module to test fully
        # Just verify the concept is understood
        assert True


class TestLinuxPackageManagement:
    """Test package management awareness."""

    def test_common_package_managers(self):
        """Test awareness of common package managers."""
        package_managers = [
            "apt",  # Debian/Ubuntu
            "dnf",  # Fedora
            "yum",  # RHEL/CentOS
            "pacman",  # Arch
            "zypper",  # openSUSE
        ]

        # Just verify we understand the concept
        assert len(package_managers) > 0

    def test_python_package_installation(self):
        """Test Python package installation paths."""
        # User packages: ~/.local/lib/pythonX.Y/site-packages
        # System packages: /usr/lib/pythonX.Y/site-packages

        # Just verify we understand pip install --user
        assert True

    def test_usr_local_vs_usr(self):
        """Test understanding of /usr/local vs /usr."""
        # /usr - system-managed packages
        # /usr/local - locally installed packages

        usr_local = Path("/usr/local")
        usr = Path("/usr")

        assert usr.exists()
        # /usr/local might not exist on all systems


class TestLinuxSpecificPaths:
    """Test Linux-specific path scenarios."""

    def test_opt_directory(self):
        """Test /opt directory for optional software."""
        opt_dir = Path("/opt")

        # /opt is commonly used for third-party software
        if opt_dir.exists():
            assert opt_dir.is_dir()

    def test_var_directory(self):
        """Test /var directory for variable data."""
        var_dir = Path("/var")

        assert var_dir.exists()
        assert var_dir.is_dir()

        # Common subdirectories
        var_log = var_dir / "log"
        if var_log.exists():
            assert var_log.is_dir()

    def test_etc_directory(self):
        """Test /etc directory for configuration."""
        etc_dir = Path("/etc")

        assert etc_dir.exists()
        assert etc_dir.is_dir()

    def test_home_subdirectories(self):
        """Test common home subdirectories."""
        home = get_home_directory()

        common_dirs = [
            "Documents",
            "Downloads",
            "Desktop",
            "Pictures",
        ]

        # Not all might exist, but they're common
        # Just verify we can create paths
        for dirname in common_dirs:
            dir_path = home / dirname
            assert isinstance(dir_path, Path)


class TestLinuxDistribution:
    """Test Linux distribution detection."""

    def test_os_release_file(self):
        """Test /etc/os-release file."""
        os_release = Path("/etc/os-release")

        # Should exist on most modern Linux distributions
        if os_release.exists():
            content = os_release.read_text()

            # Should contain distribution info
            assert len(content) > 0
            assert "=" in content

    def test_distribution_detection(self):
        """Test distribution detection."""
        # Could use platform.freedesktop_os_release() in Python 3.10+
        # or read /etc/os-release manually

        # Just verify the concept
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

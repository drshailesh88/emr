"""Tests for the sync service."""

import pytest
import tempfile
from pathlib import Path

from src.services.sync import (
    LocalStorageBackend, SyncService, SyncStatus,
    create_device_id, get_or_create_device_id
)


class TestLocalStorageBackend:
    """Tests for LocalStorageBackend."""

    @pytest.fixture
    def backend(self):
        """Create a temporary local storage backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LocalStorageBackend(Path(tmpdir))

    @pytest.fixture
    def test_file(self):
        """Create a temporary test file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Test file contents for upload")
            yield Path(f.name)
            Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def large_test_file(self):
        """Create a larger test file for progress callback testing."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write 1MB to ensure progress callbacks are triggered
            f.write(b"X" * (1024 * 1024))
            yield Path(f.name)
            Path(f.name).unlink(missing_ok=True)

    def test_upload_and_download(self, backend, test_file):
        """Test uploading and downloading a file."""
        remote_key = "test/file.txt"

        # Upload
        success = backend.upload(test_file, remote_key)
        assert success

        # Verify exists
        assert backend.exists(remote_key)

        # Download to new location
        with tempfile.NamedTemporaryFile(delete=False) as f:
            download_path = Path(f.name)

        success = backend.download(remote_key, download_path)
        assert success

        # Verify contents
        assert download_path.read_bytes() == test_file.read_bytes()
        download_path.unlink()

    def test_delete(self, backend, test_file):
        """Test deleting a file."""
        remote_key = "test/to_delete.txt"

        backend.upload(test_file, remote_key)
        assert backend.exists(remote_key)

        success = backend.delete(remote_key)
        assert success
        assert not backend.exists(remote_key)

    def test_list_files(self, backend, test_file):
        """Test listing files."""
        # Upload multiple files
        backend.upload(test_file, "backups/file1.zip")
        backend.upload(test_file, "backups/file2.zip")
        backend.upload(test_file, "other/file3.txt")

        # List all
        all_files = backend.list_files()
        assert len(all_files) == 3

        # List with prefix
        backup_files = backend.list_files("backups/")
        assert len(backup_files) == 2

    def test_get_metadata(self, backend, test_file):
        """Test getting file metadata."""
        remote_key = "test/metadata.txt"
        backend.upload(test_file, remote_key)

        metadata = backend.get_metadata(remote_key)
        assert metadata is not None
        assert metadata['key'] == remote_key
        assert metadata['size'] == test_file.stat().st_size
        assert 'modified' in metadata

    def test_progress_callback(self, backend, large_test_file):
        """Test upload progress callback with large file."""
        remote_key = "test/progress.txt"
        progress_calls = []

        def callback(transferred, total):
            progress_calls.append((transferred, total))

        backend.upload(large_test_file, remote_key, progress_callback=callback)

        assert len(progress_calls) > 0
        # Last call should show complete
        assert progress_calls[-1][0] == progress_calls[-1][1]


class TestSyncService:
    """Tests for SyncService."""

    @pytest.fixture
    def sync_setup(self):
        """Create sync service with local backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            storage_dir = tmpdir / "storage"
            backup_dir = tmpdir / "backups"
            storage_dir.mkdir()
            backup_dir.mkdir()

            backend = LocalStorageBackend(storage_dir)
            sync = SyncService(backend, backup_dir)

            yield sync, backup_dir

    @pytest.fixture
    def test_backup(self, sync_setup):
        """Create a test backup file."""
        sync, backup_dir = sync_setup
        backup_path = backup_dir / "backup_2024-01-15_10-30-00.zip"
        backup_path.write_bytes(b"Test backup contents")
        return backup_path

    def test_upload_backup(self, sync_setup, test_backup):
        """Test uploading a backup."""
        sync, _ = sync_setup

        success = sync.upload_backup(test_backup)
        assert success

        # Check status
        status = sync.get_status()
        assert status.status == SyncStatus.COMPLETE

    def test_download_backup(self, sync_setup, test_backup):
        """Test downloading a backup."""
        sync, backup_dir = sync_setup

        # First upload
        sync.upload_backup(test_backup)

        # Then download
        remote_key = f"backups/{test_backup.name}"
        downloaded = sync.download_backup(remote_key)

        assert downloaded is not None
        assert downloaded.exists()
        assert downloaded.read_bytes() == test_backup.read_bytes()

    def test_list_cloud_backups(self, sync_setup, test_backup):
        """Test listing cloud backups."""
        sync, _ = sync_setup

        # Upload
        sync.upload_backup(test_backup)

        # List
        backups = sync.list_cloud_backups()
        assert len(backups) == 1
        assert backups[0]['key'].endswith('.zip')

    def test_progress_callback(self, sync_setup, test_backup):
        """Test sync progress callback."""
        sync, backup_dir = sync_setup
        progress_updates = []

        def callback(progress):
            progress_updates.append(progress)

        sync.progress_callback = callback
        sync.upload_backup(test_backup)

        assert len(progress_updates) > 0
        # Should end with complete
        assert progress_updates[-1].status == SyncStatus.COMPLETE


class TestDeviceId:
    """Tests for device ID generation."""

    def test_create_device_id(self):
        """Test device ID creation."""
        device_id = create_device_id()

        assert device_id.startswith("device-")
        assert len(device_id) > 10

    def test_device_id_consistent(self):
        """Device ID should be consistent for same machine."""
        id1 = create_device_id()
        id2 = create_device_id()

        assert id1 == id2

    def test_get_or_create_device_id(self):
        """Test get_or_create_device_id persists ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # First call creates
            id1 = get_or_create_device_id(config_dir)
            assert id1.startswith("device-")

            # Second call retrieves same ID
            id2 = get_or_create_device_id(config_dir)
            assert id1 == id2

            # File should exist
            device_file = config_dir / ".device_id"
            assert device_file.exists()

"""Tests for the backup scheduler service."""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class MockBackupService:
    """Mock backup service for testing."""

    def __init__(self):
        self.backup_count = 0
        self.last_backup_time = None
        self.auto_backup_called = False
        self.sync_called = False

    def create_backup(self, encrypt=False, password=None):
        self.backup_count += 1
        self.last_backup_time = datetime.now()
        return f"/tmp/backup_{self.backup_count}.zip"

    def auto_backup(self, encrypt=False, password=None):
        self.auto_backup_called = True
        self.backup_count += 1
        self.last_backup_time = datetime.now()
        return True

    def get_last_backup_time(self):
        return self.last_backup_time

    def sync_to_cloud(self, password=None, backend_config=None):
        self.sync_called = True
        return True


class MockDatabaseService:
    """Mock database service for change detection."""

    def __init__(self):
        self.has_changes = True

    def has_changes_since(self, timestamp):
        return self.has_changes


class TestBackupScheduler:
    """Tests for BackupScheduler."""

    @pytest.fixture
    def backup_service(self):
        """Create mock backup service."""
        return MockBackupService()

    @pytest.fixture
    def database_service(self):
        """Create mock database service."""
        return MockDatabaseService()

    @pytest.fixture
    def scheduler(self, backup_service, database_service):
        """Create scheduler with mocks."""
        from src.services.scheduler import BackupScheduler
        return BackupScheduler(
            backup_service=backup_service,
            database_service=database_service,
            settings_dict={
                'auto_backup_enabled': True,
                'backup_frequency_hours': 4,
                'backup_on_close': True,
                'cloud_sync_enabled': False,
            }
        )

    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initializes with correct defaults."""
        assert scheduler.enabled is True
        assert scheduler.frequency_hours == 4
        assert scheduler.backup_on_close_enabled is True
        assert scheduler.cloud_sync_enabled is False
        assert scheduler._running is False

    def test_scheduler_initialization_with_custom_settings(self, backup_service):
        """Test scheduler with custom settings."""
        from src.services.scheduler import BackupScheduler

        scheduler = BackupScheduler(
            backup_service=backup_service,
            settings_dict={
                'auto_backup_enabled': False,
                'backup_frequency_hours': 12,
                'backup_on_close': False,
                'cloud_sync_enabled': True,
            }
        )

        assert scheduler.enabled is False
        assert scheduler.frequency_hours == 12
        assert scheduler.backup_on_close_enabled is False
        assert scheduler.cloud_sync_enabled is True

    def test_scheduler_start_stop(self, scheduler):
        """Test starting and stopping scheduler."""
        scheduler.start()
        assert scheduler._running is True
        assert scheduler._thread is not None
        assert scheduler._thread.is_alive()

        scheduler.stop()
        assert scheduler._running is False
        time.sleep(0.1)  # Allow thread to stop

    def test_scheduler_disabled(self, backup_service):
        """Test scheduler doesn't start when disabled."""
        from src.services.scheduler import BackupScheduler

        scheduler = BackupScheduler(
            backup_service=backup_service,
            settings_dict={'auto_backup_enabled': False}
        )

        scheduler.start()
        assert scheduler._running is False
        assert scheduler._thread is None

    def test_set_frequency(self, scheduler):
        """Test changing backup frequency."""
        scheduler.set_frequency(12)
        assert scheduler.frequency_hours == 12

        scheduler.set_frequency(24)
        assert scheduler.frequency_hours == 24

    def test_set_frequency_invalid(self, scheduler):
        """Test invalid frequency values."""
        with pytest.raises(ValueError):
            scheduler.set_frequency(5)

        with pytest.raises(ValueError):
            scheduler.set_frequency(0)

    def test_enable_cloud_sync(self, scheduler):
        """Test enabling cloud sync."""
        scheduler.enable_cloud_sync(
            enabled=True,
            password="test_password",
            config={'endpoint': 'https://example.com'}
        )

        assert scheduler.cloud_sync_enabled is True
        assert scheduler.cloud_password == "test_password"
        assert scheduler.cloud_config == {'endpoint': 'https://example.com'}

    def test_enable_cloud_sync_requires_password(self, scheduler):
        """Test cloud sync requires password."""
        with pytest.raises(ValueError):
            scheduler.enable_cloud_sync(enabled=True, password=None)

    def test_get_status(self, scheduler):
        """Test status reporting."""
        status = scheduler.get_status()

        assert 'running' in status
        assert 'enabled' in status
        assert 'frequency_hours' in status
        assert 'backup_on_close' in status
        assert 'cloud_sync_enabled' in status
        assert status['frequency_hours'] == 4

    def test_backup_on_close(self, scheduler, backup_service):
        """Test backup on close triggers backup."""
        # No recent backup, should trigger
        scheduler.backup_on_close()

        assert backup_service.auto_backup_called is True

    def test_backup_on_close_skips_recent(self, scheduler, backup_service):
        """Test backup on close skips if recent backup exists."""
        # Set recent backup time (5 minutes ago)
        scheduler._last_backup_time = datetime.now() - timedelta(minutes=5)
        backup_service.auto_backup_called = False

        scheduler.backup_on_close()

        # Should skip because backup was less than 30 min ago
        assert backup_service.auto_backup_called is False

    def test_backup_on_close_disabled(self, backup_service):
        """Test backup on close respects disabled setting."""
        from src.services.scheduler import BackupScheduler

        scheduler = BackupScheduler(
            backup_service=backup_service,
            settings_dict={'backup_on_close': False}
        )

        scheduler.backup_on_close()
        assert backup_service.auto_backup_called is False

    def test_should_backup_logic(self, scheduler):
        """Test backup timing logic."""
        # No next backup time set
        scheduler._next_backup_time = None
        scheduler._backup_in_progress = False

        # Should calculate and check
        result = scheduler._should_backup()
        assert isinstance(result, bool)

    def test_should_backup_in_progress(self, scheduler):
        """Test backup skipped when already in progress."""
        scheduler._backup_in_progress = True
        assert scheduler._should_backup() is False

    def test_calculate_next_backup(self, scheduler):
        """Test next backup calculation."""
        scheduler._last_backup_time = datetime.now()
        scheduler._calculate_next_backup()

        expected = scheduler._last_backup_time + timedelta(hours=scheduler.frequency_hours)
        assert scheduler._next_backup_time == expected

    def test_calculate_next_backup_no_previous(self, scheduler):
        """Test next backup when no previous exists."""
        scheduler._last_backup_time = None
        scheduler._calculate_next_backup()

        # Should be approximately now
        assert scheduler._next_backup_time is not None
        delta = abs((scheduler._next_backup_time - datetime.now()).total_seconds())
        assert delta < 2  # Within 2 seconds

    def test_status_callback(self, scheduler):
        """Test status change callback."""
        status_messages = []

        def on_status(msg):
            status_messages.append(msg)

        scheduler.on_status_change = on_status
        scheduler._notify_status("Test message")

        assert len(status_messages) == 1
        assert status_messages[0] == "Test message"

    def test_backup_complete_callback(self, scheduler, backup_service):
        """Test backup completion callback."""
        results = []

        def on_complete(success, message):
            results.append((success, message))

        scheduler.on_backup_complete = on_complete

        # Trigger a backup
        scheduler._perform_scheduled_backup()

        # Should have called callback
        assert len(results) == 1
        assert results[0][0] is True  # Success

    def test_change_detection_skips_backup(self, scheduler, database_service, backup_service):
        """Test backup is skipped when no changes detected."""
        # Set previous backup time
        scheduler._last_backup_time = datetime.now() - timedelta(hours=1)

        # No changes since last backup
        database_service.has_changes = False
        backup_service.auto_backup_called = False

        scheduler._perform_scheduled_backup()

        # Should skip backup
        assert backup_service.auto_backup_called is False

    def test_schedule_manual_backup(self, scheduler, backup_service):
        """Test scheduling a manual backup."""
        scheduler.schedule_backup(delay_seconds=0)

        # Give thread time to run
        time.sleep(0.2)

        assert backup_service.auto_backup_called is True


class TestSchedulerThreadSafety:
    """Tests for thread safety in scheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler for thread testing."""
        from src.services.scheduler import BackupScheduler
        return BackupScheduler(
            backup_service=MockBackupService(),
            settings_dict={'auto_backup_enabled': True}
        )

    def test_concurrent_backup_prevention(self, scheduler):
        """Test that concurrent backups are prevented."""
        scheduler._backup_in_progress = True

        # Try to perform another backup
        initial_count = scheduler.backup_service.backup_count
        scheduler._perform_scheduled_backup()

        # Should be skipped
        assert scheduler.backup_service.backup_count == initial_count

    def test_start_idempotent(self, scheduler):
        """Test that multiple starts don't create multiple threads."""
        scheduler.start()
        thread1 = scheduler._thread

        scheduler.start()  # Should warn and skip
        thread2 = scheduler._thread

        assert thread1 is thread2

        scheduler.stop()

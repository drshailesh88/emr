"""Automatic backup scheduler with configurable intervals.

Manages:
- Periodic automatic backups
- Backup on app close
- Change detection to avoid unnecessary backups
- Optional cloud sync after local backup
"""

import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BackupScheduler:
    """Background scheduler for automatic backups.

    Features:
    - Runs periodic backups based on configurable frequency
    - Skips backups if no data has changed
    - Optional cloud sync after backup
    - Backup on app close
    - Thread-safe operation
    """

    def __init__(
        self,
        backup_service,
        settings_dict: Optional[Dict[str, Any]] = None,
        database_service=None
    ):
        """Initialize backup scheduler.

        Args:
            backup_service: BackupService instance
            settings_dict: Dictionary with backup settings
            database_service: DatabaseService instance (for change detection)
        """
        from .backup import BackupService

        self.backup_service: BackupService = backup_service
        self.database_service = database_service

        # Default settings
        self.enabled = True
        self.frequency_hours = 4
        self.backup_on_close_enabled = True
        self.cloud_sync_enabled = False
        self.cloud_password: Optional[str] = None
        self.cloud_config: Dict[str, Any] = {}

        # Load settings
        if settings_dict:
            self.enabled = settings_dict.get('auto_backup_enabled', True)
            self.frequency_hours = settings_dict.get('backup_frequency_hours', 4)
            self.backup_on_close_enabled = settings_dict.get('backup_on_close', True)
            self.cloud_sync_enabled = settings_dict.get('cloud_sync_enabled', False)
            self.cloud_config = settings_dict.get('cloud_config', {})

        # State
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_backup_time: Optional[datetime] = None
        self._next_backup_time: Optional[datetime] = None
        self._backup_in_progress = False
        self._lock = threading.Lock()

        # Callbacks
        self.on_backup_complete: Optional[Callable[[bool, str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None

        # Initialize last backup time from service
        self._update_last_backup_time()

    def _update_last_backup_time(self):
        """Update last backup time from backup service."""
        try:
            last_backup = self.backup_service.get_last_backup_time()
            if last_backup:
                self._last_backup_time = last_backup
                self._calculate_next_backup()
        except Exception as e:
            logger.error(f"Error getting last backup time: {e}")

    def _calculate_next_backup(self):
        """Calculate when the next backup should occur."""
        if self._last_backup_time:
            self._next_backup_time = self._last_backup_time + timedelta(hours=self.frequency_hours)
        else:
            # No previous backup, schedule for now
            self._next_backup_time = datetime.now()

    def start(self):
        """Start the scheduler thread."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        if not self.enabled:
            logger.info("Scheduler is disabled in settings")
            return

        self._running = True
        self._stop_event.clear()
        self._calculate_next_backup()

        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True, name="BackupScheduler")
        self._thread.start()

        logger.info(f"Backup scheduler started (frequency: {self.frequency_hours}h)")
        self._notify_status("Scheduler started")

    def stop(self):
        """Stop the scheduler thread."""
        if not self._running:
            return

        logger.info("Stopping backup scheduler...")
        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info("Backup scheduler stopped")
        self._notify_status("Scheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop (runs in background thread)."""
        while self._running and not self._stop_event.is_set():
            try:
                # Check if it's time for a backup
                if self._should_backup():
                    self._perform_scheduled_backup()

                # Sleep for 60 seconds before next check
                self._stop_event.wait(60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)

    def _should_backup(self) -> bool:
        """Check if a backup should be performed now."""
        if self._backup_in_progress:
            return False

        if not self._next_backup_time:
            self._calculate_next_backup()

        if not self._next_backup_time:
            return False

        return datetime.now() >= self._next_backup_time

    def _perform_scheduled_backup(self):
        """Perform a scheduled backup."""
        with self._lock:
            if self._backup_in_progress:
                return
            self._backup_in_progress = True

        try:
            # Check if data has changed since last backup
            if self._last_backup_time and self.database_service:
                if not self.database_service.has_changes_since(self._last_backup_time):
                    logger.info("No changes detected, skipping backup")
                    self._schedule_next_backup()
                    return

            logger.info("Starting scheduled backup...")
            self._notify_status("Creating backup...")

            # Create local backup
            success = self.backup_service.auto_backup(
                encrypt=self.cloud_sync_enabled,  # Encrypt if cloud sync enabled
                password=self.cloud_password if self.cloud_sync_enabled else None
            )

            if success:
                self._last_backup_time = datetime.now()
                logger.info("Scheduled backup completed")
                self._notify_status("Backup complete")

                # Sync to cloud if enabled
                if self.cloud_sync_enabled and self.cloud_password and self.cloud_config:
                    self._sync_to_cloud()

                # Notify completion
                if self.on_backup_complete:
                    self.on_backup_complete(True, "Scheduled backup completed")
            else:
                logger.error("Scheduled backup failed")
                self._notify_status("Backup failed")
                if self.on_backup_complete:
                    self.on_backup_complete(False, "Scheduled backup failed")

            # Schedule next backup
            self._schedule_next_backup()

        except Exception as e:
            logger.error(f"Error performing scheduled backup: {e}")
            self._notify_status(f"Backup error: {e}")
            if self.on_backup_complete:
                self.on_backup_complete(False, str(e))
        finally:
            with self._lock:
                self._backup_in_progress = False

    def _sync_to_cloud(self):
        """Sync backup to cloud (called after successful local backup)."""
        try:
            logger.info("Syncing to cloud...")
            self._notify_status("Syncing to cloud...")

            success = self.backup_service.sync_to_cloud(
                password=self.cloud_password,
                backend_config=self.cloud_config
            )

            if success:
                logger.info("Cloud sync completed")
                self._notify_status("Cloud sync complete")
            else:
                logger.error("Cloud sync failed")
                self._notify_status("Cloud sync failed")

        except Exception as e:
            logger.error(f"Error syncing to cloud: {e}")
            self._notify_status(f"Cloud sync error: {e}")

    def _schedule_next_backup(self):
        """Schedule the next backup."""
        self._calculate_next_backup()
        if self._next_backup_time:
            logger.info(f"Next backup scheduled for {self._next_backup_time}")

    def schedule_backup(self, delay_seconds: int = 0):
        """Schedule a manual backup after a delay.

        Args:
            delay_seconds: Delay before backup (0 for immediate)
        """
        def delayed_backup():
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            self._perform_scheduled_backup()

        threading.Thread(target=delayed_backup, daemon=True, name="ManualBackup").start()

    def backup_on_close(self):
        """Trigger backup before app closes (if enabled)."""
        if not self.backup_on_close_enabled:
            logger.info("Backup on close is disabled")
            return

        # Check if recent backup exists
        if self._last_backup_time:
            minutes_since_last = (datetime.now() - self._last_backup_time).total_seconds() / 60
            if minutes_since_last < 30:
                logger.info(f"Recent backup exists ({minutes_since_last:.0f} min ago), skipping close backup")
                return

        # Check if data has changed
        if self._last_backup_time and self.database_service:
            if not self.database_service.has_changes_since(self._last_backup_time):
                logger.info("No changes detected, skipping close backup")
                return

        logger.info("Performing backup on app close...")
        self._notify_status("Backing up before close...")

        try:
            success = self.backup_service.auto_backup(
                encrypt=self.cloud_sync_enabled,
                password=self.cloud_password if self.cloud_sync_enabled else None
            )

            if success:
                logger.info("Close backup completed")
                self._notify_status("Backup complete")
            else:
                logger.error("Close backup failed")
                self._notify_status("Backup failed")

        except Exception as e:
            logger.error(f"Error during close backup: {e}")
            self._notify_status(f"Backup error: {e}")

    def set_frequency(self, hours: int):
        """Change backup frequency.

        Args:
            hours: New frequency in hours (1, 4, 12, or 24)
        """
        if hours not in [1, 4, 12, 24]:
            raise ValueError("Frequency must be 1, 4, 12, or 24 hours")

        self.frequency_hours = hours
        self._calculate_next_backup()
        logger.info(f"Backup frequency changed to {hours} hours")

    def enable_cloud_sync(self, enabled: bool, password: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Enable or disable automatic cloud sync.

        Args:
            enabled: Whether to enable cloud sync
            password: Encryption password (required if enabled=True)
            config: Cloud backend configuration
        """
        if enabled and not password:
            raise ValueError("Password required for cloud sync")

        self.cloud_sync_enabled = enabled
        if password:
            self.cloud_password = password
        if config:
            self.cloud_config = config

        logger.info(f"Cloud sync {'enabled' if enabled else 'disabled'}")

    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status.

        Returns:
            Dictionary with status information
        """
        status = {
            'running': self._running,
            'enabled': self.enabled,
            'frequency_hours': self.frequency_hours,
            'backup_on_close': self.backup_on_close_enabled,
            'cloud_sync_enabled': self.cloud_sync_enabled,
            'last_backup': self._last_backup_time.isoformat() if self._last_backup_time else None,
            'next_backup': self._next_backup_time.isoformat() if self._next_backup_time else None,
            'backup_in_progress': self._backup_in_progress,
        }

        # Calculate time until next backup
        if self._next_backup_time:
            delta = self._next_backup_time - datetime.now()
            if delta.total_seconds() > 0:
                status['next_backup_in_minutes'] = int(delta.total_seconds() / 60)
            else:
                status['next_backup_in_minutes'] = 0

        # Calculate time since last backup
        if self._last_backup_time:
            delta = datetime.now() - self._last_backup_time
            status['last_backup_hours_ago'] = delta.total_seconds() / 3600

        return status

    def _notify_status(self, message: str):
        """Notify status change."""
        if self.on_status_change:
            try:
                self.on_status_change(message)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")

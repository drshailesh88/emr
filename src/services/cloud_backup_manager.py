"""Cloud Backup Manager - Orchestrates cloud backup operations.

Handles:
- Cloud backup/restore operations
- Encryption/decryption
- Multiple cloud providers (DocAssist, S3, Google Drive, local)
- Sync state tracking
- Conflict resolution
- Background sync scheduling
"""

import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .backup import BackupService
from .sync import SyncService, SyncStatus, LocalStorageBackend, S3StorageBackend, DocAssistCloudBackend, get_or_create_device_id
from .settings import SettingsService
from .crypto import CryptoService, is_crypto_available

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Current sync state."""
    syncing: bool = False
    last_sync_time: Optional[datetime] = None
    last_sync_success: bool = False
    last_error: Optional[str] = None
    storage_used: Optional[int] = None
    storage_quota: Optional[int] = None
    next_sync_time: Optional[datetime] = None


class CloudBackupManager:
    """Manages cloud backup operations and sync scheduling."""

    def __init__(
        self,
        backup_service: BackupService,
        settings_service: SettingsService,
        data_dir: Optional[Path] = None,
    ):
        """Initialize cloud backup manager.

        Args:
            backup_service: Backup service instance
            settings_service: Settings service instance
            data_dir: Data directory path
        """
        self.backup_service = backup_service
        self.settings_service = settings_service
        self.data_dir = Path(data_dir) if data_dir else Path("data")

        # Sync state
        self.state = SyncState()
        self._sync_lock = threading.Lock()
        self._background_thread: Optional[threading.Thread] = None
        self._stop_background = threading.Event()

        # Callbacks
        self.on_sync_start: Optional[Callable] = None
        self.on_sync_complete: Optional[Callable[[bool, Optional[str]], None]] = None
        self.on_conflict: Optional[Callable[[Dict[str, Any], Dict[str, Any]], str]] = None

    def start_background_sync(self, interval_hours: float = 4.0):
        """Start background sync thread.

        Args:
            interval_hours: Sync interval in hours
        """
        if self._background_thread and self._background_thread.is_alive():
            logger.warning("Background sync already running")
            return

        self._stop_background.clear()

        def background_loop():
            logger.info(f"Starting background sync (interval: {interval_hours} hours)")
            while not self._stop_background.is_set():
                try:
                    # Check if cloud sync is enabled
                    settings = self.settings_service.get_backup_settings()
                    if settings.cloud_sync_enabled:
                        # Perform sync
                        self.sync_now()

                    # Wait for next sync
                    self.state.next_sync_time = datetime.now() + timedelta(hours=interval_hours)
                    self._stop_background.wait(timeout=interval_hours * 3600)

                except Exception as ex:
                    logger.error(f"Background sync error: {ex}")
                    time.sleep(60)  # Wait 1 minute before retrying

            logger.info("Background sync stopped")

        self._background_thread = threading.Thread(target=background_loop, daemon=True)
        self._background_thread.start()

    def stop_background_sync(self):
        """Stop background sync thread."""
        if self._background_thread:
            logger.info("Stopping background sync...")
            self._stop_background.set()
            if self._background_thread.is_alive():
                self._background_thread.join(timeout=5)

    def sync_now(self, password: Optional[str] = None) -> bool:
        """Perform immediate sync to cloud.

        Args:
            password: Encryption password (will use saved password if None)

        Returns:
            True if successful
        """
        with self._sync_lock:
            if self.state.syncing:
                logger.warning("Sync already in progress")
                return False

            self.state.syncing = True
            self.state.last_error = None

        try:
            # Get settings
            settings = self.settings_service.get_backup_settings()
            if not settings.cloud_sync_enabled:
                raise ValueError("Cloud sync is not enabled")

            if not settings.cloud_config:
                raise ValueError("Cloud sync is not configured")

            # Notify sync start
            if self.on_sync_start:
                self.on_sync_start()

            # Get password (TODO: implement secure password storage)
            if password is None:
                password = self._get_saved_password()
                if not password:
                    raise ValueError("No encryption password available")

            # Build backend config
            backend_config = settings.cloud_config.copy()
            backend_config['type'] = settings.cloud_backend_type

            # Check for conflicts
            conflict_resolution = self._check_and_resolve_conflicts(backend_config)
            if conflict_resolution == "skip":
                logger.info("Sync skipped due to unresolved conflict")
                return False

            # Perform sync based on conflict resolution
            if conflict_resolution == "cloud":
                # Download and restore from cloud
                success = self._restore_from_cloud(password, backend_config)
            else:
                # Upload to cloud (default or "local" resolution)
                success = self.backup_service.sync_to_cloud(
                    password=password,
                    backend_config=backend_config,
                )

            # Update state
            with self._sync_lock:
                self.state.last_sync_time = datetime.now()
                self.state.last_sync_success = success
                self.state.syncing = False

            # Update storage usage (if DocAssist Cloud)
            if settings.cloud_backend_type == 'docassist':
                self._update_storage_usage(backend_config)

            # Notify completion
            if self.on_sync_complete:
                self.on_sync_complete(success, None)

            if success:
                logger.info("Cloud sync completed successfully")
            else:
                logger.error("Cloud sync failed")

            return success

        except Exception as ex:
            error_msg = str(ex)
            logger.error(f"Cloud sync error: {error_msg}")

            with self._sync_lock:
                self.state.syncing = False
                self.state.last_error = error_msg

            if self.on_sync_complete:
                self.on_sync_complete(False, error_msg)

            return False

    def _check_and_resolve_conflicts(self, backend_config: Dict[str, Any]) -> str:
        """Check for sync conflicts and resolve them.

        Args:
            backend_config: Backend configuration

        Returns:
            Resolution strategy: "local", "cloud", "both", or "skip"
        """
        try:
            # List cloud backups
            cloud_backups = self.backup_service.list_cloud_backups(backend_config)
            if not cloud_backups:
                # No cloud backups, safe to upload
                return "local"

            # Get most recent cloud backup
            cloud_backup = cloud_backups[0]
            cloud_modified = datetime.fromisoformat(cloud_backup['modified'].replace('Z', '+00:00'))

            # Get most recent local backup
            local_backups = self.backup_service.list_backups()
            if not local_backups:
                # No local backups, download from cloud
                return "cloud"

            local_backup = local_backups[0]
            local_modified = datetime.fromisoformat(local_backup.created_at)

            # Check if they differ significantly (more than 1 hour)
            time_diff = abs((cloud_modified - local_modified).total_seconds())
            if time_diff < 3600:  # Less than 1 hour difference
                # Close enough, assume same data
                return "local"

            # Significant difference - conflict detected
            logger.warning(f"Sync conflict detected: local={local_modified}, cloud={cloud_modified}")

            # Call conflict handler if available
            if self.on_conflict:
                local_info = {
                    'modified': local_backup.created_at,
                    'size': local_backup.size_bytes,
                    'patient_count': local_backup.patient_count,
                    'visit_count': local_backup.visit_count,
                }
                cloud_info = {
                    'modified': cloud_backup['modified'],
                    'size': cloud_backup.get('size', 0),
                    'patient_count': 0,  # Not available from cloud metadata
                    'visit_count': 0,
                }
                return self.on_conflict(local_info, cloud_info)

            # Default: use newer data
            if cloud_modified > local_modified:
                logger.info("Using cloud data (newer)")
                return "cloud"
            else:
                logger.info("Using local data (newer)")
                return "local"

        except Exception as ex:
            logger.error(f"Error checking conflicts: {ex}")
            return "local"  # Default to local on error

    def _restore_from_cloud(self, password: str, backend_config: Dict[str, Any]) -> bool:
        """Restore from most recent cloud backup.

        Args:
            password: Decryption password
            backend_config: Backend configuration

        Returns:
            True if successful
        """
        try:
            # List cloud backups
            cloud_backups = self.backup_service.list_cloud_backups(backend_config)
            if not cloud_backups:
                logger.warning("No cloud backups found")
                return False

            # Get most recent backup
            remote_key = cloud_backups[0]['key']

            # Restore
            return self.backup_service.restore_from_cloud(
                remote_key=remote_key,
                password=password,
                backend_config=backend_config,
            )

        except Exception as ex:
            logger.error(f"Error restoring from cloud: {ex}")
            return False

    def _update_storage_usage(self, backend_config: Dict[str, Any]):
        """Update storage usage info (DocAssist Cloud only).

        Args:
            backend_config: Backend configuration
        """
        try:
            device_id = get_or_create_device_id(self.data_dir)
            backend = DocAssistCloudBackend(
                api_key=backend_config.get('api_key', ''),
                device_id=device_id,
            )

            account_info = backend.get_account_info()
            if account_info:
                with self._sync_lock:
                    self.state.storage_used = account_info.get('storage_used', 0)
                    self.state.storage_quota = account_info.get('storage_quota', 0)

        except Exception as ex:
            logger.error(f"Error updating storage usage: {ex}")

    def _get_saved_password(self) -> Optional[str]:
        """Get saved encryption password.

        TODO: Implement secure password storage using keyring or similar.
        For now, returns None (user must provide password each time).
        """
        # SECURITY NOTE: Storing passwords is complex and platform-specific.
        # Options:
        # 1. Use system keyring (keyring library)
        # 2. Ask user each time (most secure but inconvenient)
        # 3. Store encrypted with device-specific key
        #
        # For MVP, we'll require user to enter password for cloud sync.
        return None

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status.

        Returns:
            Dict with sync status information
        """
        with self._sync_lock:
            return {
                'syncing': self.state.syncing,
                'last_sync_time': self.state.last_sync_time,
                'last_sync_success': self.state.last_sync_success,
                'last_error': self.state.last_error,
                'storage_used': self.state.storage_used,
                'storage_quota': self.state.storage_quota,
                'next_sync_time': self.state.next_sync_time,
                'error': self.state.last_error,
            }

    def list_cloud_backups(self) -> list:
        """List available cloud backups.

        Returns:
            List of cloud backup info dicts
        """
        try:
            settings = self.settings_service.get_backup_settings()
            if not settings.cloud_sync_enabled or not settings.cloud_config:
                return []

            backend_config = settings.cloud_config.copy()
            backend_config['type'] = settings.cloud_backend_type

            return self.backup_service.list_cloud_backups(backend_config)

        except Exception as ex:
            logger.error(f"Error listing cloud backups: {ex}")
            return []

    def restore_from_cloud(
        self,
        remote_key: str,
        password: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Restore specific backup from cloud.

        Args:
            remote_key: Remote backup key
            password: Decryption password
            progress_callback: Progress callback

        Returns:
            True if successful
        """
        try:
            settings = self.settings_service.get_backup_settings()
            if not settings.cloud_sync_enabled or not settings.cloud_config:
                raise ValueError("Cloud backup not configured")

            backend_config = settings.cloud_config.copy()
            backend_config['type'] = settings.cloud_backend_type

            return self.backup_service.restore_from_cloud(
                remote_key=remote_key,
                password=password,
                backend_config=backend_config,
                progress_callback=progress_callback,
            )

        except Exception as ex:
            logger.error(f"Error restoring from cloud: {ex}")
            return False

    def test_connection(self, backend_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Test cloud connection.

        Args:
            backend_config: Backend configuration

        Returns:
            Tuple of (success, error_message)
        """
        try:
            backend_type = backend_config.get('type', 'local')

            if backend_type == 'docassist':
                device_id = get_or_create_device_id(self.data_dir)
                backend = DocAssistCloudBackend(
                    api_key=backend_config['api_key'],
                    device_id=device_id,
                )
                # Test by getting account info
                info = backend.get_account_info()
                if info:
                    return (True, None)
                else:
                    return (False, "Invalid API key or account not found")

            elif backend_type == 's3':
                backend = S3StorageBackend(
                    bucket=backend_config['bucket'],
                    access_key=backend_config['access_key'],
                    secret_key=backend_config['secret_key'],
                    endpoint_url=backend_config.get('endpoint_url'),
                    region=backend_config.get('region', 'us-east-1'),
                )
                # Test by listing files
                backend.list_files()
                return (True, None)

            elif backend_type == 'local':
                backend = LocalStorageBackend(Path(backend_config['path']))
                # Test by listing files
                backend.list_files()
                return (True, None)

            else:
                return (False, f"Unknown backend type: {backend_type}")

        except Exception as ex:
            return (False, str(ex))

    def is_configured(self) -> bool:
        """Check if cloud backup is configured.

        Returns:
            True if configured
        """
        settings = self.settings_service.get_backup_settings()
        return settings.cloud_sync_enabled and bool(settings.cloud_config)

    def get_provider_name(self) -> str:
        """Get friendly provider name.

        Returns:
            Provider name
        """
        settings = self.settings_service.get_backup_settings()
        provider_names = {
            'docassist': 'DocAssist Cloud',
            's3': 'Amazon S3',
            'gdrive': 'Google Drive',
            'local': 'Local Network',
        }
        return provider_names.get(settings.cloud_backend_type, 'Unknown')

    def disable_cloud_sync(self):
        """Disable cloud sync."""
        self.stop_background_sync()
        self.settings_service.enable_cloud_sync(False)
        logger.info("Cloud sync disabled")

    def enable_cloud_sync(self, backend_type: str, config: Dict[str, Any]):
        """Enable cloud sync.

        Args:
            backend_type: Backend type ("docassist", "s3", "local")
            config: Backend configuration
        """
        self.settings_service.enable_cloud_sync(True, backend_type, config)
        logger.info(f"Cloud sync enabled with {backend_type}")

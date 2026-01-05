"""
Sync Manager - Orchestrates data synchronization.

Manages:
- Uploading pending changes to server
- Downloading updates from server
- Conflict resolution
- Background sync scheduling
- Sync status tracking
"""

import threading
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from enum import Enum
import logging

from .offline_queue import OfflineQueue, QueuedOperation, OperationType
from .sync_client import SyncClient, SyncStatus
from .local_db import LocalDatabase

logger = logging.getLogger(__name__)


class SyncState(Enum):
    """Overall sync state."""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    OFFLINE = "offline"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MANUAL = "manual"


class SyncManager:
    """
    Manages all sync operations between mobile and server.

    Usage:
        sync_manager = SyncManager(
            sync_client=sync_client,
            offline_queue=offline_queue,
            local_db=local_db,
        )

        # Start background sync
        sync_manager.start_background_sync(interval=300)  # Every 5 minutes

        # Manual sync
        sync_manager.sync_now()

        # Get sync status
        status = sync_manager.get_sync_status()
    """

    def __init__(
        self,
        sync_client: SyncClient,
        offline_queue: OfflineQueue,
        local_db: LocalDatabase,
        conflict_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
    ):
        self.sync_client = sync_client
        self.offline_queue = offline_queue
        self.local_db = local_db
        self.conflict_resolution = conflict_resolution

        self.state = SyncState.IDLE
        self._last_sync_time: Optional[datetime] = None
        self._sync_in_progress = False
        self._background_sync_thread: Optional[threading.Thread] = None
        self._background_sync_running = False
        self._sync_callbacks: list = []

        # Statistics
        self.stats = {
            'pending_count': 0,
            'failed_count': 0,
            'synced_count': 0,
            'last_error': None,
        }

    def add_sync_callback(self, callback: Callable[[SyncState, Dict], None]):
        """
        Add a callback to be notified of sync state changes.

        Args:
            callback: Function that takes (state, stats) as arguments
        """
        self._sync_callbacks.append(callback)

    def _notify_callbacks(self):
        """Notify all registered callbacks of state change."""
        for callback in self._sync_callbacks:
            try:
                callback(self.state, self.stats)
            except Exception as e:
                logger.error(f"Error in sync callback: {e}")

    def sync_now(self) -> bool:
        """
        Perform immediate synchronization.

        Returns:
            True if sync was successful
        """
        if self._sync_in_progress:
            logger.info("Sync already in progress")
            return False

        self._sync_in_progress = True
        self.state = SyncState.SYNCING
        self._notify_callbacks()

        success = False
        try:
            # Step 1: Upload pending changes
            upload_success = self.sync_pending_changes()

            # Step 2: Download updates from server
            download_success = self.download_updates()

            success = upload_success and download_success

            if success:
                self.state = SyncState.SUCCESS
                self._last_sync_time = datetime.now()
                self.stats['last_error'] = None
            else:
                self.state = SyncState.ERROR
                self.stats['last_error'] = "Sync failed"

        except Exception as e:
            logger.error(f"Sync error: {e}")
            self.state = SyncState.ERROR
            self.stats['last_error'] = str(e)
            success = False

        finally:
            self._sync_in_progress = False
            self._update_stats()
            self._notify_callbacks()

        return success

    def sync_pending_changes(self) -> bool:
        """
        Upload all pending changes to server.

        Returns:
            True if all changes were uploaded successfully
        """
        try:
            pending = self.offline_queue.get_pending_operations()

            if not pending:
                logger.info("No pending changes to sync")
                return True

            logger.info(f"Syncing {len(pending)} pending changes")

            success_count = 0
            failed_count = 0

            for operation in pending:
                try:
                    # Upload operation to server
                    result = self._upload_operation(operation)

                    if result:
                        # Mark as synced
                        self.offline_queue.mark_synced(operation.id)
                        success_count += 1
                    else:
                        # Mark as failed
                        self.offline_queue.mark_failed(operation.id, "Upload failed")
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error syncing operation {operation.id}: {e}")
                    self.offline_queue.mark_failed(operation.id, str(e))
                    failed_count += 1

            logger.info(f"Sync complete: {success_count} succeeded, {failed_count} failed")

            # Clean up synced operations
            self.offline_queue.clear_synced()

            return failed_count == 0

        except Exception as e:
            logger.error(f"Error in sync_pending_changes: {e}")
            return False

    def _upload_operation(self, operation: QueuedOperation) -> bool:
        """
        Upload a single operation to the server.

        Args:
            operation: The queued operation

        Returns:
            True if upload was successful
        """
        try:
            # In a real implementation, this would make an API call to the server
            # For now, we'll simulate success
            # TODO: Implement actual API calls when server endpoint is ready

            logger.debug(f"Uploading {operation.operation_type} to {operation.table}")

            # Simulate API call
            # response = requests.post(
            #     f"{self.sync_client.server_url}/sync/operation",
            #     json=operation.to_dict(),
            #     headers={"Authorization": f"Bearer {self.sync_client.token}"}
            # )
            # return response.status_code == 200

            # For now, just return True (simulated success)
            time.sleep(0.1)  # Simulate network delay
            return True

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False

    def download_updates(self) -> bool:
        """
        Download updates from server.

        Returns:
            True if download was successful
        """
        try:
            # Trigger sync client download
            # This will download and decrypt the latest backup
            success = self.sync_client.sync(background=False)

            if success:
                logger.info("Downloaded updates from server")
                return True
            else:
                logger.error("Failed to download updates")
                return False

        except Exception as e:
            logger.error(f"Download error: {e}")
            return False

    def resolve_conflict(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve conflict between local and remote data.

        Args:
            local_data: Local version of the data
            remote_data: Remote version of the data

        Returns:
            Merged data
        """
        if self.conflict_resolution == ConflictResolution.LAST_WRITE_WINS:
            # Compare timestamps
            local_time = local_data.get('updated_at') or local_data.get('created_at', '')
            remote_time = remote_data.get('updated_at') or remote_data.get('created_at', '')

            if local_time >= remote_time:
                logger.info("Conflict resolved: local wins (newer)")
                return local_data
            else:
                logger.info("Conflict resolved: remote wins (newer)")
                return remote_data

        elif self.conflict_resolution == ConflictResolution.SERVER_WINS:
            logger.info("Conflict resolved: server wins (policy)")
            return remote_data

        elif self.conflict_resolution == ConflictResolution.CLIENT_WINS:
            logger.info("Conflict resolved: client wins (policy)")
            return local_data

        else:  # MANUAL
            # In a real app, this would prompt the user
            logger.warning("Manual conflict resolution required")
            return remote_data  # Default to server for now

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status.

        Returns:
            Dictionary with sync status information
        """
        pending_count = self.offline_queue.get_pending_count()
        failed_count = self.offline_queue.get_failed_count()

        return {
            'state': self.state.value,
            'is_syncing': self._sync_in_progress,
            'pending_count': pending_count,
            'failed_count': failed_count,
            'last_sync': self._last_sync_time.isoformat() if self._last_sync_time else None,
            'last_sync_human': self._format_last_sync_time(),
            'has_pending_changes': pending_count > 0,
            'last_error': self.stats.get('last_error'),
        }

    def _format_last_sync_time(self) -> str:
        """Format last sync time for human reading."""
        if not self._last_sync_time:
            return "Never"

        elapsed = (datetime.now() - self._last_sync_time).total_seconds()

        if elapsed < 60:
            return "Just now"
        elif elapsed < 3600:
            minutes = int(elapsed / 60)
            return f"{minutes} min ago"
        elif elapsed < 86400:
            hours = int(elapsed / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            return self._last_sync_time.strftime("%b %d, %Y")

    def _update_stats(self):
        """Update sync statistics."""
        self.stats['pending_count'] = self.offline_queue.get_pending_count()
        self.stats['failed_count'] = self.offline_queue.get_failed_count()

    def start_background_sync(self, interval: int = 300):
        """
        Start background sync loop.

        Args:
            interval: Sync interval in seconds (default: 300 = 5 minutes)
        """
        if self._background_sync_running:
            logger.info("Background sync already running")
            return

        self._background_sync_running = True

        def sync_loop():
            logger.info(f"Starting background sync (interval: {interval}s)")
            while self._background_sync_running:
                try:
                    # Wait for interval
                    time.sleep(interval)

                    # Only sync if we have pending changes or it's been a while
                    should_sync = False

                    if self.offline_queue.get_pending_count() > 0:
                        should_sync = True
                        logger.info("Background sync: pending changes detected")

                    elif not self._last_sync_time:
                        should_sync = True
                        logger.info("Background sync: no previous sync")

                    elif (datetime.now() - self._last_sync_time).total_seconds() > interval:
                        should_sync = True
                        logger.info("Background sync: interval elapsed")

                    if should_sync:
                        self.sync_now()

                except Exception as e:
                    logger.error(f"Background sync error: {e}")

        self._background_sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self._background_sync_thread.start()

    def stop_background_sync(self):
        """Stop background sync loop."""
        if self._background_sync_running:
            logger.info("Stopping background sync")
            self._background_sync_running = False

    def get_pending_count(self) -> int:
        """Get number of pending changes."""
        return self.offline_queue.get_pending_count()

    def has_pending_changes(self) -> bool:
        """Check if there are pending changes."""
        return self.offline_queue.get_pending_count() > 0


# Export classes
__all__ = [
    'SyncManager',
    'SyncState',
    'ConflictResolution',
]

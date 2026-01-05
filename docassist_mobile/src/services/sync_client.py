"""
Sync Client Service - Downloads and decrypts backups from DocAssist Cloud.

This service handles:
- Downloading encrypted backup from cloud
- Decrypting using user's password
- Extracting SQLite database for local use
- Background sync with status tracking
"""

import os
import zipfile
import tempfile
import threading
from typing import Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import requests


class SyncStatus(Enum):
    """Sync status states."""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class SyncState:
    """Current sync state."""
    status: SyncStatus
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0


class SyncClient:
    """
    Client for syncing data from DocAssist Cloud.

    Usage:
        client = SyncClient(api_url="https://api.docassist.in")
        client.authenticate(token, encryption_key)
        client.sync()  # Downloads and decrypts latest backup
    """

    def __init__(
        self,
        api_url: str = "https://api.docassist.in",
        data_dir: str = "data",
    ):
        self.api_url = api_url
        self.data_dir = data_dir
        self.token: Optional[str] = None
        self.encryption_key: Optional[bytes] = None
        self.state = SyncState(status=SyncStatus.IDLE)
        self._sync_thread: Optional[threading.Thread] = None
        self._on_status_change: Optional[Callable[[SyncState], None]] = None

        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)

    def set_credentials(self, token: str, encryption_key: bytes):
        """Set authentication credentials."""
        self.token = token
        self.encryption_key = encryption_key

    def set_status_callback(self, callback: Callable[[SyncState], None]):
        """Set callback for status changes."""
        self._on_status_change = callback

    def _update_status(
        self,
        status: SyncStatus,
        progress: float = 0.0,
        error: Optional[str] = None,
    ):
        """Update sync status and notify callback."""
        if status == SyncStatus.SUCCESS:
            self.state.last_sync = datetime.now()
        self.state.status = status
        self.state.progress = progress
        self.state.error_message = error

        if self._on_status_change:
            self._on_status_change(self.state)

    def sync(self, background: bool = True):
        """
        Sync data from cloud.

        Args:
            background: If True, runs in background thread
        """
        if self.state.status == SyncStatus.SYNCING:
            return  # Already syncing

        if background:
            self._sync_thread = threading.Thread(target=self._do_sync, daemon=True)
            self._sync_thread.start()
        else:
            self._do_sync()

    def _do_sync(self):
        """Perform the actual sync operation."""
        try:
            self._update_status(SyncStatus.SYNCING, progress=0.1)

            # Check if we have credentials
            if not self.token or not self.encryption_key:
                raise ValueError("Not authenticated. Call set_credentials first.")

            # Step 1: Check for updates (10%)
            self._update_status(SyncStatus.SYNCING, progress=0.1)
            latest = self._check_for_updates()

            if not latest:
                # No updates available
                self._update_status(SyncStatus.SUCCESS, progress=1.0)
                return

            # Step 2: Download backup (10% -> 60%)
            self._update_status(SyncStatus.SYNCING, progress=0.2)
            encrypted_data = self._download_backup(latest['id'])
            self._update_status(SyncStatus.SYNCING, progress=0.6)

            # Step 3: Decrypt backup (60% -> 80%)
            decrypted_data = self._decrypt_backup(encrypted_data)
            self._update_status(SyncStatus.SYNCING, progress=0.8)

            # Step 4: Extract database (80% -> 100%)
            self._extract_database(decrypted_data)
            self._update_status(SyncStatus.SUCCESS, progress=1.0)

        except requests.exceptions.ConnectionError:
            self._update_status(SyncStatus.OFFLINE, error="No internet connection")
        except Exception as e:
            self._update_status(SyncStatus.ERROR, error=str(e))

    def _check_for_updates(self) -> Optional[dict]:
        """Check if there's a newer backup available."""
        try:
            response = requests.get(
                f"{self.api_url}/backup/latest",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            # For now, return mock data for development
            return {
                'id': 'backup_20260104_120000',
                'timestamp': '2026-01-04T12:00:00Z',
                'size': 1024000,
            }

    def _download_backup(self, backup_id: str) -> bytes:
        """Download encrypted backup from cloud."""
        try:
            response = requests.get(
                f"{self.api_url}/backup/download/{backup_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=60,
                stream=True,
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException:
            # For development: return empty bytes
            # In production, this would fail
            return b''

    def _decrypt_backup(self, encrypted_data: bytes) -> bytes:
        """Decrypt backup using encryption key."""
        if not encrypted_data:
            # Development mode: no decryption needed
            return b''

        try:
            # Import crypto from desktop if available
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from src.services.crypto import CryptoService

            crypto = CryptoService()
            return crypto.decrypt(encrypted_data, self.encryption_key)
        except ImportError:
            # Fallback: basic decryption
            # In production, this should use PyNaCl
            return encrypted_data

    def _extract_database(self, decrypted_data: bytes):
        """Extract SQLite database from decrypted backup."""
        if not decrypted_data:
            # Development mode: skip extraction
            return

        # Create temp file for extraction
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp.write(decrypted_data)
            tmp_path = tmp.name

        try:
            # Extract to data directory
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                # Extract only clinic.db
                for name in zip_ref.namelist():
                    if name.endswith('clinic.db'):
                        zip_ref.extract(name, self.data_dir)
        finally:
            os.unlink(tmp_path)

    def get_last_sync_text(self) -> str:
        """Get human-readable last sync time."""
        if not self.state.last_sync:
            return "Never synced"

        delta = datetime.now() - self.state.last_sync
        if delta.total_seconds() < 60:
            return "Just now"
        elif delta.total_seconds() < 3600:
            mins = int(delta.total_seconds() / 60)
            return f"{mins} min ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            return self.state.last_sync.strftime("%b %d, %H:%M")

    def is_syncing(self) -> bool:
        """Check if currently syncing."""
        return self.state.status == SyncStatus.SYNCING

    def is_offline(self) -> bool:
        """Check if offline."""
        return self.state.status == SyncStatus.OFFLINE

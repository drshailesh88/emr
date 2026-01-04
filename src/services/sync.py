"""Cloud sync service for encrypted backups.

Supports multiple storage backends:
- DocAssist Cloud (managed service)
- BYOS: Amazon S3, Backblaze B2, Google Cloud Storage
- BYOS: Local network share (SMB/NFS)

All data is encrypted client-side before upload.
The cloud service never sees plaintext data.
"""

import os
import json
import hashlib
import tempfile
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import urllib.request
import urllib.error


class SyncStatus(Enum):
    """Status of sync operation."""
    IDLE = "idle"
    UPLOADING = "uploading"
    DOWNLOADING = "downloading"
    SYNCING = "syncing"
    ERROR = "error"
    COMPLETE = "complete"


@dataclass
class BackupMetadata:
    """Metadata for a cloud backup."""
    backup_id: str
    created_at: str
    size_bytes: int
    checksum: str
    patient_count: int
    visit_count: int
    app_version: str
    device_id: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'BackupMetadata':
        return cls(**data)


@dataclass
class SyncProgress:
    """Progress information for sync operations."""
    status: SyncStatus
    progress_percent: float
    bytes_transferred: int
    total_bytes: int
    message: str
    error: Optional[str] = None


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(self, local_path: Path, remote_key: str,
               progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Upload a file to remote storage."""
        pass

    @abstractmethod
    def download(self, remote_key: str, local_path: Path,
                 progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Download a file from remote storage."""
        pass

    @abstractmethod
    def delete(self, remote_key: str) -> bool:
        """Delete a file from remote storage."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in remote storage."""
        pass

    @abstractmethod
    def exists(self, remote_key: str) -> bool:
        """Check if a file exists in remote storage."""
        pass

    @abstractmethod
    def get_metadata(self, remote_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a remote file."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local folder storage backend (for testing and local network shares)."""

    def __init__(self, base_path: Path):
        """Initialize with base storage path."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, remote_key: str) -> Path:
        """Get full local path for a remote key."""
        return self.base_path / remote_key

    def upload(self, local_path: Path, remote_key: str,
               progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            dest_path = self._get_full_path(remote_key)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            file_size = local_path.stat().st_size
            bytes_copied = 0

            with open(local_path, 'rb') as src, open(dest_path, 'wb') as dst:
                while True:
                    chunk = src.read(8192)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_copied, file_size)

            return True
        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def download(self, remote_key: str, local_path: Path,
                 progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            src_path = self._get_full_path(remote_key)
            if not src_path.exists():
                return False

            file_size = src_path.stat().st_size
            bytes_copied = 0

            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(src_path, 'rb') as src, open(local_path, 'wb') as dst:
                while True:
                    chunk = src.read(8192)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_copied, file_size)

            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False

    def delete(self, remote_key: str) -> bool:
        try:
            path = self._get_full_path(remote_key)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        files = []
        search_path = self.base_path / prefix if prefix else self.base_path

        if not search_path.exists():
            return files

        for path in search_path.rglob('*'):
            if path.is_file():
                files.append({
                    'key': str(path.relative_to(self.base_path)),
                    'size': path.stat().st_size,
                    'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                })
        return files

    def exists(self, remote_key: str) -> bool:
        return self._get_full_path(remote_key).exists()

    def get_metadata(self, remote_key: str) -> Optional[Dict[str, Any]]:
        path = self._get_full_path(remote_key)
        if not path.exists():
            return None
        stat = path.stat()
        return {
            'key': remote_key,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }


class S3StorageBackend(StorageBackend):
    """Amazon S3 / S3-compatible storage backend (Backblaze B2, MinIO, etc.)."""

    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """Initialize S3 backend.

        Args:
            bucket: S3 bucket name
            access_key: AWS access key ID
            secret_key: AWS secret access key
            endpoint_url: Custom endpoint for S3-compatible services
            region: AWS region
        """
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.region = region
        self._client = None

    def _get_client(self):
        """Lazy initialization of S3 client."""
        if self._client is None:
            try:
                import boto3
                session = boto3.Session(
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                self._client = session.client(
                    's3',
                    endpoint_url=self.endpoint_url
                )
            except ImportError:
                raise ImportError("boto3 required for S3 storage: pip install boto3")
        return self._client

    def upload(self, local_path: Path, remote_key: str,
               progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            client = self._get_client()
            file_size = local_path.stat().st_size

            if progress_callback:
                class ProgressCallback:
                    def __init__(self):
                        self.bytes_transferred = 0
                    def __call__(self, bytes_amount):
                        self.bytes_transferred += bytes_amount
                        progress_callback(self.bytes_transferred, file_size)

                client.upload_file(
                    str(local_path),
                    self.bucket,
                    remote_key,
                    Callback=ProgressCallback()
                )
            else:
                client.upload_file(str(local_path), self.bucket, remote_key)

            return True
        except Exception as e:
            print(f"S3 upload failed: {e}")
            return False

    def download(self, remote_key: str, local_path: Path,
                 progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            client = self._get_client()
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Get file size for progress
            meta = client.head_object(Bucket=self.bucket, Key=remote_key)
            file_size = meta['ContentLength']

            if progress_callback:
                class ProgressCallback:
                    def __init__(self):
                        self.bytes_transferred = 0
                    def __call__(self, bytes_amount):
                        self.bytes_transferred += bytes_amount
                        progress_callback(self.bytes_transferred, file_size)

                client.download_file(
                    self.bucket,
                    remote_key,
                    str(local_path),
                    Callback=ProgressCallback()
                )
            else:
                client.download_file(self.bucket, remote_key, str(local_path))

            return True
        except Exception as e:
            print(f"S3 download failed: {e}")
            return False

    def delete(self, remote_key: str) -> bool:
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=remote_key)
            return True
        except Exception as e:
            print(f"S3 delete failed: {e}")
            return False

    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        try:
            client = self._get_client()
            response = client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'modified': obj['LastModified'].isoformat()
                })
            return files
        except Exception as e:
            print(f"S3 list failed: {e}")
            return []

    def exists(self, remote_key: str) -> bool:
        try:
            client = self._get_client()
            client.head_object(Bucket=self.bucket, Key=remote_key)
            return True
        except Exception:
            return False

    def get_metadata(self, remote_key: str) -> Optional[Dict[str, Any]]:
        try:
            client = self._get_client()
            meta = client.head_object(Bucket=self.bucket, Key=remote_key)
            return {
                'key': remote_key,
                'size': meta['ContentLength'],
                'modified': meta['LastModified'].isoformat()
            }
        except Exception:
            return None


class DocAssistCloudBackend(StorageBackend):
    """DocAssist managed cloud storage backend.

    This connects to DocAssist's cloud service for managed backups.
    All data is encrypted client-side before upload.
    """

    # Default API endpoint (can be overridden for testing)
    DEFAULT_API_URL = "https://api.docassist.health/v1"

    def __init__(
        self,
        api_key: str,
        device_id: str,
        api_url: Optional[str] = None
    ):
        """Initialize DocAssist cloud backend.

        Args:
            api_key: User's API key (from subscription)
            device_id: Unique device identifier
            api_url: API URL (defaults to production)
        """
        self.api_key = api_key
        self.device_id = device_id
        self.api_url = api_url or self.DEFAULT_API_URL

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[bytes]:
        """Make API request."""
        url = f"{self.api_url}{endpoint}"

        all_headers = {
            'Authorization': f'Bearer {self.api_key}',
            'X-Device-ID': self.device_id,
            'User-Agent': 'DocAssist-EMR/1.0'
        }
        if headers:
            all_headers.update(headers)

        request = urllib.request.Request(
            url,
            data=data,
            headers=all_headers,
            method=method
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            print(f"API error: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"Network error: {e.reason}")
            return None

    def upload(self, local_path: Path, remote_key: str,
               progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Upload encrypted backup to DocAssist cloud."""
        try:
            with open(local_path, 'rb') as f:
                data = f.read()

            file_size = len(data)
            if progress_callback:
                progress_callback(0, file_size)

            # Upload to /backups/{device_id}/{key}
            result = self._request(
                'PUT',
                f'/backups/{self.device_id}/{remote_key}',
                data=data,
                headers={'Content-Type': 'application/octet-stream'}
            )

            if result is not None:
                if progress_callback:
                    progress_callback(file_size, file_size)
                return True
            return False

        except Exception as e:
            print(f"DocAssist upload failed: {e}")
            return False

    def download(self, remote_key: str, local_path: Path,
                 progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Download encrypted backup from DocAssist cloud."""
        try:
            data = self._request('GET', f'/backups/{self.device_id}/{remote_key}')
            if data is None:
                return False

            local_path.parent.mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback(len(data), len(data))

            with open(local_path, 'wb') as f:
                f.write(data)

            return True

        except Exception as e:
            print(f"DocAssist download failed: {e}")
            return False

    def delete(self, remote_key: str) -> bool:
        """Delete backup from DocAssist cloud."""
        try:
            result = self._request('DELETE', f'/backups/{self.device_id}/{remote_key}')
            return result is not None
        except Exception as e:
            print(f"DocAssist delete failed: {e}")
            return False

    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List backups on DocAssist cloud."""
        try:
            data = self._request('GET', f'/backups/{self.device_id}?prefix={prefix}')
            if data is None:
                return []
            return json.loads(data).get('files', [])
        except Exception as e:
            print(f"DocAssist list failed: {e}")
            return []

    def exists(self, remote_key: str) -> bool:
        """Check if backup exists on DocAssist cloud."""
        try:
            data = self._request('HEAD', f'/backups/{self.device_id}/{remote_key}')
            return data is not None
        except Exception:
            return False

    def get_metadata(self, remote_key: str) -> Optional[Dict[str, Any]]:
        """Get backup metadata from DocAssist cloud."""
        try:
            data = self._request('GET', f'/backups/{self.device_id}/{remote_key}/metadata')
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            return None

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information (quota, usage, tier)."""
        try:
            data = self._request('GET', '/account')
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            return None


class SyncService:
    """Orchestrates backup synchronization with cloud storage.

    Handles:
    - Upload/download of encrypted backups
    - Progress tracking
    - Conflict resolution
    - Background sync
    """

    def __init__(
        self,
        backend: StorageBackend,
        local_backup_dir: Path,
        progress_callback: Optional[Callable[[SyncProgress], None]] = None
    ):
        """Initialize sync service.

        Args:
            backend: Storage backend to use
            local_backup_dir: Local directory for backups
            progress_callback: Called with progress updates
        """
        self.backend = backend
        self.local_backup_dir = Path(local_backup_dir)
        self.progress_callback = progress_callback
        self._status = SyncStatus.IDLE
        self._current_progress = SyncProgress(
            status=SyncStatus.IDLE,
            progress_percent=0,
            bytes_transferred=0,
            total_bytes=0,
            message="Ready"
        )

    def _update_progress(
        self,
        status: SyncStatus,
        percent: float,
        transferred: int,
        total: int,
        message: str,
        error: Optional[str] = None
    ):
        """Update and broadcast progress."""
        self._current_progress = SyncProgress(
            status=status,
            progress_percent=percent,
            bytes_transferred=transferred,
            total_bytes=total,
            message=message,
            error=error
        )
        if self.progress_callback:
            self.progress_callback(self._current_progress)

    def get_status(self) -> SyncProgress:
        """Get current sync status."""
        return self._current_progress

    def upload_backup(self, backup_path: Path, metadata: Optional[BackupMetadata] = None) -> bool:
        """Upload a local backup to cloud storage.

        Args:
            backup_path: Path to encrypted backup file
            metadata: Optional metadata to store

        Returns:
            True if successful
        """
        if not backup_path.exists():
            self._update_progress(
                SyncStatus.ERROR, 0, 0, 0,
                "Backup file not found", str(backup_path)
            )
            return False

        try:
            file_size = backup_path.stat().st_size
            remote_key = f"backups/{backup_path.name}"

            self._update_progress(
                SyncStatus.UPLOADING, 0, 0, file_size,
                f"Uploading {backup_path.name}..."
            )

            def progress_cb(transferred: int, total: int):
                percent = (transferred / total * 100) if total > 0 else 0
                self._update_progress(
                    SyncStatus.UPLOADING, percent, transferred, total,
                    f"Uploading... {percent:.1f}%"
                )

            success = self.backend.upload(backup_path, remote_key, progress_cb)

            if success:
                # Upload metadata if provided
                if metadata:
                    meta_key = f"backups/{backup_path.stem}.meta.json"
                    meta_path = backup_path.with_suffix('.meta.json')
                    with open(meta_path, 'w') as f:
                        json.dump(metadata.to_dict(), f)
                    self.backend.upload(meta_path, meta_key)
                    meta_path.unlink()  # Clean up temp file

                self._update_progress(
                    SyncStatus.COMPLETE, 100, file_size, file_size,
                    "Upload complete"
                )
                return True
            else:
                self._update_progress(
                    SyncStatus.ERROR, 0, 0, file_size,
                    "Upload failed", "Backend error"
                )
                return False

        except Exception as e:
            self._update_progress(
                SyncStatus.ERROR, 0, 0, 0,
                "Upload failed", str(e)
            )
            return False

    def download_backup(self, remote_key: str, local_path: Optional[Path] = None) -> Optional[Path]:
        """Download a backup from cloud storage.

        Args:
            remote_key: Remote file key
            local_path: Optional local path (auto-generated if not provided)

        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            if local_path is None:
                filename = remote_key.split('/')[-1]
                local_path = self.local_backup_dir / "downloads" / filename
                local_path.parent.mkdir(parents=True, exist_ok=True)

            # Get file size first
            meta = self.backend.get_metadata(remote_key)
            total_size = meta.get('size', 0) if meta else 0

            self._update_progress(
                SyncStatus.DOWNLOADING, 0, 0, total_size,
                f"Downloading {remote_key.split('/')[-1]}..."
            )

            def progress_cb(transferred: int, total: int):
                percent = (transferred / total * 100) if total > 0 else 0
                self._update_progress(
                    SyncStatus.DOWNLOADING, percent, transferred, total,
                    f"Downloading... {percent:.1f}%"
                )

            success = self.backend.download(remote_key, local_path, progress_cb)

            if success:
                self._update_progress(
                    SyncStatus.COMPLETE, 100, total_size, total_size,
                    "Download complete"
                )
                return local_path
            else:
                self._update_progress(
                    SyncStatus.ERROR, 0, 0, total_size,
                    "Download failed", "Backend error"
                )
                return None

        except Exception as e:
            self._update_progress(
                SyncStatus.ERROR, 0, 0, 0,
                "Download failed", str(e)
            )
            return None

    def list_cloud_backups(self) -> List[Dict[str, Any]]:
        """List all backups in cloud storage.

        Returns:
            List of backup info dicts
        """
        files = self.backend.list_files("backups/")
        # Filter to only .zip files (not metadata)
        return [f for f in files if f['key'].endswith('.zip')]

    def sync_to_cloud(self, backup_path: Path, password: str) -> bool:
        """Encrypt and upload a backup to cloud.

        Args:
            backup_path: Path to unencrypted backup
            password: Encryption password

        Returns:
            True if successful
        """
        from .crypto import CryptoService

        try:
            crypto = CryptoService()

            # Create encrypted version
            encrypted_path = backup_path.with_suffix('.encrypted.zip')

            self._update_progress(
                SyncStatus.SYNCING, 10, 0, 0,
                "Encrypting backup..."
            )

            if not crypto.encrypt_file(backup_path, encrypted_path, password):
                return False

            self._update_progress(
                SyncStatus.SYNCING, 30, 0, 0,
                "Uploading encrypted backup..."
            )

            success = self.upload_backup(encrypted_path)

            # Clean up encrypted file
            if encrypted_path.exists():
                encrypted_path.unlink()

            return success

        except Exception as e:
            self._update_progress(
                SyncStatus.ERROR, 0, 0, 0,
                "Sync failed", str(e)
            )
            return False

    def restore_from_cloud(self, remote_key: str, password: str) -> Optional[Path]:
        """Download and decrypt a backup from cloud.

        Args:
            remote_key: Remote backup key
            password: Decryption password

        Returns:
            Path to decrypted backup, or None if failed
        """
        from .crypto import CryptoService

        try:
            crypto = CryptoService()

            # Download encrypted backup
            encrypted_path = self.download_backup(remote_key)
            if encrypted_path is None:
                return None

            # Decrypt
            self._update_progress(
                SyncStatus.SYNCING, 80, 0, 0,
                "Decrypting backup..."
            )

            decrypted_path = encrypted_path.with_suffix('.zip')
            if not crypto.decrypt_file(encrypted_path, decrypted_path, password):
                return None

            # Clean up encrypted file
            encrypted_path.unlink()

            self._update_progress(
                SyncStatus.COMPLETE, 100, 0, 0,
                "Restore complete"
            )

            return decrypted_path

        except Exception as e:
            self._update_progress(
                SyncStatus.ERROR, 0, 0, 0,
                "Restore failed", str(e)
            )
            return None


def create_device_id() -> str:
    """Generate a unique device identifier.

    This ID is used to identify backups from this device.
    It's stored locally and persists across app restarts.
    """
    import uuid
    import platform

    # Create a device-specific ID based on machine characteristics
    machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
    device_id = hashlib.sha256(machine_info.encode()).hexdigest()[:16]

    return f"device-{device_id}"


def get_or_create_device_id(config_dir: Path) -> str:
    """Get existing device ID or create a new one.

    Args:
        config_dir: Directory to store device ID file

    Returns:
        Device ID string
    """
    device_file = config_dir / ".device_id"

    if device_file.exists():
        return device_file.read_text().strip()

    device_id = create_device_id()
    config_dir.mkdir(parents=True, exist_ok=True)
    device_file.write_text(device_id)

    return device_id

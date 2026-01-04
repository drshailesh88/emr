"""File storage abstraction for backup blobs"""

from pathlib import Path
import hashlib
import aiofiles
import aiofiles.os
from typing import BinaryIO
import logging

logger = logging.getLogger(__name__)


class BackupStorage:
    """Manages encrypted backup blob storage"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_user_dir(self, user_id: int) -> Path:
        """Get user-specific storage directory"""
        user_dir = self.storage_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _get_backup_path(self, user_id: int, backup_id: str) -> Path:
        """Get full path for a backup file"""
        return self._get_user_dir(user_id) / f"{backup_id}.enc"

    async def save_backup(
        self,
        user_id: int,
        backup_id: str,
        file_content: bytes
    ) -> tuple[str, int]:
        """
        Save encrypted backup blob

        Returns:
            tuple: (checksum, size_bytes)
        """
        backup_path = self._get_backup_path(user_id, backup_id)

        # Calculate checksum
        checksum = hashlib.sha256(file_content).hexdigest()

        # Write file
        async with aiofiles.open(backup_path, 'wb') as f:
            await f.write(file_content)

        size_bytes = len(file_content)
        logger.info(
            f"Saved backup {backup_id} for user {user_id}: "
            f"{size_bytes} bytes, checksum={checksum[:8]}..."
        )

        return checksum, size_bytes

    async def get_backup(self, user_id: int, backup_id: str) -> bytes:
        """
        Retrieve encrypted backup blob

        Raises:
            FileNotFoundError: If backup doesn't exist
        """
        backup_path = self._get_backup_path(user_id, backup_id)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup {backup_id} not found")

        async with aiofiles.open(backup_path, 'rb') as f:
            content = await f.read()

        logger.info(
            f"Retrieved backup {backup_id} for user {user_id}: "
            f"{len(content)} bytes"
        )

        return content

    async def delete_backup(self, user_id: int, backup_id: str):
        """Delete a backup file"""
        backup_path = self._get_backup_path(user_id, backup_id)

        if backup_path.exists():
            await aiofiles.os.remove(backup_path)
            logger.info(f"Deleted backup {backup_id} for user {user_id}")

    async def get_user_backups(self, user_id: int) -> list[Path]:
        """Get list of all backup files for a user"""
        user_dir = self._get_user_dir(user_id)
        return list(user_dir.glob("*.enc"))

    def verify_checksum(self, file_content: bytes, expected_checksum: str) -> bool:
        """Verify file checksum"""
        actual_checksum = hashlib.sha256(file_content).hexdigest()
        return actual_checksum == expected_checksum


# Global storage instance
_storage: BackupStorage = None


def get_storage() -> BackupStorage:
    """Get global storage instance"""
    global _storage
    if _storage is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _storage


def init_storage(storage_path: str) -> BackupStorage:
    """Initialize global storage instance"""
    global _storage
    _storage = BackupStorage(storage_path)
    return _storage

"""Backup data models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BackupMetadata(BaseModel):
    """Backup metadata response"""
    backup_id: str
    filename: str
    size_bytes: int
    checksum: str
    device_id: Optional[str]
    device_name: Optional[str]
    created_at: datetime


class BackupUploadResponse(BaseModel):
    """Response after successful backup upload"""
    backup_id: str
    timestamp: datetime
    size_bytes: int
    message: str = "Backup uploaded successfully"


class SyncStatus(BaseModel):
    """Sync status response"""
    last_backup_time: Optional[datetime]
    backup_count: int
    total_size_bytes: int
    devices: list[str]  # List of device names that have uploaded backups

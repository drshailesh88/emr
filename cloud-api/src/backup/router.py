"""Backup API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid
import logging
from typing import Optional
import io

from .models import BackupMetadata, BackupUploadResponse, SyncStatus
from .storage import get_storage
from ..auth.jwt import get_current_user
from ..auth.models import TokenData
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["Backup"])


@router.get("/latest", response_model=BackupMetadata)
async def get_latest_backup(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get metadata of the latest backup for the authenticated user

    Returns the most recent backup's metadata without downloading the file.
    """
    db = get_db()

    async with await db.get_connection() as conn:
        cursor = await conn.execute(
            """
            SELECT backup_id, filename, size_bytes, checksum,
                   device_id, device_name, created_at
            FROM backups
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (current_user.user_id,)
        )
        backup_row = await cursor.fetchone()

        if not backup_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No backups found for this user"
            )

    return BackupMetadata(
        backup_id=backup_row["backup_id"],
        filename=backup_row["filename"],
        size_bytes=backup_row["size_bytes"],
        checksum=backup_row["checksum"],
        device_id=backup_row["device_id"],
        device_name=backup_row["device_name"],
        created_at=backup_row["created_at"]
    )


@router.get("/download/{backup_id}")
async def download_backup(
    backup_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Download an encrypted backup blob

    Returns the raw encrypted file as a binary stream.
    The client is responsible for decryption using their local key.
    """
    db = get_db()
    storage = get_storage()

    # Verify backup belongs to user
    async with await db.get_connection() as conn:
        cursor = await conn.execute(
            """
            SELECT backup_id, filename, user_id
            FROM backups
            WHERE backup_id = ?
            """,
            (backup_id,)
        )
        backup_row = await cursor.fetchone()

        if not backup_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )

        if backup_row["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this backup"
            )

    # Retrieve backup file
    try:
        backup_content = await storage.get_backup(current_user.user_id, backup_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found in storage"
        )

    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(backup_content),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={backup_row['filename']}"
        }
    )


@router.post("/upload", response_model=BackupUploadResponse)
async def upload_backup(
    file: UploadFile = File(...),
    device_id: Optional[str] = Form(None),
    device_name: Optional[str] = Form(None),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload a new encrypted backup

    - **file**: Encrypted backup blob (client-side encrypted)
    - **device_id**: Optional device identifier
    - **device_name**: Optional device name (e.g., "Desktop", "Laptop")

    The server stores the encrypted blob without decryption (zero-knowledge).
    """
    db = get_db()
    storage = get_storage()

    # Read file content
    file_content = await file.read()

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )

    # Generate unique backup ID
    backup_id = str(uuid.uuid4())

    # Save to storage
    checksum, size_bytes = await storage.save_backup(
        current_user.user_id,
        backup_id,
        file_content
    )

    # Save metadata to database
    async with await db.get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO backups
            (backup_id, user_id, filename, size_bytes, checksum, device_id, device_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                backup_id,
                current_user.user_id,
                file.filename or f"backup_{backup_id}.enc",
                size_bytes,
                checksum,
                device_id,
                device_name
            )
        )
        await conn.commit()

    logger.info(
        f"Backup uploaded: user={current_user.user_id}, "
        f"backup_id={backup_id}, size={size_bytes}"
    )

    return BackupUploadResponse(
        backup_id=backup_id,
        timestamp=datetime.utcnow(),
        size_bytes=size_bytes
    )


@router.get("/sync/status", response_model=SyncStatus)
async def get_sync_status(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get sync status for the authenticated user

    Returns information about all backups and sync state.
    """
    db = get_db()

    async with await db.get_connection() as conn:
        # Get latest backup time
        cursor = await conn.execute(
            """
            SELECT created_at
            FROM backups
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (current_user.user_id,)
        )
        latest_row = await cursor.fetchone()
        last_backup_time = latest_row["created_at"] if latest_row else None

        # Get total backup count
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM backups WHERE user_id = ?",
            (current_user.user_id,)
        )
        count_row = await cursor.fetchone()
        backup_count = count_row["count"]

        # Get total size
        cursor = await conn.execute(
            "SELECT COALESCE(SUM(size_bytes), 0) as total FROM backups WHERE user_id = ?",
            (current_user.user_id,)
        )
        size_row = await cursor.fetchone()
        total_size = size_row["total"]

        # Get unique devices
        cursor = await conn.execute(
            """
            SELECT DISTINCT device_name
            FROM backups
            WHERE user_id = ? AND device_name IS NOT NULL
            """,
            (current_user.user_id,)
        )
        device_rows = await cursor.fetchall()
        devices = [row["device_name"] for row in device_rows]

    return SyncStatus(
        last_backup_time=last_backup_time,
        backup_count=backup_count,
        total_size_bytes=total_size,
        devices=devices
    )

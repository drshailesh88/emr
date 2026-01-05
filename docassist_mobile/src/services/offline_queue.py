"""
Offline Queue Service - Manages pending edits for sync.

Queues local changes when offline and syncs them when connection is restored.
Provides:
- Add operations to queue
- Get pending operations
- Mark operations as synced/failed
- Retry logic with exponential backoff
- Persistent storage in SQLite
"""

import sqlite3
import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid


class OperationType(Enum):
    """Types of operations that can be queued."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class OperationStatus(Enum):
    """Status of queued operations."""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class QueuedOperation:
    """Represents a queued operation."""
    id: str
    operation_type: str  # insert, update, delete
    table: str  # patients, visits, investigations, etc.
    data: Dict[str, Any]  # The actual data
    created_at: str  # ISO timestamp
    retry_count: int = 0
    status: str = "pending"
    last_error: Optional[str] = None
    last_retry_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'QueuedOperation':
        """Create from dictionary."""
        return cls(**data)


class OfflineQueue:
    """
    Manages offline edit queue with retry logic.

    Usage:
        queue = OfflineQueue(db_path="data/clinic.db")

        # Add operation to queue
        op_id = queue.add_operation(
            op_type=OperationType.INSERT,
            table="visits",
            data={"patient_id": 1, "chief_complaint": "Fever"}
        )

        # Get pending operations
        pending = queue.get_pending_operations()

        # Mark as synced
        queue.mark_synced(op_id)
    """

    # Retry configuration
    MAX_RETRIES = 5
    INITIAL_RETRY_DELAY = 60  # seconds
    MAX_RETRY_DELAY = 3600  # 1 hour

    def __init__(self, db_path: str = "data/clinic.db"):
        self.db_path = db_path
        self._ensure_queue_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_queue_table(self):
        """Create sync_queue table if it doesn't exist."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    last_error TEXT,
                    last_retry_at TEXT
                )
            """)

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_queue_status
                ON sync_queue(status)
            """)

            conn.commit()
        finally:
            conn.close()

    def add_operation(
        self,
        op_type: OperationType,
        table: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Add an operation to the queue.

        Args:
            op_type: Type of operation (INSERT, UPDATE, DELETE)
            table: Table name
            data: Operation data

        Returns:
            Operation ID
        """
        operation_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        operation = QueuedOperation(
            id=operation_id,
            operation_type=op_type.value,
            table=table,
            data=data,
            created_at=created_at,
        )

        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO sync_queue (
                    id, operation_type, table_name, data, created_at,
                    retry_count, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                operation.id,
                operation.operation_type,
                operation.table,
                json.dumps(operation.data),
                operation.created_at,
                operation.retry_count,
                operation.status,
            ))
            conn.commit()
        finally:
            conn.close()

        return operation_id

    def get_pending_operations(self, limit: int = 100) -> List[QueuedOperation]:
        """
        Get pending operations that are ready to sync.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of pending operations
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM sync_queue
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))

            operations = []
            for row in cursor.fetchall():
                operations.append(QueuedOperation(
                    id=row['id'],
                    operation_type=row['operation_type'],
                    table=row['table_name'],
                    data=json.loads(row['data']),
                    created_at=row['created_at'],
                    retry_count=row['retry_count'],
                    status=row['status'],
                    last_error=row['last_error'],
                    last_retry_at=row['last_retry_at'],
                ))

            return operations
        finally:
            conn.close()

    def get_all_operations(self) -> List[QueuedOperation]:
        """Get all operations (for debugging)."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM sync_queue
                ORDER BY created_at DESC
            """)

            operations = []
            for row in cursor.fetchall():
                operations.append(QueuedOperation(
                    id=row['id'],
                    operation_type=row['operation_type'],
                    table=row['table_name'],
                    data=json.loads(row['data']),
                    created_at=row['created_at'],
                    retry_count=row['retry_count'],
                    status=row['status'],
                    last_error=row['last_error'],
                    last_retry_at=row['last_retry_at'],
                ))

            return operations
        finally:
            conn.close()

    def mark_synced(self, operation_id: str):
        """
        Mark an operation as successfully synced.

        Args:
            operation_id: ID of the operation
        """
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE sync_queue
                SET status = 'synced'
                WHERE id = ?
            """, (operation_id,))
            conn.commit()
        finally:
            conn.close()

    def mark_failed(self, operation_id: str, error: str = ""):
        """
        Mark an operation as failed and increment retry count.

        Args:
            operation_id: ID of the operation
            error: Error message
        """
        now = datetime.now().isoformat()

        conn = self._get_connection()
        try:
            # Get current retry count
            cursor = conn.execute("""
                SELECT retry_count FROM sync_queue
                WHERE id = ?
            """, (operation_id,))
            row = cursor.fetchone()

            if row:
                retry_count = row['retry_count'] + 1
                status = 'failed' if retry_count >= self.MAX_RETRIES else 'pending'

                conn.execute("""
                    UPDATE sync_queue
                    SET retry_count = ?,
                        status = ?,
                        last_error = ?,
                        last_retry_at = ?
                    WHERE id = ?
                """, (retry_count, status, error, now, operation_id))
                conn.commit()
        finally:
            conn.close()

    def get_pending_count(self) -> int:
        """
        Get number of pending operations.

        Returns:
            Count of pending operations
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM sync_queue
                WHERE status = 'pending'
            """)
            return cursor.fetchone()['count']
        finally:
            conn.close()

    def get_failed_count(self) -> int:
        """
        Get number of failed operations.

        Returns:
            Count of failed operations
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM sync_queue
                WHERE status = 'failed'
            """)
            return cursor.fetchone()['count']
        finally:
            conn.close()

    def should_retry(self, operation: QueuedOperation) -> bool:
        """
        Check if an operation should be retried based on exponential backoff.

        Args:
            operation: The queued operation

        Returns:
            True if ready to retry
        """
        if operation.retry_count >= self.MAX_RETRIES:
            return False

        if not operation.last_retry_at:
            return True

        # Calculate backoff delay
        delay = min(
            self.INITIAL_RETRY_DELAY * (2 ** operation.retry_count),
            self.MAX_RETRY_DELAY
        )

        last_retry = datetime.fromisoformat(operation.last_retry_at)
        elapsed = (datetime.now() - last_retry).total_seconds()

        return elapsed >= delay

    def clear_synced(self):
        """Remove all synced operations from the queue."""
        conn = self._get_connection()
        try:
            conn.execute("""
                DELETE FROM sync_queue
                WHERE status = 'synced'
            """)
            conn.commit()
        finally:
            conn.close()

    def clear_all(self):
        """Clear all operations (use with caution!)."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM sync_queue")
            conn.commit()
        finally:
            conn.close()

    def get_operation(self, operation_id: str) -> Optional[QueuedOperation]:
        """
        Get a specific operation by ID.

        Args:
            operation_id: ID of the operation

        Returns:
            QueuedOperation or None
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM sync_queue
                WHERE id = ?
            """, (operation_id,))
            row = cursor.fetchone()

            if row:
                return QueuedOperation(
                    id=row['id'],
                    operation_type=row['operation_type'],
                    table=row['table_name'],
                    data=json.loads(row['data']),
                    created_at=row['created_at'],
                    retry_count=row['retry_count'],
                    status=row['status'],
                    last_error=row['last_error'],
                    last_retry_at=row['last_retry_at'],
                )
            return None
        finally:
            conn.close()


# Export classes
__all__ = [
    'OfflineQueue',
    'QueuedOperation',
    'OperationType',
    'OperationStatus',
]

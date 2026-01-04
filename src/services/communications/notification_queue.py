"""Notification queue for managing and processing outbound messages."""

import logging
import sqlite3
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum
import json
import os
import uuid

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(Enum):
    """Status of notifications in queue."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Notification:
    """Notification data structure."""
    id: Optional[str] = None
    patient_id: int = 0
    phone: str = ""
    message: str = ""
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    channel: str = "whatsapp"  # whatsapp or sms
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    next_retry_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "phone": self.phone,
            "message": self.message,
            "priority": self.priority.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "channel": self.channel,
            "metadata": json.dumps(self.metadata),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "error_message": self.error_message,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'Notification':
        """Create from dictionary."""
        return Notification(
            id=data.get("id"),
            patient_id=data["patient_id"],
            phone=data["phone"],
            message=data["message"],
            priority=NotificationPriority(data.get("priority", "normal")),
            status=NotificationStatus(data.get("status", "pending")),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            channel=data.get("channel", "whatsapp"),
            metadata=json.loads(data.get("metadata", "{}")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            scheduled_for=datetime.fromisoformat(data["scheduled_for"]) if data.get("scheduled_for") else None,
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            delivered_at=datetime.fromisoformat(data["delivered_at"]) if data.get("delivered_at") else None,
            error_message=data.get("error_message"),
            next_retry_at=datetime.fromisoformat(data["next_retry_at"]) if data.get("next_retry_at") else None
        )


@dataclass
class QueueStatus:
    """Queue status statistics."""
    pending: int = 0
    processing: int = 0
    failed: int = 0
    total_today: int = 0
    sent_today: int = 0
    failed_today: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "pending": self.pending,
            "processing": self.processing,
            "failed": self.failed,
            "total_today": self.total_today,
            "sent_today": self.sent_today,
            "failed_today": self.failed_today
        }


class NotificationQueue:
    """Queue for managing outbound notifications with retry logic."""

    # Exponential backoff delays (in minutes)
    RETRY_DELAYS = [5, 15, 60, 240]  # 5min, 15min, 1hr, 4hr

    # Rate limiting (messages per minute)
    RATE_LIMIT = 20

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize notification queue.

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._processing = False

    def _init_database(self):
        """Initialize notification queue table."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_queue (
                    id TEXT PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    phone TEXT NOT NULL,
                    message TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    channel TEXT DEFAULT 'whatsapp',
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    scheduled_for TEXT,
                    sent_at TEXT,
                    delivered_at TEXT,
                    error_message TEXT,
                    next_retry_at TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notification_queue_status
                ON notification_queue(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notification_queue_scheduled
                ON notification_queue(scheduled_for)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notification_queue_priority
                ON notification_queue(priority, scheduled_for)
            """)

            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing notification queue: {e}")
            raise
        finally:
            conn.close()

    def _generate_notification_id(self) -> str:
        """Generate unique notification ID."""
        return f"NTF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def enqueue(self, notification: Notification) -> str:
        """
        Add notification to queue.

        Args:
            notification: Notification object

        Returns:
            Notification ID

        Example:
            >>> nq = NotificationQueue()
            >>> notif = Notification(
            ...     patient_id=45,
            ...     phone="9876543210",
            ...     message="Your appointment is confirmed",
            ...     priority=NotificationPriority.HIGH
            ... )
            >>> notif_id = nq.enqueue(notif)
        """
        if not notification.id:
            notification.id = self._generate_notification_id()

        if not notification.created_at:
            notification.created_at = datetime.now()

        if not notification.scheduled_for:
            notification.scheduled_for = datetime.now()

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            data = notification.to_dict()

            cursor.execute("""
                INSERT INTO notification_queue (
                    id, patient_id, phone, message, priority, status,
                    retry_count, max_retries, channel, metadata,
                    created_at, scheduled_for, sent_at, delivered_at,
                    error_message, next_retry_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["patient_id"], data["phone"], data["message"],
                data["priority"], data["status"], data["retry_count"],
                data["max_retries"], data["channel"], data["metadata"],
                data["created_at"], data["scheduled_for"], data["sent_at"],
                data["delivered_at"], data["error_message"], data["next_retry_at"]
            ))

            conn.commit()
            logger.info(f"Enqueued notification {notification.id}")
            return notification.id

        except Exception as e:
            logger.error(f"Error enqueuing notification: {e}")
            raise
        finally:
            conn.close()

    async def process_queue(self, max_batch_size: int = 50) -> Dict[str, int]:
        """
        Process pending notifications in the queue.

        Args:
            max_batch_size: Maximum notifications to process in one batch

        Returns:
            Dictionary with processing statistics

        Example:
            >>> nq = NotificationQueue()
            >>> import asyncio
            >>> stats = asyncio.run(nq.process_queue())
            >>> print(f"Sent: {stats['sent']}, Failed: {stats['failed']}")
        """
        if self._processing:
            logger.warning("Queue processing already in progress")
            return {"sent": 0, "failed": 0, "skipped": 0}

        self._processing = True
        stats = {"sent": 0, "failed": 0, "skipped": 0}

        try:
            # Import WhatsApp client
            from ..whatsapp.client import WhatsAppClient

            # Get pending notifications
            notifications = self._get_pending_notifications(max_batch_size)

            if not notifications:
                logger.info("No pending notifications to process")
                return stats

            logger.info(f"Processing {len(notifications)} notifications")

            # Initialize WhatsApp client
            whatsapp = WhatsAppClient()

            # Process notifications with rate limiting
            for i, notification in enumerate(notifications):
                # Rate limiting: wait if needed
                if i > 0 and i % self.RATE_LIMIT == 0:
                    logger.info(f"Rate limit reached, waiting 60 seconds...")
                    await asyncio.sleep(60)

                try:
                    # Update status to processing
                    self._update_status(notification.id, NotificationStatus.PROCESSING)

                    # Send via WhatsApp
                    if notification.channel == "whatsapp":
                        result = await whatsapp.send_text(
                            to=notification.phone,
                            message=notification.message
                        )

                        if result.status.value in ["sent", "delivered"]:
                            # Success
                            self._mark_sent(notification.id, result.message_id)
                            stats["sent"] += 1
                            logger.info(f"Sent notification {notification.id}")
                        else:
                            # Failed
                            self._mark_failed(notification.id, result.error)
                            stats["failed"] += 1
                            logger.error(f"Failed to send notification {notification.id}: {result.error}")
                    else:
                        # SMS not implemented yet
                        logger.warning(f"SMS channel not implemented for {notification.id}")
                        stats["skipped"] += 1

                except Exception as e:
                    logger.error(f"Error processing notification {notification.id}: {e}")
                    self._mark_failed(notification.id, str(e))
                    stats["failed"] += 1

            # Close WhatsApp client
            await whatsapp.close()

            logger.info(f"Queue processing complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in queue processing: {e}")
            raise
        finally:
            self._processing = False

    def get_queue_status(self) -> QueueStatus:
        """
        Get current queue status.

        Returns:
            QueueStatus object with statistics

        Example:
            >>> nq = NotificationQueue()
            >>> status = nq.get_queue_status()
            >>> print(f"Pending: {status.pending}, Failed: {status.failed}")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Get counts by status
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as processing,
                    SUM(CASE WHEN status = ? OR status = ? THEN 1 ELSE 0 END) as failed
                FROM notification_queue
            """, (
                NotificationStatus.PENDING.value,
                NotificationStatus.PROCESSING.value,
                NotificationStatus.FAILED.value,
                NotificationStatus.RETRY.value
            ))

            row = cursor.fetchone()

            # Get today's statistics
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = ? OR status = ? THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed
                FROM notification_queue
                WHERE created_at >= ?
            """, (
                NotificationStatus.SENT.value,
                NotificationStatus.DELIVERED.value,
                NotificationStatus.FAILED.value,
                today_start.isoformat()
            ))

            today_row = cursor.fetchone()

            return QueueStatus(
                pending=row[0] or 0,
                processing=row[1] or 0,
                failed=row[2] or 0,
                total_today=today_row[0] or 0,
                sent_today=today_row[1] or 0,
                failed_today=today_row[2] or 0
            )

        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return QueueStatus()
        finally:
            conn.close()

    def retry_failed(self, notification_id: str) -> bool:
        """
        Retry a failed notification.

        Args:
            notification_id: Notification ID to retry

        Returns:
            True if retry scheduled, False otherwise

        Example:
            >>> nq = NotificationQueue()
            >>> success = nq.retry_failed("NTF-20240115-ABC123")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # Get notification
            cursor.execute("""
                SELECT * FROM notification_queue WHERE id = ?
            """, (notification_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Notification {notification_id} not found")
                return False

            notification = Notification.from_dict(dict(row))

            # Check if retry count exceeded
            if notification.retry_count >= notification.max_retries:
                logger.warning(f"Notification {notification_id} has exceeded max retries")
                return False

            # Calculate next retry time with exponential backoff
            retry_delay_minutes = self.RETRY_DELAYS[
                min(notification.retry_count, len(self.RETRY_DELAYS) - 1)
            ]
            next_retry = datetime.now() + timedelta(minutes=retry_delay_minutes)

            # Update notification for retry
            cursor.execute("""
                UPDATE notification_queue
                SET status = ?,
                    retry_count = retry_count + 1,
                    next_retry_at = ?,
                    scheduled_for = ?
                WHERE id = ?
            """, (
                NotificationStatus.RETRY.value,
                next_retry.isoformat(),
                next_retry.isoformat(),
                notification_id
            ))

            conn.commit()
            logger.info(f"Scheduled retry for {notification_id} at {next_retry}")
            return True

        except Exception as e:
            logger.error(f"Error retrying notification {notification_id}: {e}")
            return False
        finally:
            conn.close()

    def cancel_notification(self, notification_id: str) -> bool:
        """
        Cancel a pending notification.

        Args:
            notification_id: Notification ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM notification_queue
                WHERE id = ? AND status = ?
            """, (notification_id, NotificationStatus.PENDING.value))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Cancelled notification {notification_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling notification {notification_id}: {e}")
            return False
        finally:
            conn.close()

    def _get_pending_notifications(self, limit: int) -> List[Notification]:
        """Get pending notifications ordered by priority and scheduled time."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # Priority order: urgent > high > normal > low
            priority_order = {
                NotificationPriority.URGENT.value: 1,
                NotificationPriority.HIGH.value: 2,
                NotificationPriority.NORMAL.value: 3,
                NotificationPriority.LOW.value: 4
            }

            cursor.execute("""
                SELECT * FROM notification_queue
                WHERE (status = ? OR status = ?)
                AND (scheduled_for IS NULL OR scheduled_for <= ?)
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    scheduled_for ASC
                LIMIT ?
            """, (
                NotificationStatus.PENDING.value,
                NotificationStatus.RETRY.value,
                datetime.now().isoformat(),
                limit
            ))

            rows = cursor.fetchall()
            return [Notification.from_dict(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}")
            return []
        finally:
            conn.close()

    def _update_status(self, notification_id: str, status: NotificationStatus):
        """Update notification status."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notification_queue
                SET status = ?
                WHERE id = ?
            """, (status.value, notification_id))
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating status for {notification_id}: {e}")
        finally:
            conn.close()

    def _mark_sent(self, notification_id: str, message_id: Optional[str] = None):
        """Mark notification as sent."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            metadata = {"whatsapp_message_id": message_id} if message_id else {}
            cursor.execute("""
                UPDATE notification_queue
                SET status = ?,
                    sent_at = ?,
                    metadata = ?
                WHERE id = ?
            """, (
                NotificationStatus.SENT.value,
                datetime.now().isoformat(),
                json.dumps(metadata),
                notification_id
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as sent: {e}")
        finally:
            conn.close()

    def _mark_failed(self, notification_id: str, error_message: str):
        """Mark notification as failed and schedule retry if possible."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # Get current notification
            cursor.execute("SELECT * FROM notification_queue WHERE id = ?", (notification_id,))
            row = cursor.fetchone()

            if not row:
                return

            notification = Notification.from_dict(dict(row))

            # Check if we should retry
            if notification.retry_count < notification.max_retries:
                # Schedule retry
                self.retry_failed(notification_id)
            else:
                # Mark as permanently failed
                cursor.execute("""
                    UPDATE notification_queue
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, (NotificationStatus.FAILED.value, error_message, notification_id))
                conn.commit()

        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as failed: {e}")
        finally:
            conn.close()

"""Broadcast service for clinic notices, health tips, and campaigns."""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum
import json
import os
import uuid

logger = logging.getLogger(__name__)


class BroadcastType(Enum):
    """Types of broadcasts."""
    CLINIC_NOTICE = "clinic_notice"
    HEALTH_TIP = "health_tip"
    CAMPAIGN = "campaign"


class BroadcastStatus(Enum):
    """Status of broadcast."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DeliveryStats:
    """Delivery statistics for a broadcast."""
    total: int = 0
    sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0
    pending: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "sent": self.sent,
            "delivered": self.delivered,
            "read": self.read,
            "failed": self.failed,
            "pending": self.pending
        }

    @staticmethod
    def from_dict(data: dict) -> 'DeliveryStats':
        """Create from dictionary."""
        return DeliveryStats(
            total=data.get("total", 0),
            sent=data.get("sent", 0),
            delivered=data.get("delivered", 0),
            read=data.get("read", 0),
            failed=data.get("failed", 0),
            pending=data.get("pending", 0)
        )


@dataclass
class Segment:
    """Patient segment for targeted broadcasts."""
    id: Optional[str] = None
    name: str = ""
    criteria: Dict[str, Any] = field(default_factory=dict)
    patient_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "criteria": json.dumps(self.criteria),
            "patient_count": self.patient_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'Segment':
        """Create from dictionary."""
        return Segment(
            id=data.get("id"),
            name=data["name"],
            criteria=json.loads(data.get("criteria", "{}")),
            patient_count=data.get("patient_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


@dataclass
class Campaign:
    """Marketing campaign."""
    id: Optional[str] = None
    name: str = ""
    description: str = ""
    message: str = ""
    segment_id: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    status: BroadcastStatus = BroadcastStatus.DRAFT
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "message": self.message,
            "segment_id": self.segment_id,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class BroadcastService:
    """Service for sending broadcast messages to patients."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize broadcast service.

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize broadcast database tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Broadcasts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    segment_id TEXT,
                    scheduled_time TEXT,
                    status TEXT NOT NULL,
                    delivery_stats TEXT,
                    created_at TEXT,
                    completed_at TEXT
                )
            """)

            # Broadcast recipients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcast_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    broadcast_id TEXT NOT NULL,
                    patient_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    sent_at TEXT,
                    delivered_at TEXT,
                    read_at TEXT,
                    error_message TEXT,
                    FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id),
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Patient segments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patient_segments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    criteria TEXT NOT NULL,
                    patient_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Patient preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patient_communication_preferences (
                    patient_id INTEGER PRIMARY KEY,
                    opt_out_broadcasts BOOLEAN DEFAULT 0,
                    opt_out_health_tips BOOLEAN DEFAULT 0,
                    opt_out_reminders BOOLEAN DEFAULT 0,
                    preferred_language TEXT DEFAULT 'en',
                    preferred_time TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_broadcasts_status
                ON broadcasts(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_broadcast_recipients_broadcast_id
                ON broadcast_recipients(broadcast_id)
            """)

            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing broadcast database: {e}")
            raise
        finally:
            conn.close()

    def _generate_broadcast_id(self) -> str:
        """Generate unique broadcast ID."""
        return f"BC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def _generate_segment_id(self) -> str:
        """Generate unique segment ID."""
        return f"SEG-{uuid.uuid4().hex[:8].upper()}"

    def send_clinic_notice(
        self,
        patient_ids: List[int],
        message: str,
        schedule_time: Optional[datetime] = None,
        name: str = "Clinic Notice"
    ) -> str:
        """
        Send clinic notice (holiday, unavailability, etc.).

        Args:
            patient_ids: List of patient IDs to send to
            message: Notice message
            schedule_time: When to send (None for immediate)
            name: Name of the notice

        Returns:
            Broadcast ID

        Example:
            >>> bs = BroadcastService()
            >>> patient_ids = [1, 2, 3, 4, 5]
            >>> message = "Clinic will be closed on 26-Jan for Republic Day"
            >>> broadcast_id = bs.send_clinic_notice(patient_ids, message)
        """
        broadcast_id = self._generate_broadcast_id()

        # Filter out patients who have opted out
        eligible_patients = self._filter_opted_out_patients(patient_ids, BroadcastType.CLINIC_NOTICE)

        status = BroadcastStatus.SCHEDULED if schedule_time else BroadcastStatus.SENDING

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Create broadcast record
            cursor.execute("""
                INSERT INTO broadcasts (
                    id, type, name, message, scheduled_time, status,
                    delivery_stats, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                broadcast_id,
                BroadcastType.CLINIC_NOTICE.value,
                name,
                message,
                schedule_time.isoformat() if schedule_time else None,
                status.value,
                json.dumps(DeliveryStats(total=len(eligible_patients), pending=len(eligible_patients)).to_dict()),
                datetime.now().isoformat()
            ))

            # Create recipient records
            for patient_id in eligible_patients:
                cursor.execute("""
                    INSERT INTO broadcast_recipients (
                        broadcast_id, patient_id, status
                    ) VALUES (?, ?, ?)
                """, (broadcast_id, patient_id, "pending"))

            conn.commit()
            logger.info(f"Created clinic notice broadcast {broadcast_id} for {len(eligible_patients)} patients")

        except Exception as e:
            logger.error(f"Error creating clinic notice: {e}")
            raise
        finally:
            conn.close()

        return broadcast_id

    def send_health_tip(
        self,
        segment: str,
        tip: str,
        schedule_time: Optional[datetime] = None
    ) -> str:
        """
        Send health tip to patient segment.

        Args:
            segment: Segment name ("diabetics", "hypertensives", "all", etc.)
            tip: Health tip message
            schedule_time: When to send (None for immediate)

        Returns:
            Broadcast ID

        Example:
            >>> bs = BroadcastService()
            >>> tip = "Drink at least 8 glasses of water daily for better health"
            >>> broadcast_id = bs.send_health_tip("all", tip)
        """
        broadcast_id = self._generate_broadcast_id()

        # Get patients in segment
        patient_ids = self._get_segment_patients(segment)
        eligible_patients = self._filter_opted_out_patients(patient_ids, BroadcastType.HEALTH_TIP)

        status = BroadcastStatus.SCHEDULED if schedule_time else BroadcastStatus.SENDING

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO broadcasts (
                    id, type, name, message, scheduled_time, status,
                    delivery_stats, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                broadcast_id,
                BroadcastType.HEALTH_TIP.value,
                f"Health Tip - {segment}",
                tip,
                schedule_time.isoformat() if schedule_time else None,
                status.value,
                json.dumps(DeliveryStats(total=len(eligible_patients), pending=len(eligible_patients)).to_dict()),
                datetime.now().isoformat()
            ))

            for patient_id in eligible_patients:
                cursor.execute("""
                    INSERT INTO broadcast_recipients (
                        broadcast_id, patient_id, status
                    ) VALUES (?, ?, ?)
                """, (broadcast_id, patient_id, "pending"))

            conn.commit()
            logger.info(f"Created health tip broadcast {broadcast_id} for segment '{segment}'")

        except Exception as e:
            logger.error(f"Error creating health tip broadcast: {e}")
            raise
        finally:
            conn.close()

        return broadcast_id

    def send_campaign(self, campaign: Campaign) -> str:
        """
        Send marketing campaign.

        Args:
            campaign: Campaign object

        Returns:
            Broadcast ID

        Example:
            >>> bs = BroadcastService()
            >>> campaign = Campaign(
            ...     name="Free Diabetes Screening Camp",
            ...     message="Join our free diabetes screening on 15-Jan...",
            ...     segment_id="SEG-DIABETES"
            ... )
            >>> broadcast_id = bs.send_campaign(campaign)
        """
        if not campaign.id:
            campaign.id = self._generate_broadcast_id()

        # Get patients from segment
        if campaign.segment_id:
            segment = self.get_segment(campaign.segment_id)
            if segment:
                patient_ids = self._get_patients_by_criteria(segment.criteria)
            else:
                patient_ids = []
        else:
            patient_ids = self._get_all_patient_ids()

        eligible_patients = self._filter_opted_out_patients(patient_ids, BroadcastType.CAMPAIGN)

        status = BroadcastStatus.SCHEDULED if campaign.scheduled_time else BroadcastStatus.SENDING

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO broadcasts (
                    id, type, name, message, segment_id, scheduled_time, status,
                    delivery_stats, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign.id,
                BroadcastType.CAMPAIGN.value,
                campaign.name,
                campaign.message,
                campaign.segment_id,
                campaign.scheduled_time.isoformat() if campaign.scheduled_time else None,
                status.value,
                json.dumps(DeliveryStats(total=len(eligible_patients), pending=len(eligible_patients)).to_dict()),
                datetime.now().isoformat()
            ))

            for patient_id in eligible_patients:
                cursor.execute("""
                    INSERT INTO broadcast_recipients (
                        broadcast_id, patient_id, status
                    ) VALUES (?, ?, ?)
                """, (campaign.id, patient_id, "pending"))

            conn.commit()
            logger.info(f"Created campaign broadcast {campaign.id} for {len(eligible_patients)} patients")

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
        finally:
            conn.close()

        return campaign.id

    def get_delivery_stats(self, broadcast_id: str) -> Optional[DeliveryStats]:
        """
        Get delivery statistics for a broadcast.

        Args:
            broadcast_id: Broadcast ID

        Returns:
            DeliveryStats object or None if not found

        Example:
            >>> bs = BroadcastService()
            >>> stats = bs.get_delivery_stats("BC-20240115-ABC123")
            >>> print(f"Sent: {stats.sent}, Delivered: {stats.delivered}")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # Get counts from recipients table
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' OR status = 'delivered' OR status = 'read' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'delivered' OR status = 'read' THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as read,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM broadcast_recipients
                WHERE broadcast_id = ?
            """, (broadcast_id,))

            row = cursor.fetchone()
            if row:
                return DeliveryStats(
                    total=row["total"] or 0,
                    sent=row["sent"] or 0,
                    delivered=row["delivered"] or 0,
                    read=row["read"] or 0,
                    failed=row["failed"] or 0,
                    pending=row["pending"] or 0
                )
            return None

        except Exception as e:
            logger.error(f"Error getting delivery stats for {broadcast_id}: {e}")
            return None
        finally:
            conn.close()

    def create_patient_segment(self, name: str, criteria: dict) -> Segment:
        """
        Create a reusable patient segment.

        Args:
            name: Segment name
            criteria: Filter criteria (diagnosis, age_range, last_visit_days, gender, etc.)

        Returns:
            Segment object

        Example:
            >>> bs = BroadcastService()
            >>> segment = bs.create_patient_segment(
            ...     "Diabetic Patients",
            ...     {"diagnosis": "diabetes", "age_range": [40, 80]}
            ... )
        """
        segment_id = self._generate_segment_id()

        # Count patients matching criteria
        patient_count = len(self._get_patients_by_criteria(criteria))

        segment = Segment(
            id=segment_id,
            name=name,
            criteria=criteria,
            patient_count=patient_count,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            data = segment.to_dict()
            cursor.execute("""
                INSERT INTO patient_segments (
                    id, name, criteria, patient_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["name"], data["criteria"],
                data["patient_count"], data["created_at"], data["updated_at"]
            ))
            conn.commit()
            logger.info(f"Created patient segment '{name}' with {patient_count} patients")

        except Exception as e:
            logger.error(f"Error creating segment: {e}")
            raise
        finally:
            conn.close()

        return segment

    def get_segment(self, segment_id: str) -> Optional[Segment]:
        """Get segment by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patient_segments WHERE id = ?", (segment_id,))
            row = cursor.fetchone()
            if row:
                return Segment.from_dict(dict(row))
            return None
        except Exception as e:
            logger.error(f"Error getting segment {segment_id}: {e}")
            return None
        finally:
            conn.close()

    def update_broadcast_status(
        self,
        broadcast_id: str,
        status: BroadcastStatus
    ) -> bool:
        """Update broadcast status."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            completed_at = datetime.now().isoformat() if status == BroadcastStatus.COMPLETED else None

            cursor.execute("""
                UPDATE broadcasts
                SET status = ?, completed_at = ?
                WHERE id = ?
            """, (status.value, completed_at, broadcast_id))
            conn.commit()

            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating broadcast status: {e}")
            return False
        finally:
            conn.close()

    def _filter_opted_out_patients(
        self,
        patient_ids: List[int],
        broadcast_type: BroadcastType
    ) -> List[int]:
        """Filter out patients who have opted out of this type of communication."""
        if not patient_ids:
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Determine which opt-out column to check
            opt_out_column = {
                BroadcastType.CLINIC_NOTICE: "opt_out_broadcasts",
                BroadcastType.HEALTH_TIP: "opt_out_health_tips",
                BroadcastType.CAMPAIGN: "opt_out_broadcasts"
            }.get(broadcast_type, "opt_out_broadcasts")

            placeholders = ",".join("?" * len(patient_ids))
            cursor.execute(f"""
                SELECT patient_id FROM patient_communication_preferences
                WHERE patient_id IN ({placeholders})
                AND {opt_out_column} = 1
            """, patient_ids)

            opted_out = {row[0] for row in cursor.fetchall()}
            return [pid for pid in patient_ids if pid not in opted_out]

        except Exception as e:
            logger.error(f"Error filtering opted-out patients: {e}")
            return patient_ids  # Return all on error to be safe
        finally:
            conn.close()

    def _get_segment_patients(self, segment: str) -> List[int]:
        """Get patient IDs for a predefined segment."""
        if segment == "all":
            return self._get_all_patient_ids()

        # Map common segments to criteria
        segment_criteria = {
            "diabetics": {"diagnosis": "diabetes"},
            "hypertensives": {"diagnosis": "hypertension"},
            "cardiac": {"diagnosis": "cardiac"},
        }

        criteria = segment_criteria.get(segment.lower(), {})
        return self._get_patients_by_criteria(criteria)

    def _get_patients_by_criteria(self, criteria: dict) -> List[int]:
        """Get patient IDs matching criteria."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Build query based on criteria
            conditions = []
            params = []

            if "diagnosis" in criteria:
                conditions.append("""
                    p.id IN (
                        SELECT DISTINCT patient_id FROM visits
                        WHERE diagnosis LIKE ?
                    )
                """)
                params.append(f"%{criteria['diagnosis']}%")

            if "age_range" in criteria:
                min_age, max_age = criteria["age_range"]
                conditions.append("p.age BETWEEN ? AND ?")
                params.extend([min_age, max_age])

            if "gender" in criteria:
                conditions.append("p.gender = ?")
                params.append(criteria["gender"])

            if "last_visit_days" in criteria:
                conditions.append("""
                    p.id IN (
                        SELECT patient_id FROM visits
                        WHERE julianday('now') - julianday(visit_date) <= ?
                    )
                """)
                params.append(criteria["last_visit_days"])

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT id FROM patients p WHERE {where_clause}"

            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting patients by criteria: {e}")
            return []
        finally:
            conn.close()

    def _get_all_patient_ids(self) -> List[int]:
        """Get all patient IDs."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM patients WHERE phone IS NOT NULL AND phone != ''")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all patient IDs: {e}")
            return []
        finally:
            conn.close()

"""Reminder service for appointment, follow-up, medication, and preventive care reminders."""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


class ReminderType(Enum):
    """Types of reminders."""
    APPOINTMENT = "appointment"
    FOLLOW_UP = "follow_up"
    MEDICATION = "medication"
    PREVENTIVE_CARE = "preventive_care"
    LAB_DUE = "lab_due"


class ReminderChannel(Enum):
    """Communication channels for reminders."""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    BOTH = "both"


class ReminderStatus(Enum):
    """Status of reminders."""
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Reminder:
    """Reminder data structure."""
    id: Optional[str] = None
    patient_id: int = 0
    type: ReminderType = ReminderType.APPOINTMENT
    scheduled_time: datetime = field(default_factory=datetime.now)
    message: str = ""
    channel: ReminderChannel = ReminderChannel.WHATSAPP
    status: ReminderStatus = ReminderStatus.SCHEDULED
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "type": self.type.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            "message": self.message,
            "channel": self.channel.value,
            "status": self.status.value,
            "metadata": json.dumps(self.metadata),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error_message": self.error_message
        }

    @staticmethod
    def from_dict(data: dict) -> 'Reminder':
        """Create Reminder from dictionary."""
        return Reminder(
            id=data.get("id"),
            patient_id=data["patient_id"],
            type=ReminderType(data["type"]),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            message=data["message"],
            channel=ReminderChannel(data["channel"]),
            status=ReminderStatus(data["status"]),
            metadata=json.loads(data.get("metadata", "{}")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            error_message=data.get("error_message")
        )


class ReminderService:
    """Service for scheduling and managing patient reminders."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize reminder service.

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize reminder database table."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    message TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT,
                    sent_at TEXT,
                    error_message TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_patient_id
                ON reminders(patient_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_time
                ON reminders(scheduled_time)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_status
                ON reminders(status)
            """)

            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing reminder database: {e}")
            raise
        finally:
            conn.close()

    def _generate_reminder_id(self) -> str:
        """Generate unique reminder ID."""
        import uuid
        return f"REM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def schedule_appointment_reminder(
        self,
        appointment: dict,
        patient_preferences: Optional[dict] = None
    ) -> List[str]:
        """
        Schedule appointment reminders (1 day before and 2 hours before).

        Args:
            appointment: Dictionary with keys: id, patient_id, doctor_name,
                        appointment_time, clinic_name, clinic_phone
            patient_preferences: Patient communication preferences (time windows, channel)

        Returns:
            List of reminder IDs created

        Example:
            >>> rs = ReminderService()
            >>> appointment = {
            ...     "id": 123,
            ...     "patient_id": 45,
            ...     "doctor_name": "Dr. Sharma",
            ...     "appointment_time": datetime(2024, 1, 15, 10, 0),
            ...     "clinic_name": "DocAssist Clinic",
            ...     "clinic_phone": "9876543210"
            ... }
            >>> reminder_ids = rs.schedule_appointment_reminder(appointment)
        """
        reminder_ids = []
        appointment_time = appointment["appointment_time"]

        if isinstance(appointment_time, str):
            appointment_time = datetime.fromisoformat(appointment_time)

        # Get patient preferences
        channel = ReminderChannel.WHATSAPP
        if patient_preferences:
            pref_channel = patient_preferences.get("preferred_channel", "whatsapp")
            channel = ReminderChannel(pref_channel)

        # Schedule 1 day before reminder
        one_day_before = appointment_time - timedelta(days=1)
        one_day_before = one_day_before.replace(hour=18, minute=0)  # Send at 6 PM

        # Schedule 2 hours before reminder
        two_hours_before = appointment_time - timedelta(hours=2)

        # Only schedule if times are in the future
        now = datetime.now()

        for reminder_time, reminder_type_suffix in [
            (one_day_before, "1day"),
            (two_hours_before, "2hrs")
        ]:
            if reminder_time > now:
                reminder = Reminder(
                    id=self._generate_reminder_id(),
                    patient_id=appointment["patient_id"],
                    type=ReminderType.APPOINTMENT,
                    scheduled_time=reminder_time,
                    message="",  # Will be populated by template manager
                    channel=channel,
                    status=ReminderStatus.SCHEDULED,
                    metadata={
                        "appointment_id": appointment.get("id"),
                        "doctor_name": appointment.get("doctor_name", ""),
                        "appointment_time": appointment_time.isoformat(),
                        "clinic_name": appointment.get("clinic_name", ""),
                        "clinic_phone": appointment.get("clinic_phone", ""),
                        "reminder_type": reminder_type_suffix
                    },
                    created_at=datetime.now()
                )

                self._save_reminder(reminder)
                reminder_ids.append(reminder.id)
                logger.info(f"Scheduled appointment reminder {reminder.id} for {reminder_time}")

        return reminder_ids

    def schedule_follow_up_reminder(
        self,
        visit: dict,
        patient_preferences: Optional[dict] = None
    ) -> Optional[str]:
        """
        Schedule follow-up reminder based on visit data.

        Args:
            visit: Dictionary with keys: patient_id, follow_up_date, doctor_name, clinic_phone
            patient_preferences: Patient communication preferences

        Returns:
            Reminder ID if scheduled, None otherwise

        Example:
            >>> rs = ReminderService()
            >>> visit = {
            ...     "patient_id": 45,
            ...     "follow_up_date": date(2024, 2, 1),
            ...     "doctor_name": "Dr. Sharma",
            ...     "clinic_phone": "9876543210"
            ... }
            >>> reminder_id = rs.schedule_follow_up_reminder(visit)
        """
        follow_up_date = visit.get("follow_up_date")
        if not follow_up_date:
            return None

        if isinstance(follow_up_date, str):
            follow_up_date = date.fromisoformat(follow_up_date)

        # Schedule reminder 3 days before follow-up date
        reminder_date = follow_up_date - timedelta(days=3)
        reminder_time = datetime.combine(reminder_date, datetime.min.time()).replace(hour=18)

        if reminder_time <= datetime.now():
            return None

        channel = ReminderChannel.WHATSAPP
        if patient_preferences:
            pref_channel = patient_preferences.get("preferred_channel", "whatsapp")
            channel = ReminderChannel(pref_channel)

        reminder = Reminder(
            id=self._generate_reminder_id(),
            patient_id=visit["patient_id"],
            type=ReminderType.FOLLOW_UP,
            scheduled_time=reminder_time,
            message="",
            channel=channel,
            status=ReminderStatus.SCHEDULED,
            metadata={
                "follow_up_date": follow_up_date.isoformat(),
                "doctor_name": visit.get("doctor_name", ""),
                "clinic_phone": visit.get("clinic_phone", "")
            },
            created_at=datetime.now()
        )

        self._save_reminder(reminder)
        logger.info(f"Scheduled follow-up reminder {reminder.id} for {reminder_time}")
        return reminder.id

    def schedule_medication_reminders(
        self,
        prescription: dict,
        patient: dict,
        patient_preferences: Optional[dict] = None
    ) -> List[str]:
        """
        Schedule daily medication reminders for a prescription.

        Args:
            prescription: Dictionary with medications list
            patient: Patient information (id, name)
            patient_preferences: Patient communication preferences

        Returns:
            List of reminder IDs created

        Example:
            >>> rs = ReminderService()
            >>> prescription = {
            ...     "medications": [
            ...         {
            ...             "drug_name": "Metformin",
            ...             "dose": "500mg",
            ...             "frequency": "BD",
            ...             "duration": "30 days",
            ...             "instructions": "after meals"
            ...         }
            ...     ]
            ... }
            >>> patient = {"id": 45, "name": "Ram Lal"}
            >>> reminder_ids = rs.schedule_medication_reminders(prescription, patient)
        """
        reminder_ids = []
        medications = prescription.get("medications", [])

        if not medications:
            return reminder_ids

        channel = ReminderChannel.WHATSAPP
        if patient_preferences:
            pref_channel = patient_preferences.get("preferred_channel", "whatsapp")
            channel = ReminderChannel(pref_channel)

        # Get preferred reminder times from preferences, default to 9 AM and 9 PM
        reminder_times = patient_preferences.get("medication_reminder_times", ["09:00", "21:00"]) if patient_preferences else ["09:00", "21:00"]

        # Schedule reminders for each medication
        for med in medications:
            duration_str = med.get("duration", "7 days")
            try:
                # Parse duration (e.g., "30 days", "2 weeks")
                if "week" in duration_str.lower():
                    days = int(duration_str.split()[0]) * 7
                else:
                    days = int(duration_str.split()[0])
            except (ValueError, IndexError):
                days = 7  # Default to 7 days

            # Create one reminder per day for the duration
            for day in range(min(days, 90)):  # Cap at 90 days to avoid too many reminders
                for time_str in reminder_times:
                    hour, minute = map(int, time_str.split(":"))
                    reminder_time = datetime.now() + timedelta(days=day)
                    reminder_time = reminder_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    if reminder_time <= datetime.now():
                        continue

                    reminder = Reminder(
                        id=self._generate_reminder_id(),
                        patient_id=patient["id"],
                        type=ReminderType.MEDICATION,
                        scheduled_time=reminder_time,
                        message="",
                        channel=channel,
                        status=ReminderStatus.SCHEDULED,
                        metadata={
                            "medication": med.get("drug_name", ""),
                            "dose": med.get("dose", ""),
                            "frequency": med.get("frequency", ""),
                            "instructions": med.get("instructions", "")
                        },
                        created_at=datetime.now()
                    )

                    self._save_reminder(reminder)
                    reminder_ids.append(reminder.id)

            if reminder_ids:
                logger.info(f"Scheduled {len(reminder_ids)} medication reminders for patient {patient['id']}")

        return reminder_ids

    def schedule_preventive_care(
        self,
        patient: dict,
        patient_preferences: Optional[dict] = None
    ) -> List[str]:
        """
        Schedule preventive care reminders (annual checkup, screenings).

        Args:
            patient: Patient dictionary with id, age, gender, chronic_conditions
            patient_preferences: Patient communication preferences

        Returns:
            List of reminder IDs created

        Example:
            >>> rs = ReminderService()
            >>> patient = {
            ...     "id": 45,
            ...     "age": 65,
            ...     "gender": "M",
            ...     "chronic_conditions": ["diabetes", "hypertension"]
            ... }
            >>> reminder_ids = rs.schedule_preventive_care(patient)
        """
        reminder_ids = []

        channel = ReminderChannel.WHATSAPP
        if patient_preferences:
            pref_channel = patient_preferences.get("preferred_channel", "whatsapp")
            channel = ReminderChannel(pref_channel)

        # Annual health checkup reminder (1 year from last checkup or registration)
        annual_checkup_date = datetime.now() + timedelta(days=365)
        reminder_time = annual_checkup_date.replace(hour=18, minute=0)

        reminder = Reminder(
            id=self._generate_reminder_id(),
            patient_id=patient["id"],
            type=ReminderType.PREVENTIVE_CARE,
            scheduled_time=reminder_time,
            message="",
            channel=channel,
            status=ReminderStatus.SCHEDULED,
            metadata={
                "preventive_type": "annual_checkup",
                "description": "Annual health checkup"
            },
            created_at=datetime.now()
        )
        self._save_reminder(reminder)
        reminder_ids.append(reminder.id)

        # Condition-specific preventive care
        chronic_conditions = patient.get("chronic_conditions", [])

        # Diabetes: HbA1c every 3 months
        if "diabetes" in chronic_conditions:
            for months in [3, 6, 9, 12]:
                hba1c_date = datetime.now() + timedelta(days=months * 30)
                reminder = Reminder(
                    id=self._generate_reminder_id(),
                    patient_id=patient["id"],
                    type=ReminderType.PREVENTIVE_CARE,
                    scheduled_time=hba1c_date.replace(hour=18, minute=0),
                    message="",
                    channel=channel,
                    status=ReminderStatus.SCHEDULED,
                    metadata={
                        "preventive_type": "hba1c_screening",
                        "description": "HbA1c test for diabetes monitoring"
                    },
                    created_at=datetime.now()
                )
                self._save_reminder(reminder)
                reminder_ids.append(reminder.id)

        # Women over 40: Annual mammogram
        if patient.get("gender") == "F" and patient.get("age", 0) >= 40:
            mammo_date = datetime.now() + timedelta(days=365)
            reminder = Reminder(
                id=self._generate_reminder_id(),
                patient_id=patient["id"],
                type=ReminderType.PREVENTIVE_CARE,
                scheduled_time=mammo_date.replace(hour=18, minute=0),
                message="",
                channel=channel,
                status=ReminderStatus.SCHEDULED,
                metadata={
                    "preventive_type": "mammogram",
                    "description": "Annual mammogram screening"
                },
                created_at=datetime.now()
            )
            self._save_reminder(reminder)
            reminder_ids.append(reminder.id)

        logger.info(f"Scheduled {len(reminder_ids)} preventive care reminders for patient {patient['id']}")
        return reminder_ids

    def schedule_lab_due_reminder(
        self,
        patient: dict,
        test: str,
        due_date: date,
        patient_preferences: Optional[dict] = None
    ) -> Optional[str]:
        """
        Schedule reminder for overdue or upcoming lab test.

        Args:
            patient: Patient dictionary
            test: Test name (e.g., "HbA1c", "Lipid Profile")
            due_date: When the test is due
            patient_preferences: Patient communication preferences

        Returns:
            Reminder ID if scheduled, None otherwise

        Example:
            >>> rs = ReminderService()
            >>> patient = {"id": 45, "name": "Ram Lal"}
            >>> reminder_id = rs.schedule_lab_due_reminder(
            ...     patient, "HbA1c", date(2024, 2, 1)
            ... )
        """
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date)

        # Schedule reminder 7 days before due date
        reminder_date = due_date - timedelta(days=7)
        reminder_time = datetime.combine(reminder_date, datetime.min.time()).replace(hour=18)

        if reminder_time <= datetime.now():
            return None

        channel = ReminderChannel.WHATSAPP
        if patient_preferences:
            pref_channel = patient_preferences.get("preferred_channel", "whatsapp")
            channel = ReminderChannel(pref_channel)

        reminder = Reminder(
            id=self._generate_reminder_id(),
            patient_id=patient["id"],
            type=ReminderType.LAB_DUE,
            scheduled_time=reminder_time,
            message="",
            channel=channel,
            status=ReminderStatus.SCHEDULED,
            metadata={
                "test_name": test,
                "due_date": due_date.isoformat()
            },
            created_at=datetime.now()
        )

        self._save_reminder(reminder)
        logger.info(f"Scheduled lab due reminder {reminder.id} for {test} on {reminder_time}")
        return reminder.id

    def cancel_reminder(self, reminder_id: str) -> bool:
        """
        Cancel a scheduled reminder.

        Args:
            reminder_id: Reminder ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminders
                SET status = ?
                WHERE id = ? AND status = ?
            """, (ReminderStatus.CANCELLED.value, reminder_id, ReminderStatus.SCHEDULED.value))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Cancelled reminder {reminder_id}")
                return True
            else:
                logger.warning(f"Reminder {reminder_id} not found or already processed")
                return False
        except Exception as e:
            logger.error(f"Error cancelling reminder {reminder_id}: {e}")
            return False
        finally:
            conn.close()

    def get_pending_reminders(self, patient_id: int) -> List[Reminder]:
        """
        Get all scheduled reminders for a patient.

        Args:
            patient_id: Patient ID

        Returns:
            List of pending Reminder objects

        Example:
            >>> rs = ReminderService()
            >>> reminders = rs.get_pending_reminders(45)
            >>> for r in reminders:
            ...     print(f"{r.type.value} - {r.scheduled_time}")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders
                WHERE patient_id = ? AND status = ?
                ORDER BY scheduled_time ASC
            """, (patient_id, ReminderStatus.SCHEDULED.value))

            rows = cursor.fetchall()
            return [Reminder.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching pending reminders for patient {patient_id}: {e}")
            return []
        finally:
            conn.close()

    def get_due_reminders(self, before_time: Optional[datetime] = None) -> List[Reminder]:
        """
        Get all reminders due to be sent.

        Args:
            before_time: Get reminders scheduled before this time (default: now)

        Returns:
            List of due Reminder objects
        """
        if before_time is None:
            before_time = datetime.now()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders
                WHERE status = ? AND scheduled_time <= ?
                ORDER BY scheduled_time ASC
            """, (ReminderStatus.SCHEDULED.value, before_time.isoformat()))

            rows = cursor.fetchall()
            return [Reminder.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching due reminders: {e}")
            return []
        finally:
            conn.close()

    def update_reminder_status(
        self,
        reminder_id: str,
        status: ReminderStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update reminder status.

        Args:
            reminder_id: Reminder ID
            status: New status
            error_message: Error message if status is FAILED

        Returns:
            True if updated, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            sent_at = datetime.now().isoformat() if status == ReminderStatus.SENT else None

            cursor.execute("""
                UPDATE reminders
                SET status = ?, sent_at = ?, error_message = ?
                WHERE id = ?
            """, (status.value, sent_at, error_message, reminder_id))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Updated reminder {reminder_id} status to {status.value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating reminder {reminder_id}: {e}")
            return False
        finally:
            conn.close()

    def _save_reminder(self, reminder: Reminder):
        """Save reminder to database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            data = reminder.to_dict()
            cursor.execute("""
                INSERT INTO reminders (
                    id, patient_id, type, scheduled_time, message, channel,
                    status, metadata, created_at, sent_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["patient_id"], data["type"], data["scheduled_time"],
                data["message"], data["channel"], data["status"], data["metadata"],
                data["created_at"], data["sent_at"], data["error_message"]
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving reminder: {e}")
            raise
        finally:
            conn.close()

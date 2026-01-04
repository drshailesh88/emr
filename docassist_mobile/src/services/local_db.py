"""
Local Database Service - Access to synced patient data with offline edit queue support.

This service provides:
- Patient search and retrieval
- Visit history access
- Lab results access
- Appointment queries
- Offline edit queue integration
- Conflict detection via timestamps

Operations can be queued for sync when offline.
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from dataclasses import dataclass

# Import offline queue for edit operations
try:
    from .offline_queue import OfflineQueue, OperationType
except ImportError:
    # Fallback if offline_queue is not available
    OfflineQueue = None
    OperationType = None


@dataclass
class Patient:
    """Patient data model."""
    id: int
    uhid: str
    name: str
    age: Optional[int]
    gender: str
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    last_visit_date: Optional[date] = None


@dataclass
class Visit:
    """Visit data model."""
    id: int
    patient_id: int
    visit_date: date
    chief_complaint: Optional[str]
    clinical_notes: Optional[str]
    diagnosis: Optional[str]
    prescription_json: Optional[str]


@dataclass
class Investigation:
    """Investigation/lab result data model."""
    id: int
    patient_id: int
    test_name: str
    result: Optional[str]
    unit: Optional[str]
    reference_range: Optional[str]
    test_date: date
    is_abnormal: bool


@dataclass
class Procedure:
    """Procedure data model."""
    id: int
    patient_id: int
    procedure_name: str
    details: Optional[str]
    procedure_date: date
    notes: Optional[str]


@dataclass
class Appointment:
    """Appointment data model."""
    id: int
    patient_id: int
    patient_name: str
    appointment_time: datetime
    reason: Optional[str]


class LocalDatabase:
    """
    Local database for mobile app with offline edit queue support.

    Usage:
        db = LocalDatabase("data/clinic.db")
        patients = db.search_patients("Ram")
        visits = db.get_patient_visits(patient_id=1)

        # With offline queue (for edits)
        db = LocalDatabase("data/clinic.db", enable_queue=True)
        db.add_visit_queued(patient_id=1, visit_data={...})  # Queued for sync
    """

    def __init__(self, db_path: str = "data/clinic.db", enable_queue: bool = False):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self.enable_queue = enable_queue
        self.offline_queue: Optional[OfflineQueue] = None

        # Initialize offline queue if enabled
        if enable_queue and OfflineQueue:
            self.offline_queue = OfflineQueue(db_path)

        # Ensure tables have proper schema
        self._ensure_timestamp_columns()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._connection is None:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database not found: {self.db_path}")

            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row

        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _ensure_timestamp_columns(self):
        """
        Ensure all tables have updated_at timestamps for conflict detection.
        This adds columns if they don't exist (safe migration).
        """
        try:
            conn = self._get_connection()

            # Add updated_at to patients if missing
            try:
                conn.execute("ALTER TABLE patients ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Add updated_at to visits if missing
            try:
                conn.execute("ALTER TABLE visits ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            # Add updated_at to investigations if missing
            try:
                conn.execute("ALTER TABLE investigations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
            except sqlite3.OperationalError:
                pass

        except Exception:
            # Ignore errors during schema update
            pass

    # -------------------------------------------------------------------------
    # Patient Operations
    # -------------------------------------------------------------------------

    def get_all_patients(self, limit: int = 100, offset: int = 0) -> List[Patient]:
        """Get all patients, sorted by most recent visit."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT p.*, MAX(v.visit_date) as last_visit_date
            FROM patients p
            LEFT JOIN visits v ON p.id = v.patient_id
            GROUP BY p.id
            ORDER BY last_visit_date DESC NULLS LAST, p.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        return [self._row_to_patient(row) for row in cursor.fetchall()]

    def search_patients(self, query: str, limit: int = 50) -> List[Patient]:
        """Search patients by name, UHID, or phone."""
        if not query or len(query) < 2:
            return []

        conn = self._get_connection()
        search_term = f"%{query}%"

        cursor = conn.execute("""
            SELECT p.*, MAX(v.visit_date) as last_visit_date
            FROM patients p
            LEFT JOIN visits v ON p.id = v.patient_id
            WHERE p.name LIKE ?
               OR p.uhid LIKE ?
               OR p.phone LIKE ?
            GROUP BY p.id
            ORDER BY
                CASE WHEN p.name LIKE ? THEN 0 ELSE 1 END,
                last_visit_date DESC NULLS LAST
            LIMIT ?
        """, (search_term, search_term, search_term, f"{query}%", limit))

        return [self._row_to_patient(row) for row in cursor.fetchall()]

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """Get a single patient by ID."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT p.*, MAX(v.visit_date) as last_visit_date
            FROM patients p
            LEFT JOIN visits v ON p.id = v.patient_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (patient_id,))

        row = cursor.fetchone()
        return self._row_to_patient(row) if row else None

    def get_patient_count(self) -> int:
        """Get total number of patients."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM patients")
        return cursor.fetchone()[0]

    def add_patient(
        self,
        name: str,
        phone: Optional[str] = None,
        age: Optional[int] = None,
        gender: str = "O",
        address: Optional[str] = None,
    ) -> int:
        """
        Add a new patient to the database.

        Args:
            name: Patient name (required)
            phone: Phone number
            age: Patient age
            gender: Gender (M/F/O)
            address: Address

        Returns:
            Patient ID of newly created patient
        """
        conn = self._get_connection()

        # Generate UHID
        cursor = conn.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        uhid = f"EMR-{datetime.now().year}-{patient_count + 1:04d}"

        # Insert patient
        cursor = conn.execute("""
            INSERT INTO patients (uhid, name, age, gender, phone, address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            uhid,
            name,
            age,
            gender,
            phone,
            address,
            datetime.now().isoformat(),
        ))

        conn.commit()
        return cursor.lastrowid

    # -------------------------------------------------------------------------
    # Visit Operations
    # -------------------------------------------------------------------------

    def get_patient_visits(
        self,
        patient_id: int,
        limit: int = 50,
    ) -> List[Visit]:
        """Get visit history for a patient."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM visits
            WHERE patient_id = ?
            ORDER BY visit_date DESC
            LIMIT ?
        """, (patient_id, limit))

        return [self._row_to_visit(row) for row in cursor.fetchall()]

    def get_visit(self, visit_id: int) -> Optional[Visit]:
        """Get a single visit by ID."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,))
        row = cursor.fetchone()
        return self._row_to_visit(row) if row else None

    def get_visit_count(self) -> int:
        """Get total number of visits."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM visits")
        return cursor.fetchone()[0]

    # -------------------------------------------------------------------------
    # Investigation Operations
    # -------------------------------------------------------------------------

    def get_patient_investigations(
        self,
        patient_id: int,
        limit: int = 100,
    ) -> List[Investigation]:
        """Get lab results for a patient."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM investigations
            WHERE patient_id = ?
            ORDER BY test_date DESC
            LIMIT ?
        """, (patient_id, limit))

        return [self._row_to_investigation(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Procedure Operations
    # -------------------------------------------------------------------------

    def get_patient_procedures(
        self,
        patient_id: int,
        limit: int = 50,
    ) -> List[Procedure]:
        """Get procedures for a patient."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM procedures
            WHERE patient_id = ?
            ORDER BY procedure_date DESC
            LIMIT ?
        """, (patient_id, limit))

        return [self._row_to_procedure(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Appointment Operations
    # -------------------------------------------------------------------------

    def get_todays_appointments(self) -> List[Appointment]:
        """Get today's appointments."""
        conn = self._get_connection()
        today = date.today().isoformat()

        # Note: This assumes an appointments table exists
        # If not, we'll return empty list for now
        try:
            cursor = conn.execute("""
                SELECT a.*, p.name as patient_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE DATE(a.appointment_time) = ?
                ORDER BY a.appointment_time
            """, (today,))

            return [self._row_to_appointment(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Get database statistics."""
        stats = {
            'patient_count': self.get_patient_count(),
            'visit_count': self.get_visit_count(),
        }

        # Add queue stats if enabled
        if self.offline_queue:
            stats['pending_sync_count'] = self.offline_queue.get_pending_count()
            stats['failed_sync_count'] = self.offline_queue.get_failed_count()

        return stats

    # -------------------------------------------------------------------------
    # Write Operations (with queue support)
    # -------------------------------------------------------------------------

    def add_visit_queued(self, patient_id: int, visit_data: Dict[str, Any]) -> Optional[str]:
        """
        Add a new visit (queued for sync if offline queue enabled).

        Args:
            patient_id: Patient ID
            visit_data: Visit data dictionary

        Returns:
            Operation ID if queued, None otherwise
        """
        data = {
            'patient_id': patient_id,
            'visit_date': visit_data.get('visit_date', date.today().isoformat()),
            'chief_complaint': visit_data.get('chief_complaint'),
            'clinical_notes': visit_data.get('clinical_notes'),
            'diagnosis': visit_data.get('diagnosis'),
            'prescription_json': visit_data.get('prescription_json'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        if self.offline_queue and OperationType:
            # Queue the operation
            operation_id = self.offline_queue.add_operation(
                op_type=OperationType.INSERT,
                table='visits',
                data=data
            )
            return operation_id
        return None

    def add_investigation_queued(self, patient_id: int, investigation_data: Dict[str, Any]) -> Optional[str]:
        """
        Add a new investigation/lab result (queued for sync).

        Args:
            patient_id: Patient ID
            investigation_data: Investigation data dictionary

        Returns:
            Operation ID if queued
        """
        data = {
            'patient_id': patient_id,
            'test_name': investigation_data.get('test_name'),
            'result': investigation_data.get('result'),
            'unit': investigation_data.get('unit'),
            'reference_range': investigation_data.get('reference_range'),
            'test_date': investigation_data.get('test_date', date.today().isoformat()),
            'is_abnormal': investigation_data.get('is_abnormal', False),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        if self.offline_queue and OperationType:
            operation_id = self.offline_queue.add_operation(
                op_type=OperationType.INSERT,
                table='investigations',
                data=data
            )
            return operation_id
        return None

    def update_visit_queued(self, visit_id: int, visit_data: Dict[str, Any]) -> Optional[str]:
        """
        Update an existing visit (queued for sync).

        Args:
            visit_id: Visit ID
            visit_data: Updated visit data

        Returns:
            Operation ID if queued
        """
        data = {
            'id': visit_id,
            **visit_data,
            'updated_at': datetime.now().isoformat(),
        }

        if self.offline_queue and OperationType:
            operation_id = self.offline_queue.add_operation(
                op_type=OperationType.UPDATE,
                table='visits',
                data=data
            )
            return operation_id
        return None

    def has_pending_changes(self) -> bool:
        """Check if there are pending changes in the queue."""
        if self.offline_queue:
            return self.offline_queue.get_pending_count() > 0
        return False

    def get_pending_count(self) -> int:
        """Get number of pending changes."""
        if self.offline_queue:
            return self.offline_queue.get_pending_count()
        return 0

    def detect_conflict(self, local_updated_at: str, remote_updated_at: str) -> bool:
        """
        Detect if there's a conflict between local and remote data.

        Args:
            local_updated_at: Local update timestamp (ISO format)
            remote_updated_at: Remote update timestamp (ISO format)

        Returns:
            True if there's a conflict
        """
        try:
            local_time = datetime.fromisoformat(local_updated_at)
            remote_time = datetime.fromisoformat(remote_updated_at)
            time_diff = abs((local_time - remote_time).total_seconds())
            return time_diff >= 1  # Conflict if more than 1 second apart
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Row Converters
    # -------------------------------------------------------------------------

    def _row_to_patient(self, row: sqlite3.Row) -> Patient:
        """Convert database row to Patient object."""
        return Patient(
            id=row['id'],
            uhid=row['uhid'],
            name=row['name'],
            age=row['age'],
            gender=row['gender'] or 'O',
            phone=row['phone'],
            address=row['address'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            last_visit_date=date.fromisoformat(row['last_visit_date']) if row.get('last_visit_date') else None,
        )

    def _row_to_visit(self, row: sqlite3.Row) -> Visit:
        """Convert database row to Visit object."""
        return Visit(
            id=row['id'],
            patient_id=row['patient_id'],
            visit_date=date.fromisoformat(row['visit_date']) if row['visit_date'] else date.today(),
            chief_complaint=row['chief_complaint'],
            clinical_notes=row['clinical_notes'],
            diagnosis=row['diagnosis'],
            prescription_json=row['prescription_json'],
        )

    def _row_to_investigation(self, row: sqlite3.Row) -> Investigation:
        """Convert database row to Investigation object."""
        return Investigation(
            id=row['id'],
            patient_id=row['patient_id'],
            test_name=row['test_name'],
            result=row['result'],
            unit=row['unit'],
            reference_range=row['reference_range'],
            test_date=date.fromisoformat(row['test_date']) if row['test_date'] else date.today(),
            is_abnormal=bool(row['is_abnormal']),
        )

    def _row_to_procedure(self, row: sqlite3.Row) -> Procedure:
        """Convert database row to Procedure object."""
        return Procedure(
            id=row['id'],
            patient_id=row['patient_id'],
            procedure_name=row['procedure_name'],
            details=row['details'],
            procedure_date=date.fromisoformat(row['procedure_date']) if row['procedure_date'] else date.today(),
            notes=row['notes'],
        )

    def _row_to_appointment(self, row: sqlite3.Row) -> Appointment:
        """Convert database row to Appointment object."""
        return Appointment(
            id=row['id'],
            patient_id=row['patient_id'],
            patient_name=row['patient_name'],
            appointment_time=datetime.fromisoformat(row['appointment_time']),
            reason=row.get('reason'),
        )

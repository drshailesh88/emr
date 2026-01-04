"""
Local Database Service - Read-only access to synced patient data.

This service provides:
- Patient search and retrieval
- Visit history access
- Lab results access
- Appointment queries

All operations are read-only for Mobile Lite.
"""

import sqlite3
import os
from typing import List, Optional
from datetime import date, datetime
from dataclasses import dataclass


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
    Read-only local database for mobile app.

    Usage:
        db = LocalDatabase("data/clinic.db")
        patients = db.search_patients("Ram")
        visits = db.get_patient_visits(patient_id=1)
    """

    def __init__(self, db_path: str = "data/clinic.db"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

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
        return {
            'patient_count': self.get_patient_count(),
            'visit_count': self.get_visit_count(),
        }

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

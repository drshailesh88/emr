"""SQLite database service for EMR data."""

import logging
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional, Tuple
from contextlib import contextmanager

from ..models.schemas import Patient, Visit, Investigation, Procedure

logger = logging.getLogger(__name__)


class DatabaseService:
    """Handles all SQLite database operations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Database transaction error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Patients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uhid TEXT UNIQUE,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    phone TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Visits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    visit_date DATE,
                    chief_complaint TEXT,
                    clinical_notes TEXT,
                    diagnosis TEXT,
                    prescription_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Investigations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investigations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    test_name TEXT NOT NULL,
                    result TEXT,
                    unit TEXT,
                    reference_range TEXT,
                    test_date DATE,
                    is_abnormal BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Procedures table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS procedures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    procedure_name TEXT NOT NULL,
                    details TEXT,
                    procedure_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Metadata table for change tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for faster search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigations_patient ON investigations(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_procedures_patient ON procedures(patient_id)")

    def _generate_uhid(self) -> str:
        """Generate unique hospital ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients")
            count = cursor.fetchone()[0]
            year = datetime.now().year
            return f"EMR-{year}-{count + 1:04d}"

    # ============== PATIENT OPERATIONS ==============

    def add_patient(self, patient: Patient) -> Patient:
        """Add a new patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            uhid = self._generate_uhid()
            cursor.execute("""
                INSERT INTO patients (uhid, name, age, gender, phone, address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uhid, patient.name, patient.age, patient.gender,
                  patient.phone, patient.address))
            patient.id = cursor.lastrowid
            patient.uhid = uhid
        self.mark_data_changed()
        return patient

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            row = cursor.fetchone()
            if row:
                return Patient(**dict(row))
            return None

    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients ORDER BY name")
            return [Patient(**dict(row)) for row in cursor.fetchall()]

    def search_patients_basic(self, query: str) -> List[Patient]:
        """Basic text search on patient name and UHID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM patients
                WHERE name LIKE ? OR uhid LIKE ?
                ORDER BY name
            """, (search_term, search_term))
            return [Patient(**dict(row)) for row in cursor.fetchall()]

    def update_patient(self, patient: Patient) -> bool:
        """Update patient details."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE patients
                SET name = ?, age = ?, gender = ?, phone = ?, address = ?
                WHERE id = ?
            """, (patient.name, patient.age, patient.gender,
                  patient.phone, patient.address, patient.id))
            updated = cursor.rowcount > 0
        if updated:
            self.mark_data_changed()
        return updated

    # ============== VISIT OPERATIONS ==============

    def add_visit(self, visit: Visit) -> Visit:
        """Add a new visit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            visit_date = visit.visit_date or date.today()
            cursor.execute("""
                INSERT INTO visits (patient_id, visit_date, chief_complaint,
                                   clinical_notes, diagnosis, prescription_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (visit.patient_id, visit_date, visit.chief_complaint,
                  visit.clinical_notes, visit.diagnosis, visit.prescription_json))
            visit.id = cursor.lastrowid
        self.mark_data_changed()
        return visit

    def get_patient_visits(self, patient_id: int) -> List[Visit]:
        """Get all visits for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM visits WHERE patient_id = ?
                ORDER BY visit_date DESC, created_at DESC
            """, (patient_id,))
            return [Visit(**dict(row)) for row in cursor.fetchall()]

    def update_visit(self, visit: Visit) -> bool:
        """Update a visit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE visits
                SET chief_complaint = ?, clinical_notes = ?,
                    diagnosis = ?, prescription_json = ?
                WHERE id = ?
            """, (visit.chief_complaint, visit.clinical_notes,
                  visit.diagnosis, visit.prescription_json, visit.id))
            updated = cursor.rowcount > 0
        if updated:
            self.mark_data_changed()
        return updated

    # ============== INVESTIGATION OPERATIONS ==============

    def add_investigation(self, investigation: Investigation) -> Investigation:
        """Add a new investigation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            test_date = investigation.test_date or date.today()
            cursor.execute("""
                INSERT INTO investigations (patient_id, test_name, result, unit,
                                           reference_range, test_date, is_abnormal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (investigation.patient_id, investigation.test_name,
                  investigation.result, investigation.unit,
                  investigation.reference_range, test_date,
                  investigation.is_abnormal))
            investigation.id = cursor.lastrowid
        self.mark_data_changed()
        return investigation

    def get_patient_investigations(self, patient_id: int) -> List[Investigation]:
        """Get all investigations for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM investigations WHERE patient_id = ?
                ORDER BY test_date DESC
            """, (patient_id,))
            return [Investigation(**dict(row)) for row in cursor.fetchall()]

    # ============== PROCEDURE OPERATIONS ==============

    def add_procedure(self, procedure: Procedure) -> Procedure:
        """Add a new procedure."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            procedure_date = procedure.procedure_date or date.today()
            cursor.execute("""
                INSERT INTO procedures (patient_id, procedure_name, details,
                                       procedure_date, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (procedure.patient_id, procedure.procedure_name,
                  procedure.details, procedure_date, procedure.notes))
            procedure.id = cursor.lastrowid
        self.mark_data_changed()
        return procedure

    def get_patient_procedures(self, patient_id: int) -> List[Procedure]:
        """Get all procedures for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM procedures WHERE patient_id = ?
                ORDER BY procedure_date DESC
            """, (patient_id,))
            return [Procedure(**dict(row)) for row in cursor.fetchall()]

    # ============== RAG HELPER METHODS ==============

    def get_patient_summary(self, patient_id: int) -> str:
        """Get a text summary of patient for embedding."""
        patient = self.get_patient(patient_id)
        if not patient:
            return ""

        parts = [f"Patient: {patient.name}"]
        if patient.uhid:
            parts.append(f"UHID: {patient.uhid}")
        if patient.age:
            parts.append(f"Age: {patient.age}")
        if patient.gender:
            parts.append(f"Gender: {patient.gender}")

        # Add key diagnoses from visits
        visits = self.get_patient_visits(patient_id)
        diagnoses = set()
        for visit in visits[:10]:  # Last 10 visits
            if visit.diagnosis:
                diagnoses.add(visit.diagnosis)
        if diagnoses:
            parts.append(f"Diagnoses: {', '.join(diagnoses)}")

        # Add procedures
        procedures = self.get_patient_procedures(patient_id)
        if procedures:
            proc_names = [p.procedure_name for p in procedures[:5]]
            parts.append(f"Procedures: {', '.join(proc_names)}")

        return ". ".join(parts)

    def get_patient_documents_for_rag(self, patient_id: int) -> List[Tuple[str, str, dict]]:
        """Get all documents for a patient for RAG indexing.

        Returns list of (doc_id, content, metadata) tuples.
        """
        documents = []

        # Visits
        for visit in self.get_patient_visits(patient_id):
            doc_id = f"visit_{visit.id}"
            content = f"Visit on {visit.visit_date}: "
            if visit.chief_complaint:
                content += f"Chief complaint: {visit.chief_complaint}. "
            if visit.clinical_notes:
                content += f"Notes: {visit.clinical_notes}. "
            if visit.diagnosis:
                content += f"Diagnosis: {visit.diagnosis}. "
            if visit.prescription_json:
                try:
                    rx = json.loads(visit.prescription_json)
                    if rx.get("medications"):
                        meds = [m.get("drug_name", "") for m in rx["medications"]]
                        content += f"Medications: {', '.join(meds)}. "
                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse prescription JSON for visit {visit.id}: {e}")

            metadata = {
                "type": "visit",
                "patient_id": patient_id,
                "date": str(visit.visit_date)
            }
            documents.append((doc_id, content, metadata))

        # Investigations
        for inv in self.get_patient_investigations(patient_id):
            doc_id = f"investigation_{inv.id}"
            content = f"Investigation on {inv.test_date}: {inv.test_name}"
            if inv.result:
                content += f" = {inv.result}"
            if inv.unit:
                content += f" {inv.unit}"
            if inv.is_abnormal:
                content += " (ABNORMAL)"

            metadata = {
                "type": "investigation",
                "patient_id": patient_id,
                "date": str(inv.test_date),
                "test_name": inv.test_name
            }
            documents.append((doc_id, content, metadata))

        # Procedures
        for proc in self.get_patient_procedures(patient_id):
            doc_id = f"procedure_{proc.id}"
            content = f"Procedure on {proc.procedure_date}: {proc.procedure_name}"
            if proc.details:
                content += f". Details: {proc.details}"
            if proc.notes:
                content += f". Notes: {proc.notes}"

            metadata = {
                "type": "procedure",
                "patient_id": patient_id,
                "date": str(proc.procedure_date)
            }
            documents.append((doc_id, content, metadata))

        return documents

    # ============== CHANGE TRACKING ==============

    def mark_data_changed(self):
        """Mark that data has been modified.

        This updates the 'last_modified' timestamp in the metadata table,
        which is used by the backup scheduler to determine if a backup is needed.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES ('last_modified', ?, CURRENT_TIMESTAMP)
            """, (datetime.now().isoformat(),))

    def has_changes_since(self, timestamp: datetime) -> bool:
        """Check if there are changes since the given timestamp.

        Args:
            timestamp: Reference timestamp to check against

        Returns:
            True if data has been modified since timestamp, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check metadata table for last modification
            cursor.execute("""
                SELECT value, updated_at FROM metadata WHERE key = 'last_modified'
            """)
            row = cursor.fetchone()

            if not row:
                # No modification tracking yet, check if any data exists
                cursor.execute("SELECT COUNT(*) FROM patients")
                patient_count = cursor.fetchone()[0]
                return patient_count > 0

            # Parse the timestamp from metadata
            try:
                last_modified_str = row[0]
                last_modified = datetime.fromisoformat(last_modified_str)
                return last_modified > timestamp
            except (ValueError, TypeError):
                # If we can't parse the timestamp, assume there are changes
                return True

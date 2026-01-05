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

    # Current schema version
    SCHEMA_VERSION = 1

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
        """Initialize database and run migrations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create schema_versions table first
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Run any pending migrations
        self._run_migrations()

    def _get_schema_version(self) -> int:
        """Get the current schema version from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_versions")
            result = cursor.fetchone()[0]
            return result if result is not None else 0

    def _set_schema_version(self, version: int):
        """Set the schema version after applying a migration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schema_versions (version)
                VALUES (?)
            """, (version,))
            logger.info(f"Applied migration to schema version {version}")

    def _run_migrations(self):
        """Run all pending migrations."""
        current_version = self._get_schema_version()
        logger.info(f"Current schema version: {current_version}")

        for version in range(current_version + 1, self.SCHEMA_VERSION + 1):
            if version in self._migrations:
                logger.info(f"Running migration to version {version}")
                self._migrations[version]()
                self._set_schema_version(version)
            else:
                logger.warning(f"No migration defined for version {version}")

        if current_version < self.SCHEMA_VERSION:
            logger.info(f"Schema updated from version {current_version} to {self.SCHEMA_VERSION}")

    def _migration_v1(self):
        """Initial schema creation - v1."""
        logger.info("Creating initial database schema (v1)")
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

    def _migration_v2(self):
        """Sample placeholder migration - v2.

        This is an example of how to add future migrations.
        When you need to modify the schema, increment SCHEMA_VERSION
        and add the migration logic here.

        Example:
            # Add a new column to patients table
            cursor.execute("ALTER TABLE patients ADD COLUMN email TEXT")
        """
        logger.info("Running migration v2 (placeholder - no changes)")
        # This migration intentionally does nothing
        # It's here as a template for future migrations
        pass

    # Migration mapping - add new migrations here
    @property
    def _migrations(self):
        """Map of version numbers to migration functions."""
        return {
            1: self._migration_v1,
            # 2: self._migration_v2,  # Uncomment when ready to apply v2
        }

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

    # ============== ANALYTICS QUERIES ==============

    def get_total_patients(self) -> int:
        """Get total count of patients."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients")
            return cursor.fetchone()[0]

    def get_patients_this_month(self) -> int:
        """Get count of new patients this month."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM patients
                WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            """)
            return cursor.fetchone()[0]

    def get_visits_today(self) -> int:
        """Get count of visits today."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM visits
                WHERE DATE(visit_date) = DATE('now')
            """)
            return cursor.fetchone()[0]

    def get_visits_this_week(self) -> int:
        """Get count of visits in the last 7 days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM visits
                WHERE visit_date >= DATE('now', '-7 days')
            """)
            return cursor.fetchone()[0]

    def get_visits_by_date(self, target_date: date) -> List[dict]:
        """Get all visits for a specific date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, p.name as patient_name, p.phone
                FROM visits v
                LEFT JOIN patients p ON v.patient_id = p.id
                WHERE DATE(v.visit_date) = ?
                ORDER BY v.created_at
            """, (target_date,))
            return [dict(row) for row in cursor.fetchall()]

    def get_visits_by_date_range(self, start_date: date, end_date: date) -> List[dict]:
        """Get all visits in a date range."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, p.name as patient_name, p.phone
                FROM visits v
                LEFT JOIN patients p ON v.patient_id = p.id
                WHERE DATE(v.visit_date) BETWEEN ? AND ?
                ORDER BY v.visit_date
            """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]

    def get_top_diagnoses(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most common diagnoses."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT diagnosis, COUNT(*) as count
                FROM visits
                WHERE diagnosis IS NOT NULL AND diagnosis != ''
                GROUP BY diagnosis
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_patient_demographics(self) -> dict:
        """Get patient demographics (age and gender distribution)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Gender distribution
            cursor.execute("""
                SELECT gender, COUNT(*) as count
                FROM patients
                WHERE gender IS NOT NULL
                GROUP BY gender
            """)
            gender_dist = {row[0]: row[1] for row in cursor.fetchall()}

            # Age distribution (age groups)
            cursor.execute("""
                SELECT
                    CASE
                        WHEN age < 18 THEN '0-17'
                        WHEN age BETWEEN 18 AND 30 THEN '18-30'
                        WHEN age BETWEEN 31 AND 45 THEN '31-45'
                        WHEN age BETWEEN 46 AND 60 THEN '46-60'
                        ELSE '60+'
                    END as age_group,
                    COUNT(*) as count
                FROM patients
                WHERE age IS NOT NULL
                GROUP BY age_group
                ORDER BY age_group
            """)
            age_dist = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "gender": gender_dist,
                "age_groups": age_dist
            }

    def get_new_patients_by_month(self, months: int = 12) -> List[Tuple[str, int]]:
        """Get new patients grouped by month."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM patients
                WHERE created_at >= DATE('now', ? || ' months')
                GROUP BY month
                ORDER BY month DESC
            """, (f'-{months}',))
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_patient_visit_counts(self) -> List[dict]:
        """Get all patients with their visit counts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.phone,
                    p.created_at,
                    COUNT(v.id) as visit_count,
                    MAX(v.visit_date) as last_visit_date
                FROM patients p
                LEFT JOIN visits v ON p.id = v.patient_id
                GROUP BY p.id
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_returning_patients(self) -> int:
        """Get count of patients with more than one visit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT patient_id) FROM (
                    SELECT patient_id, COUNT(*) as visit_count
                    FROM visits
                    GROUP BY patient_id
                    HAVING visit_count > 1
                )
            """)
            return cursor.fetchone()[0]

    def get_visits_by_hour(self) -> dict:
        """Get visit distribution by hour of day."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Since we don't have time in visit_date, estimate based on creation time
            cursor.execute("""
                SELECT strftime('%H', created_at) as hour, COUNT(*) as count
                FROM visits
                WHERE created_at IS NOT NULL
                GROUP BY hour
                ORDER BY hour
            """)
            return {int(row[0]): row[1] for row in cursor.fetchall()}

    def get_all_patients_with_stats(self, as_of_date: date = None) -> List[dict]:
        """Get all patients with computed statistics."""
        if as_of_date is None:
            as_of_date = date.today()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.phone,
                    p.created_at,
                    COUNT(v.id) as visit_count,
                    MAX(v.visit_date) as last_visit_date,
                    GROUP_CONCAT(DISTINCT v.diagnosis) as conditions
                FROM patients p
                LEFT JOIN visits v ON p.id = v.patient_id
                WHERE DATE(p.created_at) <= ?
                GROUP BY p.id
            """, (as_of_date,))
            return [dict(row) for row in cursor.fetchall()]

"""SQLite database service for EMR data."""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional, Tuple
from contextlib import contextmanager

from ..models.schemas import Patient, Visit, Investigation, Procedure, Vitals


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
        except Exception:
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
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
                    is_deleted INTEGER DEFAULT 0,
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
                    is_deleted INTEGER DEFAULT 0,
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
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Vitals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vitals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    visit_id INTEGER,
                    recorded_at TEXT DEFAULT (datetime('now')),
                    bp_systolic INTEGER,
                    bp_diastolic INTEGER,
                    pulse INTEGER,
                    temperature REAL,
                    spo2 INTEGER,
                    respiratory_rate INTEGER,
                    weight REAL,
                    height REAL,
                    bmi REAL,
                    blood_sugar REAL,
                    sugar_type TEXT CHECK (sugar_type IN ('FBS', 'RBS', 'PPBS')),
                    notes TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (visit_id) REFERENCES visits(id)
                )
            """)

            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
                    old_value TEXT,
                    new_value TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # Drugs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generic_name TEXT NOT NULL,
                    brand_names TEXT,
                    strengths TEXT,
                    forms TEXT,
                    category TEXT,
                    is_custom INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT
                )
            """)

            # Templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    prescription_json TEXT NOT NULL,
                    is_custom INTEGER DEFAULT 0,
                    is_favorite INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT
                )
            """)

            # Phrases table for quick text expansion
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phrases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shortcut TEXT UNIQUE NOT NULL,
                    expansion TEXT NOT NULL,
                    category TEXT,
                    is_custom INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0
                )
            """)

            # Patient access log table (for recent patients)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patient_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    accessed_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Appointments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT,
                    duration_minutes INTEGER DEFAULT 15,
                    appointment_type TEXT DEFAULT 'follow-up',
                    status TEXT DEFAULT 'scheduled',
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create indexes for faster search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigations_patient ON investigations(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_procedures_patient ON procedures(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vitals_date ON vitals(recorded_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_generic ON drugs(generic_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_usage ON drugs(usage_count DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_favorite ON templates(is_favorite)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_phrases_shortcut ON phrases(shortcut)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_patient ON patient_access_log(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_time ON patient_access_log(accessed_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appt_date ON appointments(appointment_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appt_patient ON appointments(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appt_status ON appointments(status)")

            # Add is_deleted column to existing tables if not exists
            self._add_column_if_not_exists(cursor, "patients", "is_deleted", "INTEGER DEFAULT 0")
            self._add_column_if_not_exists(cursor, "visits", "is_deleted", "INTEGER DEFAULT 0")
            self._add_column_if_not_exists(cursor, "investigations", "is_deleted", "INTEGER DEFAULT 0")
            self._add_column_if_not_exists(cursor, "procedures", "is_deleted", "INTEGER DEFAULT 0")

            # Add is_favorite column to patients table if not exists
            self._add_column_if_not_exists(cursor, "patients", "is_favorite", "INTEGER DEFAULT 0")

            # Initialize default phrases if table is empty
            self._init_default_phrases(cursor)

    def _add_column_if_not_exists(self, cursor, table_name: str, column_name: str, column_def: str):
        """Add column to table if it doesn't exist."""
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        except sqlite3.OperationalError:
            # Column already exists
            pass

    def _generate_uhid(self) -> str:
        """Generate unique hospital ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients WHERE is_deleted = 0")
            count = cursor.fetchone()[0]
            year = datetime.now().year
            return f"EMR-{year}-{count + 1:04d}"

    # ============== AUDIT LOG OPERATIONS ==============

    def log_audit(self, table_name: str, record_id: int, operation: str,
                  old_value: dict = None, new_value: dict = None):
        """Log an audit entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            old_json = json.dumps(old_value) if old_value else None
            new_json = json.dumps(new_value) if new_value else None

            cursor.execute("""
                INSERT INTO audit_log (table_name, record_id, operation, old_value, new_value)
                VALUES (?, ?, ?, ?, ?)
            """, (table_name, record_id, operation, old_json, new_json))

    def get_audit_history(self, table_name: str = None, record_id: int = None,
                          limit: int = 100) -> list[dict]:
        """Get audit history, optionally filtered by table/record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []

            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)

            if record_id is not None:
                query += " AND record_id = ?"
                params.append(record_id)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                entry = dict(row)
                # Parse JSON values
                if entry.get('old_value'):
                    try:
                        entry['old_value'] = json.loads(entry['old_value'])
                    except:
                        pass
                if entry.get('new_value'):
                    try:
                        entry['new_value'] = json.loads(entry['new_value'])
                    except:
                        pass
                results.append(entry)

            return results

    def get_patient_audit_history(self, patient_id: int) -> list[dict]:
        """Get all audit entries related to a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get all records related to this patient
            audit_entries = []

            # Patient record changes
            patient_audits = self.get_audit_history(table_name="patients", record_id=patient_id, limit=1000)
            audit_entries.extend(patient_audits)

            # Visit changes
            cursor.execute("SELECT id FROM visits WHERE patient_id = ?", (patient_id,))
            visit_ids = [row[0] for row in cursor.fetchall()]
            for visit_id in visit_ids:
                visit_audits = self.get_audit_history(table_name="visits", record_id=visit_id, limit=1000)
                audit_entries.extend(visit_audits)

            # Investigation changes
            cursor.execute("SELECT id FROM investigations WHERE patient_id = ?", (patient_id,))
            inv_ids = [row[0] for row in cursor.fetchall()]
            for inv_id in inv_ids:
                inv_audits = self.get_audit_history(table_name="investigations", record_id=inv_id, limit=1000)
                audit_entries.extend(inv_audits)

            # Procedure changes
            cursor.execute("SELECT id FROM procedures WHERE patient_id = ?", (patient_id,))
            proc_ids = [row[0] for row in cursor.fetchall()]
            for proc_id in proc_ids:
                proc_audits = self.get_audit_history(table_name="procedures", record_id=proc_id, limit=1000)
                audit_entries.extend(proc_audits)

            # Sort by timestamp descending
            audit_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return audit_entries

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

            # Log audit
            self.log_audit(
                table_name="patients",
                record_id=patient.id,
                operation="INSERT",
                new_value={
                    "uhid": uhid,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "address": patient.address
                }
            )

            return patient

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE id = ? AND is_deleted = 0", (patient_id,))
            row = cursor.fetchone()
            if row:
                return Patient(**dict(row))
            return None

    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE is_deleted = 0 ORDER BY name")
            return [Patient(**dict(row)) for row in cursor.fetchall()]

    def search_patients_basic(self, query: str) -> List[Patient]:
        """Basic text search on patient name and UHID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM patients
                WHERE (name LIKE ? OR uhid LIKE ?)
                AND is_deleted = 0
                ORDER BY name
            """, (search_term, search_term))
            return [Patient(**dict(row)) for row in cursor.fetchall()]

    def update_patient(self, patient: Patient) -> bool:
        """Update patient details."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get old values for audit log
            cursor.execute("SELECT * FROM patients WHERE id = ?", (patient.id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Update patient
            cursor.execute("""
                UPDATE patients
                SET name = ?, age = ?, gender = ?, phone = ?, address = ?
                WHERE id = ?
            """, (patient.name, patient.age, patient.gender,
                  patient.phone, patient.address, patient.id))

            if cursor.rowcount > 0:
                # Log only changed fields
                new_data = {
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "address": patient.address
                }

                changed_fields_old = {}
                changed_fields_new = {}

                for key in new_data:
                    if old_data.get(key) != new_data[key]:
                        changed_fields_old[key] = old_data.get(key)
                        changed_fields_new[key] = new_data[key]

                if changed_fields_old:  # Only log if something actually changed
                    self.log_audit(
                        table_name="patients",
                        record_id=patient.id,
                        operation="UPDATE",
                        old_value=changed_fields_old,
                        new_value=changed_fields_new
                    )

                return True

            return False

    def delete_patient(self, patient_id: int) -> bool:
        """Soft delete a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get patient data for audit
            cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Soft delete
            cursor.execute("UPDATE patients SET is_deleted = 1 WHERE id = ?", (patient_id,))

            if cursor.rowcount > 0:
                self.log_audit(
                    table_name="patients",
                    record_id=patient_id,
                    operation="DELETE",
                    old_value={
                        "uhid": old_data.get("uhid"),
                        "name": old_data.get("name"),
                        "age": old_data.get("age"),
                        "gender": old_data.get("gender")
                    }
                )
                return True

            return False

    # ============== PATIENT ACCESS & FAVORITES ==============

    def log_patient_access(self, patient_id: int):
        """Log when a patient is accessed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patient_access_log (patient_id)
                VALUES (?)
            """, (patient_id,))

            # Keep only last 100 accesses per patient to prevent bloat
            cursor.execute("""
                DELETE FROM patient_access_log
                WHERE patient_id = ?
                AND id NOT IN (
                    SELECT id FROM patient_access_log
                    WHERE patient_id = ?
                    ORDER BY accessed_at DESC
                    LIMIT 100
                )
            """, (patient_id, patient_id))

    def get_recent_patients(self, limit: int = 10) -> list[dict]:
        """Get recently accessed patients (distinct, ordered by last access)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT p.*, MAX(pal.accessed_at) as last_accessed
                FROM patients p
                INNER JOIN patient_access_log pal ON p.id = pal.patient_id
                WHERE p.is_deleted = 0
                GROUP BY p.id
                ORDER BY last_accessed DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_favorite_patients(self) -> list[dict]:
        """Get favorite patients."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM patients
                WHERE is_favorite = 1 AND is_deleted = 0
                ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]

    def toggle_patient_favorite(self, patient_id: int) -> bool:
        """Toggle favorite status, return new status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current status
            cursor.execute("SELECT is_favorite FROM patients WHERE id = ?", (patient_id,))
            row = cursor.fetchone()
            if not row:
                return False

            new_status = 0 if row[0] else 1
            cursor.execute("UPDATE patients SET is_favorite = ? WHERE id = ?", (new_status, patient_id))

            return bool(new_status)

    def get_todays_patients(self) -> list[dict]:
        """Get patients with visits today."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            today = date.today()
            cursor.execute("""
                SELECT DISTINCT p.*
                FROM patients p
                INNER JOIN visits v ON p.id = v.patient_id
                WHERE v.visit_date = ? AND p.is_deleted = 0 AND v.is_deleted = 0
                ORDER BY v.created_at DESC
            """, (today,))
            return [dict(row) for row in cursor.fetchall()]

    def clear_recent_patients(self):
        """Clear the recent patients access log."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patient_access_log")

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

            # Log audit
            self.log_audit(
                table_name="visits",
                record_id=visit.id,
                operation="INSERT",
                new_value={
                    "patient_id": visit.patient_id,
                    "visit_date": str(visit_date),
                    "chief_complaint": visit.chief_complaint,
                    "diagnosis": visit.diagnosis
                }
            )

            return visit

    def get_patient_visits(self, patient_id: int) -> List[Visit]:
        """Get all visits for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM visits
                WHERE patient_id = ? AND is_deleted = 0
                ORDER BY visit_date DESC, created_at DESC
            """, (patient_id,))
            return [Visit(**dict(row)) for row in cursor.fetchall()]


    def get_visit(self, visit_id: int) -> Optional[Visit]:
        """Get visit by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM visits WHERE id = ? AND is_deleted = 0", (visit_id,))
            row = cursor.fetchone()
            if row:
                return Visit(**dict(row))
            return None

    def update_visit(self, visit: Visit) -> bool:
        """Update a visit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get old values for audit log
            cursor.execute("SELECT * FROM visits WHERE id = ?", (visit.id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Update visit
            cursor.execute("""
                UPDATE visits
                SET chief_complaint = ?, clinical_notes = ?,
                    diagnosis = ?, prescription_json = ?
                WHERE id = ?
            """, (visit.chief_complaint, visit.clinical_notes,
                  visit.diagnosis, visit.prescription_json, visit.id))

            if cursor.rowcount > 0:
                # Log only changed fields
                new_data = {
                    "chief_complaint": visit.chief_complaint,
                    "clinical_notes": visit.clinical_notes,
                    "diagnosis": visit.diagnosis,
                    "prescription_json": visit.prescription_json
                }

                changed_fields_old = {}
                changed_fields_new = {}

                for key in new_data:
                    if old_data.get(key) != new_data[key]:
                        changed_fields_old[key] = old_data.get(key)
                        changed_fields_new[key] = new_data[key]

                if changed_fields_old:
                    self.log_audit(
                        table_name="visits",
                        record_id=visit.id,
                        operation="UPDATE",
                        old_value=changed_fields_old,
                        new_value=changed_fields_new
                    )

                return True

            return False

    def delete_visit(self, visit_id: int) -> bool:
        """Soft delete a visit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get visit data for audit
            cursor.execute("SELECT * FROM visits WHERE id = ?", (visit_id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Soft delete
            cursor.execute("UPDATE visits SET is_deleted = 1 WHERE id = ?", (visit_id,))

            if cursor.rowcount > 0:
                self.log_audit(
                    table_name="visits",
                    record_id=visit_id,
                    operation="DELETE",
                    old_value={
                        "visit_date": old_data.get("visit_date"),
                        "chief_complaint": old_data.get("chief_complaint"),
                        "diagnosis": old_data.get("diagnosis")
                    }
                )
                return True

            return False

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

            # Log audit
            self.log_audit(
                table_name="investigations",
                record_id=investigation.id,
                operation="INSERT",
                new_value={
                    "patient_id": investigation.patient_id,
                    "test_name": investigation.test_name,
                    "result": investigation.result,
                    "test_date": str(test_date),
                    "is_abnormal": investigation.is_abnormal
                }
            )

            return investigation

    def get_patient_investigations(self, patient_id: int) -> List[Investigation]:
        """Get all investigations for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM investigations
                WHERE patient_id = ? AND is_deleted = 0
                ORDER BY test_date DESC
            """, (patient_id,))
            return [Investigation(**dict(row)) for row in cursor.fetchall()]


    def get_investigation(self, investigation_id: int) -> Optional[Investigation]:
        """Get investigation by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investigations WHERE id = ? AND is_deleted = 0", (investigation_id,))
            row = cursor.fetchone()
            if row:
                return Investigation(**dict(row))
            return None

    def update_investigation(self, investigation: Investigation) -> bool:
        """Update an investigation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get old values for audit log
            cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation.id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Update investigation
            cursor.execute("""
                UPDATE investigations
                SET test_name = ?, result = ?, unit = ?,
                    reference_range = ?, test_date = ?, is_abnormal = ?
                WHERE id = ?
            """, (investigation.test_name, investigation.result, investigation.unit,
                  investigation.reference_range, investigation.test_date,
                  investigation.is_abnormal, investigation.id))

            if cursor.rowcount > 0:
                # Log only changed fields
                new_data = {
                    "test_name": investigation.test_name,
                    "result": investigation.result,
                    "unit": investigation.unit,
                    "reference_range": investigation.reference_range,
                    "test_date": str(investigation.test_date) if investigation.test_date else None,
                    "is_abnormal": investigation.is_abnormal
                }

                changed_fields_old = {}
                changed_fields_new = {}

                for key in new_data:
                    old_val = old_data.get(key)
                    if key == "test_date" and old_val:
                        old_val = str(old_val)
                    if old_val != new_data[key]:
                        changed_fields_old[key] = old_val
                        changed_fields_new[key] = new_data[key]

                if changed_fields_old:
                    self.log_audit(
                        table_name="investigations",
                        record_id=investigation.id,
                        operation="UPDATE",
                        old_value=changed_fields_old,
                        new_value=changed_fields_new
                    )

                return True

            return False

    def delete_investigation(self, investigation_id: int) -> bool:
        """Soft delete an investigation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get investigation data for audit
            cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Soft delete
            cursor.execute("UPDATE investigations SET is_deleted = 1 WHERE id = ?", (investigation_id,))

            if cursor.rowcount > 0:
                self.log_audit(
                    table_name="investigations",
                    record_id=investigation_id,
                    operation="DELETE",
                    old_value={
                        "test_name": old_data.get("test_name"),
                        "result": old_data.get("result"),
                        "test_date": old_data.get("test_date")
                    }
                )
                return True

            return False

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

            # Log audit
            self.log_audit(
                table_name="procedures",
                record_id=procedure.id,
                operation="INSERT",
                new_value={
                    "patient_id": procedure.patient_id,
                    "procedure_name": procedure.procedure_name,
                    "procedure_date": str(procedure_date),
                    "details": procedure.details
                }
            )

            return procedure

    def get_patient_procedures(self, patient_id: int) -> List[Procedure]:
        """Get all procedures for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM procedures
                WHERE patient_id = ? AND is_deleted = 0
                ORDER BY procedure_date DESC
            """, (patient_id,))
            return [Procedure(**dict(row)) for row in cursor.fetchall()]


    def get_procedure(self, procedure_id: int) -> Optional[Procedure]:
        """Get procedure by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM procedures WHERE id = ? AND is_deleted = 0", (procedure_id,))
            row = cursor.fetchone()
            if row:
                return Procedure(**dict(row))
            return None

    def update_procedure(self, procedure: Procedure) -> bool:
        """Update a procedure."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get old values for audit log
            cursor.execute("SELECT * FROM procedures WHERE id = ?", (procedure.id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Update procedure
            cursor.execute("""
                UPDATE procedures
                SET procedure_name = ?, details = ?,
                    procedure_date = ?, notes = ?
                WHERE id = ?
            """, (procedure.procedure_name, procedure.details,
                  procedure.procedure_date, procedure.notes, procedure.id))

            if cursor.rowcount > 0:
                # Log only changed fields
                new_data = {
                    "procedure_name": procedure.procedure_name,
                    "details": procedure.details,
                    "procedure_date": str(procedure.procedure_date) if procedure.procedure_date else None,
                    "notes": procedure.notes
                }

                changed_fields_old = {}
                changed_fields_new = {}

                for key in new_data:
                    old_val = old_data.get(key)
                    if key == "procedure_date" and old_val:
                        old_val = str(old_val)
                    if old_val != new_data[key]:
                        changed_fields_old[key] = old_val
                        changed_fields_new[key] = new_data[key]

                if changed_fields_old:
                    self.log_audit(
                        table_name="procedures",
                        record_id=procedure.id,
                        operation="UPDATE",
                        old_value=changed_fields_old,
                        new_value=changed_fields_new
                    )

                return True

            return False

    def delete_procedure(self, procedure_id: int) -> bool:
        """Soft delete a procedure."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get procedure data for audit
            cursor.execute("SELECT * FROM procedures WHERE id = ?", (procedure_id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            old_data = dict(old_row)

            # Soft delete
            cursor.execute("UPDATE procedures SET is_deleted = 1 WHERE id = ?", (procedure_id,))

            if cursor.rowcount > 0:
                self.log_audit(
                    table_name="procedures",
                    record_id=procedure_id,
                    operation="DELETE",
                    old_value={
                        "procedure_name": old_data.get("procedure_name"),
                        "procedure_date": old_data.get("procedure_date"),
                        "details": old_data.get("details")
                    }
                )
                return True

            return False

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
                except json.JSONDecodeError:
                    pass

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

    # ============== TEMPLATE OPERATIONS ==============

    def get_all_templates(self) -> list[dict]:
        """Get all templates grouped by category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM templates
                ORDER BY is_favorite DESC, category, usage_count DESC, name
            """)

            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                # Parse prescription JSON
                try:
                    template['prescription'] = json.loads(template['prescription_json'])
                except json.JSONDecodeError:
                    template['prescription'] = {}
                templates.append(template)

            return templates

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get template by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()

            if row:
                template = dict(row)
                try:
                    template['prescription'] = json.loads(template['prescription_json'])
                except json.JSONDecodeError:
                    template['prescription'] = {}
                return template
            return None

    def add_custom_template(self, name: str, category: str, prescription: dict) -> str:
        """Create custom template from prescription."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Generate unique ID
            import uuid
            template_id = f"custom-{uuid.uuid4().hex[:8]}"

            prescription_json = json.dumps(prescription)

            cursor.execute("""
                INSERT INTO templates (id, name, category, prescription_json, is_custom)
                VALUES (?, ?, ?, ?, 1)
            """, (template_id, name, category, prescription_json))

            return template_id

    def update_template(self, template_id: str, name: str, category: str, prescription: dict) -> bool:
        """Update an existing template."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            prescription_json = json.dumps(prescription)

            cursor.execute("""
                UPDATE templates
                SET name = ?, category = ?, prescription_json = ?, updated_at = datetime('now')
                WHERE id = ? AND is_custom = 1
            """, (name, category, prescription_json, template_id))

            return cursor.rowcount > 0

    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id = ? AND is_custom = 1", (template_id,))
            return cursor.rowcount > 0

    def toggle_template_favorite(self, template_id: str) -> bool:
        """Toggle favorite status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current status
            cursor.execute("SELECT is_favorite FROM templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            if not row:
                return False

            new_status = 0 if row[0] else 1
            cursor.execute("UPDATE templates SET is_favorite = ? WHERE id = ?", (new_status, template_id))

            return cursor.rowcount > 0

    def increment_template_usage(self, template_id: str):
        """Track usage for sorting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE templates
                SET usage_count = usage_count + 1
                WHERE id = ?
            """, (template_id,))

    def load_initial_templates(self, templates_data: list[dict]):
        """Load initial templates from JSON data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            for template in templates_data:
                # Check if template already exists
                cursor.execute("SELECT id FROM templates WHERE id = ?", (template['id'],))
                if cursor.fetchone():
                    continue  # Skip if already exists

                prescription_json = json.dumps(template['prescription'])

                cursor.execute("""
                    INSERT INTO templates (id, name, category, prescription_json, is_custom)
                    VALUES (?, ?, ?, ?, 0)
                """, (template['id'], template['name'], template['category'], prescription_json))

    # ============== PHRASE OPERATIONS ==============

    def _init_default_phrases(self, cursor):
        """Initialize default phrases if table is empty."""
        cursor.execute("SELECT COUNT(*) FROM phrases")
        count = cursor.fetchone()[0]

        if count == 0:
            # Load default phrases from JSON file
            data_dir = Path(__file__).parent.parent / "data"
            phrases_file = data_dir / "initial_phrases.json"

            if phrases_file.exists():
                try:
                    with open(phrases_file, 'r') as f:
                        phrases_data = json.load(f)

                    for phrase in phrases_data.get("phrases", []):
                        cursor.execute("""
                            INSERT INTO phrases (shortcut, expansion, category, is_custom)
                            VALUES (?, ?, ?, 0)
                        """, (phrase["shortcut"], phrase["expansion"], phrase.get("category")))
                except Exception as e:
                    print(f"Warning: Could not load default phrases: {e}")

    def get_all_phrases(self) -> list[dict]:
        """Get all phrases."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, shortcut, expansion, category, is_custom, usage_count
                FROM phrases
                ORDER BY usage_count DESC, shortcut ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_phrase(self, shortcut: str) -> str | None:
        """Get expansion for shortcut (case-insensitive)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT expansion FROM phrases
                WHERE LOWER(shortcut) = LOWER(?)
            """, (shortcut,))
            row = cursor.fetchone()
            return row[0] if row else None

    def add_phrase(self, shortcut: str, expansion: str, category: str = None) -> int:
        """Add custom phrase. Returns phrase ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO phrases (shortcut, expansion, category, is_custom)
                VALUES (?, ?, ?, 1)
            """, (shortcut.strip(), expansion.strip(), category))
            return cursor.lastrowid

    def update_phrase(self, phrase_id: int, shortcut: str, expansion: str, category: str = None) -> bool:
        """Update a phrase."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE phrases
                SET shortcut = ?, expansion = ?, category = ?
                WHERE id = ?
            """, (shortcut.strip(), expansion.strip(), category, phrase_id))
            return cursor.rowcount > 0

    def delete_phrase(self, phrase_id: int) -> bool:
        """Delete a phrase (only custom phrases can be deleted)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM phrases
                WHERE id = ? AND is_custom = 1
            """, (phrase_id,))
            return cursor.rowcount > 0

    def increment_phrase_usage(self, shortcut: str):
        """Track usage of a phrase."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE phrases
                SET usage_count = usage_count + 1
                WHERE LOWER(shortcut) = LOWER(?)
            """, (shortcut,))

    def search_phrases(self, query: str) -> list[dict]:
        """Search phrases by shortcut or expansion."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT id, shortcut, expansion, category, is_custom, usage_count
                FROM phrases
                WHERE shortcut LIKE ? OR expansion LIKE ?
                ORDER BY usage_count DESC, shortcut ASC
            """, (search_term, search_term))
            return [dict(row) for row in cursor.fetchall()]

    # ============== DRUG DATABASE OPERATIONS ==============

    def search_drugs(self, query: str, limit: int = 10) -> list[dict]:
        """Fuzzy search drugs by generic or brand name.
        Returns sorted by usage_count (most used first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Case-insensitive LIKE search on generic name and brand names
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM drugs
                WHERE generic_name LIKE ? OR brand_names LIKE ?
                ORDER BY usage_count DESC, generic_name ASC
                LIMIT ?
            """, (search_term, search_term, limit))

            results = []
            for row in cursor.fetchall():
                drug = dict(row)
                # Parse JSON arrays
                if drug.get('brand_names'):
                    try:
                        drug['brand_names'] = json.loads(drug['brand_names'])
                    except:
                        drug['brand_names'] = []
                else:
                    drug['brand_names'] = []

                if drug.get('strengths'):
                    try:
                        drug['strengths'] = json.loads(drug['strengths'])
                    except:
                        drug['strengths'] = []
                else:
                    drug['strengths'] = []

                if drug.get('forms'):
                    try:
                        drug['forms'] = json.loads(drug['forms'])
                    except:
                        drug['forms'] = []
                else:
                    drug['forms'] = []

                results.append(drug)

            return results

    def add_custom_drug(self, generic_name: str, brand_names: list,
                        strengths: list, forms: list, category: str) -> int:
        """Add a custom drug to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drugs (generic_name, brand_names, strengths, forms, category, is_custom)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                generic_name,
                json.dumps(brand_names),
                json.dumps(strengths),
                json.dumps(forms),
                category
            ))
            return cursor.lastrowid

    def increment_drug_usage(self, drug_id: int):
        """Increment usage count when drug is prescribed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE drugs
                SET usage_count = usage_count + 1,
                    last_used = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), drug_id))

    def get_drug_by_id(self, drug_id: int) -> Optional[dict]:
        """Get drug details by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drugs WHERE id = ?", (drug_id,))
            row = cursor.fetchone()

            if row:
                drug = dict(row)
                # Parse JSON arrays
                if drug.get('brand_names'):
                    try:
                        drug['brand_names'] = json.loads(drug['brand_names'])
                    except:
                        drug['brand_names'] = []
                else:
                    drug['brand_names'] = []

                if drug.get('strengths'):
                    try:
                        drug['strengths'] = json.loads(drug['strengths'])
                    except:
                        drug['strengths'] = []
                else:
                    drug['strengths'] = []

                if drug.get('forms'):
                    try:
                        drug['forms'] = json.loads(drug['forms'])
                    except:
                        drug['forms'] = []
                else:
                    drug['forms'] = []

                return drug
            return None

    def seed_initial_drugs(self, drugs_data: list[dict]) -> int:
        """Seed database with initial drug data if empty.
        Returns number of drugs added.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if drugs already exist
            cursor.execute("SELECT COUNT(*) FROM drugs WHERE is_custom = 0")
            if cursor.fetchone()[0] > 0:
                return 0  # Already seeded

            # Insert drugs
            count = 0
            for drug in drugs_data:
                cursor.execute("""
                    INSERT INTO drugs (generic_name, brand_names, strengths, forms, category, is_custom)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (
                    drug.get('generic_name'),
                    json.dumps(drug.get('brand_names', [])),
                    json.dumps(drug.get('strengths', [])),
                    json.dumps(drug.get('forms', [])),
                    drug.get('category', '')
                ))
                count += 1

            return count

    # ============== VITALS OPERATIONS ==============

    def add_vitals(self, vitals_data: dict) -> int:
        """Add vitals record. Auto-calculate BMI if weight and height provided."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Auto-calculate BMI if weight and height are provided
            weight = vitals_data.get('weight')
            height = vitals_data.get('height')
            bmi = vitals_data.get('bmi')

            if weight and height and not bmi:
                # BMI = weight (kg) / (height (m))^2
                height_m = height / 100  # Convert cm to m
                bmi = round(weight / (height_m ** 2), 1)
                vitals_data['bmi'] = bmi

            cursor.execute("""
                INSERT INTO vitals (
                    patient_id, visit_id, recorded_at,
                    bp_systolic, bp_diastolic, pulse, temperature, spo2, respiratory_rate,
                    weight, height, bmi,
                    blood_sugar, sugar_type, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vitals_data.get('patient_id'),
                vitals_data.get('visit_id'),
                vitals_data.get('recorded_at'),
                vitals_data.get('bp_systolic'),
                vitals_data.get('bp_diastolic'),
                vitals_data.get('pulse'),
                vitals_data.get('temperature'),
                vitals_data.get('spo2'),
                vitals_data.get('respiratory_rate'),
                vitals_data.get('weight'),
                vitals_data.get('height'),
                vitals_data.get('bmi'),
                vitals_data.get('blood_sugar'),
                vitals_data.get('sugar_type'),
                vitals_data.get('notes')
            ))

            return cursor.lastrowid

    def get_patient_vitals(self, patient_id: int, limit: int = 20) -> list[dict]:
        """Get patient's vitals history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vitals
                WHERE patient_id = ?
                ORDER BY recorded_at DESC
                LIMIT ?
            """, (patient_id, limit))

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            return results

    def get_latest_vitals(self, patient_id: int) -> dict | None:
        """Get most recent vitals for patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vitals
                WHERE patient_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
            """, (patient_id,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_last_height(self, patient_id: int) -> float | None:
        """Get last recorded height (doesn't change often)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT height FROM vitals
                WHERE patient_id = ? AND height IS NOT NULL
                ORDER BY recorded_at DESC
                LIMIT 1
            """, (patient_id,))

            row = cursor.fetchone()
            if row:
                return row[0]
            return None

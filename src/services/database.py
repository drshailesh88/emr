"""SQLite database service for EMR data."""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
from contextlib import contextmanager

from ..models.schemas import (
    Patient, Visit, Investigation, Procedure,
    Doctor, Consultation, CareTeamMember, AuditLogEntry, PatientSnapshot,
    Medication
)


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

            # Create indexes for faster search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigations_patient ON investigations(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_procedures_patient ON procedures(patient_id)")

            # ============== NEW TABLES FOR HOSPITAL FEATURES ==============

            # Doctors/Staff table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialty TEXT,
                    department TEXT,
                    employee_id TEXT UNIQUE,
                    designation TEXT,
                    phone TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Consultations table (inter-department referrals)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    requesting_doctor_id INTEGER,
                    consulting_doctor_id INTEGER,
                    consulting_specialty TEXT NOT NULL,
                    consult_date DATE NOT NULL,
                    reason_for_referral TEXT,
                    clinical_question TEXT,
                    findings TEXT,
                    impression TEXT,
                    recommendations TEXT,
                    follow_up_needed BOOLEAN DEFAULT 0,
                    follow_up_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (requesting_doctor_id) REFERENCES doctors(id),
                    FOREIGN KEY (consulting_doctor_id) REFERENCES doctors(id)
                )
            """)

            # Care team table (who is involved in patient's care)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS care_team (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    specialty TEXT,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    added_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                    UNIQUE(patient_id, doctor_id, role)
                )
            """)

            # Audit log table (compliance requirement)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    user_role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id INTEGER,
                    patient_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    workstation_id TEXT
                )
            """)

            # Patient snapshot table (pre-computed summaries)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patient_snapshots (
                    patient_id INTEGER PRIMARY KEY,
                    uhid TEXT,
                    demographics TEXT,
                    active_problems_json TEXT,
                    current_medications_json TEXT,
                    allergies_json TEXT,
                    key_labs_json TEXT,
                    vitals_json TEXT,
                    blood_group TEXT,
                    code_status TEXT DEFAULT 'FULL',
                    on_anticoagulation BOOLEAN DEFAULT 0,
                    anticoag_drug TEXT,
                    last_visit_date DATE,
                    major_events_json TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Patient allergies table (critical safety data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patient_allergies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    allergen TEXT NOT NULL,
                    reaction TEXT,
                    severity TEXT,
                    verified BOOLEAN DEFAULT 0,
                    verified_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    UNIQUE(patient_id, allergen)
                )
            """)

            # Add phonetic column to patients for fuzzy search
            cursor.execute("""
                ALTER TABLE patients ADD COLUMN name_phonetic TEXT
            """) if not self._column_exists(cursor, 'patients', 'name_phonetic') else None

            # Add doctor_id to visits for authorship tracking
            cursor.execute("""
                ALTER TABLE visits ADD COLUMN doctor_id INTEGER REFERENCES doctors(id)
            """) if not self._column_exists(cursor, 'visits', 'doctor_id') else None

            # Add note_type to visits
            cursor.execute("""
                ALTER TABLE visits ADD COLUMN note_type TEXT DEFAULT 'progress'
            """) if not self._column_exists(cursor, 'visits', 'note_type') else None

            # Additional indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultations_specialty ON consultations(consulting_specialty)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_care_team_patient ON care_team(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_patient ON audit_log(patient_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_phonetic ON patients(name_phonetic)")

            # ============== FTS5 FULL-TEXT SEARCH ==============
            self._init_fts(cursor)

    def _column_exists(self, cursor, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns

    def _init_fts(self, cursor):
        """Initialize FTS5 full-text search tables."""
        # FTS5 for patient name/address search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS patients_fts USING fts5(
                name, address, content='patients', content_rowid='id',
                tokenize='porter unicode61'
            )
        """)

        # FTS5 for clinical content search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS clinical_fts USING fts5(
                patient_id UNINDEXED,
                content,
                doc_type,
                doc_date UNINDEXED,
                source_id UNINDEXED,
                tokenize='porter unicode61'
            )
        """)

        # Triggers to keep patients_fts in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS patients_fts_insert AFTER INSERT ON patients
            BEGIN
                INSERT INTO patients_fts(rowid, name, address)
                VALUES (NEW.id, NEW.name, COALESCE(NEW.address, ''));
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS patients_fts_update AFTER UPDATE ON patients
            BEGIN
                UPDATE patients_fts SET name = NEW.name, address = COALESCE(NEW.address, '')
                WHERE rowid = NEW.id;
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS patients_fts_delete AFTER DELETE ON patients
            BEGIN
                DELETE FROM patients_fts WHERE rowid = OLD.id;
            END
        """)

        # Triggers to keep clinical_fts in sync with visits
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS visits_fts_insert AFTER INSERT ON visits
            BEGIN
                INSERT INTO clinical_fts(patient_id, content, doc_type, doc_date, source_id)
                VALUES (
                    NEW.patient_id,
                    COALESCE(NEW.chief_complaint, '') || ' ' ||
                    COALESCE(NEW.clinical_notes, '') || ' ' ||
                    COALESCE(NEW.diagnosis, ''),
                    'visit',
                    NEW.visit_date,
                    NEW.id
                );
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS visits_fts_update AFTER UPDATE ON visits
            BEGIN
                DELETE FROM clinical_fts WHERE doc_type = 'visit' AND source_id = OLD.id;
                INSERT INTO clinical_fts(patient_id, content, doc_type, doc_date, source_id)
                VALUES (
                    NEW.patient_id,
                    COALESCE(NEW.chief_complaint, '') || ' ' ||
                    COALESCE(NEW.clinical_notes, '') || ' ' ||
                    COALESCE(NEW.diagnosis, ''),
                    'visit',
                    NEW.visit_date,
                    NEW.id
                );
            END
        """)

        # Triggers for investigations
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS investigations_fts_insert AFTER INSERT ON investigations
            BEGIN
                INSERT INTO clinical_fts(patient_id, content, doc_type, doc_date, source_id)
                VALUES (
                    NEW.patient_id,
                    NEW.test_name || ' ' || COALESCE(NEW.result, '') || ' ' || COALESCE(NEW.unit, ''),
                    'investigation',
                    NEW.test_date,
                    NEW.id
                );
            END
        """)

        # Triggers for procedures
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS procedures_fts_insert AFTER INSERT ON procedures
            BEGIN
                INSERT INTO clinical_fts(patient_id, content, doc_type, doc_date, source_id)
                VALUES (
                    NEW.patient_id,
                    NEW.procedure_name || ' ' || COALESCE(NEW.details, '') || ' ' || COALESCE(NEW.notes, ''),
                    'procedure',
                    NEW.procedure_date,
                    NEW.id
                );
            END
        """)

        # Triggers for consultations
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS consultations_fts_insert AFTER INSERT ON consultations
            BEGIN
                INSERT INTO clinical_fts(patient_id, content, doc_type, doc_date, source_id)
                VALUES (
                    NEW.patient_id,
                    NEW.consulting_specialty || ' ' ||
                    COALESCE(NEW.reason_for_referral, '') || ' ' ||
                    COALESCE(NEW.findings, '') || ' ' ||
                    COALESCE(NEW.impression, '') || ' ' ||
                    COALESCE(NEW.recommendations, ''),
                    'consultation',
                    NEW.consult_date,
                    NEW.id
                );
            END
        """)

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
            return cursor.rowcount > 0

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
            return cursor.rowcount > 0

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

    # ============== FTS5 SEARCH OPERATIONS ==============

    def fts_search_patients(self, query: str, limit: int = 20) -> List[Patient]:
        """Full-text search on patient names and addresses."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Escape special FTS characters
            safe_query = query.replace('"', '""')
            cursor.execute("""
                SELECT p.* FROM patients p
                JOIN patients_fts fts ON p.id = fts.rowid
                WHERE patients_fts MATCH ?
                ORDER BY bm25(patients_fts)
                LIMIT ?
            """, (f'"{safe_query}"*', limit))
            return [Patient(**dict(row)) for row in cursor.fetchall()]

    def fts_search_clinical(
        self,
        query: str,
        patient_id: Optional[int] = None,
        doc_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search on clinical content."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            safe_query = query.replace('"', '""')

            sql = """
                SELECT patient_id, content, doc_type, doc_date, source_id,
                       bm25(clinical_fts) as relevance
                FROM clinical_fts
                WHERE clinical_fts MATCH ?
            """
            params = [f'"{safe_query}"*']

            if patient_id:
                sql += " AND patient_id = ?"
                params.append(patient_id)

            if doc_type:
                sql += " AND doc_type = ?"
                params.append(doc_type)

            sql += " ORDER BY relevance LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    # ============== DOCTOR OPERATIONS ==============

    def add_doctor(self, doctor: Doctor) -> Doctor:
        """Add a new doctor."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO doctors (name, specialty, department, employee_id,
                                    designation, phone, email, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (doctor.name, doctor.specialty, doctor.department,
                  doctor.employee_id, doctor.designation, doctor.phone,
                  doctor.email, doctor.is_active))
            doctor.id = cursor.lastrowid
            return doctor

    def get_doctor(self, doctor_id: int) -> Optional[Doctor]:
        """Get doctor by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
            row = cursor.fetchone()
            if row:
                return Doctor(**dict(row))
            return None

    def get_doctors_by_specialty(self, specialty: str) -> List[Doctor]:
        """Get all doctors of a specialty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM doctors
                WHERE specialty = ? AND is_active = 1
                ORDER BY name
            """, (specialty,))
            return [Doctor(**dict(row)) for row in cursor.fetchall()]

    def get_all_doctors(self, active_only: bool = True) -> List[Doctor]:
        """Get all doctors."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM doctors"
            if active_only:
                sql += " WHERE is_active = 1"
            sql += " ORDER BY specialty, name"
            cursor.execute(sql)
            return [Doctor(**dict(row)) for row in cursor.fetchall()]

    # ============== CONSULTATION OPERATIONS ==============

    def add_consultation(self, consultation: Consultation) -> Consultation:
        """Add a new consultation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            consult_date = consultation.consult_date or date.today()
            cursor.execute("""
                INSERT INTO consultations (
                    patient_id, requesting_doctor_id, consulting_doctor_id,
                    consulting_specialty, consult_date, reason_for_referral,
                    clinical_question, findings, impression, recommendations,
                    follow_up_needed, follow_up_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                consultation.patient_id, consultation.requesting_doctor_id,
                consultation.consulting_doctor_id, consultation.consulting_specialty,
                consult_date, consultation.reason_for_referral,
                consultation.clinical_question, consultation.findings,
                consultation.impression, consultation.recommendations,
                consultation.follow_up_needed, consultation.follow_up_date
            ))
            consultation.id = cursor.lastrowid

            # Auto-add to care team
            self._add_to_care_team_on_consult(cursor, consultation)

            return consultation

    def _add_to_care_team_on_consult(self, cursor, consultation: Consultation):
        """Add consulting doctor to care team when consultation is created."""
        if consultation.consulting_doctor_id:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO care_team (
                        patient_id, doctor_id, role, specialty, start_date
                    ) VALUES (?, ?, 'consultant', ?, ?)
                """, (
                    consultation.patient_id,
                    consultation.consulting_doctor_id,
                    consultation.consulting_specialty,
                    consultation.consult_date or date.today()
                ))
            except Exception:
                pass  # Ignore if already exists

    def get_consultations_by_specialty(
        self,
        patient_id: int,
        specialty: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all consultations from a specific specialty for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.consult_date, c.reason_for_referral,
                    c.clinical_question, c.findings, c.impression,
                    c.recommendations, c.follow_up_needed, c.follow_up_date,
                    d.name as doctor_name, d.designation
                FROM consultations c
                LEFT JOIN doctors d ON c.consulting_doctor_id = d.id
                WHERE c.patient_id = ?
                  AND c.consulting_specialty = ?
                ORDER BY c.consult_date DESC
                LIMIT ?
            """, (patient_id, specialty, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_patient_consultations(
        self,
        patient_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all consultations for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.*,
                    d.name as doctor_name,
                    d.specialty,
                    d.designation
                FROM consultations c
                LEFT JOIN doctors d ON c.consulting_doctor_id = d.id
                WHERE c.patient_id = ?
                ORDER BY c.consult_date DESC
                LIMIT ?
            """, (patient_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ============== CARE TEAM OPERATIONS ==============

    def add_to_care_team(self, member: CareTeamMember) -> CareTeamMember:
        """Add a doctor to a patient's care team."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_date = member.start_date or date.today()
            cursor.execute("""
                INSERT OR REPLACE INTO care_team (
                    patient_id, doctor_id, role, specialty, start_date, added_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                member.patient_id, member.doctor_id, member.role,
                member.specialty, start_date, member.added_by
            ))
            member.id = cursor.lastrowid
            return member

    def get_patient_care_team(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all active care team members for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ct.*,
                    d.name as doctor_name,
                    d.designation
                FROM care_team ct
                JOIN doctors d ON ct.doctor_id = d.id
                WHERE ct.patient_id = ?
                  AND (ct.end_date IS NULL OR ct.end_date >= CURRENT_DATE)
                ORDER BY ct.role, ct.start_date
            """, (patient_id,))
            return [dict(row) for row in cursor.fetchall()]

    def is_in_care_team(self, doctor_id: int, patient_id: int) -> bool:
        """Check if a doctor is in a patient's care team."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM care_team
                WHERE patient_id = ? AND doctor_id = ?
                  AND (end_date IS NULL OR end_date >= CURRENT_DATE)
                LIMIT 1
            """, (patient_id, doctor_id))
            return cursor.fetchone() is not None

    # ============== ALLERGY OPERATIONS ==============

    def add_allergy(
        self,
        patient_id: int,
        allergen: str,
        reaction: str = "",
        severity: str = ""
    ) -> int:
        """Add an allergy for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO patient_allergies (
                    patient_id, allergen, reaction, severity
                ) VALUES (?, ?, ?, ?)
            """, (patient_id, allergen.upper(), reaction, severity))
            return cursor.lastrowid

    def get_patient_allergies(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all allergies for a patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM patient_allergies
                WHERE patient_id = ?
                ORDER BY allergen
            """, (patient_id,))
            return [dict(row) for row in cursor.fetchall()]

    def check_allergy(self, patient_id: int, drug_name: str) -> Optional[Dict[str, Any]]:
        """Check if patient is allergic to a drug."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check exact match and partial match
            cursor.execute("""
                SELECT * FROM patient_allergies
                WHERE patient_id = ?
                  AND (UPPER(allergen) = UPPER(?)
                       OR UPPER(?) LIKE '%' || UPPER(allergen) || '%'
                       OR UPPER(allergen) LIKE '%' || UPPER(?) || '%')
                LIMIT 1
            """, (patient_id, drug_name, drug_name, drug_name))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ============== PATIENT SNAPSHOT OPERATIONS ==============

    def save_patient_snapshot(self, snapshot: PatientSnapshot):
        """Save or update a patient's snapshot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO patient_snapshots (
                    patient_id, uhid, demographics,
                    active_problems_json, current_medications_json, allergies_json,
                    key_labs_json, vitals_json, blood_group, code_status,
                    on_anticoagulation, anticoag_drug, last_visit_date,
                    major_events_json, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.patient_id, snapshot.uhid, snapshot.demographics,
                json.dumps(snapshot.active_problems),
                json.dumps([m.model_dump() for m in snapshot.current_medications]),
                json.dumps(snapshot.allergies),
                json.dumps(snapshot.key_labs),
                json.dumps(snapshot.vitals),
                snapshot.blood_group, snapshot.code_status,
                snapshot.on_anticoagulation, snapshot.anticoag_drug,
                snapshot.last_visit_date,
                json.dumps(snapshot.major_events),
                datetime.now()
            ))

    def get_patient_snapshot(self, patient_id: int) -> Optional[PatientSnapshot]:
        """Get a patient's snapshot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM patient_snapshots WHERE patient_id = ?
            """, (patient_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                return PatientSnapshot(
                    patient_id=data['patient_id'],
                    uhid=data['uhid'] or '',
                    demographics=data['demographics'] or '',
                    active_problems=json.loads(data['active_problems_json'] or '[]'),
                    current_medications=[
                        Medication(**m) for m in json.loads(data['current_medications_json'] or '[]')
                    ],
                    allergies=json.loads(data['allergies_json'] or '[]'),
                    key_labs=json.loads(data['key_labs_json'] or '{}'),
                    vitals=json.loads(data['vitals_json'] or '{}'),
                    blood_group=data['blood_group'],
                    code_status=data['code_status'] or 'FULL',
                    on_anticoagulation=bool(data['on_anticoagulation']),
                    anticoag_drug=data['anticoag_drug'],
                    last_visit_date=data['last_visit_date'],
                    major_events=json.loads(data['major_events_json'] or '[]'),
                    last_updated=data['last_updated']
                )
            return None

    def compute_patient_snapshot(self, patient_id: int) -> PatientSnapshot:
        """Compute and save a patient's snapshot from their data."""
        patient = self.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        # Build demographics string
        demographics = patient.name
        if patient.age:
            demographics += f", {patient.age}"
        if patient.gender:
            demographics += patient.gender

        # Get allergies
        allergies = [a['allergen'] for a in self.get_patient_allergies(patient_id)]

        # Get active problems from recent visits
        visits = self.get_patient_visits(patient_id)
        active_problems = []
        seen_diagnoses = set()
        for visit in visits[:20]:  # Last 20 visits
            if visit.diagnosis and visit.diagnosis not in seen_diagnoses:
                active_problems.append(visit.diagnosis)
                seen_diagnoses.add(visit.diagnosis)
            if len(active_problems) >= 10:
                break

        # Get current medications from most recent visit
        current_medications = []
        for visit in visits:
            if visit.prescription_json:
                try:
                    rx = json.loads(visit.prescription_json)
                    if rx.get('medications'):
                        current_medications = [Medication(**m) for m in rx['medications']]
                        break
                except (json.JSONDecodeError, Exception):
                    pass

        # Get key labs (most recent of each important test)
        key_labs = {}
        key_test_names = ['creatinine', 'hba1c', 'hemoglobin', 'potassium', 'sodium']
        investigations = self.get_patient_investigations(patient_id)
        for inv in investigations:
            test_lower = inv.test_name.lower()
            for key_test in key_test_names:
                if key_test in test_lower and key_test not in key_labs:
                    key_labs[key_test] = {
                        'value': inv.result,
                        'unit': inv.unit,
                        'date': str(inv.test_date),
                        'abnormal': inv.is_abnormal
                    }

        # Get major procedures
        procedures = self.get_patient_procedures(patient_id)
        major_events = [
            f"{p.procedure_name} - {p.procedure_date}"
            for p in procedures[:5]
        ]

        # Check for anticoagulation
        anticoag_drugs = ['warfarin', 'rivaroxaban', 'apixaban', 'dabigatran', 'heparin', 'enoxaparin']
        on_anticoag = False
        anticoag_drug = None
        for med in current_medications:
            if any(ac in med.drug_name.lower() for ac in anticoag_drugs):
                on_anticoag = True
                anticoag_drug = med.drug_name
                break

        # Create snapshot
        snapshot = PatientSnapshot(
            patient_id=patient_id,
            uhid=patient.uhid or '',
            demographics=demographics,
            active_problems=active_problems,
            current_medications=current_medications,
            allergies=allergies,
            key_labs=key_labs,
            vitals={},  # Would need vitals table
            blood_group=None,  # Would need to extract from data
            code_status='FULL',
            on_anticoagulation=on_anticoag,
            anticoag_drug=anticoag_drug,
            last_visit_date=visits[0].visit_date if visits else None,
            major_events=major_events,
            last_updated=datetime.now()
        )

        # Save it
        self.save_patient_snapshot(snapshot)
        return snapshot

    # ============== AUDIT LOG OPERATIONS ==============

    def log_action(
        self,
        user_id: int,
        user_name: str,
        user_role: str,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        workstation_id: Optional[str] = None
    ):
        """Log an action to the audit trail."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log (
                    user_id, user_name, user_role, action, resource_type,
                    resource_id, patient_id, details, ip_address, workstation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, user_name, user_role, action, resource_type,
                resource_id, patient_id, details, ip_address, workstation_id
            ))

    def get_patient_audit_log(
        self,
        patient_id: int,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit log for a specific patient."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_log
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (patient_id, limit))
            return [AuditLogEntry(**dict(row)) for row in cursor.fetchall()]

    def get_user_audit_log(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit log for a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_log
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            return [AuditLogEntry(**dict(row)) for row in cursor.fetchall()]

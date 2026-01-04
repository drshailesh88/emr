"""Tests for the database service."""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta

from src.services.database import DatabaseService
from src.models.schemas import Patient, Visit, Investigation, Procedure


class TestDatabaseService:
    """Tests for DatabaseService initialization."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield db_path

    @pytest.fixture
    def db_service(self, temp_db):
        """Create database service with temp database."""
        return DatabaseService(db_path=str(temp_db))

    def test_database_initialization(self, db_service, temp_db):
        """Test database file is created."""
        assert temp_db.exists()

    def test_tables_created(self, db_service, temp_db):
        """Test all tables are created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert 'patients' in tables
        assert 'visits' in tables
        assert 'investigations' in tables
        assert 'procedures' in tables
        assert 'metadata' in tables

        conn.close()

    def test_indexes_created(self, db_service, temp_db):
        """Test indexes are created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]

        assert 'idx_patients_name' in indexes
        assert 'idx_visits_patient' in indexes

        conn.close()


class TestPatientOperations:
    """Tests for patient CRUD operations."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    def test_add_patient(self, db_service):
        """Test adding a patient."""
        patient = Patient(
            name="Test Patient",
            age=45,
            gender="M",
            phone="9876543210"
        )

        result = db_service.add_patient(patient)

        assert result.id is not None
        assert result.uhid is not None
        assert result.uhid.startswith("EMR-")
        assert result.name == "Test Patient"

    def test_add_patient_generates_uhid(self, db_service):
        """Test UHID is auto-generated."""
        patient1 = db_service.add_patient(Patient(name="Patient 1"))
        patient2 = db_service.add_patient(Patient(name="Patient 2"))

        assert patient1.uhid != patient2.uhid
        # UHID format: EMR-YYYY-NNNN
        assert "-" in patient1.uhid

    def test_get_patient(self, db_service):
        """Test retrieving a patient by ID."""
        original = db_service.add_patient(Patient(
            name="John Doe",
            age=50,
            gender="M"
        ))

        retrieved = db_service.get_patient(original.id)

        assert retrieved is not None
        assert retrieved.id == original.id
        assert retrieved.name == "John Doe"
        assert retrieved.age == 50

    def test_get_patient_not_found(self, db_service):
        """Test retrieving non-existent patient returns None."""
        result = db_service.get_patient(99999)
        assert result is None

    def test_get_all_patients(self, db_service):
        """Test retrieving all patients."""
        db_service.add_patient(Patient(name="Alice"))
        db_service.add_patient(Patient(name="Bob"))
        db_service.add_patient(Patient(name="Charlie"))

        patients = db_service.get_all_patients()

        assert len(patients) == 3
        # Should be sorted by name
        names = [p.name for p in patients]
        assert names == sorted(names)

    def test_search_patients_by_name(self, db_service):
        """Test searching patients by name."""
        db_service.add_patient(Patient(name="Ram Kumar"))
        db_service.add_patient(Patient(name="Shyam Sharma"))
        db_service.add_patient(Patient(name="Ram Prasad"))

        results = db_service.search_patients_basic("Ram")

        assert len(results) == 2
        assert all("Ram" in p.name for p in results)

    def test_search_patients_by_uhid(self, db_service):
        """Test searching patients by UHID."""
        patient = db_service.add_patient(Patient(name="Test"))

        results = db_service.search_patients_basic(patient.uhid)

        assert len(results) == 1
        assert results[0].uhid == patient.uhid

    def test_search_patients_case_insensitive(self, db_service):
        """Test search is case-insensitive."""
        db_service.add_patient(Patient(name="John Smith"))

        results1 = db_service.search_patients_basic("john")
        results2 = db_service.search_patients_basic("JOHN")

        assert len(results1) == 1
        assert len(results2) == 1

    def test_update_patient(self, db_service):
        """Test updating patient details."""
        patient = db_service.add_patient(Patient(
            name="Original Name",
            age=30
        ))

        patient.name = "Updated Name"
        patient.age = 31
        result = db_service.update_patient(patient)

        assert result is True

        # Verify update
        updated = db_service.get_patient(patient.id)
        assert updated.name == "Updated Name"
        assert updated.age == 31


class TestVisitOperations:
    """Tests for visit CRUD operations."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    @pytest.fixture
    def patient(self, db_service):
        """Create test patient."""
        return db_service.add_patient(Patient(name="Test Patient"))

    def test_add_visit(self, db_service, patient):
        """Test adding a visit."""
        visit = Visit(
            patient_id=patient.id,
            chief_complaint="Fever",
            clinical_notes="High temperature",
            diagnosis="Viral fever"
        )

        result = db_service.add_visit(visit)

        assert result.id is not None
        assert result.patient_id == patient.id

        # Verify visit was stored correctly
        visits = db_service.get_patient_visits(patient.id)
        assert len(visits) == 1
        assert visits[0].visit_date is not None

    def test_add_visit_with_prescription(self, db_service, patient):
        """Test adding visit with prescription JSON."""
        import json

        prescription = {
            "medications": [
                {"drug_name": "Paracetamol", "dose": "500mg"}
            ]
        }

        visit = Visit(
            patient_id=patient.id,
            diagnosis="Fever",
            prescription_json=json.dumps(prescription)
        )

        result = db_service.add_visit(visit)
        assert result.prescription_json is not None

    def test_get_patient_visits(self, db_service, patient):
        """Test retrieving all visits for a patient."""
        db_service.add_visit(Visit(patient_id=patient.id, chief_complaint="Visit 1"))
        db_service.add_visit(Visit(patient_id=patient.id, chief_complaint="Visit 2"))

        visits = db_service.get_patient_visits(patient.id)

        assert len(visits) == 2

    def test_visits_sorted_by_date(self, db_service, patient):
        """Test visits are sorted newest first."""
        db_service.add_visit(Visit(
            patient_id=patient.id,
            visit_date=date(2024, 1, 1),
            chief_complaint="Old visit"
        ))
        db_service.add_visit(Visit(
            patient_id=patient.id,
            visit_date=date(2024, 12, 1),
            chief_complaint="New visit"
        ))

        visits = db_service.get_patient_visits(patient.id)

        assert visits[0].chief_complaint == "New visit"
        assert visits[1].chief_complaint == "Old visit"

    def test_update_visit(self, db_service, patient):
        """Test updating a visit."""
        visit = db_service.add_visit(Visit(
            patient_id=patient.id,
            diagnosis="Initial diagnosis"
        ))

        visit.diagnosis = "Updated diagnosis"
        result = db_service.update_visit(visit)

        assert result is True

        # Verify
        visits = db_service.get_patient_visits(patient.id)
        assert visits[0].diagnosis == "Updated diagnosis"


class TestInvestigationOperations:
    """Tests for investigation operations."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    @pytest.fixture
    def patient(self, db_service):
        """Create test patient."""
        return db_service.add_patient(Patient(name="Test Patient"))

    def test_add_investigation(self, db_service, patient):
        """Test adding an investigation."""
        inv = Investigation(
            patient_id=patient.id,
            test_name="Creatinine",
            result="1.2",
            unit="mg/dL",
            reference_range="0.7-1.3"
        )

        result = db_service.add_investigation(inv)

        assert result.id is not None
        assert result.test_name == "Creatinine"

    def test_add_abnormal_investigation(self, db_service, patient):
        """Test adding abnormal investigation."""
        inv = Investigation(
            patient_id=patient.id,
            test_name="HbA1c",
            result="9.5",
            unit="%",
            is_abnormal=True
        )

        result = db_service.add_investigation(inv)
        assert result.is_abnormal is True

    def test_get_patient_investigations(self, db_service, patient):
        """Test retrieving patient investigations."""
        db_service.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="CBC"
        ))
        db_service.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="LFT"
        ))

        investigations = db_service.get_patient_investigations(patient.id)

        assert len(investigations) == 2


class TestProcedureOperations:
    """Tests for procedure operations."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    @pytest.fixture
    def patient(self, db_service):
        """Create test patient."""
        return db_service.add_patient(Patient(name="Test Patient"))

    def test_add_procedure(self, db_service, patient):
        """Test adding a procedure."""
        proc = Procedure(
            patient_id=patient.id,
            procedure_name="Angioplasty",
            details="Single vessel PCI",
            notes="Successful procedure"
        )

        result = db_service.add_procedure(proc)

        assert result.id is not None
        assert result.procedure_name == "Angioplasty"

    def test_get_patient_procedures(self, db_service, patient):
        """Test retrieving patient procedures."""
        db_service.add_procedure(Procedure(
            patient_id=patient.id,
            procedure_name="CABG"
        ))

        procedures = db_service.get_patient_procedures(patient.id)

        assert len(procedures) == 1
        assert procedures[0].procedure_name == "CABG"


class TestRAGHelpers:
    """Tests for RAG helper methods."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    @pytest.fixture
    def patient_with_data(self, db_service):
        """Create patient with visits, investigations, and procedures."""
        patient = db_service.add_patient(Patient(
            name="John Smith",
            age=65,
            gender="M"
        ))

        db_service.add_visit(Visit(
            patient_id=patient.id,
            diagnosis="Hypertension",
            clinical_notes="BP 160/100"
        ))

        db_service.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="Creatinine",
            result="1.8",
            is_abnormal=True
        ))

        db_service.add_procedure(Procedure(
            patient_id=patient.id,
            procedure_name="Angiography"
        ))

        return patient

    def test_get_patient_summary(self, db_service, patient_with_data):
        """Test patient summary for RAG."""
        summary = db_service.get_patient_summary(patient_with_data.id)

        assert "John Smith" in summary
        assert "65" in summary
        assert "Hypertension" in summary

    def test_get_patient_summary_not_found(self, db_service):
        """Test summary for non-existent patient."""
        summary = db_service.get_patient_summary(99999)
        assert summary == ""

    def test_get_patient_documents_for_rag(self, db_service, patient_with_data):
        """Test getting documents for RAG indexing."""
        docs = db_service.get_patient_documents_for_rag(patient_with_data.id)

        assert len(docs) == 3  # 1 visit + 1 investigation + 1 procedure

        # Check document structure
        for doc_id, content, metadata in docs:
            assert isinstance(doc_id, str)
            assert isinstance(content, str)
            assert isinstance(metadata, dict)
            assert 'type' in metadata
            assert 'patient_id' in metadata

    def test_rag_documents_include_visit(self, db_service, patient_with_data):
        """Test visit is included in RAG documents."""
        docs = db_service.get_patient_documents_for_rag(patient_with_data.id)

        visit_docs = [d for d in docs if d[2]['type'] == 'visit']
        assert len(visit_docs) == 1
        assert "Hypertension" in visit_docs[0][1]

    def test_rag_documents_include_investigation(self, db_service, patient_with_data):
        """Test investigation is included in RAG documents."""
        docs = db_service.get_patient_documents_for_rag(patient_with_data.id)

        inv_docs = [d for d in docs if d[2]['type'] == 'investigation']
        assert len(inv_docs) == 1
        assert "Creatinine" in inv_docs[0][1]
        assert "ABNORMAL" in inv_docs[0][1]


class TestChangeTracking:
    """Tests for change detection."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    def test_mark_data_changed(self, db_service):
        """Test marking data as changed."""
        # Add patient triggers mark_data_changed
        db_service.add_patient(Patient(name="Test"))

        # Check metadata was updated
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key = 'last_modified'")
            row = cursor.fetchone()

            assert row is not None
            assert row[0] is not None

    def test_has_changes_since(self, db_service):
        """Test detecting changes since timestamp."""
        old_time = datetime.now() - timedelta(hours=1)

        # Add data (marks as changed)
        db_service.add_patient(Patient(name="Test"))

        # Should detect changes
        assert db_service.has_changes_since(old_time) is True

    def test_no_changes_since(self, db_service):
        """Test no changes detected when none made."""
        # Add patient
        db_service.add_patient(Patient(name="Test"))

        # Future timestamp - no changes since then
        future_time = datetime.now() + timedelta(hours=1)

        assert db_service.has_changes_since(future_time) is False

    def test_has_changes_no_metadata(self, db_service):
        """Test change detection with no metadata but data exists."""
        # Manually insert patient without triggering mark_data_changed
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO patients (name, uhid) VALUES (?, ?)",
                ("Test", "EMR-TEST-0001")
            )
            # Clear metadata
            cursor.execute("DELETE FROM metadata WHERE key = 'last_modified'")

        # Should return True because patients exist
        assert db_service.has_changes_since(datetime.now()) is True
